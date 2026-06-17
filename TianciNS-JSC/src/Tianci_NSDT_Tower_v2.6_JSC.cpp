#define _USE_MATH_DEFINES

#include <iostream>

#include <fstream>

#include <cmath>

#include <cstring>

#include <iomanip>

#include <chrono>

#include <string>

#include <vector>

#include <algorithm>

#include <memory>

#include <random>
#include <cassert>

#include <deque>

#include <numeric>

#include <map>
#include <direct.h>
#include <sys/stat.h>



using namespace std;



// ============================================================================

// Tianci NSDT Tower v2.6 JSC

// Design philosophy: no runtime patches to sustain the system; let the system's own structure dissolve instability at its root
// Core changes (vs v2.4):

//   1. Remove EvolutionStage enum -- all operators always online, execution operators physics-triggered

//   2. Xi anchoring with deviation computation -- prerequisite for [Xi,Lambda]=0 assumption
//   3. Sigma switched to 3-component clip model -- sigma_data/0.5, delta_model(L^2)/2.0, eta_shock/1.0

//   4. MAC projection driven by divergence residual -- enabled when |div|_max > threshold

//   5. Cloud memory adapted to vortex-center drift -- larger drift triggers more frequent updates
// ============================================================================

// Compile: g++ -O3 -std=c++17 -Wl,--stack,134217728 -o tower_v25 main.cpp

// ============================================================================



// ============================================================================

// EnergyBudget -- rain energy closed-loop accounting (kept from v2.5)
// ============================================================================

class EnergyBudget {

public:

    double dt_, cell_area_;

    int window_size_, buf_idx_, buf_count_;

    static constexpr int MAX_WINDOW = 512;

    double p_rain_hist_[MAX_WINDOW];

    double dke_dt_hist_[MAX_WINDOW];

    double p_rain_, p_in_, p_diss_, phase_lock_;

public:

    EnergyBudget(double dt, double cell_area, int window_size = 0)

        : dt_(dt), cell_area_(cell_area), window_size_(min((window_size > 0 ? window_size : (int)(6e-3 / dt)), MAX_WINDOW)),

        buf_idx_(0), buf_count_(0), p_rain_(0.0), p_in_(0.0), p_diss_(0.0), phase_lock_(0.0) {}

    void setDt(double dt) { dt_ = dt; }

    void reset() { buf_idx_ = 0; buf_count_ = 0; phase_lock_ = 0.0; }

    inline void resetRainPower() { p_rain_ = 0.0; }

    inline void addRainPower(double amp, double u_local, double v_local) {

        p_rain_ += amp * 0.5 * (u_local * u_local + v_local * v_local);

    }

    inline void finalizeRainPower() { p_rain_ = p_rain_ * cell_area_ / dt_; }

    inline void computePIn(double U_LID, double u[][512], int N) {

        double shear_sum = 0.0, dx = 1.0 / (N - 1);

        for (int j = 1; j < N - 1; ++j) shear_sum += (u[N - 1][j] - u[N - 2][j]) / dx * dx;

        p_in_ = U_LID * shear_sum;

    }

    inline void computePDiss(double nu, double u[][512], double v[][512], int N) {

        double diss_sum = 0.0, dx = 1.0 / (N - 1), dx_inv = 1.0 / dx;

        for (int i = 1; i < N - 1; ++i) for (int j = 1; j < N - 1; ++j) {

            double du_dx = (u[i][j + 1] - u[i][j - 1]) * 0.5 * dx_inv;

            double du_dy = (u[i + 1][j] - u[i - 1][j]) * 0.5 * dx_inv;

            double dv_dx = (v[i][j + 1] - v[i][j - 1]) * 0.5 * dx_inv;

            double dv_dy = (v[i + 1][j] - v[i - 1][j]) * 0.5 * dx_inv;

            diss_sum += (du_dx * du_dx + du_dy * du_dy + dv_dx * dv_dx + dv_dy * dv_dy) * cell_area_;

        }

        p_diss_ = nu * diss_sum;

    }

    inline void update(double ke_curr, double ke_prev) {

        double dke_dt = (ke_curr - ke_prev) / dt_;

        p_rain_hist_[buf_idx_] = p_rain_; dke_dt_hist_[buf_idx_] = dke_dt;

        buf_idx_ = (buf_idx_ + 1) % window_size_; if (buf_count_ < window_size_) buf_count_++;

        if (buf_count_ >= window_size_) {

            double sx = 0, sy = 0, sxy = 0, sx2 = 0, sy2 = 0;

            for (int k = 0; k < window_size_; ++k) {

                double x = p_rain_hist_[k], y = dke_dt_hist_[k];

                sx += x; sy += y; sxy += x * y; sx2 += x * x; sy2 += y * y;

            }

            double denom = sqrt((window_size_ * sx2 - sx * sx) * (window_size_ * sy2 - sy * sy));

            phase_lock_ = (denom < 1e-15) ? 0.0 : (window_size_ * sxy - sx * sy) / denom;

        }

    }

    inline bool isSelfCloud() const { return (buf_count_ >= window_size_) && (phase_lock_ < -0.7); }

    inline double getPRain() const { return p_rain_; }

    inline double getPIn() const { return p_in_; }

    inline double getPDiss() const { return p_diss_; }

    inline double getPhaseLock() const { return phase_lock_; }

    inline bool isWindowReady() const { return buf_count_ >= window_size_; }

};



// ============================================================================

// Basic structures

// ============================================================================

string rain_level = "Light";

double rain_last_ke_dev = 0;



struct NestMemory {

    double vortex_x, vortex_y, vortex_strength;

    double stable_dt, lambda;

    int    converged_step;

    double bl_thickness, wall_shear_max;

    double final_ke, final_wmax, poisson_res;

    double cloud_gamma_max, cloud_memory_time;

    bool   converged;

    string abort_reason;

    void zero() {

        vortex_x = vortex_y = 0.5; vortex_strength = 0.0;

        stable_dt = 1e-4; lambda = 0.5; converged_step = 0;

        bl_thickness = 0.05; wall_shear_max = 0.0;

        final_ke = final_wmax = poisson_res = 0.0;

        converged = false; abort_reason = "";

    }

};



struct LevelConfig {

    int    N;

    double Re, U_LID, NU, DT_INIT, ALPHA;

    int    MAX_STEPS;

    double TARGET_TIME;

    int    POISSON_ITER;

    double POISSON_TOL;

    int    RK4_SUB_POISSON_ITER;

    double RK4_SUB_POISSON_TOL;

};



struct OperatorMeta {

    string id, formula, name, math, physics;

};



struct Field {

    static const int MAXN = 512;

    double w[MAXN][MAXN], s[MAXN][MAXN], u[MAXN][MAXN], v[MAXN][MAXN];

    double wmax, ke, ke_prev, poisson_res;

    int    active_N;

    void zero(int N) {

        active_N = N;

        memset(w, 0, sizeof(w)); memset(s, 0, sizeof(s));

        memset(u, 0, sizeof(u)); memset(v, 0, sizeof(v));

        wmax = 0; ke = 0; ke_prev = 0; poisson_res = 1e20;

    }

};



class Operator {

protected:

    double dt_scale_ = 1.0;

    bool should_rain_ = false;

public:

    virtual ~Operator() = default;

    virtual void apply() = 0;

    virtual OperatorMeta get_meta() const = 0;

    virtual bool succeeded() const { return true; }

    virtual double residual() const { return 0.0; }

    virtual void set_response(int warning_level) {

        dt_scale_ = 1.0; should_rain_ = false;

        if (warning_level == 1) { dt_scale_ = 0.8; }

        else if (warning_level == 2) { dt_scale_ = 0.5; should_rain_ = true; }

    }

    virtual double get_dt_scale() const { return dt_scale_; }

    virtual bool should_rain() const { return should_rain_; }

};



class LevelSolver;

void rain_test(Field& field, double& ke, double& wmax, int current_step,

    Operator* xi, Operator* gtr, Operator* theta,

    Operator* dri, Operator* energy,

    LevelSolver* solver);



// ============================================================================

// v2.5 core: operator self-triggering -- physics-driven, not step-driven
// Each execution operator has should_activate(), reading flow field state for autonomous decision
// Monitor operators always online (zero gating cost: read-only field scalar reduction)

// ============================================================================



// ============================================================================

// XiAnchorOp -- anchor boundary + deviation computation (v2.5: added target_deviation)
// Theory mapping: Prop 3.1' requires [Xi,Lambda]=0, so Xi must compute deviation
// ============================================================================

class XiAnchorOp : public Operator {

    Field& f; double dx, U_LID;

    double target_deviation_;  // v2.5 added: boundary deviation

    double boundary_error_;    // v2.5 added: boundary condition residual
public:

    XiAnchorOp(Field& field, double dx_val, double u_lid)

        : f(field), dx(dx_val), U_LID(u_lid), target_deviation_(0.0), boundary_error_(0.0) {}

    void set_response(int warning_level) {

        dt_scale_ = 1.0; should_rain_ = false;

        if (warning_level == 1) { dt_scale_ = 0.8; }

        else if (warning_level == 2) { dt_scale_ = 0.5; should_rain_ = true; }

    }

    double get_dt_scale() const { return dt_scale_; }

    bool should_rain() const { return should_rain_; }

    void apply() override {

        int N = f.active_N;

        // Anchor stream-function boundary
        for (int j = 0; j < N; j++) { f.s[0][j] = 0; f.s[N - 1][j] = 0; }

        for (int i = 0; i < N; i++) { f.s[i][0] = 0; f.s[i][N - 1] = 0; }

        // Anchor velocity boundary

        for (int j = 0; j < N; j++) {

            f.u[0][j] = 0; f.u[N - 1][j] = U_LID; f.v[0][j] = 0; f.v[N - 1][j] = 0;

        }

        for (int i = 0; i < N; i++) {

            f.u[i][0] = 0; f.u[i][N - 1] = 0; f.v[i][0] = 0; f.v[i][N - 1] = 0;

        }



        // v2.5 added: compute boundary deviation target_deviation

        // Definition: L2 distance between inner-layer neighbor velocity and Dirichlet target

        double dev2 = 0.0;

        int cnt = 0;

        // Top wall: u should approach U_LID

        for (int j = 1; j < N - 1; j++) {

            double dev = f.u[N - 2][j] - U_LID;

            dev2 += dev * dev; cnt++;

        }

        // Bottom wall: u should approach 0

        for (int j = 1; j < N - 1; j++) {

            double dev = f.u[1][j];

            dev2 += dev * dev; cnt++;

        }

        // Left/right walls: v should approach 0

        for (int i = 1; i < N - 1; i++) {

            dev2 += f.v[i][1] * f.v[i][1] + f.v[i][N - 2] * f.v[i][N - 2]; cnt += 2;

        }

        target_deviation_ = (cnt > 0) ? sqrt(dev2 / cnt) : 0.0;



        // v2.5 added: boundary condition residual (inconsistency between boundary and interior stream-function values)
        boundary_error_ = 0.0;

        for (int j = 1; j < N - 1; j++) {

            // Top-wall vorticity consistency with second derivative of stream-function
            double s2_top = (f.s[N - 1][j] - 2.0 * f.s[N - 2][j] + f.s[N - 3][j]) / (dx * dx);

            boundary_error_ += fabs(s2_top + f.w[N - 1][j]);

        }

        boundary_error_ /= max(1, N - 2);

    }

    double get_target_deviation() const { return target_deviation_; }

    double get_boundary_error() const { return boundary_error_; }

    // v2.5: boundary correction strength -- adaptive based on deviation

    double get_boundary_correction() const { return min(1.0, target_deviation_ / 10.0); }

    OperatorMeta get_meta() const override {

        return { "Xi-001","A1-001","Anchor+Deviation","psi=0, dev=||u_b-u_target||","Boundary" };

    }

};



// ============================================================================

// ThetaGradientOp -- velocity gradient reconstruction (v2.5: full-domain 2nd-order accuracy, unchanged)

// ============================================================================

class ThetaGradientOp : public Operator {

    Field& f; double dx, U_LID;

public:

    ThetaGradientOp(Field& field, double dx_val, double u_lid)

        : f(field), dx(dx_val), U_LID(u_lid) {}

    void set_response(int warning_level) {

        dt_scale_ = 1.0; should_rain_ = false;

        if (warning_level == 1) { dt_scale_ = 0.8; }

        else if (warning_level == 2) { dt_scale_ = 0.5; should_rain_ = true; }

    }

    double get_dt_scale() const { return dt_scale_; }

    bool should_rain() const { return should_rain_; }

    void apply() override {

        int N = f.active_N; double dx2 = 2.0 * dx;

        for (int i = 2; i < N - 2; i++)

            for (int j = 2; j < N - 2; j++) {

                f.u[i][j] = (f.s[i + 1][j] - f.s[i - 1][j]) / dx2;

                f.v[i][j] = -(f.s[i][j + 1] - f.s[i][j - 1]) / dx2;

            }

        for (int j = 1; j < N - 1; j++) {

            f.u[N - 2][j] = (3 * f.s[N - 1][j] - 4 * f.s[N - 2][j] + f.s[N - 3][j]) / dx2;

            f.v[N - 2][j] = -(f.s[N - 2][j + 1] - f.s[N - 2][j - 1]) / dx2;

            f.u[1][j] = (-3 * f.s[0][j] + 4 * f.s[1][j] - f.s[2][j]) / dx2;

            f.v[1][j] = -(f.s[1][j + 1] - f.s[1][j - 1]) / dx2;

        }

        for (int i = 1; i < N - 1; i++) {

            f.u[i][1] = (f.s[i + 1][1] - f.s[i - 1][1]) / dx2;

            f.v[i][1] = -(-3 * f.s[i][0] + 4 * f.s[i][1] - f.s[i][2]) / dx2;

            f.u[i][N - 2] = (f.s[i + 1][N - 2] - f.s[i - 1][N - 2]) / dx2;

            f.v[i][N - 2] = -(3 * f.s[i][N - 1] - 4 * f.s[i][N - 2] + f.s[i][N - 3]) / dx2;

        }

        for (int j = 0; j < N; j++) {

            f.u[0][j] = 0; f.v[0][j] = 0;

            f.u[N - 1][j] = U_LID; f.v[N - 1][j] = 0;

        }

        for (int i = 0; i < N; i++) {

            f.u[i][0] = 0; f.v[i][0] = 0;

            f.u[i][N - 1] = 0; f.v[i][N - 1] = 0;

        }

    }

    OperatorMeta get_meta() const override {

        return { "Theta-002","A1-002","Gradient","u=dpsi/dy","Velocity" };

    }

};



// ============================================================================

// GTRPoissonOp -- Gamma variable-coefficient Poisson + MAC projection (v2.5: MAC driven by divergence residual)
// ============================================================================

