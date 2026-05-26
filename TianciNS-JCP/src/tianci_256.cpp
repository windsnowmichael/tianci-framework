// tianci_256.cpp - TianCi Paradigm 256x256 Lid-Driven Cavity Flow Optimized Version
// Optimizations: lambda_update_sor every 200 steps / SOR adaptive iteration / C² correction / u output correction
#include <iostream>
#include <cmath>
#include <cstring>
#include <vector>
#include <fstream>
#include <algorithm>
#include <iomanip>
using namespace std;

const int Nx = 256, Ny = 256;
const double dx = 1.0/(Ny-1), dy = 1.0/(Ny-1);
const double dt = 0.0005, Re = 100.0;
const int TOTAL_STEPS = 100000;
const int SAVE_EVERY = 200;
const double OMEGA_BC_RELAX = 0.5;
const double delta_max_change = 5.0;

double omega[Ny][Nx] = {0.0}, psi[Ny][Nx] = {0.0};
double u_f[Ny][Nx] = {0.0}, v_f[Ny][Nx] = {0.0};
double ckpt_omega[Ny][Nx], ckpt_psi[Ny][Nx], ckpt_u[Ny][Nx], ckpt_v[Ny][Nx];

double sigma_sor_beta = 1.5;
double last_sigma = 0.0;
int sor_max_iter = 200;  // SOR adaptive iteration count

void tridiag(const double* a, const double* b, const double* c,
             const double* d, double* x, int n) {
    vector<double> cp(n), dp(n);
    cp[0] = c[0] / b[0]; dp[0] = d[0] / b[0];
    for (int i = 1; i < n; ++i) {
        double den = b[i] - a[i] * cp[i-1];
        cp[i] = c[i] / den;
        dp[i] = (d[i] - a[i] * dp[i-1]) / den;
    }
    x[n-1] = dp[n-1];
    for (int i = n-2; i >= 0; --i) x[i] = dp[i] - cp[i] * x[i+1];
}

void adi_step() {
    double nu = 1.0/Re, r = nu*dt/(dx*dx);
    double a_coef = -r, b_coef = 1.0+2.0*r, c_coef = -r;
    double half_dt = 0.5*dt;
    double star[Ny][Nx]; memcpy(star, omega, sizeof(omega));
    // X sweep
    for (int i = 1; i < Ny-1; ++i) {
        int n = Nx-2;
        vector<double> a(n, a_coef), b(n, b_coef), c(n, c_coef), rhs(n), sol(n);
        for (int j = 1; j < Nx-1; ++j) {
            int idx = j-1;
            double conv = u_f[i][j]*(omega[i][j+1]-omega[i][j-1])/(2*dx)
                        + v_f[i][j]*(omega[i+1][j]-omega[i-1][j])/(2*dy);
            rhs[idx] = omega[i][j] + half_dt*( -conv + nu*(omega[i+1][j]-2*omega[i][j]+omega[i-1][j])/(dy*dy) );
        }
        tridiag(a.data(), b.data(), c.data(), rhs.data(), sol.data(), n);
        for (int j = 1; j < Nx-1; ++j) star[i][j] = sol[j-1];
    }
    // Y sweep
    double result[Ny][Nx]; memcpy(result, star, sizeof(star));
    for (int j = 1; j < Nx-1; ++j) {
        int n = Ny-2;
        vector<double> a(n, a_coef), b(n, b_coef), c(n, c_coef), rhs(n), sol(n);
        for (int i = 1; i < Ny-1; ++i) {
            int idx = i-1;
            double conv = u_f[i][j]*(star[i][j+1]-star[i][j-1])/(2*dx)
                        + v_f[i][j]*(star[i+1][j]-star[i-1][j])/(2*dy);
            rhs[idx] = star[i][j] + half_dt*( -conv + nu*(star[i][j+1]-2*star[i][j]+star[i][j-1])/(dx*dx) );
        }
        tridiag(a.data(), b.data(), c.data(), rhs.data(), sol.data(), n);
        for (int i = 1; i < Ny-1; ++i) result[i][j] = sol[i-1];
    }
    // δ limiter
    for (int i = 1; i < Ny-1; ++i)
        for (int j = 1; j < Nx-1; ++j) {
            double diff = result[i][j] - omega[i][j];
            if (abs(diff) > delta_max_change)
                diff = (diff > 0 ? delta_max_change : -delta_max_change);
            omega[i][j] += diff;
        }
}

