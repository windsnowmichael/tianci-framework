#define _USE_MATH_DEFINES
#include <complex>
#include <iostream>
#include <cmath>
#include <cstring>
#include <iomanip>
#include <chrono>
using namespace std;

// ==================== 全局参数（严格对齐场方程） ====================
const int Nx = 256, Ny = 256;
const double dx = 1.0 / (Ny - 1), dy = 1.0 / (Ny - 1), Re = 100.0, U_LID = 1.0;
const double dt_init = 0.0002;
const int POISSON_ITER = 200;
const int FFT_CUTOFF = Nx / 8;

// ==================== 全局场变量（静态连续内存，性能最优） ====================
static double w[Ny][Nx] = {0}, s[Ny][Nx] = {0}, u[Ny][Nx] = {0}, v[Ny][Nx] = {0};
static double ckpt_w[Ny][Nx], ckpt_s[Ny][Nx], ckpt_u[Ny][Nx], ckpt_v[Ny][Nx];
static double dt = dt_init, last_Msigma = 0, lambda = 0.5;
static double k1[Ny][Nx], k2[Ny][Nx], k3[Ny][Nx], k4[Ny][Nx];
static double wt1[Ny][Nx], wt2[Ny][Nx], wt3[Ny][Nx]; // RK4专用中间态数组，无覆盖
static double r_poisson[Ny][Nx] = {0}, p_poisson[Ny][Nx] = {0}, Ap_poisson[Ny][Nx] = {0};

typedef complex<double> Complex;
const double PI = M_PI;

// ==================== 算子基类（统一接口） ====================
class Operator {
public:
    virtual void apply() = 0;
    virtual ~Operator() = default;
};

// ==================== 算子1：速度场更新 VEL ====================
class VelocityOp : public Operator {
public:
    double ul;
    VelocityOp(double lid_vel) : ul(lid_vel) {}
    
    void apply() override {
        for (int i = 1; i < Ny-1; i++)
            for (int j = 1; j < Nx-1; j++) {
                u[i][j] = (s[i+1][j] - s[i-1][j]) / (2 * dy);
                v[i][j] = -(s[i][j+1] - s[i][j-1]) / (2 * dx);
            }
        // 边界速度
        for (int j = 0; j < Nx; j++) {
            u[0][j] = 0; v[0][j] = 0;
            u[Ny-1][j] = ul; v[Ny-1][j] = 0;
        }
        for (int i = 0; i < Ny; i++) {
            u[i][0] = 0; v[i][0] = 0;
            u[i][Nx-1] = 0; v[i][Nx-1] = 0;
        }
    }
};

// ==================== 算子2：边界条件 BC ====================
class BoundaryOp : public Operator {
public:
    double ul, rho;
    BoundaryOp(double lid_vel, double rho_val) : ul(lid_vel), rho(rho_val) {}
    
    void apply() override {
        // 上下边界
        for (int j = 1; j < Nx-1; j++) {
            double nt = -3*(s[Ny-1][j]-s[Ny-2][j])/(dy*dy) - 0.5*w[Ny-2][j] + 3*ul/dy;
            w[Ny-1][j] = rho*nt + (1-rho)*w[Ny-1][j];
            double nb = -3*(s[1][j]-s[0][j])/(dy*dy) - 0.5*w[1][j];
            w[0][j] = rho*nb + (1-rho)*w[0][j];
        }
        // 左右边界
        for (int i = 1; i < Ny-1; i++) {
            w[i][0] = rho*(-3*(s[i][1]-s[i][0])/(dx*dx) - 0.5*w[i][1]) + (1-rho)*w[i][0];
            w[i][Nx-1] = rho*(-3*(s[i][Nx-1]-s[i][Nx-2])/(dx*dx) - 0.5*w[i][Nx-2]) + (1-rho)*w[i][Nx-1];
        }
    }
};