class GTRPoissonOp : public Operator {

    Field& f; double dx;

    double res_max; bool converged;

    int max_iter; double tol;

    double r[Field::MAXN][Field::MAXN], p[Field::MAXN][Field::MAXN], Ap[Field::MAXN][Field::MAXN];

    double gamma_half_x[Field::MAXN][Field::MAXN], gamma_half_y[Field::MAXN][Field::MAXN];

    double gamma[Field::MAXN][Field::MAXN];

    double alpha_coeff;

    // v2.5 added: MAC projection divergence residual

    double mac_div_max_;

    bool mac_active_;

public:

    GTRPoissonOp(Field& field, double dx_val, int max_it, double tol_val, double alpha_val = 0.1)

        : f(field), dx(dx_val), res_max(1e20), converged(false), max_iter(max_it), tol(tol_val), alpha_coeff(alpha_val),

          mac_div_max_(0.0), mac_active_(false) {

        memset(gamma, 0, sizeof(gamma)); memset(gamma_half_x, 0, sizeof(gamma_half_x)); memset(gamma_half_y, 0, sizeof(gamma_half_y));

    }



    void set_response(int warning_level) {

        dt_scale_ = 1.0; should_rain_ = false;

        if (warning_level == 1) { dt_scale_ = 0.8; }

        else if (warning_level == 2) { dt_scale_ = 0.5; should_rain_ = true; }

    }

    double get_dt_scale() const { return dt_scale_; }

    bool should_rain() const { return should_rain_; }

    void apply() override { solve_cg(); }



    void compute_gamma(int N) {

        const double h = dx, eps = 1e-8;

        for (int i = 0; i < N; ++i) for (int j = 0; j < N; ++j) {

            double du_dx, du_dy, dv_dx, dv_dy;

            if (i == 0) du_dx = (f.u[i + 1][j] - f.u[i][j]) / h;

            else if (i == N - 1) du_dx = (f.u[i][j] - f.u[i - 1][j]) / h;

            else du_dx = (f.u[i + 1][j] - f.u[i - 1][j]) / (2.0 * h);

            if (j == 0) du_dy = (f.u[i][j + 1] - f.u[i][j]) / h;

            else if (j == N - 1) du_dy = (f.u[i][j] - f.u[i][j - 1]) / h;

            else du_dy = (f.u[i][j + 1] - f.u[i][j - 1]) / (2.0 * h);

            if (i == 0) dv_dx = (f.v[i + 1][j] - f.v[i][j]) / h;

            else if (i == N - 1) dv_dx = (f.v[i][j] - f.v[i - 1][j]) / h;

            else dv_dx = (f.v[i + 1][j] - f.v[i - 1][j]) / (2.0 * h);

            if (j == 0) dv_dy = (f.v[i][j + 1] - f.v[i][j]) / h;

            else if (j == N - 1) dv_dy = (f.v[i][j] - f.v[i][j - 1]) / h;

            else dv_dy = (f.v[i][j + 1] - f.v[i][j - 1]) / (2.0 * h);

            double Gnorm2 = du_dx * du_dx + du_dy * du_dy + dv_dx * dv_dx + dv_dy * dv_dy;

            double val = 1.0 + alpha_coeff * sqrt(Gnorm2 + 1e-12);

            // Soft saturation: asymptotically approaches 10, never hard-clips
            val = 1.0 + 9.0 * tanh((val - 1.0) / 9.0);

            if (!(val > eps)) val = eps;

            gamma[i][j] = val;

        }

    }



    void compute_gamma_half(int N) {

        for (int i = 0; i < N; ++i) for (int j = 0; j < N; ++j) {

            if (i < N - 1) gamma_half_x[i][j] = 0.5 * (gamma[i][j] + gamma[i + 1][j]);

            else gamma_half_x[i][j] = gamma[i][j];

            if (j < N - 1) gamma_half_y[i][j] = 0.5 * (gamma[i][j] + gamma[i][j + 1]);

            else gamma_half_y[i][j] = gamma[i][j];

        }

    }



    // Main-step CG: full variable-coefficient

    void solve_cg() {

        int N = f.active_N; double dx2 = dx * dx;

        compute_gamma(N);

        compute_gamma_half(N);

        double rsold = 0.0;

        for (int i = 1; i < N - 1; i++) for (int j = 1; j < N - 1; j++) {

            double lap = (f.s[i][j + 1] + f.s[i][j - 1] + f.s[i + 1][j] + f.s[i - 1][j] - 4.0 * f.s[i][j]) / dx2;

            r[i][j] = f.w[i][j] + lap;

            p[i][j] = r[i][j];

            rsold += r[i][j] * r[i][j];

        }

        for (int j = 0; j < N; j++) { r[0][j] = r[N - 1][j] = 0; }

        for (int i = 0; i < N; i++) { r[i][0] = r[i][N - 1] = 0; }



        converged = false;

        res_max = sqrt(rsold / ((N - 2) * (N - 2)));

        if (res_max < tol) { converged = true; f.poisson_res = res_max; return; }



        for (int iter = 0; iter < max_iter; iter++) {

            if (iter >= 2000 && res_max < 1e-3) { converged = true; break; }

            for (int i = 1; i < N - 1; i++) for (int j = 1; j < N - 1; j++) {

                double gx = gamma_half_x[i][j], gy = gamma_half_y[i][j];

                Ap[i][j] = -(gx * (p[i][j + 1] - p[i][j]) - gx * (p[i][j] - p[i][j - 1])

                           + gy * (p[i + 1][j] - p[i][j]) - gy * (p[i][j] - p[i - 1][j])) / dx2;

            }

            double pAp = 0.0;

            for (int i = 1; i < N - 1; i++) for (int j = 1; j < N - 1; j++) pAp += p[i][j] * Ap[i][j];

            if (fabs(pAp) < 1e-20) { converged = true; break; }

            double alpha_cg = rsold / pAp;

            double rsnew = 0.0; res_max = 0.0;

            for (int i = 1; i < N - 1; i++) for (int j = 1; j < N - 1; j++) {

                f.s[i][j] += alpha_cg * p[i][j];

                r[i][j] -= alpha_cg * Ap[i][j];

                rsnew += r[i][j] * r[i][j];

                if (fabs(r[i][j]) > res_max) res_max = fabs(r[i][j]);

            }

            double res_rms = sqrt(rsnew / ((N - 2) * (N - 2)));

            if (res_rms < tol) { converged = true; f.poisson_res = res_rms; break; }

            double beta = rsnew / rsold;

            for (int i = 1; i < N - 1; i++) for (int j = 1; j < N - 1; j++) p[i][j] = r[i][j] + beta * p[i][j];

            rsold = rsnew;

        }

        f.poisson_res = res_max;

        for (int j = 0; j < N; j++) { f.s[0][j] = 0; f.s[N - 1][j] = 0; }

        for (int i = 0; i < N; i++) { f.s[i][0] = 0; f.s[i][N - 1] = 0; }

    }



    // Sub-step fast CG: frozen Gamma, constant coefficient

    void solve_cg_fast(double w_in[][512], double s_inout[][512], int N, int max_fast = 50) {

        double dx2 = dx * dx;

        double r_sub[512][512], p_sub[512][512], Ap_sub[512][512];

        memset(r_sub, 0, sizeof(r_sub)); memset(p_sub, 0, sizeof(p_sub)); memset(Ap_sub, 0, sizeof(Ap_sub));



        double rsold = 0;

        for (int i = 1; i < N - 1; i++) for (int j = 1; j < N - 1; j++) {

            double lap = (s_inout[i][j + 1] + s_inout[i][j - 1] + s_inout[i + 1][j] + s_inout[i - 1][j] - 4.0 * s_inout[i][j]) / dx2;

            r_sub[i][j] = w_in[i][j] + lap;

            p_sub[i][j] = r_sub[i][j];

            rsold += r_sub[i][j] * r_sub[i][j];

        }



        for (int iter = 0; iter < max_fast; iter++) {

            for (int i = 1; i < N - 1; i++) for (int j = 1; j < N - 1; j++) {

                Ap_sub[i][j] = -(p_sub[i][j + 1] + p_sub[i][j - 1] + p_sub[i + 1][j] + p_sub[i - 1][j] - 4.0 * p_sub[i][j]) / dx2;

            }

            double pAp = 0;

            for (int i = 1; i < N - 1; i++) for (int j = 1; j < N - 1; j++) pAp += p_sub[i][j] * Ap_sub[i][j];

            if (fabs(pAp) < 1e-20) break;

            double alpha_cg = rsold / pAp;

            double rsnew = 0;

            for (int i = 1; i < N - 1; i++) for (int j = 1; j < N - 1; j++) {

                s_inout[i][j] += alpha_cg * p_sub[i][j];

                r_sub[i][j] -= alpha_cg * Ap_sub[i][j];

                rsnew += r_sub[i][j] * r_sub[i][j];

            }

            if (sqrt(rsnew / ((N - 2) * (N - 2))) < 1e-3) break;

            double beta = rsnew / rsold;

            for (int i = 1; i < N - 1; i++) for (int j = 1; j < N - 1; j++)

                p_sub[i][j] = r_sub[i][j] + beta * p_sub[i][j];

            rsold = rsnew;

        }

        for (int j = 0; j < N; j++) { s_inout[0][j] = 0; s_inout[N - 1][j] = 0; }

        for (int i = 0; i < N; i++) { s_inout[i][0] = 0; s_inout[i][N - 1] = 0; }

    }



    // v2.5 refactor: MAC projection -- divergence-residual driven, not stage-driven
    // Compute divergence residual first; project only if above threshold, otherwise skip (zero cost)
    bool mac_project_if_needed(double u[][512], double v[][512], int N, double div_threshold = 1e-3) {

        double dx2 = dx * dx;

        // Step 1: compute maximum divergence residual
        mac_div_max_ = 0.0;

        for (int i = 1; i < N - 1; i++) for (int j = 1; j < N - 1; j++) {

            double div = (u[i][j + 1] - u[i][j - 1]) / (2 * dx) + (v[i + 1][j] - v[i - 1][j]) / (2 * dx);

            if (fabs(div) > mac_div_max_) mac_div_max_ = fabs(div);

        }



        // v2.5 core: physics-triggered -- project only when divergence residual exceeds threshold

        if (mac_div_max_ < div_threshold) {

            mac_active_ = false;

            return false;

        }

        mac_active_ = true;



        // Execute projection

        vector<double> div(N * N, 0.0), p_mac(N * N, 0.0);

        auto idx = [N](int i, int j) { return i * N + j; };

        for (int i = 1; i < N - 1; i++) for (int j = 1; j < N - 1; j++) {

            div[idx(i, j)] = (u[i][j + 1] - u[i][j - 1]) / (2 * dx) + (v[i + 1][j] - v[i - 1][j]) / (2 * dx);

        }

        // Jacobi iteration count proportional to residual: larger residual -> more iterations
        int mac_iter = min(100, max(20, (int)(mac_div_max_ / div_threshold * 30)));

        for (int iter = 0; iter < mac_iter; iter++) {

            for (int i = 1; i < N - 1; i++) for (int j = 1; j < N - 1; j++) {

                p_mac[idx(i, j)] = 0.25 * (p_mac[idx(i + 1, j)] + p_mac[idx(i - 1, j)] + p_mac[idx(i, j + 1)] + p_mac[idx(i, j - 1)] - dx2 * div[idx(i, j)]);

            }

        }

        for (int i = 1; i < N - 1; i++) for (int j = 1; j < N - 1; j++) {

            u[i][j] -= (p_mac[idx(i, j + 1)] - p_mac[idx(i, j - 1)]) / (2 * dx);

            v[i][j] -= (p_mac[idx(i + 1, j)] - p_mac[idx(i - 1, j)]) / (2 * dx);

        }

        return true;

    }



    // Keep legacy interface for sub-step calls (unchanged)

    void mac_project(double u[][512], double v[][512], int N) {

        double dx2 = dx * dx;

        vector<double> div(N * N, 0.0), p_mac(N * N, 0.0);

        auto idx = [N](int i, int j) { return i * N + j; };

        for (int i = 1; i < N - 1; i++) for (int j = 1; j < N - 1; j++) {

            div[idx(i, j)] = (u[i][j + 1] - u[i][j - 1]) / (2 * dx) + (v[i + 1][j] - v[i - 1][j]) / (2 * dx);

        }

        for (int iter = 0; iter < 50; iter++) {

            for (int i = 1; i < N - 1; i++) for (int j = 1; j < N - 1; j++) {

                p_mac[idx(i, j)] = 0.25 * (p_mac[idx(i + 1, j)] + p_mac[idx(i - 1, j)] + p_mac[idx(i, j + 1)] + p_mac[idx(i, j - 1)] - dx2 * div[idx(i, j)]);

            }

        }

        for (int i = 1; i < N - 1; i++) for (int j = 1; j < N - 1; j++) {

            u[i][j] -= (p_mac[idx(i, j + 1)] - p_mac[idx(i, j - 1)]) / (2 * dx);

            v[i][j] -= (p_mac[idx(i + 1, j)] - p_mac[idx(i - 1, j)]) / (2 * dx);

        }

    }



    void set_max_iter(int new_max) { max_iter = new_max; }

    void set_alpha(double new_alpha) { alpha_coeff = new_alpha; }
    double get_alpha() const { return alpha_coeff; }

    OperatorMeta get_meta() const override {

        return { "GTR-004","A1-004","Poisson+MAC(div)","nabla^2 psi = -omega","Projection" };

    }

    bool succeeded() const override { return converged; }

    double residual() const override { return res_max; }

    double getGamma(int i, int j) const { return gamma[i][j]; }

    double getMaxGamma() const { double mg = 1.0; for (int i = 0; i < 512; i++) for (int j = 0; j < 512; j++) if (gamma[i][j] > mg) mg = gamma[i][j]; return mg; }
    double getAvgGamma() const { double sum = 0; int cnt = 0; for (int i = 1; i < 511; i++) for (int j = 1; j < 511; j++) { sum += gamma[i][j]; cnt++; } return cnt > 0 ? sum / cnt : 1.0; }

    void setGamma(int i, int j, double val) { gamma[i][j] = val; }

    void syncGammaFromCloud(double gamma_src[][512], int N) { for (int i = 0; i < N; i++) for (int j = 0; j < N; j++) gamma[i][j] = gamma_src[i][j]; }

    void syncGammaToCloud(double gamma_dst[][512], int N) { for (int i = 0; i < N; i++) for (int j = 0; j < N; j++) gamma_dst[i][j] = gamma[i][j]; }

    double (*getGammaHalfX())[Field::MAXN] { return gamma_half_x; }

    double (*getGammaHalfY())[Field::MAXN] { return gamma_half_y; }

    double get_mac_div_max() const { return mac_div_max_; }