void poisson_sor(double tol = 1e-5) {
    double dx2 = dx*dx, dy2 = dy*dy;
    double beta = sigma_sor_beta;
    for (int iter = 0; iter < sor_max_iter; ++iter) {
        double err = 0.0;
        for (int i = 1; i < Ny-1; ++i)
            for (int j = 1; j < Nx-1; ++j) {
                double old = psi[i][j];
                double new_val = (1-beta)*old + beta*(
                    (psi[i][j+1]+psi[i][j-1])*dy2 +
                    (psi[i+1][j]+psi[i-1][j])*dx2 +
                    omega[i][j]*dx2*dy2
                ) / (2*(dx2+dy2));
                psi[i][j] = new_val;
                err += abs(new_val - old);
            }
        if (err/(Nx*Ny) < tol) break;
    }
}

void update_vort_bc(double u_lid) {
    double relax = OMEGA_BC_RELAX;
    for (int j = 1; j < Nx-1; ++j) {
        double nt = -2*(psi[Ny-1][j]-psi[Ny-2][j])/(dy*dy) - 2*u_lid/dy;
        omega[Ny-1][j] = relax*nt + (1-relax)*omega[Ny-1][j];
        double nb = -2*(psi[1][j]-psi[0][j])/(dy*dy);
        omega[0][j] = relax*nb + (1-relax)*omega[0][j];
    }
    for (int i = 1; i < Ny-1; ++i) {
        double nl = -2*(psi[i][1]-psi[i][0])/(dx*dx);
        omega[i][0] = relax*nl + (1-relax)*omega[i][0];
        double nr = -2*(psi[i][Nx-1]-psi[i][Nx-2])/(dx*dx);
        omega[i][Nx-1] = relax*nr + (1-relax)*omega[i][Nx-1];
    }
}

void update_vel(double u_lid) {
    for (int i = 1; i < Ny-1; ++i)
        for (int j = 1; j < Nx-1; ++j) {
            u_f[i][j] =  (psi[i+1][j]-psi[i-1][j])/(2*dy);
            v_f[i][j] = -(psi[i][j+1]-psi[i][j-1])/(2*dx);
        }
    for (int j = 0; j < Nx; ++j) {
        u_f[0][j] = 0.0; v_f[0][j] = 0.0;
        u_f[Ny-1][j] = u_lid; v_f[Ny-1][j] = 0.0;
    }
    for (int i = 0; i < Ny; ++i) {
        u_f[i][0] = 0.0; v_f[i][0] = 0.0;
        u_f[i][Nx-1] = 0.0; v_f[i][Nx-1] = 0.0;
    }
}

// ========== Λ Alert ==========
bool lambda_alert() {
    for (int i = 0; i < Ny; ++i)
        for (int j = 0; j < Nx; ++j) {
            if (isnan(omega[i][j]) || isnan(psi[i][j])) return true;
            if (isinf(omega[i][j]) || isinf(psi[i][j])) return true;
            if (abs(omega[i][j]) > 1e6) return true;
        }
    return false;
}

// ========== Ξ Rollback ==========
void save_ckpt() {
    memcpy(ckpt_omega, omega, sizeof(omega));
    memcpy(ckpt_psi, psi, sizeof(psi));
    memcpy(ckpt_u, u_f, sizeof(u_f));
    memcpy(ckpt_v, v_f, sizeof(v_f));
}
void xi_rollback() {
    memcpy(omega, ckpt_omega, sizeof(omega));
    memcpy(psi, ckpt_psi, sizeof(psi));
    memcpy(u_f, ckpt_u, sizeof(u_f));
    memcpy(v_f, ckpt_v, sizeof(v_f));
}

// ========== ρ Ramp-Up ==========
double rho_ramp(int step) {
    if (step >= 2000) return 1.0;
    return 0.5 * (1.0 - cos(M_PI * step / 2000.0));
}

// ========== λ Dynamic SOR (Called only every 200 steps) ==========
void lambda_update_sor() {
    double max_grad = 0.0;
    for (int i = 1; i < Ny-1; ++i)
        for (int j = 1; j < Nx-1; ++j) {
            double gx = abs(psi[i][j+1]-psi[i][j-1])/(2*dx);
            double gy = abs(psi[i+1][j]-psi[i-1][j])/(2*dy);
            max_grad = max(max_grad, sqrt(gx*gx+gy*gy));
        }
    if (max_grad > 0.15) sigma_sor_beta = 1.7;
    else if (max_grad < 0.02) sigma_sor_beta = 1.3;
    else sigma_sor_beta = 1.5;
}