// ==================== 算子3：标准RK4时间步进（完全重写，无覆盖） ====================
class RK4Op : public Operator {
public:
    double stability; // 稳定性输出，无外部引用
    RK4Op() : stability(0.0) {}
    
    void apply() override {
        double nu = 1.0 / Re;
        double r = nu * dt / (dx*dx);
        if (r > 0.25) { stability = 0.96; success = false; return; }
        double ul_local = U_LID;
        
        // True Standard RK4: each substep Poisson + velocity update
        static double wt_save[Ny][Nx], s_sub[Ny][Nx], u_sub[Ny][Nx], v_sub[Ny][Nx];
        
        // Step 1: k1 = f(w, u, v)
        RHS(w, u, v, k1);
        for (int i = 1; i < Ny-1; i++)
            for (int j = 1; j < Nx-1; j++)
                wt_save[i][j] = w[i][j] + 0.5*dt*k1[i][j];
        // Substep 1: Poisson for wt_save, update s_sub -> u_sub,v_sub
        PoissonSub(wt_save, s_sub);
        VelocitySub(s_sub, u_sub, v_sub, ul_local);
        
        // Step 2: k2 = f(wt_save, u_sub, v_sub)
        RHS(wt_save, u_sub, v_sub, k2);
        for (int i = 1; i < Ny-1; i++)
            for (int j = 1; j < Nx-1; j++)
                wt_save[i][j] = w[i][j] + 0.5*dt*k2[i][j];
        PoissonSub(wt_save, s_sub);
        VelocitySub(s_sub, u_sub, v_sub, ul_local);
        
        // Step 3: k3 = f(wt_save, u_sub, v_sub)
        RHS(wt_save, u_sub, v_sub, k3);
        for (int i = 1; i < Ny-1; i++)
            for (int j = 1; j < Nx-1; j++)
                wt_save[i][j] = w[i][j] + dt*k3[i][j];
        PoissonSub(wt_save, s_sub);
        VelocitySub(s_sub, u_sub, v_sub, ul_local);
        
        // Step 4: k4 = f(wt_save, u_sub, v_sub)
        RHS(wt_save, u_sub, v_sub, k4);
        
        // 最终更新涡量
        for (int i = 1; i < Ny-1; i++)
            for (int j = 1; j < Nx-1; j++) {
                w[i][j] += dt/6*(k1[i][j] + 2*k2[i][j] + 2*k3[i][j] + k4[i][j]);
                if (fabs(w[i][j]) > 1e4 || isnan(w[i][j]) || isinf(w[i][j])) {
                    stability = 1.0;
                    success = false;
                    return;
                }
            }
        success = true;
    }
    
    bool is_success() const { return success; }