    bool is_mac_active() const { return mac_active_; }

};





// ============================================================================

// DRIBoundaryOp -- Thom/Briley formula (unchanged)

// ============================================================================

class DRIBoundaryOp : public Operator {

    Field& f; double dx, rho, U_LID;

public:

    DRIBoundaryOp(Field& field, double dx_val, double rho_val, double u_lid)

        : f(field), dx(dx_val), rho(rho_val), U_LID(u_lid) {}

    void set_response(int warning_level) {

        dt_scale_ = 1.0; should_rain_ = false;

        if (warning_level == 1) { dt_scale_ = 0.8; }

        else if (warning_level == 2) { dt_scale_ = 0.5; should_rain_ = true; }

    }

    double get_dt_scale() const { return dt_scale_; }

    bool should_rain() const { return should_rain_; }

    void apply() override {

        int N = f.active_N; double dx2 = dx * dx;

        bool can_briley = (N >= 7);

        for (int j = 1; j < N - 1; j++) {

            if (can_briley) {

                double s0 = f.s[N - 1][j], s1 = f.s[N - 2][j], s2 = f.s[N - 3][j], s3 = f.s[N - 4][j], s4 = f.s[N - 5][j];

                double d2s = (35.0 * s0 - 104.0 * s1 + 114.0 * s2 - 56.0 * s3 + 11.0 * s4) / (12.0 * dx2);

                double nt = -d2s - 0.5 * f.w[N - 2][j] + 3.0 * U_LID / dx;

                f.w[N - 1][j] = rho * nt + (1.0 - rho) * f.w[N - 1][j];

            } else {

                double nt = -3.0 * (f.s[N - 1][j] - f.s[N - 2][j]) / dx2 - 0.5 * f.w[N - 2][j] + 3.0 * U_LID / dx;

                f.w[N - 1][j] = rho * nt + (1.0 - rho) * f.w[N - 1][j];

            }

        }

        for (int j = 1; j < N - 1; j++) {

            if (can_briley) {

                double s0 = f.s[0][j], s1 = f.s[1][j], s2 = f.s[2][j], s3 = f.s[3][j], s4 = f.s[4][j];

                double d2s = (35.0 * s0 - 104.0 * s1 + 114.0 * s2 - 56.0 * s3 + 11.0 * s4) / (12.0 * dx2);

                double nb = -d2s - 0.5 * f.w[1][j];

                f.w[0][j] = rho * nb + (1.0 - rho) * f.w[0][j];

            } else {

                double nb = -3.0 * (f.s[1][j] - f.s[0][j]) / dx2 - 0.5 * f.w[1][j];

                f.w[0][j] = rho * nb + (1.0 - rho) * f.w[0][j];

            }

        }

        for (int i = 1; i < N - 1; i++) {

            if (can_briley) {

                double s0 = f.s[i][0], s1 = f.s[i][1], s2 = f.s[i][2], s3 = f.s[i][3], s4 = f.s[i][4];

                double d2s = (35.0 * s0 - 104.0 * s1 + 114.0 * s2 - 56.0 * s3 + 11.0 * s4) / (12.0 * dx2);

                double nl = -d2s - 0.5 * f.w[i][1];

                f.w[i][0] = rho * nl + (1.0 - rho) * f.w[i][0];

            } else {

                double nl = -3.0 * (f.s[i][1] - f.s[i][0]) / dx2 - 0.5 * f.w[i][1];

                f.w[i][0] = rho * nl + (1.0 - rho) * f.w[i][0];

            }

        }

        for (int i = 1; i < N - 1; i++) {

            if (can_briley) {

                double s0 = f.s[i][N - 1], s1 = f.s[i][N - 2], s2 = f.s[i][N - 3], s3 = f.s[i][N - 4], s4 = f.s[i][N - 5];

                double d2s = (35.0 * s0 - 104.0 * s1 + 114.0 * s2 - 56.0 * s3 + 11.0 * s4) / (12.0 * dx2);

                double nr = -d2s - 0.5 * f.w[i][N - 2];

                f.w[i][N - 1] = rho * nr + (1.0 - rho) * f.w[i][N - 1];

            } else {

                double nr = -3.0 * (f.s[i][N - 1] - f.s[i][N - 2]) / dx2 - 0.5 * f.w[i][N - 2];

                f.w[i][N - 1] = rho * nr + (1.0 - rho) * f.w[i][N - 1];

            }

        }

        f.w[0][0] = 0.5 * (f.w[0][1] + f.w[1][0]);

        f.w[0][N - 1] = 0.5 * (f.w[0][N - 2] + f.w[1][N - 1]);

        f.w[N - 1][0] = 0.5 * (f.w[N - 1][1] + f.w[N - 2][0]);

        f.w[N - 1][N - 1] = 0.5 * (f.w[N - 1][N - 2] + f.w[N - 2][N - 1]);

    }

    OperatorMeta get_meta() const override {

        return { "DRI-005","A1-005","Boundary","omega_wall=Thom/Briley","Vorticity BC" };

    }

};



// ============================================================================

// RK4TimeOp -- 4th-order Runge-Kutta (v2.5: removed EvolutionStage dependency)
// ============================================================================

class RK4TimeOp : public Operator {

    Field& f;

    double dt, dx, nu, U_LID;

    bool success; double stability;

    int sub_poisson_iter; double sub_poisson_tol;

    double k1[512][512], k2[512][512], k3[512][512], k4[512][512];

    double w_tmp[512][512], s_tmp[512][512], u_tmp[512][512], v_tmp[512][512];

    GTRPoissonOp* gtr_op;

    // v2.5: removed EvolutionStage stage; no longer need stage flag
    static constexpr int MAX_PROBES = 16;

    struct RainProbe { double x, y, intensity; };

    static RainProbe rain_probes[MAX_PROBES];

    static int probe_count;

public:

    RK4TimeOp(Field& field, double dt_val, double dx_val, double nu_val,

        double u_lid, int sub_it, double sub_tol, GTRPoissonOp* gtr)

        : f(field), dt(dt_val), dx(dx_val), nu(nu_val), U_LID(u_lid),

        success(true), stability(0.0), sub_poisson_iter(sub_it), sub_poisson_tol(sub_tol),

        gtr_op(gtr) {}

    void set_response(int warning_level) {

        dt_scale_ = 1.0; should_rain_ = false;

        if (warning_level == 1) { dt_scale_ = 0.8; }

        else if (warning_level == 2) { dt_scale_ = 0.5; should_rain_ = true; }

    }

    double get_dt_scale() const { return dt_scale_; }

    bool should_rain() const { return should_rain_; }

    void apply() override {

        int N = f.active_N;

        double r = nu * dt / (dx * dx);

        if (r > 0.25) { stability = 1.0; success = false; return; }



        memset(k1, 0, sizeof(k1)); memset(k2, 0, sizeof(k2));

        memset(k3, 0, sizeof(k3)); memset(k4, 0, sizeof(k4));

        memset(w_tmp, 0, sizeof(w_tmp)); memset(s_tmp, 0, sizeof(s_tmp));

        memset(u_tmp, 0, sizeof(u_tmp)); memset(v_tmp, 0, sizeof(v_tmp));



        // Stage 1

        compute_rhs(f.w, f.u, f.v, k1);

        update_interior(f.w, k1, 0.5, w_tmp);

        copy_boundary_w(f.w, w_tmp);

        solve_poisson_substep(w_tmp, s_tmp, u_tmp, v_tmp, N);

        compute_rhs(w_tmp, u_tmp, v_tmp, k2);



        // Stage 2

        update_interior(f.w, k2, 0.5, w_tmp);

        copy_boundary_w(f.w, w_tmp);

        solve_poisson_substep(w_tmp, s_tmp, u_tmp, v_tmp, N);

        compute_rhs(w_tmp, u_tmp, v_tmp, k3);



        // Stage 3

        update_interior(f.w, k3, 1.0, w_tmp);

        copy_boundary_w(f.w, w_tmp);

        solve_poisson_substep(w_tmp, s_tmp, u_tmp, v_tmp, N);

        compute_rhs(w_tmp, u_tmp, v_tmp, k4);



        // Final

        double wmax_new = 0.0;

        for (int i = 1; i < N - 1; i++) for (int j = 1; j < N - 1; j++) {

            f.w[i][j] += dt / 6.0 * (k1[i][j] + 2 * k2[i][j] + 2 * k3[i][j] + k4[i][j]);

            double wabs = fabs(f.w[i][j]);

            if (wabs > wmax_new) wmax_new = wabs;

            if (isnan(f.w[i][j]) || isinf(f.w[i][j]) || wabs > 1e8) {

                stability = 1.0; success = false; return;

            }

        }

        f.wmax = wmax_new;

        success = true;

    }

    OperatorMeta get_meta() const override {

        return { "RK4-003","A1-003","RK4","dw/dt","Time Integration" };

    }

    bool succeeded() const override { return success; }

    double get_stability() const { return stability; }

    void set_dt(double new_dt) { dt = new_dt; }

    // v2.5: removed set_stage() -- no more stage concept

    static void clearProbes() { probe_count = 0; }

    static void addProbe(double x, double y, double intensity) {

        if (probe_count < MAX_PROBES) {

            rain_probes[probe_count++] = {x, y, intensity};

        }

    }

    static const RainProbe* getProbes() { return rain_probes; }

    static int getProbeCount() { return probe_count; }



private:

    void compute_rhs(double w_in[][512], double u_in[][512], double v_in[][512], double rhs[][512]) {

        int N = f.active_N; double dx2_inv = 1.0 / (dx * dx);

        for (int i = 1; i < N - 1; i++) for (int j = 1; j < N - 1; j++) {

            double dwdx_c = (w_in[i][j + 1] - w_in[i][j - 1]) / (2.0 * dx);

            double dwdy_c = (w_in[i + 1][j] - w_in[i - 1][j]) / (2.0 * dx);

            double dwdx_u = (u_in[i][j] >= 0.0) ? (w_in[i][j] - w_in[i][j - 1]) / dx : (w_in[i][j + 1] - w_in[i][j]) / dx;

            double dwdy_u = (v_in[i][j] >= 0.0) ? (w_in[i][j] - w_in[i - 1][j]) / dx : (w_in[i + 1][j] - w_in[i][j]) / dx;

            double phi_x = fabs(u_in[i][j]) * dt / dx * 2.0;

            double phi_y = fabs(v_in[i][j]) * dt / dx * 2.0;

            if (phi_x < 0.0) phi_x = 0.0; if (phi_x > 1.0) phi_x = 1.0;

            if (phi_y < 0.0) phi_y = 0.0; if (phi_y > 1.0) phi_y = 1.0;

            double dwdx = (1.0 - phi_x) * dwdx_c + phi_x * dwdx_u;

            double dwdy = (1.0 - phi_y) * dwdy_c + phi_y * dwdy_u;

            double conv = u_in[i][j] * dwdx + v_in[i][j] * dwdy;

            double lap = (w_in[i][j + 1] - 2.0 * w_in[i][j] + w_in[i][j - 1]) * dx2_inv

                + (w_in[i + 1][j] - 2.0 * w_in[i][j] + w_in[i - 1][j]) * dx2_inv;

            rhs[i][j] = -conv + nu * lap;

        }

    }

    void update_interior(double src[][512], double rhs[][512], double coef, double dst[][512]) {

        int N = f.active_N;

        for (int i = 1; i < N - 1; i++) for (int j = 1; j < N - 1; j++)

            dst[i][j] = src[i][j] + coef * dt * rhs[i][j];

    }

    void copy_boundary_w(double src[][512], double dst[][512]) {

        int N = f.active_N;

        for (int j = 0; j < N; j++) { dst[0][j] = src[0][j]; dst[N - 1][j] = src[N - 1][j]; }

        for (int i = 0; i < N; i++) { dst[i][0] = src[i][0]; dst[i][N - 1] = src[i][N - 1]; }

    }

    void apply_velocity_bc(double u[][512], double v[][512], int N) {

        for (int j = 0; j < N; j++) { u[0][j] = 0; u[N - 1][j] = U_LID; v[0][j] = 0; v[N - 1][j] = 0; }

        for (int i = 0; i < N; i++) { u[i][0] = 0; u[i][N - 1] = 0; v[i][0] = 0; v[i][N - 1] = 0; }

    }

    void compute_velocity_sub(double s_in[][512], double u_out[][512], double v_out[][512], int N) {

        double dx2 = 2.0 * dx;

        for (int i = 1; i < N - 1; i++) for (int j = 1; j < N - 1; j++) {

            u_out[i][j] = (s_in[i + 1][j] - s_in[i - 1][j]) / dx2;

            v_out[i][j] = -(s_in[i][j + 1] - s_in[i][j - 1]) / dx2;

        }

    }

    void solve_poisson_substep(double w_in[][512], double s_out[][512],

        double u_out[][512], double v_out[][512], int N) {

        for (int i = 0; i < N; i++) for (int j = 0; j < N; j++)

            s_out[i][j] = f.s[i][j];

        gtr_op->solve_cg_fast(w_in, s_out, N, sub_poisson_iter);

        compute_velocity_sub(s_out, u_out, v_out, N);

        apply_velocity_bc(u_out, v_out, N);

    }

};

int RK4TimeOp::probe_count = 0;

RK4TimeOp::RainProbe RK4TimeOp::rain_probes[RK4TimeOp::MAX_PROBES];



// ============================================================================

// Monitor Committee operators (v2.5: always online, no stage gating)

// ============================================================================

class MSigmaOp : public Operator {

    Field& f; double& last_Msigma;

public:

    double value = 0;

    MSigmaOp(Field& field, double& last_ms) : f(field), last_Msigma(last_ms) {}

    void set_response(int warning_level) {

        dt_scale_ = 1.0; should_rain_ = false;

        if (warning_level == 1) { dt_scale_ = 0.8; }

        else if (warning_level == 2) { dt_scale_ = 0.5; should_rain_ = true; }

    }

    double get_dt_scale() const { return dt_scale_; }

    bool should_rain() const { return should_rain_; }

    void apply() override {

        int N = f.active_N;

        double sum = 0, sum2 = 0; int cnt = 0;

        for (int i = 1; i < N - 1; i++) for (int j = 1; j < N - 1; j++) {

            sum += f.w[i][j]; sum2 += f.w[i][j] * f.w[i][j]; cnt++;

        }

        if (cnt == 0) { value = 0; return; }

        double sig = sqrt(sum2 / cnt - (sum / cnt) * (sum / cnt));

        value = fabs(sig - last_Msigma);

        last_Msigma = sig;

    }

    OperatorMeta get_meta() const override { return { "MSigma-010","2.1-001","MetaSigma","d(sigma)/dt","Uncertainty" }; }

};



class RhoElasticityOp : public Operator {