// ========== MΣ ==========
double compute_Msigma() {
    double sum = 0.0, sum2 = 0.0; int count = 0;
    for (int i = 1; i < Ny-1; ++i)
        for (int j = 1; j < Nx-1; ++j) {
            sum += omega[i][j]; sum2 += omega[i][j]*omega[i][j]; ++count;
        }
    double mean = sum/count;
    double sigma_now = sqrt(sum2/count - mean*mean);
    double Msig = abs(sigma_now - last_sigma);
    last_sigma = sigma_now;
    return Msig;
}

// ========== Con ==========
double check_divergence() {
    double max_div = 0.0;
    for (int i = 1; i < Ny-1; ++i)
        for (int j = 1; j < Nx-1; ++j) {
            double div = (u_f[i][j+1]-u_f[i][j-1])/(2*dx) + (v_f[i+1][j]-v_f[i-1][j])/(2*dy);
            if (abs(div) > max_div) max_div = abs(div);
        }
    return max_div;
}

// ========== C² (Corrected: Frobenius Norm Squared of Hessian) ==========
double compute_C2() {
    double c2_sum = 0.0;
    for (int i = 2; i < Ny-2; ++i)
        for (int j = 2; j < Nx-2; ++j) {
            double hxx = (omega[i][j+1]-2*omega[i][j]+omega[i][j-1])/(dx*dx);
            double hyy = (omega[i+1][j]-2*omega[i][j]+omega[i-1][j])/(dy*dy);
            double hxy = (omega[i+1][j+1]-omega[i+1][j-1]-omega[i-1][j+1]+omega[i-1][j-1])/(4*dx*dy);
            c2_sum += hxx*hxx + hyy*hyy + 2*hxy*hxy;
        }
    return c2_sum/(Nx*Ny);
}

// ========== Main Program ==========
int main() {
    for (int j = 0; j < Nx; ++j) u_f[Ny-1][j] = 0.0;
    save_ckpt();

    ofstream logfile("operator_log.txt");
    logfile << "# step lid M_Sigma Con_maxDiv C2\n" << flush;

    cout << "Tianci Optimized 6-op 256x256 start." << endl;
    for (int step = 0; step < TOTAL_STEPS; ++step) {
        double u_lid = rho_ramp(step);
        for (int j = 0; j < Nx; ++j) u_f[Ny-1][j] = u_lid;

        update_vort_bc(u_lid);
        adi_step();

        // First 5000 steps use 200 SOR iterations, then gradually reduce
        if (step < 5000) sor_max_iter = 200;
        else if (step < 20000) sor_max_iter = 100;
        else sor_max_iter = 50;

        poisson_sor(1e-5);
        update_vel(u_lid);

        if (lambda_alert()) {
            cerr << "[Lambda] step " << step << " rollback\n";
            xi_rollback(); --step;
            if (step < -1) break;
            continue;
        }

        // λ operator changed to call every 200 steps
        if (step % SAVE_EVERY == 0) {
            lambda_update_sor();
            double Msig = compute_Msigma();
            double con_val = check_divergence();
            double c2_val = compute_C2();
            save_ckpt();
            logfile << step << " " << u_lid << " " << Msig << " " << con_val << " " << c2_val << endl;
            cout << "Step: " << step << " MΣ=" << Msig << " Con=" << con_val << " C2=" << c2_val << " ✓" << endl;
        }
    }
    logfile.close();

    // Output centerline velocity (corrected version)
    int j_mid = Nx/2;
    ofstream fout("u_centerline.txt");
    fout << "# y u\n";
    for (int i = 0; i < Ny; ++i) {
        double y = i*dy;
        double u_center;
        if (i == 0) u_center = 0.0;
        else if (i == Ny-1) u_center = 1.0;
        else u_center = (psi[i+1][j_mid] - psi[i-1][j_mid]) / (2.0*dy);
        fout << y << " " << u_center << "\n";
    }
    fout.close();
    cout << "Simulation complete. u_centerline.txt saved." << endl;
    return 0;
}