    void PoissonSub(double wi[Ny][Nx], double si[Ny][Nx]) {
        double dx2 = dx*dx, dy2 = dy*dy;
        memset(si, 0, sizeof(double)*Ny*Nx);
        double r_sub[Ny][Nx], p_sub[Ny][Nx], Ap_sub[Ny][Nx];
        double rsold = 0;
        for (int i = 1; i < Ny-1; i++)
            for (int j = 1; j < Nx-1; j++) {
                double lap = (si[i][j+1]+si[i][j-1])/dx2 + (si[i+1][j]+si[i-1][j])/dy2 - 2*(1/dx2+1/dy2)*si[i][j];
                r_sub[i][j] = -wi[i][j] - lap;
                p_sub[i][j] = r_sub[i][j];
                rsold += r_sub[i][j]*r_sub[i][j];
            }
        for (int it = 0; it < 30; it++) {
            for (int i = 1; i < Ny-1; i++)
                for (int j = 1; j < Nx-1; j++)
                    Ap_sub[i][j] = (p_sub[i][j+1]+p_sub[i][j-1])/dx2 + (p_sub[i+1][j]+p_sub[i-1][j])/dy2 - 2*(1/dx2+1/dy2)*p_sub[i][j];
            double pAp = 0;
            for (int i = 1; i < Ny-1; i++)
                for (int j = 1; j < Nx-1; j++) pAp += p_sub[i][j]*Ap_sub[i][j];
            if (fabs(pAp) < 1e-20) break;
            double alpha = rsold / pAp;
            double rsnew = 0;
            for (int i = 1; i < Ny-1; i++)
                for (int j = 1; j < Nx-1; j++) {
                    si[i][j] += alpha * p_sub[i][j];
                    r_sub[i][j] -= alpha * Ap_sub[i][j];
                    rsnew += r_sub[i][j]*r_sub[i][j];
                }
            if (sqrt(rsnew/(Nx*Ny)) < 1e-4) break;
            double beta = rsnew / rsold;
            for (int i = 1; i < Ny-1; i++)
                for (int j = 1; j < Nx-1; j++) p_sub[i][j] = r_sub[i][j] + beta*p_sub[i][j];
            rsold = rsnew;
        }
    }
    void VelocitySub(double si[Ny][Nx], double ui[Ny][Nx], double vi[Ny][Nx], double ul) {
        for (int i = 1; i < Ny-1; i++)
            for (int j = 1; j < Nx-1; j++) {
                ui[i][j] = (si[i+1][j] - si[i-1][j]) / (2 * dy);
                vi[i][j] = -(si[i][j+1] - si[i][j-1]) / (2 * dx);
            }
        for (int j = 0; j < Nx; j++) { ui[0][j]=0; vi[0][j]=0; ui[Ny-1][j]=ul; vi[Ny-1][j]=0; }
        for (int i = 0; i < Ny; i++) { ui[i][0]=0; vi[i][0]=0; ui[i][Nx-1]=0; vi[i][Nx-1]=0; }
    }

private:
    bool success = true;
    
    void RHS(double wi[Ny][Nx], double ui[Ny][Nx], double vi[Ny][Nx], double rhs[Ny][Nx]) {
        double nu = 1.0 / Re;
        for (int i = 1; i < Ny-1; i++)
            for (int j = 1; j < Nx-1; j++) {
                double cv = ui[i][j]*(wi[i][j+1]-wi[i][j-1])/(2*dx) + vi[i][j]*(wi[i+1][j]-wi[i-1][j])/(2*dy);
                double df = nu*((wi[i+1][j]-2*wi[i][j]+wi[i-1][j])/(dy*dy) + (wi[i][j+1]-2*wi[i][j]+wi[i][j-1])/(dx*dx));
                rhs[i][j] = -cv + df;
            }
    }
};

// ==================== 算子4：泊松CG求解 ====================
class PoissonCGOp : public Operator {
public:
    void apply() override {
        double dx2 = dx*dx, dy2 = dy*dy;
        double rsold = 0.0;
        
        // 初始残差
        for (int i = 1; i < Ny-1; i++)
            for (int j = 1; j < Nx-1; j++) {
                double lap = (s[i][j+1]+s[i][j-1])/dx2 + (s[i+1][j]+s[i-1][j])/dy2 - 2*(1/dx2+1/dy2)*s[i][j];
                r_poisson[i][j] = -w[i][j] - lap;
                p_poisson[i][j] = r_poisson[i][j];
                rsold += r_poisson[i][j] * r_poisson[i][j];
            }
        
        // CG迭代
        for (int it = 0; it < POISSON_ITER; it++) {
            // Ap = A*p
            for (int i = 1; i < Ny-1; i++)
                for (int j = 1; j < Nx-1; j++)
                    Ap_poisson[i][j] = (p_poisson[i][j+1]+p_poisson[i][j-1])/dx2 + (p_poisson[i+1][j]+p_poisson[i-1][j])/dy2 - 2*(1/dx2+1/dy2)*p_poisson[i][j];
            
            double pAp = 0.0;
            for (int i = 1; i < Ny-1; i++)
                for (int j = 1; j < Nx-1; j++)
                    pAp += p_poisson[i][j] * Ap_poisson[i][j];
            
            if (fabs(pAp) < 1e-20) break;
            
            double alpha = rsold / pAp;
            double rsnew = 0.0;
            
            // 更新s和r
            for (int i = 1; i < Ny-1; i++)
                for (int j = 1; j < Nx-1; j++) {
                    s[i][j] += alpha * p_poisson[i][j];
                    r_poisson[i][j] -= alpha * Ap_poisson[i][j];
                    rsnew += r_poisson[i][j] * r_poisson[i][j];
                }
            
            if (sqrt(rsnew/(Nx*Ny)) < 1e-6) break;
            
            double beta = rsnew / rsold;
            for (int i = 1; i < Ny-1; i++)
                for (int j = 1; j < Nx-1; j++)
                    p_poisson[i][j] = r_poisson[i][j] + beta * p_poisson[i][j];
            
            rsold = rsnew;
        }
    }
};