    Field& f; double dx;

public:

    double value = 1.0;

    RhoElasticityOp(Field& field, double dx_val) : f(field), dx(dx_val) {}

    void set_response(int warning_level) {

        dt_scale_ = 1.0; should_rain_ = false;

        if (warning_level == 1) { dt_scale_ = 0.8; }

        else if (warning_level == 2) { dt_scale_ = 0.5; should_rain_ = true; }

    }

    double get_dt_scale() const { return dt_scale_; }

    bool should_rain() const { return should_rain_; }

    void apply() override {

        int N = f.active_N;

        double mx = 0;

        for (int i = 1; i < N - 1; i++) for (int j = 1; j < N - 1; j++) {

            double gx = fabs(f.w[i][j + 1] - f.w[i][j - 1]) / (2 * dx);

            double gy = fabs(f.w[i + 1][j] - f.w[i - 1][j]) / (2 * dx);

            mx = fmax(mx, sqrt(gx * gx + gy * gy));

        }

        value = 1.0 / (1.0 + mx * 0.1);

    }

    OperatorMeta get_meta() const override { return { "Rho-011","2.2-001","Elasticity","1/(1+mx*0.1)","Damping" }; }

};



class DeltaSaturationOp : public Operator {

    Field& f; double& prev_ke;

public:

    double value = 0;

    DeltaSaturationOp(Field& field, double& pke) : f(field), prev_ke(pke) {}

    void set_response(int warning_level) {

        dt_scale_ = 1.0; should_rain_ = false;

        if (warning_level == 1) { dt_scale_ = 0.8; }

        else if (warning_level == 2) { dt_scale_ = 0.5; should_rain_ = true; }

    }

    double get_dt_scale() const { return dt_scale_; }

    bool should_rain() const { return should_rain_; }

    void apply() override {

        int N = f.active_N;

        double ke = 0;

        for (int i = 1; i < N - 1; i++) for (int j = 1; j < N - 1; j++)

            ke += 0.5 * (f.u[i][j] * f.u[i][j] + f.v[i][j] * f.v[i][j]);

        ke /= ((N - 2) * (N - 2));

        if (prev_ke > 0) value = (ke - prev_ke) / prev_ke;

        else value = 0;

        prev_ke = ke;

    }

    OperatorMeta get_meta() const override { return { "Delta-007","2.3-001","Saturation","dKE/dt","Marginal" }; }

};



class ConsistencyOp : public Operator {

    Field& f; double dx;

public:

    double divergence_max = 0;

    bool consistent = true;

    ConsistencyOp(Field& field, double dx_val) : f(field), dx(dx_val) {}

    void set_response(int warning_level) {

        dt_scale_ = 1.0; should_rain_ = false;

        if (warning_level == 1) { dt_scale_ = 0.8; }

        else if (warning_level == 2) { dt_scale_ = 0.5; should_rain_ = true; }

    }

    double get_dt_scale() const { return dt_scale_; }

    bool should_rain() const { return should_rain_; }

    void apply() override {

        int N = f.active_N;

        divergence_max = 0;

        for (int i = 2; i < N - 2; i++) for (int j = 2; j < N - 2; j++) {

            double div = (f.u[i][j + 1] - f.u[i][j - 1]) / (2 * dx) + (f.v[i + 1][j] - f.v[i - 1][j]) / (2 * dx);

            if (fabs(div) > divergence_max) divergence_max = fabs(div);

        }

        consistent = (divergence_max < 1e-3);

    }

    OperatorMeta get_meta() const override { return { "Con-016","A1-010","Continuity","div(u)","Mass" }; }

};



class LambdaCouplingOp : public Operator {

    Field& f;

public:

    double value = 0.5;

    LambdaCouplingOp(Field& field) : f(field) {}

    void set_response(int warning_level) {

        dt_scale_ = 1.0; should_rain_ = false;

        if (warning_level == 1) { dt_scale_ = 0.8; }

        else if (warning_level == 2) { dt_scale_ = 0.5; should_rain_ = true; }

    }

    double get_dt_scale() const { return dt_scale_; }

    bool should_rain() const { return should_rain_; }

    void apply() override {

        int N = f.active_N;

        double u_max = 0, v_max = 0;

        for (int i = 1; i < N - 1; i++) for (int j = 1; j < N - 1; j++) {

            if (fabs(f.u[i][j]) > u_max) u_max = fabs(f.u[i][j]);

            if (fabs(f.v[i][j]) > v_max) v_max = fabs(f.v[i][j]);

        }

        double cfl = 1.0 / (u_max + v_max + 1e-10);

        value = fmin(0.9, cfl * 0.1);

    }

    OperatorMeta get_meta() const override { return { "Lambda-012","A1-006","Coupling","CFL-based","Coordination" }; }

};



class CurvatureEnergyOp : public Operator {

    Field& f; double dx;

public:

    double value = 0;

    CurvatureEnergyOp(Field& field, double dx_val) : f(field), dx(dx_val) {}

    void set_response(int warning_level) {

        dt_scale_ = 1.0; should_rain_ = false;

        if (warning_level == 1) { dt_scale_ = 0.8; }

        else if (warning_level == 2) { dt_scale_ = 0.5; should_rain_ = true; }

    }

    double get_dt_scale() const { return dt_scale_; }

    bool should_rain() const { return should_rain_; }

    void apply() override {

        int N = f.active_N;

        double c2 = 0;

        for (int i = 2; i < N - 2; i++) for (int j = 2; j < N - 2; j++) {

            double wxx = (f.w[i][j + 1] - 2 * f.w[i][j] + f.w[i][j - 1]) / (dx * dx);

            double wyy = (f.w[i + 1][j] - 2 * f.w[i][j] + f.w[i - 1][j]) / (dx * dx);

            double wxy = (f.w[i + 1][j + 1] - f.w[i + 1][j - 1] - f.w[i - 1][j + 1] + f.w[i - 1][j - 1]) / (4 * dx * dx);

            c2 += wxx * wxx + wyy * wyy + 2 * wxy * wxy;

        }

        value = c2 / ((N - 4) * (N - 4));

    }

    OperatorMeta get_meta() const override { return { "C2-008","2.6-001","Curvature","Hessian(w)","Critical" }; }

};



// ============================================================================

// Triple-gate Phi gating (ZFC/not-CH/Phi consensus) -- always online
// ============================================================================

class PhiGateOp : public Operator {

    Field& f;

    double msigma, rho, delta, lambda, c2;

    double poisson_res, energy_change;

    int step;

    static constexpr int HISTORY_LEN = 50;

    static double poi_history[HISTORY_LEN];

    static double ke_history[HISTORY_LEN];

    static double wmax_history[HISTORY_LEN];

    static int hist_idx;

    static int hist_cnt;

public:

    bool converged = false;

    bool has_paradox = false;

    string paradox_message;

    int warning_level = 0;

    string warning_message;

    double poi_trend = 0.0;

    double ke_trend = 0.0;

    double gamma_consistency = 0.0;

    double spectral_entropy = 0.0;



    PhiGateOp(Field& field, double ms, double rh, double de, double la, double c2v,

              double pr, double ec, int st)

        : f(field), msigma(ms), rho(rh), delta(de), lambda(la), c2(c2v),

          poisson_res(pr), energy_change(ec), step(st), warning_level(0) {}



    void set_response(int warning_level) {

        dt_scale_ = 1.0; should_rain_ = false;

        if (warning_level == 1) { dt_scale_ = 0.8; }

        else if (warning_level == 2) { dt_scale_ = 0.5; should_rain_ = true; }

    }

    double get_dt_scale() const { return dt_scale_; }

    bool should_rain() const { return should_rain_; }



    void apply() override {

        static int converged_counter = 0;

        has_paradox = false; paradox_message = "";

        warning_level = 0; warning_message = "";

        int N = f.active_N;



        poi_history[hist_idx] = poisson_res;

        ke_history[hist_idx] = f.ke;

        wmax_history[hist_idx] = f.wmax;

        hist_idx = (hist_idx + 1) % HISTORY_LEN;

        if (hist_cnt < HISTORY_LEN) hist_cnt++;



        for (int i = 1; i < N - 1; i++) for (int j = 1; j < N - 1; j++) {

            if (isnan(f.w[i][j]) || isinf(f.w[i][j])) {

                has_paradox = true; paradox_message = "ZFC: NaN/Inf in vorticity"; return;

            }

            if (fabs(f.w[i][j]) > 1e6) {

                has_paradox = true; paradox_message = "ZFC: w_max > 1e6"; return;

            }

        }

        double ke = 0;

        for (int i = 1; i < N - 1; i++) for (int j = 1; j < N - 1; j++)

            ke += f.u[i][j] * f.u[i][j] + f.v[i][j] * f.v[i][j];

        ke *= 0.5 / ((N - 2) * (N - 2));

        if (ke > 1000.0) {

            has_paradox = true; paradox_message = "ZFC: KE explosion > 1000"; return;

        }



        if (hist_cnt >= 10) {

            double recent_poi = 0, old_poi = 0;

            for (int k = 0; k < 5; k++) {

                int idx_r = (hist_idx - 1 - k + HISTORY_LEN) % HISTORY_LEN;

                int idx_o = (hist_idx - 6 - k + HISTORY_LEN) % HISTORY_LEN;

                recent_poi += poi_history[idx_r];

                old_poi += poi_history[idx_o];

            }

            poi_trend = (recent_poi - old_poi) / (old_poi + 1e-10);



            double recent_ke = 0, old_ke = 0;

            for (int k = 0; k < 5; k++) {

                int idx_r = (hist_idx - 1 - k + HISTORY_LEN) % HISTORY_LEN;

                int idx_o = (hist_idx - 6 - k + HISTORY_LEN) % HISTORY_LEN;

                recent_ke += ke_history[idx_r];

                old_ke += ke_history[idx_o];

            }

            ke_trend = (recent_ke - old_ke) / (old_ke + 1e-10);



            double g_mean = 0, g_var = 0;

            int g_cnt = 0;

            for (int i = 2; i < N - 2; i++) for (int j = 2; j < N - 2; j++) {

                double gx = fabs(f.w[i][j+1] - f.w[i][j-1]);

                double gy = fabs(f.w[i+1][j] - f.w[i-1][j]);

                double g = sqrt(gx*gx + gy*gy);

                g_mean += g; g_var += g*g; g_cnt++;

            }

            if (g_cnt > 0) {

                g_mean /= g_cnt;

                g_var = g_var/g_cnt - g_mean*g_mean;

                gamma_consistency = sqrt(max(0.0, g_var)) / (g_mean + 1e-10);

            }



            double wmax_mean = 0;

            for (int k = 0; k < hist_cnt; k++) wmax_mean += wmax_history[k];

            wmax_mean /= hist_cnt;

            spectral_entropy = (wmax_mean > 1e-10) ? fabs(f.wmax - wmax_mean) / wmax_mean : 0.0;

        }



        // L0: unsteady structural warning -- trend only, not absolute values
        if (step < 1000) {

            // Condition A: Poisson residual accelerating deterioration (CG solver can't keep up with flow evolution)
            if (poi_trend > 1.0) {

                warning_level = 1;

                warning_message = "L0: CG lagging (poi_trend=" + to_string((int)(poi_trend*100)) + "%)";

            }

            // Condition B: abnormal KE loss (excessive numerical dissipation or energy leak)

            else if (ke_trend < -0.5 && f.ke > 1.0) {

                warning_level = 1;

                warning_message = "L0: KE draining";

            }

            // Condition C: wmax exponential growth (imminent blow-up)

            else if (spectral_entropy > 1.0) {

                warning_level = 2;

                warning_message = "L0: wmax runaway";

            }

        }



        // L1: developing-phase structural reorganization detection
        if (step >= 1000 && warning_level == 0) {

            // Check MSigma+Rho combination only (structural reorganization signal), not Poisson absolute value
            if (msigma > 0.1 && rho < 0.3) {

                warning_level = 1;

                warning_message = "L1: Structure reorganization";

            }

            // Long-term Poisson residual trend deterioration (CG budget insufficient)
            else if (poi_trend > 2.0) {

                warning_level = 1;

                warning_message = "L1: CG severely lagging";

            }

        }



        if (step > 10000 && poisson_res < 1e-4 && fabs(energy_change) < 1e-2

            && msigma < 0.05 && rho > 0.5) {

            converged_counter++;

        } else {

            converged_counter = 0;

        }

        converged = (converged_counter > 10);

    }



    bool is_converged() const { return converged; }

    bool is_safe() const { return !has_paradox; }

    string get_paradox() const { return paradox_message; }

    OperatorMeta get_meta() const override { return { "Phi-017","A3-001","Gate","ZFC+~CH+Phi","Axiom" }; }

};



double PhiGateOp::poi_history[PhiGateOp::HISTORY_LEN] = {0};

double PhiGateOp::ke_history[PhiGateOp::HISTORY_LEN] = {0};

double PhiGateOp::wmax_history[PhiGateOp::HISTORY_LEN] = {0};

int PhiGateOp::hist_idx = 0;

int PhiGateOp::hist_cnt = 0;

class TauRollbackOp : public Operator {

    Field& f; Field& checkpoint;

    double dt_scale_;

    bool should_rain_;

public:

    TauRollbackOp(Field& field, Field& ckpt) : f(field), checkpoint(ckpt), dt_scale_(1.0), should_rain_(false) {}

    void set_response(int warning_level) {

        dt_scale_ = 1.0; should_rain_ = false;

        if (warning_level == 1) { dt_scale_ = 0.8; }

        else if (warning_level == 2) { dt_scale_ = 0.5; should_rain_ = true; }

    }

    double get_dt_scale() const { return dt_scale_; }

    bool should_rain() const { return should_rain_; }

    void apply() override {

        int N = f.active_N;

        for (int i = 0; i < N; i++) for (int j = 0; j < N; j++) {

            f.w[i][j] = checkpoint.w[i][j];

            f.s[i][j] = checkpoint.s[i][j];

            f.u[i][j] = checkpoint.u[i][j];

            f.v[i][j] = checkpoint.v[i][j];

        }

        f.ke = checkpoint.ke;

        f.wmax = checkpoint.wmax;

        f.poisson_res = checkpoint.poisson_res;

    }

    OperatorMeta get_meta() const override {

        return { "Tau-007","A1-007","Rollback","S_t <- ckpt","Recovery" };

    }

};



// ============================================================================

// LambdaGlobalOp -- Lambda deviation warning

// ============================================================================

class LambdaGlobalOp : public Operator {

    Field& f; double lambda_val;

public:

    LambdaGlobalOp(Field& field) : f(field), lambda_val(0.5) {}

    void set_response(int warning_level) {

        dt_scale_ = 1.0; should_rain_ = false;

        if (warning_level == 1) { dt_scale_ = 0.8; }

        else if (warning_level == 2) { dt_scale_ = 0.5; should_rain_ = true; }

    }