// ==================== 算子5：FFT谱分析 Σ（静态数组，无new/delete） ====================
class SpectralOp : public Operator {
public:
    double value;
    static Complex fft_data[Nx*Ny]; // 静态数组，只分配一次
    
    void apply() override {
        for (int i = 0; i < Ny; i++)
            for (int j = 0; j < Nx; j++)
                fft_data[i*Nx+j] = Complex(w[i][j], 0);
        
        fft2d(fft_data, Nx, Ny);
        
        double total_power = 0, high_power = 0;
        for (int i = 0; i < Ny; i++) {
            for (int j = 0; j < Nx; j++) {
                int kx = (j < Nx/2 ? j : j - Nx);
                int ky = (i < Ny/2 ? i : i - Ny);
                double freq = sqrt(kx*kx + ky*ky);
                double power = norm(fft_data[i*Nx+j]);
                total_power += power;
                if (freq > FFT_CUTOFF) high_power += power;
            }
        }
        
        value = total_power > 0 ? high_power / total_power : 0;
    }

private:
    void fft1d(Complex* x, int n) {
        for (int i = 1, j = 0; i < n; i++) {
            int bit = n >> 1;
            for (; j & bit; bit >>= 1) j ^= bit;
            j ^= bit;
            if (i < j) swap(x[i], x[j]);
        }
        for (int len = 2; len <= n; len <<= 1) {
            double ang = 2*PI/len;
            Complex wlen(cos(ang), sin(ang));
            for (int i = 0; i < n; i += len) {
                Complex w(1);
                for (int j = 0; j < len/2; j++) {
                    Complex u = x[i+j], v = x[i+j+len/2] * w;
                    x[i+j] = u + v;
                    x[i+j+len/2] = u - v;
                    w *= wlen;
                }
            }
        }
    }
    
    void fft2d(Complex* data, int Nx, int Ny) {
        static Complex row[256]; // 静态行数组
        for (int i = 0; i < Ny; i++) {
            for (int j = 0; j < Nx; j++) row[j] = data[i*Nx+j];
            fft1d(row, Nx);
            for (int j = 0; j < Nx; j++) data[i*Nx+j] = row[j];
        }
        for (int j = 0; j < Nx; j++) {
            for (int i = 0; i < Ny; i++) row[i] = data[i*Nx+j];
            fft1d(row, Ny);
            for (int i = 0; i < Ny; i++) data[i*Nx+j] = row[i];
        }
    }
};
Complex SpectralOp::fft_data[Nx*Ny]; // 静态数组定义

// ==================== 算子6：V1监控（修复初始化bug） ====================
class MonitorV1Op : public Operator {
public:
    double value;
    static double prev_w[Ny][Nx];
    
    void init(double init_w[Ny][Nx]) {
        memcpy(prev_w, init_w, sizeof(prev_w));
    }
    
    void apply() override {
        double dev = 0; int cnt = 0;
        for (int i = 1; i < Ny-1; i++)
            for (int j = 1; j < Nx-1; j++) {
                dev += fabs(w[i][j] - prev_w[i][j]);
                cnt++;
                prev_w[i][j] = w[i][j];
            }
        value = cnt > 0 ? dev / cnt : 0;
    }
};
double MonitorV1Op::prev_w[Ny][Nx] = {0};

// ==================== 算子7：V2监控 ====================
class MonitorV2Op : public Operator {
public:
    double value;
    void apply() override {
        double s2 = 0, w2 = 0; int cnt = 0;
        double dx2 = dx*dx, dy2 = dy*dy;
        for (int i = 2; i < Ny-2; i++)
            for (int j = 2; j < Nx-2; j++) {
                double hxx = (w[i][j+1]-2*w[i][j]+w[i][j-1])/dx2;
                double hyy = (w[i+1][j]-2*w[i][j]+w[i-1][j])/dy2;
                double hxy = (w[i+1][j+1]-w[i+1][j-1]-w[i-1][j+1]+w[i-1][j-1])/(4*dx*dy);
                if (fabs(hxx) < 1e3 && fabs(hyy) < 1e3 && fabs(hxy) < 1e3) {
                    s2 += hxx*hxx + hyy*hyy + 2*hxy*hxy;
                    w2 += w[i][j] * w[i][j];
                    cnt++;
                }
            }
        value = (cnt > 0 && w2 > 1e-10) ? sqrt(s2 / (w2 + 1e-10)) : 0;
    }
};

// ==================== 算子8：Ι拓扑监控 ====================
class MonitorIOTAOp : public Operator {
public:
    double value;
    void apply() override {
        int sign_change = 0;
        for (int i = 1; i < Ny-1; i++) {
            for (int j = 1; j < Nx-2; j++)
                if (w[i][j] * w[i][j+1] < 0) sign_change++;
            for (int j = 1; j < Nx-1; j++)
                if (w[i][j] * w[i+1][j] < 0) sign_change++;
        }
        value = (double)sign_change / (Nx * Ny);
    }
};

// ==================== 算子9：MSigma监控 ====================
class MSigmaOp : public Operator {
public:
    double value;
    void apply() override {
        double sum = 0, sum2 = 0; int cnt = 0;
        for (int i = 1; i < Ny-1; i++)
            for (int j = 1; j < Nx-1; j++) {
                sum += w[i][j];
                sum2 += w[i][j] * w[i][j];
                cnt++;
            }
        if (cnt == 0) { value = 0; return; }
        double sig = sqrt(sum2/cnt - (sum/cnt)*(sum/cnt));
        value = fabs(sig - last_Msigma);
        last_Msigma = sig;
    }
};

// ==================== 算子10：RHO边界松弛系数 ====================
class RHOOp : public Operator {
public:
    double value;
    void apply() override {
        double mx = 0;
        for (int i = 1; i < Ny-1; i++)
            for (int j = 1; j < Nx-1; j++) {
                double gx = fabs(w[i][j+1]-w[i][j-1])/(2*dx);
                double gy = fabs(w[i+1][j]-w[i-1][j])/(2*dy);
                mx = fmax(mx, sqrt(gx*gx + gy*gy));
            }
        value = 1.0 / (1.0 + mx * 0.1);
    }
};

// ==================== 算子11：Lambda更新 ====================
class LambdaUpdateOp : public Operator {
public:
    double sp;
    LambdaUpdateOp(double spectral) : sp(spectral) {}
    void apply() override {
        lambda = (sp > 0.5 ? 0.8 : (sp > 0.3 ? 0.5 : 0.3));
    }
};

// ==================== 算子12：TAU时间步调整 ====================
class TauOp : public Operator {
public:
    double lv;
    TauOp(double lambda_val) : lv(lambda_val) {}
    void apply() override {
        dt *= (1 - lv);
        if (dt < 1e-8) dt = 1e-8;
    }
};