    double get_dt_scale() const { return dt_scale_; }

    bool should_rain() const { return should_rain_; }

    void apply() override {

        int N = f.active_N;

        double wsum = 0.0, w2sum = 0.0;

        for (int i = 1; i < N - 1; i++) for (int j = 1; j < N - 1; j++) {

            wsum += fabs(f.w[i][j]);

            w2sum += f.w[i][j] * f.w[i][j];

        }

        double meanw = wsum / ((N - 2) * (N - 2));

        double varw = w2sum / ((N - 2) * (N - 2)) - meanw * meanw;

        lambda_val = sqrt(max(0.0, varw)) / (meanw + 1e-10);

    }

    double get_lambda() const { return lambda_val; }

    OperatorMeta get_meta() const override {

        return { "Lambda-008","A1-008","Warning","sqrt(var)/mean","Deviation" };

    }

};



// ============================================================================

// PsiReconstructOp -- Psi-014 field reconstruction + dt suggestion

// ============================================================================

class PsiReconstructOp : public Operator {

    Field& f; double dx, nu;

    double suggested_dt;

public:

    PsiReconstructOp(Field& field, double dx_val, double nu_val)

        : f(field), dx(dx_val), nu(nu_val), suggested_dt(1e-4) {}

    void set_response(int warning_level) {

        dt_scale_ = 1.0; should_rain_ = false;

        if (warning_level == 1) { dt_scale_ = 0.8; }

        else if (warning_level == 2) { dt_scale_ = 0.5; should_rain_ = true; }

    }

    double get_dt_scale() const { return dt_scale_; }

    bool should_rain() const { return should_rain_; }

    void apply() override {

        int N = f.active_N;

        double umax = 0.0;

        for (int i = 0; i < N; i++) for (int j = 0; j < N; j++) {

            double vel = fabs(f.u[i][j]) + fabs(f.v[i][j]);

            if (vel > umax) umax = vel;

        }

        double cfl = 0.5 * dx / (umax + 1e-10);

        double diff = 0.25 * dx * dx / nu;

        suggested_dt = min(cfl, diff);

        suggested_dt = max(1e-6, min(0.01, suggested_dt));

    }

    OperatorMeta get_meta() const override {

        return { "Psi-014","A1-009","Reconstruction","dt=min(CFL,diff)","Adaptive dt" };

    }

    double get_suggested_dt() const { return suggested_dt; }

};



// ============================================================================

// SigmaSpectralOp -- Sigma uncertainty (v2.5: 3-component clip model)
// Theory mapping: sigma_data/0.5, delta_model(L^2)/2.0, eta_shock/1.0

// Prop 3.1' requires [Gamma,Sigma]=0, so delta_model uses L2 norm

// ============================================================================

// EnergyBudgetOp -- energy budget monitor operator (v2.5-fix: operator-ified, in monitor pipeline)

// ============================================================================

class EnergyBudgetOp : public Operator {

    Field& f;

    EnergyBudget& eb;

    double& last_ke_;

    double phase_lock_val_;

    bool window_ready_;

    bool self_cloud_;

public:

    EnergyBudgetOp(Field& field, EnergyBudget& budget, double& last_ke)

        : f(field), eb(budget), last_ke_(last_ke), phase_lock_val_(0.0), window_ready_(false), self_cloud_(false) {}

    void set_response(int warning_level) {

        dt_scale_ = 1.0; should_rain_ = false;

        if (warning_level == 1) { dt_scale_ = 0.8; }

        else if (warning_level == 2) { dt_scale_ = 0.5; should_rain_ = true; }

    }

    double get_dt_scale() const { return dt_scale_; }

    bool should_rain() const { return should_rain_; }

    void apply() override {

        eb.update(f.ke, last_ke_);

        last_ke_ = f.ke;

        phase_lock_val_ = eb.getPhaseLock();

        window_ready_ = eb.isWindowReady();

        self_cloud_ = eb.isSelfCloud();

    }

    double getPhaseLock() const { return phase_lock_val_; }

    bool isWindowReady() const { return window_ready_; }

    bool isSelfCloud() const { return self_cloud_; }

    OperatorMeta get_meta() const override {

        return { "EB-019","A2-019","EnergyBudget","update+cloud_state","Self-Cloud" };

    }

};



// ============================================================================

class SigmaSpectralOp : public Operator {

    Field& f; double dx;

    double sigma_val;

    // v2.5 added: 3 components

    double sigma_data_;   // data component: vorticity field std / 0.5

    double delta_model_;  // model component: velocity L2 residual / 2.0 ([Gamma,Sigma]=0 condition)
    double eta_shock_;    // shock component: wmax sudden-change rate / 1.0

    double prev_wmax_;

public:

    SigmaSpectralOp(Field& field, double dx_val = 0.0)

        : f(field), dx(dx_val), sigma_val(0.0),

          sigma_data_(0.0), delta_model_(0.0), eta_shock_(0.0), prev_wmax_(0.0) {}

    void set_response(int warning_level) {

        dt_scale_ = 1.0; should_rain_ = false;

        if (warning_level == 1) { dt_scale_ = 0.8; }

        else if (warning_level == 2) { dt_scale_ = 0.5; should_rain_ = true; }

    }

    double get_dt_scale() const { return dt_scale_; }

    bool should_rain() const { return should_rain_; }

    void apply() override {

        int N = f.active_N;

        int inner = (N - 2) * (N - 2);



        // Component 1: sigma_data = std / 0.5 (generalization of classic std/mean)

        double mean = 0.0;

        for (int i = 1; i < N - 1; i++) for (int j = 1; j < N - 1; j++) mean += f.w[i][j];

        mean /= inner;

        double var = 0.0;

        for (int i = 1; i < N - 1; i++) for (int j = 1; j < N - 1; j++) var += (f.w[i][j] - mean) * (f.w[i][j] - mean);

        var /= inner;

        sigma_data_ = sqrt(max(0.0, var)) / (fabs(mean) + 1e-10);

        sigma_data_ = min(sigma_data_, 0.5);  // clip at 0.5



        // Component 2: delta_model = ||u - u_ref||_{L2} / 2.0

        // u_ref = Theta-reconstructed velocity; here use current u-field divergence residual as model error proxy

        // [Gamma,Sigma]=0 condition requires L2 norm

        if (dx > 0) {

            double l2_err = 0.0;

            for (int i = 1; i < N - 1; i++) for (int j = 1; j < N - 1; j++) {

                // Continuity residual as model error
                double div = (f.u[i][j + 1] - f.u[i][j - 1]) / (2 * dx) + (f.v[i + 1][j] - f.v[i - 1][j]) / (2 * dx);

                l2_err += div * div;

            }

            delta_model_ = sqrt(l2_err / inner);

            delta_model_ = min(delta_model_, 5.0);  // clip at 2.0

        } else {

            delta_model_ = 0.0;

        }



        // Component 3: eta_shock = |dwmax/dt| / 1.0

        double wmax_curr = 0.0;

        for (int i = 1; i < N - 1; i++) for (int j = 1; j < N - 1; j++) {

            if (fabs(f.w[i][j]) > wmax_curr) wmax_curr = fabs(f.w[i][j]);

        }

        eta_shock_ = (prev_wmax_ > 1e-10) ? fabs(wmax_curr - prev_wmax_) / prev_wmax_ : 0.0;

        eta_shock_ = min(eta_shock_, 1.0);  // clip at 1.0

        prev_wmax_ = wmax_curr;



        // Total Sigma = max(3 components) -- oplus max, explicitly annotated
        sigma_val = max({sigma_data_, delta_model_, eta_shock_});

    }

    double get_sigma() const { return sigma_val; }

    double get_sigma_data() const { return sigma_data_; }

    double get_delta_model() const { return delta_model_; }

    double get_eta_shock() const { return eta_shock_; }

    OperatorMeta get_meta() const override {

        return { "Sigma-009","A1-009","Spectral3Clip","max(sigma_d/0.5,delta_m/2.0,eta_s/1.0)","Uncertainty" };

    }

};



class MonitorV1Op : public Operator {

    Field& f; double v1;

public:

    MonitorV1Op(Field& field) : f(field), v1(0.0) {}

    void set_response(int warning_level) {

        dt_scale_ = 1.0; should_rain_ = false;

        if (warning_level == 1) { dt_scale_ = 0.8; }

        else if (warning_level == 2) { dt_scale_ = 0.5; should_rain_ = true; }

    }

    double get_dt_scale() const { return dt_scale_; }

    bool should_rain() const { return should_rain_; }

    void apply() override {

        int N = f.active_N;

        double max_dw = 0.0;

        for (int i = 1; i < N - 1; i++) for (int j = 1; j < N - 1; j++) {

            double dw = fabs(f.w[i][j]);

            if (dw > max_dw) max_dw = dw;

        }

        v1 = (f.wmax > 1e-10) ? max_dw / f.wmax : 0;

    }

    double get_value() const { return v1; }

    OperatorMeta get_meta() const override { return { "V1-011","A2-011","Monitor","max|w|/wmax","Change rate" }; }

};



class EnergyMonitorOp : public Operator {

    Field& f; double dx;

public:

    EnergyMonitorOp(Field& field, double dx_val) : f(field), dx(dx_val) {}

    void set_response(int warning_level) {

        dt_scale_ = 1.0; should_rain_ = false;

        if (warning_level == 1) { dt_scale_ = 0.8; }

        else if (warning_level == 2) { dt_scale_ = 0.5; should_rain_ = true; }

    }

    double get_dt_scale() const { return dt_scale_; }

    bool should_rain() const { return should_rain_; }

    void apply() override {

        int N = f.active_N;

        double area = dx * dx;

        double ke = 0.0;

        for (int i = 0; i < N; i++) for (int j = 0; j < N; j++) {

            ke += 0.5 * (f.u[i][j] * f.u[i][j] + f.v[i][j] * f.v[i][j]) * area;

        }

        f.ke_prev = f.ke;

        f.ke = ke;

    }

    OperatorMeta get_meta() const override { return { "E_mon-012","A2-012","Energy","0.5*rho*(u^2+v^2)","KE monitor" }; }

};



class VortexLocatorOp : public Operator {

    Field& f; double dx;

    double vx, vy, strength;

    // v2.5 added: vortex-center drift rate (for cloud memory adaptation)

    double prev_vx_, prev_vy_;

    double drift_rate_;

public:

    VortexLocatorOp(Field& field, double dx_val) : f(field), dx(dx_val), vx(0.5), vy(0.5), strength(0.0),

        prev_vx_(0.5), prev_vy_(0.5), drift_rate_(0.0) {}

    void set_response(int warning_level) {

        dt_scale_ = 1.0; should_rain_ = false;

        if (warning_level == 1) { dt_scale_ = 0.8; }

        else if (warning_level == 2) { dt_scale_ = 0.5; should_rain_ = true; }

    }

    double get_dt_scale() const { return dt_scale_; }

    bool should_rain() const { return should_rain_; }

    void apply() override {

        int N = f.active_N;

        // Primary vortex center = argmax(psi) in interior region
        // For lid-driven cavity with ∇²ψ = -ω: primary vortex (ω<0) has ψ > 0
        // So the primary vortex center corresponds to the MAXIMUM of ψ
        int margin = max(2, N / 16);
        double maxpsi = -1e20;
        int mi = N / 2, mj = N / 2;

        for (int i = margin; i < N - margin; i++) for (int j = margin; j < N - margin; j++) {

            if (f.s[i][j] > maxpsi) { maxpsi = f.s[i][j]; mi = i; mj = j; }

        }

        prev_vx_ = vx; prev_vy_ = vy;

        vx = mj * dx;

        vy = mi * dx;

        strength = fabs(maxpsi);

        // drift rate
        double ddx = vx - prev_vx_, ddy = vy - prev_vy_;

        drift_rate_ = sqrt(ddx * ddx + ddy * ddy);

    }

    double get_vx() const { return vx; }

    double get_vy() const { return vy; }

    double get_strength() const { return strength; }

    double get_drift_rate() const { return drift_rate_; }

    OperatorMeta get_meta() const override { return { "Vort-013","A2-013","Locator+Drift","argmin(psi)+drift","Vortex center" }; }

};



class BoundaryLayerOp : public Operator {

    Field& f; double dx;

    double bl_thick, shear_max;

public:

    BoundaryLayerOp(Field& field, double dx_val) : f(field), dx(dx_val), bl_thick(0.05), shear_max(0.0) {}

    void set_response(int warning_level) {

        dt_scale_ = 1.0; should_rain_ = false;

        if (warning_level == 1) { dt_scale_ = 0.8; }

        else if (warning_level == 2) { dt_scale_ = 0.5; should_rain_ = true; }

    }

    double get_dt_scale() const { return dt_scale_; }

    bool should_rain() const { return should_rain_; }

    void apply() override {

        int N = f.active_N;

        double u_target = 0.99 * 1.0;

        int bl_grid = 0;

        for (int i = N - 2; i >= 0; i--) {

            if (fabs(f.u[i][N / 2]) < u_target) { bl_grid = N - 1 - i; break; }

        }

        bl_thick = bl_grid * dx;

        shear_max = 0.0;

        for (int j = 1; j < N - 1; j++) {

            double shear = fabs(3*f.u[N-1][j] - 4*f.u[N-2][j] + f.u[N-3][j]) / (2*dx);

            if (shear > shear_max) shear_max = shear;

        }

    }

    double get_bl_thickness() const { return bl_thick; }

    double get_shear_max() const { return shear_max; }

    OperatorMeta get_meta() const override { return { "BL-015","A2-015","BL","delta99","Boundary layer" }; }

};



// ============================================================================

// InterpolationOp -- inter-level interpolation (unchanged)
// ============================================================================

class InterpolationOp : public Operator {

    Field& src; Field& dst;

    NestMemory& mem; double U_LID;

    double (*src_gamma_)[512]; double (*dst_gamma_)[512];

    GTRPoissonOp* dst_gtr_;

public:

    InterpolationOp(Field& s, Field& d, NestMemory& m, double u_lid,

        double (*sg)[512] = nullptr, double (*dg)[512] = nullptr, GTRPoissonOp* dgtr = nullptr)

        : src(s), dst(d), mem(m), U_LID(u_lid), src_gamma_(sg), dst_gamma_(dg), dst_gtr_(dgtr) {}

    void set_response(int warning_level) {

        dt_scale_ = 1.0; should_rain_ = false;

        if (warning_level == 1) { dt_scale_ = 0.8; }

        else if (warning_level == 2) { dt_scale_ = 0.5; should_rain_ = true; }

    }

    double get_dt_scale() const { return dt_scale_; }

    bool should_rain() const { return should_rain_; }

    void apply() override {

        int Ns = src.active_N;

        int Nd = dst.active_N;

        double dx_d = 1.0 / (Nd - 1);



        for (int i = 0; i < Nd; i++) for (int j = 0; j < Nd; j++) {

            double x = j * (Ns - 1.0) / (Nd - 1.0);

            double y = i * (Ns - 1.0) / (Nd - 1.0);

            int i0 = (int)y, j0 = (int)x;

            int i1 = min(i0 + 1, Ns - 1), j1 = min(j0 + 1, Ns - 1);

            double wy = y - i0, wx = x - j0;

            dst.w[i][j] = (1-wy)*(1-wx)*src.w[i0][j0] + (1-wy)*wx*src.w[i0][j1] + wy*(1-wx)*src.w[i1][j0] + wy*wx*src.w[i1][j1];

            dst.s[i][j] = (1-wy)*(1-wx)*src.s[i0][j0] + (1-wy)*wx*src.s[i0][j1] + wy*(1-wx)*src.s[i1][j0] + wy*wx*src.s[i1][j1];

            dst.u[i][j] = (1-wy)*(1-wx)*src.u[i0][j0] + (1-wy)*wx*src.u[i0][j1] + wy*(1-wx)*src.u[i1][j0] + wy*wx*src.u[i1][j1];

            dst.v[i][j] = (1-wy)*(1-wx)*src.v[i0][j0] + (1-wy)*wx*src.v[i0][j1] + wy*(1-wx)*src.v[i1][j0] + wy*wx*src.v[i1][j1];

        }

        dst.active_N = Nd;



        if (src_gamma_ && dst_gamma_ && dst_gtr_) {

            double cloud_scale = (Nd - 1.0) / (Nd - 2.0);

            for (int i = 0; i < Nd; i++) for (int j = 0; j < Nd; j++) {

                double x = j * (Ns - 1.0) / (Nd - 1.0);

                double y = i * (Ns - 1.0) / (Nd - 1.0);

                int i0 = (int)y, j0 = (int)x;

                int i1 = min(i0 + 1, Ns - 1), j1 = min(j0 + 1, Ns - 1);

                double wy = y - i0, wx = x - j0;

                double g = (1-wy)*(1-wx)*src_gamma_[i0][j0]

                         + (1-wy)*wx*src_gamma_[i0][j1]

                         + wy*(1-wx)*src_gamma_[i1][j0]

                         + wy*wx*src_gamma_[i1][j1];

                dst_gamma_[i][j] = g * cloud_scale;

            }

            // Gamma field post-interpolation smoothing (suppress high-frequency noise)

            for (int iter = 0; iter < 3; iter++) {

                for (int i = 1; i < Nd - 1; i++) for (int j = 1; j < Nd - 1; j++) {

                    dst_gamma_[i][j] = 0.25 * (dst_gamma_[i][j] + dst_gamma_[i-1][j] + dst_gamma_[i+1][j] + dst_gamma_[i][j-1] + dst_gamma_[i][j+1]);

                }

            }

            // Gamma field post-interpolation smoothing (suppress high-frequency noise)

            for (int iter = 0; iter < 3; iter++) {

                for (int i = 1; i < Nd - 1; i++) for (int j = 1; j < Nd - 1; j++) {

                    dst_gamma_[i][j] = 0.25 * (dst_gamma_[i][j] + dst_gamma_[i-1][j] + dst_gamma_[i+1][j] + dst_gamma_[i][j-1] + dst_gamma_[i][j+1]);

                }

            }

            dst_gtr_->syncGammaFromCloud(dst_gamma_, Nd);

            dst_gtr_->compute_gamma_half(Nd);

            cout << "[CLOUD] Gamma interpolated, max=" << dst_gtr_->getMaxGamma()

                 << " scale=" << cloud_scale << endl;

        }



        for (int j = 0; j < Nd; j++) { dst.s[0][j] = 0; dst.s[Nd - 1][j] = 0; }

        for (int i = 0; i < Nd; i++) { dst.s[i][0] = 0; dst.s[i][Nd - 1] = 0; }

        for (int j = 0; j < Nd; j++) { dst.u[0][j] = 0; dst.u[Nd - 1][j] = U_LID; dst.v[0][j] = 0; dst.v[Nd - 1][j] = 0; }

        for (int i = 0; i < Nd; i++) { dst.u[i][0] = 0; dst.u[i][Nd - 1] = 0; dst.v[i][0] = 0; dst.v[i][Nd - 1] = 0; }



        for (int j = 0; j < Nd; j++) { dst.s[0][j] = 0; dst.s[Nd - 1][j] = 0; }

        for (int i = 0; i < Nd; i++) { dst.s[i][0] = 0; dst.s[i][Nd - 1] = 0; }

        for (int j = 0; j < Nd; j++) { dst.u[0][j] = 0; dst.u[Nd - 1][j] = U_LID; dst.v[0][j] = 0; dst.v[Nd - 1][j] = 0; }

        for (int i = 0; i < Nd; i++) { dst.u[i][0] = 0; dst.u[i][Nd - 1] = 0; dst.v[i][0] = 0; dst.v[i][Nd - 1] = 0; }

        

        dst.wmax = 0.0;

        for (int i = 0; i < Nd; i++) for (int j = 0; j < Nd; j++)

            if (fabs(dst.w[i][j]) > dst.wmax) dst.wmax = fabs(dst.w[i][j]);

        double wmin=1e20, wmean=0; int wcnt=0;

        for(int i=0;i<Nd;i++)for(int j=0;j<Nd;j++){if(fabs(dst.w[i][j])<wmin)wmin=fabs(dst.w[i][j]);wmean+=fabs(dst.w[i][j]);wcnt++;}

        wmean/=wcnt;

        cout << "[INTERP] w interpolated directly, wmax=" << dst.wmax << " wmin=" << wmin << " wmean=" << wmean << endl;

    }

    OperatorMeta get_meta() const override { return { "Interp-016","A3-016","Interpolate","bilinear+init_chain","Grid transfer" }; }

};





// ============================================================================

// LevelSolver -- unsteady solver main controller (v2.5: operator self-decision, no stage enum)

// ============================================================================

class LevelSolver {

public:

    LevelConfig cfg;

    Field field, checkpoint;

    NestMemory memory;



    unique_ptr<XiAnchorOp> xi;

    unique_ptr<ThetaGradientOp> theta;

    unique_ptr<GTRPoissonOp> gtr;

    unique_ptr<DRIBoundaryOp> dri;

    unique_ptr<RK4TimeOp> rk4;

    unique_ptr<PsiReconstructOp> psi;

    unique_ptr<PhiGateOp> phi;

    unique_ptr<TauRollbackOp> tau;

    unique_ptr<LambdaGlobalOp> lambda;

    unique_ptr<SigmaSpectralOp> sigma;

    unique_ptr<MonitorV1Op> v1;

    unique_ptr<EnergyMonitorOp> energy;

    unique_ptr<VortexLocatorOp> vortloc;

    unique_ptr<BoundaryLayerOp> bl;

    unique_ptr<EnergyBudget> energy_budget;

    unique_ptr<EnergyBudgetOp> energy_budget_op;



    // Monitor Committee (always online)
    unique_ptr<MSigmaOp> msigma_op;

    unique_ptr<RhoElasticityOp> rho_op;

    unique_ptr<DeltaSaturationOp> delta_op;

    unique_ptr<ConsistencyOp> con_op;

    unique_ptr<LambdaCouplingOp> lambda_coupling;

    unique_ptr<CurvatureEnergyOp> c2_op;



    double dt;

    int current_step;

    double time;

    int rollback_count;

    double cloud_memory_gamma_max;

    double cloud_memory_time;

    double cloud_gamma_cache[512][512];
    ofstream csv_fout;
    string csv_path;
    struct ConvergenceRecord { int step; double time, dt, ke, wmax, poi_res, sigma, lambda_val; };
    vector<ConvergenceRecord> conv_history;

    double last_Msigma;

    double prev_ke;



    // v2.5 added: MAC divergence threshold (adaptive, no longer hard-coded stage checks)
    double mac_div_threshold_;

    // v2.5 added: cloud memory adaptive interval parameters

    double cloud_update_interval_;   // current update interval (physical time)

    double cloud_min_interval_;      // minimum interval
    double cloud_max_interval_;      // maximum interval
    double report_vx_, report_vy_;   // vortex center position at last report



    LevelSolver(const LevelConfig& c)

        : cfg(c), dt(c.DT_INIT), current_step(0), time(0.0), rollback_count(0),

          cloud_memory_gamma_max(1.0), cloud_memory_time(0.0), last_Msigma(0.0), prev_ke(0.0),

          mac_div_threshold_(1e-3), cloud_update_interval_(1.425e-3),

          cloud_min_interval_(1e-4), cloud_max_interval_(0.01),

          report_vx_(0.5), report_vy_(0.5) {

        field.zero(c.N); checkpoint.zero(c.N); memory.zero();

        double dx = 1.0 / (c.N - 1);



        xi = make_unique<XiAnchorOp>(field, dx, c.U_LID);

        theta = make_unique<ThetaGradientOp>(field, dx, c.U_LID);

        gtr = make_unique<GTRPoissonOp>(field, dx, c.POISSON_ITER, c.POISSON_TOL, c.ALPHA);

        dri = make_unique<DRIBoundaryOp>(field, dx, 0.1, c.U_LID);

        rk4 = make_unique<RK4TimeOp>(field, dt, dx, c.NU, c.U_LID,

            c.RK4_SUB_POISSON_ITER, c.RK4_SUB_POISSON_TOL, gtr.get());

        psi = make_unique<PsiReconstructOp>(field, dx, c.NU);

        phi = make_unique<PhiGateOp>(field, 0.0, 0.5, 0.0, 0.5, 0.0, 0.0, 0.0, 0);

        tau = make_unique<TauRollbackOp>(field, checkpoint);

        lambda = make_unique<LambdaGlobalOp>(field);

        sigma = make_unique<SigmaSpectralOp>(field, dx);

        v1 = make_unique<MonitorV1Op>(field);

        energy = make_unique<EnergyMonitorOp>(field, dx);

        energy_budget = make_unique<EnergyBudget>(dt, dx * dx);

        energy_budget_op = make_unique<EnergyBudgetOp>(field, *energy_budget, prev_ke);        vortloc = make_unique<VortexLocatorOp>(field, dx);

        bl = make_unique<BoundaryLayerOp>(field, dx);



        msigma_op = make_unique<MSigmaOp>(field, last_Msigma);

        rho_op = make_unique<RhoElasticityOp>(field, dx);

        delta_op = make_unique<DeltaSaturationOp>(field, prev_ke);

        con_op = make_unique<ConsistencyOp>(field, dx);

        lambda_coupling = make_unique<LambdaCouplingOp>(field);

        c2_op = make_unique<CurvatureEnergyOp>(field, dx);



        memset(cloud_gamma_cache, 0, sizeof(cloud_gamma_cache));

    }



    void cold_start() {

        int N = cfg.N;

        for (int i = N / 4; i < 3 * N / 4; i++)

            for (int j = N / 4; j < 3 * N / 4; j++)

                field.w[i][j] = 0.001 * sin(M_PI * (i - N / 4.0) / (N / 2.0)) * sin(M_PI * (j - N / 4.0) / (N / 2.0));



        xi->apply();

        gtr->apply();

        theta->apply();

        dri->apply();

        energy->apply();



        field.wmax = 0.0;

        for (int i = 0; i < N; i++) for (int j = 0; j < N; j++)

            if (fabs(field.w[i][j]) > field.wmax) field.wmax = fabs(field.w[i][j]);

    }



    void warm_start(const NestMemory& parent_mem) {

        energy_budget->reset();

        memory = parent_mem;

        dt = parent_mem.stable_dt;

        cloud_memory_gamma_max = parent_mem.cloud_gamma_max;

        cloud_memory_time = 0.0;

        // v2.5.1 fix: stricter dt floor to prevent dt=0 from abnormal stable_dt
        if (dt < 1e-6 || dt > 0.1 || std::isnan(dt)) {
            // Estimate reasonable initial dt from grid size: CFL condition dt ~ 0.25*h^2/nu
            double h = 1.0 / (cfg.N - 1);
            dt = 0.25 * h * h / cfg.NU;
            dt = max(1e-6, min(0.01, dt));
        }

        energy_budget->setDt(dt);

        gtr->set_max_iter(cfg.POISSON_ITER * 2);
        // v2.6: open CSV for incremental writing
        csv_path = "results/Re" + to_string((int)cfg.Re) + "/L" + to_string(cfg.N) + "_convergence.csv";
        csv_fout.open(csv_path);
        if (csv_fout.is_open()) csv_fout << "step,time,dt,KE,wmax,poisson_res,sigma,lambda" << endl;

        // v2.5: no STAGE_0_INTERP, no stage concept

    }