// ==================== 算子13：XI状态保存/回滚 ====================
class XiSaveOp : public Operator {
public:
    void apply() override {
        memcpy(ckpt_w, w, sizeof(w));
        memcpy(ckpt_s, s, sizeof(s));
        memcpy(ckpt_u, u, sizeof(u));
        memcpy(ckpt_v, v, sizeof(v));
    }
};

class XiRollbackOp : public Operator {
public:
    void apply() override {
        memcpy(w, ckpt_w, sizeof(w));
        memcpy(s, ckpt_s, sizeof(s));
        memcpy(u, ckpt_u, sizeof(u));
        memcpy(v, ckpt_v, sizeof(v));
    }
};

// ==================== 算子14：Φ公理门控 ====================
class PhiGateOp : public Operator {
public:
    double v1, v2, sp, io;
    bool converged;
    
    int st;
    PhiGateOp(double v1_val, double v2_val, double sp_val, double io_val, int step_val)
        : v1(v1_val), v2(v2_val), sp(sp_val), io(io_val), st(step_val), converged(false) {}
    
    void apply() override {
        static double u_mid_prev = 0;
        static int converged_counter = 0;
        double du = (u_mid_prev != 0) ? fabs(v1 - u_mid_prev) : 1.0;
        u_mid_prev = v1;
        if (st > 20000 && v1 < 0.01 && io < 0.02 && du < 1e-4) {
            converged_counter++;
        } else if (du >= 1e-4) {
            converged_counter = 0;
        }
        converged = (converged_counter > 20);
    }
    
    bool is_converged() const { return converged; }
};

// ==================== 算子15：天赐范式自洽验证 ====================
class ResultVerifyOp : public Operator {
public:
    double u_mid_final, u_min, w_max, ke;
    void apply() override {
        u_mid_final = u[Ny/2][Nx/2];
        u_min = 1e10;
        w_max = 0;
        ke = 0;
        for (int i = 1; i < Ny-1; i++) {
            double ui = (s[i+1][Nx/2] - s[i-1][Nx/2]) / (2 * dy);
            u_min = fmin(u_min, ui);
            for (int j = 0; j < Nx; j++) {
                w_max = fmax(w_max, fabs(w[i][j]));
                ke += u[i][j]*u[i][j] + v[i][j]*v[i][j];
            }
        }
        ke *= 0.5 / (Nx * Ny);
    }
};

// ==================== 初始化算子 ====================
class InitFieldOp : public Operator {
public:
    void apply() override {
        for (int i = Ny/4; i < 3*Ny/4; i++)
            for (int j = Nx/4; j < 3*Nx/4; j++)
                w[i][j] = 0.1 * sin(M_PI*(i-Ny/4)/(Ny/2.0)) * sin(M_PI*(j-Nx/4)/(Nx/2.0));
        double dx2 = dx*dx, dy2 = dy*dy;
        for (int iter = 0; iter < 200; iter++) {
            for (int i = 1; i < Ny-1; i++)
                for (int j = 1; j < Nx-1; j++)
                    s[i][j] = 0.25*((s[i][j+1]+s[i][j-1])*dx2 + (s[i+1][j]+s[i-1][j])*dy2 + w[i][j]*dx2*dy2) / (dx2+dy2);
        }
        for (int i = 1; i < Ny-1; i++)
            for (int j = 1; j < Nx-1; j++) {
                u[i][j] = (s[i+1][j] - s[i-1][j]) / (2 * dy);
                v[i][j] = -(s[i][j+1] - s[i][j-1]) / (2 * dx);
            }
    }
};