    bool advance() {

        int N = cfg.N;

        if (dt < 1e-10 || dt > 0.1 || std::isnan(dt)) {

            cerr << "[FATAL] dt abnormal: " << dt << ", rollback" << endl;

            tau->apply(); dt = 1e-6; return true;

        }



        // v2.5 core: operator self-decision pipeline

        // All operators always online -- monitor operators zero gating cost, execution operators internally physics-triggered


        // ---- Monitor pipeline (always online, read-only scalar reduction) ----

        msigma_op->apply();

        rho_op->apply();

        delta_op->apply();

        con_op->apply();

        lambda_coupling->apply();

        c2_op->apply();

        lambda->apply();

        v1->apply();

        sigma->apply();   // v2.5: 3-component clip

        vortloc->apply(); // v2.5: includes drift rate

        bl->apply();

        energy_budget_op->apply(); // v2.5-fix: EnergyBudget operator-ified, in monitor pipeline

        // ---- Strategy adaptation (physics-triggered, no step thresholds) ----

        static int last_dt_adapt_step = -100;

        static int last_cg_adapt_step = -100;

        static int last_gamma_adapt_step = -100;

        int adapt_cooldown = 10;



        // 1. dt adaptation: wmax surge relative to historical mean
        static double wmax_history_avg = 0;

        static int wmax_history_cnt = 0;

        if (field.wmax > 0 && wmax_history_cnt < 5000) {

            wmax_history_avg = (wmax_history_avg * wmax_history_cnt + field.wmax) / (wmax_history_cnt + 1);

            wmax_history_cnt++;

        }

        double wmax_threshold = (wmax_history_cnt >= 100) ? wmax_history_avg * 1.5 : 1e20;

        if (field.wmax > wmax_threshold && (current_step - last_dt_adapt_step) > adapt_cooldown) {

            dt *= 0.8;

            if (dt < 1e-6) dt = 1e-6;

            energy_budget->setDt(dt);

            last_dt_adapt_step = current_step;

        }



        // 2. CG budget adaptation: increase iterations when Poisson residual rebounds
        if (field.poisson_res > 1.0 && (current_step - last_cg_adapt_step) > adapt_cooldown) {

            int new_iter = min(5000, (int)(cfg.POISSON_ITER * 1.5));

            gtr->set_max_iter(new_iter);

            last_cg_adapt_step = current_step;

        }



        // 3. Gamma preconditioner adaptation: strengthen alpha during vortex-center drift

        double vort_drift = fabs(vortloc->get_vy() - memory.vortex_y);

        if (vort_drift > 0.1 && (current_step - last_gamma_adapt_step) > adapt_cooldown) {

            double new_alpha = min(0.5, cfg.ALPHA * 1.2);

            gtr->set_alpha(new_alpha);

            last_gamma_adapt_step = current_step;

        }



        // 4. v2.5 added: MAC divergence threshold adaptation -- gradually tighten as flow develops

        // MAC divergence threshold dynamic adjustment -- based on Poisson residual + step count

        double poi_res = field.poisson_res;

        if (poi_res > 1.0) {

            mac_div_threshold_ = 0.5;      // Poisson divergence phase: relaxed

        } else if (poi_res > 0.1) {

            mac_div_threshold_ = 0.1;      // è¿æ¸¡æ?
        } else if (current_step < 500) {

            mac_div_threshold_ = 0.1;      // startup phase
        } else if (current_step < 3000) {

            mac_div_threshold_ = 0.05;     // developing phase
        } else {

            mac_div_threshold_ = 0.01;     // steady phase: still not tightened to 1e-3

        }





        // âââ æ§è¡æµæ°´çº?âââ

        xi->apply();      // v2.5: includes deviation computation
        theta->apply();

        dri->apply();



        // [CLOUD+Rain] Cloud memory adaptive update interval (v2.5: vortex-center drift-driven)

        // Large drift -> frequent updates (small interval); small drift -> sparse updates (large interval)
        double drift = vortloc->get_drift_rate();

        if (drift > 1e-6) {

            // Inverse mapping: drift rate to update interval
            // Larger drift -> shorter interval (more frequent updates)

            double drift_scaled = drift * 1000.0;

            if (drift_scaled > 10.0) drift_scaled = 10.0;

            cloud_update_interval_ = cloud_min_interval_ + (cloud_max_interval_ - cloud_min_interval_) * exp(-drift_scaled);



        } else {

            // Use maximum interval when drift is negligible
            cloud_update_interval_ = cloud_max_interval_;

        }



        if (current_step > 0 && current_step % 50 == 0) {

            double wmax_char = (field.wmax > 1e-10) ? field.wmax : 1.0;

            double gamma_max = gtr->getMaxGamma();



            // v2.5: cloud memory update -- drift-adaptive interval

            if ((time - cloud_memory_time) >= cloud_update_interval_) {

                cloud_memory_gamma_max = gamma_max;

                cloud_memory_time = time;

            }



            double cloud_signal = gamma_max - 1.0;

            double gamma_change = (cloud_memory_gamma_max > 1.0) ?

                (gamma_max - cloud_memory_gamma_max) / (cloud_memory_gamma_max - 1.0 + 1e-10) : 0.0;



            double rain_drop_count = 0, rain_amp = 0.0;
            bool rain_active = false;

            static double last_rain_time = -10.0;



            // Triple-track parallel (oplus=max explicitly annotated)
            double ke_change = fabs(field.ke - field.ke_prev) / (field.ke_prev + 1e-10);

            double phase = energy_budget_op->getPhaseLock();

            bool window_ready = energy_budget_op->isWindowReady();



            // Track 1: energy relative change rate

            static double ke_history[100] = {0};

            static int ke_idx = 0, ke_cnt = 0;

            ke_history[ke_idx] = ke_change;

            ke_idx = (ke_idx + 1) % 100;

            if (ke_cnt < 100) ke_cnt++;

            double ke_avg = 0;

            for (int i = 0; i < ke_cnt; i++) ke_avg += ke_history[i];

            ke_avg /= (ke_cnt + 1e-10);

             // v2.6.2: energy_trigger dual gating -- absolute threshold + full-course cooldown
             // Normal fluctuation: dKE/KE~5e-05(0.005%) should not trigger
             // Tower transition: ke_change~0.07(7%) should trigger
             // Pre-divergence: ke_change>0.1(10%) must trigger
             // Threshold at 1%: 200x above normal fluctuation, 7x below tower transition
             double energy_ratio = 1.05;  // 5% above historical mean
             bool energy_trigger = (ke_change > ke_avg * energy_ratio && ke_change > 0.01);



            // Track 2: PhaseLock relative change rate
            static double phase_history[100] = {0};

            static int phase_idx = 0, phase_cnt = 0;

            if (window_ready) {

                phase_history[phase_idx] = phase;

                phase_idx = (phase_idx + 1) % 100;

                if (phase_cnt < 100) phase_cnt++;

            }

            double phase_avg = 0;

            for (int i = 0; i < phase_cnt; i++) phase_avg += phase_history[i];

            phase_avg /= (phase_cnt + 1e-10);

            bool phase_trigger = (window_ready && phase < phase_avg * 0.95 && phase < -0.005);



            // Track 3: Gamma relative change rate
            static double gamma_history[100] = {0};

            static int gamma_idx = 0, gamma_cnt = 0;

            gamma_history[gamma_idx] = gamma_max;

            gamma_idx = (gamma_idx + 1) % 100;

            if (gamma_cnt < 100) gamma_cnt++;

            double gamma_avg = 0;

            for (int i = 0; i < gamma_cnt; i++) gamma_avg += gamma_history[i];

            gamma_avg /= (gamma_cnt + 1e-10);

            bool gamma_trigger = (gamma_max > gamma_avg * 1.05 && gamma_max > 1.05);



            // Triple-track mixed coupling: oplus=max (any trigger suffices)
            bool gamma_change_trigger = (cloud_memory_gamma_max > 1.0) && (fabs(gamma_change) > 0.05);
            // v2.6.2 fix: full-course cooldown 1e-2 -- tower every 50 steps ~ 1.6e-03, 1e-3 cooldown is ineffective
            double rain_cooldown = 1.0e-2;
            bool phi_rain_trigger = (phi && phi->warning_level >= 2);  // Only CRITICAL level allows Phi to trigger RAIN
            bool should_rain = phi_rain_trigger || ((energy_trigger || phase_trigger || gamma_trigger || gamma_change_trigger)

                              && (time - last_rain_time > rain_cooldown));



                        if (should_rain) {
                            last_rain_time = time;
                            // v2.5.1 fix: dose floor 0.1, prevent zero-KE-change rain when Gamma/Phase triggers
                            double dose = min(1.0, max(0.1, ke_change / 0.1));
                            rain_amp = field.wmax * dose * 0.005;
                            rain_drop_count = min(8.0, 1.0 + dose * 3.0);
                            rain_active = (rain_amp > 0.0);
                            if (rain_active) {
                                cout << "[RAIN] triggered at t=" << scientific << setprecision(3) << time << " step=" << current_step << fixed << setprecision(1) << " drops=" << rain_drop_count << " amp=" << setprecision(2) << rain_amp << " dose=" << setprecision(2) << dose << " trigger=" 
                                     << (energy_trigger?"E":"") << (phase_trigger?"P":"") << (gamma_trigger?"G":"") << (gamma_change_trigger?"C":"") << endl;
                            }
                        }



            if (rain_active) {
                assert(rain_amp > 0.0);
                // Rain execution log (trigger info already printed above, skip duplicate output)
                double dx_val = 1.0 / (N - 1);

                double r_phys = max(0.005, bl->get_bl_thickness() * 0.04);

                int r_grid = max(1, (int)(r_phys / dx_val));

                mt19937 rng_damp(42 + current_step);

                uniform_real_distribution<double> d_xy(0.2, 0.8);

                energy_budget->resetRainPower();

                for (int d = 0; d < (int)rain_drop_count; d++) {

                    double cx = d_xy(rng_damp), cy = d_xy(rng_damp);

                    int ic = (int)(cy * (N - 1)), jc = (int)(cx * (N - 1));

                    energy_budget->addRainPower(rain_amp, field.u[ic][jc], field.v[ic][jc]);

                    for (int i = max(1, ic - r_grid); i < min(N - 1, ic + r_grid); i++)

                        for (int j = max(1, jc - r_grid); j < min(N - 1, jc + r_grid); j++) {

                            double dist = sqrt((double)(i - ic) * (i - ic) + (double)(j - jc) * (j - jc)) / (double)r_grid;

                            if (dist < 1.0) field.w[i][j] += rain_amp * exp(-dist * dist);

                        }

                }

                energy_budget->finalizeRainPower();

            }

        }



        rk4->set_dt(dt);

        rk4->apply();

        if (!rk4->succeeded()) {

            if (++rollback_count > 20) {

                memory.abort_reason = "Max rollbacks";

                return false;

            }

            dt *= 0.5;

            if (dt < 1e-6) dt = 1e-6;

            energy_budget->setDt(dt);

            tau->apply();

            return true;

        }

        rollback_count = 0;

        current_step++;



        gtr->apply();

        gtr->syncGammaToCloud(cloud_gamma_cache, N);



        // v2.5 core: cloud memory update -- vortex-center drift-adaptive

        double gamma_max = gtr->getMaxGamma();

        if ((time - cloud_memory_time) >= cloud_update_interval_) {

            cloud_memory_gamma_max = gamma_max;

            cloud_memory_time = time;

        }



        // v2.5 core: MAC projection -- divergence-residual driven, not stage-driven
        gtr->mac_project_if_needed(field.u, field.v, N, mac_div_threshold_);



        theta->apply();

        energy->apply();



        // Î¦é¨æ§ï¼æ¯100æ­¥ï¼

        if (current_step % 50 == 0) {

            phi = make_unique<PhiGateOp>(field, msigma_op->value, rho_op->value, delta_op->value,

                lambda_coupling->value, c2_op->value,

                gtr->residual(), field.ke - field.ke_prev, current_step);

            phi->apply();

            

            // Triple-gate cascade: PhiGate perception -> LambdaGlobal coordination -> TauRollback execution

            if (phi->warning_level > 0) {

                

                // LambdaGlobal coordination: adjust coupling based on warning

                double new_lambda = lambda->get_lambda();

                if (phi->warning_level == 1) { new_lambda *= 0.9; }

                else if (phi->warning_level == 2) { new_lambda *= 0.7; }

                

                // TauRollback preparing response

                tau->set_response(phi->warning_level);

                

                // Yellow card: tighten dt, strengthen Gamma

                if (phi->warning_level == 1) {

                    dt *= tau->get_dt_scale();

                    if (dt < 1e-6) dt = 1e-6;

                    energy_budget->setDt(dt);

                    double new_alpha = min(0.5, cfg.ALPHA * 1.2);

                    gtr->set_alpha(new_alpha);

                }

                // Red card: tighten dt + micro-rain

                else if (phi->warning_level == 2) {

                    dt *= tau->get_dt_scale();

                    if (dt < 1e-6) dt = 1e-6;

                    energy_budget->setDt(dt);

                    double phi_rain_amp = field.wmax * 0.001;

                    int ic = (int)(vortloc->get_vy() * (N - 1)), jc = (int)(vortloc->get_vx() * (N - 1));

                    for (int i = max(1, ic - 2); i < min(N - 1, ic + 2); i++)

                        for (int j = max(1, jc - 2); j < min(N - 1, jc + 2); j++)

                            field.w[i][j] += phi_rain_amp * exp(-((i - ic) * (i - ic) + (j - jc) * (j - jc)) / 2.0);

                }

            }

            

            // ZFCç¡¬è¾¹çæ£æ?
            if (!phi->is_safe()) {

                if (current_step < 2000 && phi->warning_level < 3) {

                } else {

                    memory.abort_reason = phi->get_paradox();
                if (csv_fout.is_open()) csv_fout.close();

                    return false;

                }

            }

        }



        // Save checkpoint

        for (int i = 0; i < N; i++) for (int j = 0; j < N; j++) {

            checkpoint.w[i][j] = field.w[i][j];

            checkpoint.s[i][j] = field.s[i][j];

            checkpoint.u[i][j] = field.u[i][j];

            checkpoint.v[i][j] = field.v[i][j];

        }

        checkpoint.ke = field.ke;

        checkpoint.wmax = field.wmax;

        checkpoint.poisson_res = field.poisson_res;



        // dt adaptation

        psi->apply();

        double dt_new = psi->get_suggested_dt();

        energy_budget->setDt(dt_new);

        if (dt > 0) {

            dt_new = max(dt_new, 0.8 * dt);

            dt_new = min(dt_new, 5.0 * dt);

        }

        dt = max(1e-6, min(0.01, dt_new));

        time += dt;



        field.wmax = 0.0;

        for (int i = 0; i < N; i++) for (int j = 0; j < N; j++)

            if (fabs(field.w[i][j]) > field.wmax) field.wmax = fabs(field.w[i][j]);



        return true;

    }



    void report() {

        double vort_dx = vortloc->get_vx() - report_vx_;

        double vort_dy = vortloc->get_vy() - report_vy_;

        double vort_drift = sqrt(vort_dx * vort_dx + vort_dy * vort_dy);

        report_vx_ = vortloc->get_vx();

        report_vy_ = vortloc->get_vy();

        

        double h = 1.0 / (cfg.N - 1);
        double u_max = 0;
        for (int i = 0; i < cfg.N; i++) for (int j = 0; j < cfg.N; j++) {
            double spd = sqrt(field.u[i][j]*field.u[i][j] + field.v[i][j]*field.v[i][j]);
            if (spd > u_max) u_max = spd;
        }
        double cfl = u_max * dt / h;
        double ke_rel = (field.ke_prev > 1e-15) ? fabs(field.ke - field.ke_prev) / field.ke_prev : 0;
        cout << "[N=" << cfg.N << " step=" << setw(5) << current_step
             << "] t=" << fixed << setprecision(4) << time
             << " dt=" << scientific << setprecision(2) << dt
             << " CFL=" << fixed << setprecision(3) << cfl
             << " |u|_max=" << scientific << setprecision(3) << u_max
             << " |w|_max=" << setprecision(3) << field.wmax
             << " Vort(" << fixed << setprecision(3) << vortloc->get_vx() << "," << setprecision(3) << vortloc->get_vy() << ")"
             << " KE=" << fixed << setprecision(6) << field.ke
             << " dKE/KE=" << scientific << setprecision(2) << ke_rel
             << " Poi_res=" << setprecision(2) << field.poisson_res
             << endl;
        // Tianci paradigm operator state
        const char* phase_str = "SELF";
        if (phi && phi->warning_level == 1) phase_str = "RAIN";
        else if (phi && phi->warning_level >= 2) phase_str = "ROLL";
        double gamma_avg = gtr->getAvgGamma();
        const char* cloud_str = "--";
        if (energy_budget_op && energy_budget_op->isSelfCloud()) cloud_str = "SC";
        cout << "                     "
             << "Xi=" << fixed << setprecision(3) << sigma->get_sigma()
             << " Ph=" << phase_str
             << " Ga=" << fixed << setprecision(3) << gamma_avg
             << " Lm=" << setprecision(3) << lambda->get_lambda()
             << " tau=" << setprecision(2) << tau->get_dt_scale()
             << " Cl=" << cloud_str
             << endl;
    }



    bool run() {

        while (current_step < cfg.MAX_STEPS && time < cfg.TARGET_TIME) {

            if (!advance()) {

                memory.converged = false;

                return false;

            }

            if (current_step % 500 == 0) { report(); conv_history.push_back({current_step, time, dt, field.ke, field.wmax, field.poisson_res, sigma->get_sigma(), lambda->get_lambda()});
                if (csv_fout.is_open()) {
                    csv_fout << current_step << "," << fixed << setprecision(8) << time << "," << scientific << setprecision(6) << dt << "," << fixed << setprecision(8) << field.ke << "," << scientific << setprecision(6) << field.wmax << "," << field.poisson_res << "," << sigma->get_sigma() << "," << lambda->get_lambda() << endl;
                    if (current_step % 5000 == 0) csv_fout.flush();
                } }

        }

        memory.converged = true;
        if (csv_fout.is_open()) csv_fout.close();

        extract_memory();

        return true;

    }



    void extract_memory() {

        memory.vortex_x = vortloc->get_vx();

        memory.vortex_y = vortloc->get_vy();

        memory.vortex_strength = vortloc->get_strength();

        memory.stable_dt = dt;

        memory.lambda = lambda->get_lambda();

        memory.bl_thickness = bl->get_bl_thickness();

        memory.wall_shear_max = bl->get_shear_max();

        memory.final_ke = field.ke;

        memory.final_wmax = field.wmax;

        memory.poisson_res = field.poisson_res;

        memory.cloud_gamma_max = cloud_memory_gamma_max;

        memory.cloud_memory_time = cloud_memory_time;

    }

};



// ============================================================================

// Extrapolation Tower controller
// ============================================================================

// Ghia1982 benchmark data (u along vertical centerline x=0.5)
struct GhiaData { double y; double u_re100, u_re400, u_re1000; };
static const GhiaData ghia_table[] = {
    {1.0000,  1.0000,  1.0000,  1.0000},
    {0.9766,  0.84123, 0.75837, 0.65928},
    {0.9688,  0.78871, 0.68439, 0.57492},
    {0.9609,  0.73722, 0.61756, 0.51117},
    {0.9531,  0.68717, 0.55480, 0.46604},
    {0.8516,  0.23151, 0.29052, 0.33414},
    {0.7344,  0.00332, 0.16256, 0.18719},
    {0.6172, -0.13641, 0.02135, 0.05702},
    {0.5000, -0.20581,-0.11477,-0.06080},
    {0.4531, -0.21090,-0.17119,-0.10648},
    {0.2813, -0.15662,-0.32726,-0.27805},
    {0.1719, -0.10150,-0.24299,-0.38289},
    {0.1016, -0.06434,-0.16647,-0.29730},
    {0.0703, -0.04775,-0.12603,-0.22220},
    {0.0625, -0.04192,-0.10338,-0.18193},
    {0.0391, -0.02694,-0.07206,-0.12146},
    {0.0000,  0.00000, 0.00000, 0.00000},
};
static const int ghia_count = sizeof(ghia_table)/sizeof(ghia_table[0]);

class ExtrapolationTower {

public:

    vector<LevelConfig> configs;

    vector<unique_ptr<LevelSolver>> levels;

    vector<NestMemory> memories;



    double target_Re;

    ExtrapolationTower(double Re) : target_Re(Re) {
        double NU = 1.0 / Re;
        double h128 = 1.0/127.0, h256 = 1.0/255.0, h512 = 1.0/511.0;
        double dt128 = max(1e-6, min(0.01, 0.25*h128*h128/NU));
        double dt256 = max(1e-6, min(0.01, 0.25*h256*h256/NU));
        double dt512 = max(1e-6, min(0.01, 0.25*h512*h512/NU));
        LevelConfig c0{ 128, Re, 1.0, NU, dt128, 0.02, 30000, 20.0, 100, 1e-4, 50, 1e-3 };
        LevelConfig c1{ 256, Re, 1.0, NU, dt256, 0.02, 10000, 20.0, 200, 1e-3, 100, 1e-3 };
        LevelConfig c2{ 512, Re, 1.0, NU, dt512, 0.02, 10000, 20.0, 400, 5e-3, 200, 5e-3 };
        configs = { c0, c1, c2 };

        for (auto& c : configs) {

            levels.push_back(make_unique<LevelSolver>(c));

            memories.emplace_back();

        }

    }



    bool run_tower() {

        auto start = chrono::high_resolution_clock::now();

for (size_t L = 0; L < levels.size(); L++) {

            cout << "\n>>> CLIMBING TO LEVEL " << configs[L].N << " <<<" << endl;



            if (L == 0) {

                cout << "[Tower] Level 0 cold start (v12.1 style)..." << endl;

                levels[L]->cold_start();

            } else {

                cout << "[Tower] Level " << L << " warm start with memory + interpolation..." << endl;

                memories[L] = memories[L - 1];

                levels[L]->warm_start(memories[L - 1]);



                InterpolationOp interp(levels[L-1]->field, levels[L]->field, memories[L],

                    configs[L].U_LID,

                    levels[L-1]->cloud_gamma_cache, levels[L]->cloud_gamma_cache,

                    levels[L]->gtr.get());

                interp.apply();



                double cloud_scale = (configs[L].N - 1.0) / (configs[L].N - 2.0);

                double gamma_max = levels[L]->gtr->getMaxGamma();

                double h_f = 1.0 / (configs[L].N - 1.0);

                double dt_diff = 0.25 * h_f * h_f / (configs[L].NU * max(1.0, gamma_max));

                double dt_cfl = memories[L - 1].stable_dt * cloud_scale * cloud_scale;

                // v2.5.1 fix: if parent stable_dt is abnormal and dt_cfl too small, use dt_diff as floor
                if (dt_cfl < 1e-8) dt_cfl = dt_diff;

                levels[L]->dt = min(dt_cfl, dt_diff);

                levels[L]->dt = max(1e-6, min(0.01, levels[L]->dt));

                levels[L]->energy_budget->setDt(levels[L]->dt);

                cout << "[Tower] L" << configs[L].N << " dt scaled to " << scientific << setprecision(2) << levels[L]->dt << endl;



                int N = configs[L].N;

                for (int i = 0; i < N; i++) for (int j = 0; j < N; j++) {

                    levels[L]->checkpoint.w[i][j] = levels[L]->field.w[i][j];

                    levels[L]->checkpoint.s[i][j] = levels[L]->field.s[i][j];

                    levels[L]->checkpoint.u[i][j] = levels[L]->field.u[i][j];

                    levels[L]->checkpoint.v[i][j] = levels[L]->field.v[i][j];

                }

                levels[L]->checkpoint.ke = levels[L]->field.ke;

                levels[L]->checkpoint.wmax = levels[L]->field.wmax;

            }



            bool ok = levels[L]->run();

            if (ok) {

                levels[L]->extract_memory();

                memories[L] = levels[L]->memory;

            }



            cout << "\n[Tower] Level " << configs[L].N << " MEMORY:" << endl;

            cout << "  Vortex: (" << fixed << setprecision(3) << memories[L].vortex_x << ", " << memories[L].vortex_y

                 << ") strength=" << scientific << setprecision(2) << memories[L].vortex_strength << endl;

            cout << "  KE=" << fixed << setprecision(1) << memories[L].final_ke << " wmax=" << scientific << setprecision(2) << memories[L].final_wmax << endl;

            cout << "  dt=" << scientific << setprecision(2) << memories[L].stable_dt << " lambda=" << setprecision(4) << memories[L].lambda << endl;

            cout << "  BL=" << fixed << setprecision(3) << memories[L].bl_thickness << " shear=" << scientific << setprecision(2) << memories[L].wall_shear_max << endl;

            cout << "  Converged=" << (memories[L].converged ? "Yes" : "No") << endl;

            if (!memories[L].abort_reason.empty())

                cout << "  Abort: " << memories[L].abort_reason << endl;



            if (!ok) {

                cout << "\n[Tower] LEVEL " << configs[L].N << " FAILED!" << endl;

                return false;

            }

        }



        auto end = chrono::high_resolution_clock::now();

        auto dur = chrono::duration_cast<chrono::seconds>(end - start).count();

        cout << "\n============================================================" << endl;

        cout << "   TOWER COMPLETE | Total time: " << dur << "s" << endl;

        cout << "============================================================" << endl;

        return true;

    }



    void write_tecplot(const string& filename, int level) {

        int N = configs[level].N;

        ofstream fout(filename);

        fout << "TITLE=\"Tianci Tower v2.5 L" << N << "\"" << endl;

        fout << "VARIABLES=\"X\",\"Y\",\"U\",\"V\",\"W\",\"S\"" << endl;

        fout << "ZONE I=" << N << ",J=" << N << ",F=POINT" << endl;

        double dx = 1.0 / (N - 1);

        for (int i = 0; i < N; i++) for (int j = 0; j < N; j++) {

            fout << j*dx << " " << i*dx << " "

                 << levels[level]->field.u[i][j] << " "

                 << levels[level]->field.v[i][j] << " "

                 << levels[level]->field.w[i][j] << " "

                 << levels[level]->field.s[i][j] << endl;

        }

    }


    // ========================================================================
    // v2.6: JSC output methods
    // ========================================================================
    void write_convergence_csv(const string& dir) {
        // v2.6: CSV written incrementally during run, this just ensures files are closed
        for (size_t L = 0; L < levels.size(); L++) {
            if (levels[L]->csv_fout.is_open()) levels[L]->csv_fout.close();
        }
    }
    void write_ghia_comparison(const string& dir, double Re) {
        if (levels.size() < 3) return;
        int N = configs[2].N; int jc = N / 2;
        ofstream fout(dir + "/ghia_comparison.txt");
        fout << "Ghia1982 Comparison (Re=" << Re << ", N=" << N << ")" << endl;
        fout << setw(10) << "y" << setw(15) << "u_computed" << setw(15) << "u_ghia" << setw(15) << "error" << endl;
        double max_err = 0, l2_err = 0, l2_ghia = 0; int cnt = 0;
        for (int g = 0; g < ghia_count; g++) {
            double y = ghia_table[g].y;
            double u_ghia;
            if (fabs(Re-100.0)<1.0) u_ghia = ghia_table[g].u_re100;
            else if (fabs(Re-400.0)<1.0) u_ghia = ghia_table[g].u_re400;
            else u_ghia = ghia_table[g].u_re1000;
            int ic = max(0, min(N-1, (int)(y*(N-1)+0.5)));
            double u_comp = levels[2]->field.u[ic][jc];
            double err = fabs(u_comp - u_ghia);
            max_err = max(max_err, err); l2_err += err*err; l2_ghia += u_ghia*u_ghia; cnt++;
            fout << fixed << setprecision(6) << setw(10) << y << setw(15) << u_comp << setw(15) << u_ghia << scientific << setprecision(3) << setw(15) << err << endl;
        }
        double rel_l2 = (l2_ghia > 1e-10) ? sqrt(l2_err/cnt)/sqrt(l2_ghia/cnt) : 0;
        fout << "Max |error|: " << scientific << setprecision(4) << max_err << endl;
        fout << "L2 relative error: " << setprecision(4) << rel_l2 << endl;
    }
    void write_preconditioner_report(const string& dir) {
        ofstream fout(dir + "/preconditioner.txt");
        fout << "Fisher Preconditioner Performance" << endl;
        for (size_t L = 0; L < levels.size(); L++) {
            fout << "L" << configs[L].N << ": alpha=" << fixed << setprecision(4)
                 << levels[L]->gtr->get_alpha() << " gamma_max=" << scientific
                 << setprecision(4) << levels[L]->gtr->getMaxGamma() << endl;
        }
    }
    void write_summary(const string& dir, double Re) {
        ofstream fout(dir + "/summary.txt");
        time_t now_time = chrono::system_clock::to_time_t(chrono::system_clock::now());
        fout << "Tianci NSDT Tower v2.6 JSC" << endl;
        fout << "Re = " << Re << endl;
        fout << "Date: " << ctime(&now_time);
        for (size_t L = 0; L < levels.size(); L++) {
            fout << "Level " << configs[L].N << ": converged=" << (memories[L].converged?"Y":"N")
                 << " steps=" << levels[L]->current_step
                 << " KE=" << fixed << setprecision(6) << memories[L].final_ke
                 << " dt=" << scientific << setprecision(4) << memories[L].stable_dt
                 << " rollbacks=" << levels[L]->rollback_count << endl;
        }
    }

};



// ============================================================================

// main

// ============================================================================



int main(int argc, char* argv[]) {
    double Re = 100.0;
    for (int i = 1; i < argc; i++) {
        string arg = argv[i];
        if (arg == "--Re" && i+1 < argc) { Re = atof(argv[++i]); }
    }
    if (Re < 1.0 || Re > 100000.0) {
        cerr << "Usage: tower_v26.exe --Re <Reynolds_number>" << endl;
        cerr << "Re must be in [1, 100000]" << endl;
        return 1;
    }
    cout << endl;
    cout << "============================================================" << endl;
    cout << "   Tianci NSDT Tower v2.6 JSC" << endl;
    cout << "   Self-Adaptive | Zero Manual Tuning" << endl;
    cout << "   Input: Re = " << Re << endl;
    cout << "============================================================" << endl;

    string dir = "results/Re" + to_string((int)Re);
#ifdef _WIN32
    _mkdir("results");
    _mkdir(dir.c_str());
#else
    mkdir("results", 0755);
    mkdir(dir.c_str(), 0755);
#endif

    ExtrapolationTower tower(Re);
    bool ok = tower.run_tower();
    if (ok) {
        tower.write_tecplot(dir + "/L128.plt", 0);
        tower.write_tecplot(dir + "/L256.plt", 1);
        tower.write_tecplot(dir + "/L512.plt", 2);
        tower.write_convergence_csv(dir);
        tower.write_ghia_comparison(dir, Re);
        tower.write_preconditioner_report(dir);
        tower.write_summary(dir, Re);
        cout << endl;
        cout << "[Output] All results written to " << dir << "/" << endl;
    }
    return ok ? 0 : 1;
}