// ==================== 主程序：算子共振流水线 ====================
int main() {
    auto start_total = chrono::high_resolution_clock::now();
    
    cout << "============================================================" << endl;
    cout << "   TianCi Paradigm v11.0 | 256x256 DPSK Final" << endl;
    cout << "   Standard RK4 | Phi-Gate | All Bugs Fixed" << endl;
    cout << "============================================================" << endl;
    
    // 初始化
    InitFieldOp init_op; init_op.apply();
    XiSaveOp xi_save_op; xi_save_op.apply();
    
    // V1 Init: sync prev_w after w init
    MonitorV1Op v1_op;
    v1_op.init(w);
    
    int rb = 0, step = 0;
    const int max_step = 80000;
    
    // 算子实例化（只构造一次，避免循环内重复构造）
    RHOOp rho_op;
    RK4Op rk4_op; // 无参数构造，稳定性存在成员变量里
    PoissonCGOp poisson_op;
    SpectralOp spectral_op;
    MonitorV2Op v2_op;
    MonitorIOTAOp iota_op;
    MSigmaOp msigma_op;
    XiRollbackOp xi_rollback_op;
    
    while (step < max_step) {
        double ul = (step >= 2000 ? 1.0 : 0.5*(1 - cos(M_PI*step/2000.0)));
        
        // ==================== 算子共振顺序（严格对齐场方程） ====================
        VelocityOp vel_op(ul); vel_op.apply();       // 1. VEL
        rho_op.apply();                               // 2. 计算RHO
        BoundaryOp bc_op(ul, rho_op.value); bc_op.apply(); // 3. BC
        
        rk4_op.apply();                               // 4. 标准RK4
        
        if (!rk4_op.is_success()) {
            if (++rb > 20) {
                cout << "[TAU-PHI] ABORT at Step " << step << endl;
                break;
            }
            // RK4 stability from member var
            double lv = (rk4_op.stability > 0.9 ? 0.8 : (rk4_op.stability > 0.7 ? 0.5 : 0.3));
            TauOp tau_op(lv); tau_op.apply();         // 5. TAU熔断
            xi_rollback_op.apply();                    // 6. XI回滚
            continue;
        } else {
            rb = 0;
            step++;
        }
        
        poisson_op.apply();
        vel_op.apply();
        
        // ==================== 监控算子 ====================
        msigma_op.apply();
        v1_op.apply();
        v2_op.apply();
        spectral_op.apply();
        iota_op.apply();
        
// Sigma: monitor only物理映射：高频能量占比超阈值时降dt
                LambdaUpdateOp lambda_op(spectral_op.value); lambda_op.apply();        
        // ==================== 输出与收敛判决 ====================
        // step>10 guard against false convergence
        if (step % 500 == 0 && step > 10) {
            cout << "[OPs] " << setw(5) << step
                 << " | MSigma=" << fixed << setprecision(6) << msigma_op.value
                 << " | V1=" << setprecision(4) << v1_op.value
                 << " | V2=" << setprecision(4) << v2_op.value
                 << " | Sigma=" << setprecision(4) << spectral_op.value
                 << " | Iota=" << setprecision(4) << iota_op.value
                 << " | u_mid=" << setprecision(6) << u[Ny/2][Nx/2] << endl;
            
            PhiGateOp phi_op(v1_op.value, v2_op.value, spectral_op.value, iota_op.value, step);
            phi_op.apply();
            if (phi_op.is_converged()) {
                cout << "\n[PHI] Converged at Step " << step << endl;
                break;
            }
        }
    }
    
    // ==================== 结果验证 ====================
    ResultVerifyOp verify_op; verify_op.apply();
    auto end_total = chrono::high_resolution_clock::now();
    auto dur_total = chrono::duration_cast<chrono::seconds>(end_total - start_total).count();
    
    cout << "\n============================================================" << endl;
    cout << "   Done | Time: " << dur_total << "s" << endl;
    cout << "============================================================" << endl;
    cout << "u_mid_final: " << verify_op.u_mid_final << endl;
    cout << "U_min: " << verify_op.u_min << endl;
    cout << "W_max: " << verify_op.w_max << endl;
    cout << "Kinetic Energy: " << verify_op.ke << endl;
    cout << "============================================================" << endl;
    
    system("pause");
    return 0;
}