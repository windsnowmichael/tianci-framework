# -*- coding: utf-8 -*-
"""
天赐范式 · NS 方程云端求解器 (算子流版)
Ξ 锚定收敛目标 / Σ 不确定性 / Λ-τ 熔断
"""
import numpy as np
from scipy.ndimage import gaussian_filter
import os, argparse, json, time

def tridiagonal_solve(a, b, c, d):
    n = len(d)
    cp, dp = np.zeros(n-1), np.zeros(n)
    cp[0] = c[0]/b[0]; dp[0] = d[0]/b[0]
    for i in range(1, n-1):
        den = b[i] - a[i-1]*cp[i-1]
        cp[i] = c[i]/den
        dp[i] = (d[i] - a[i-1]*dp[i-1])/den
    dp[n-1] = (d[n-1] - a[n-2]*dp[n-2])/(b[n-1] - a[n-2]*cp[n-2])
    x = np.zeros(n)
    x[-1] = dp[-1]
    for i in range(n-2, -1, -1):
        x[i] = dp[i] - cp[i]*x[i+1]
    return x

def adi_step(omega, u, v, dx, dy, dt, Re):
    Ny, Nx = omega.shape
    nu = 1.0/Re
    r = nu*dt/(dx*dx)
    omega_star = omega.copy()
    for i in range(1, Ny-1):
        rhs = (omega[i,1:-1]*(1-2*r) + r*(omega[i,2:] + omega[i,:-2])
               - dt*(u[i,1:-1]*(omega[i,2:]-omega[i,:-2])/(2*dx)
                     + v[i,1:-1]*(omega[i+1,1:-1]-omega[i-1,1:-1])/(2*dy)))
        a = -r*np.ones(Nx-2); b = (1+2*r)*np.ones(Nx-2); c = -r*np.ones(Nx-2)
        omega_star[i,1:-1] = tridiagonal_solve(a, b, c, rhs)
    omega_new = omega_star.copy()
    for j in range(1, Nx-1):
        rhs = (omega_star[1:-1,j]*(1-2*r) + r*(omega_star[2:,j] + omega_star[:-2,j])
               - dt*(u[1:-1,j]*(omega_star[1:-1,j+1]-omega_star[1:-1,j-1])/(2*dx)
                     + v[1:-1,j]*(omega_star[2:,j]-omega_star[:-2,j])/(2*dy)))
        a = -r*np.ones(Ny-2); b = (1+2*r)*np.ones(Ny-2); c = -r*np.ones(Ny-2)
        omega_new[1:-1,j] = tridiagonal_solve(a, b, c, rhs)
    return omega_new

def poisson_sor(omega, psi0, dx, dy, tol=1e-5, max_iter=3000, relax=1.7):
    Ny, Nx = omega.shape
    psi = psi0.copy()
    psi[0,:]=0; psi[-1,:]=0; psi[:,0]=0; psi[:,-1]=0
    for _ in range(max_iter):
        psi_old = psi.copy()
        for i in range(1,Ny-1):
            for j in range(1,Nx-1):
                psi[i,j] = (1-relax)*psi[i,j] + relax*(
                    ((psi[i+1,j]+psi[i-1,j])/dy**2 + (psi[i,j+1]+psi[i,j-1])/dx**2 + omega[i,j]) /
                    (2/dx**2 + 2/dy**2))
        psi[0,:]=0; psi[-1,:]=0; psi[:,0]=0; psi[:,-1]=0
        if np.linalg.norm(psi-psi_old) < tol:
            break
    return psi

def solve_cavity_tianci(N=128, Re=1000, dt0=0.0004, steps=20000):
    dx = dy = 1.0/(N-1)
    psi = np.zeros((N,N))
    omega = np.zeros((N,N))
    for j in range(1,N-1):
        omega[0,j] = -2.0/dy
    dt = dt0
    original_dt = dt0
    prev_energy = None
    sigma = 0.0
    energy_history = []
    sigma_history = []
    for step in range(1, steps+1):
        psi_prev, omega_prev = psi.copy(), omega.copy()
        energy_now = np.sum(omega**2)
        energy_history.append(energy_now)
        if prev_energy is not None and (energy_now > 1.5*prev_energy or np.isnan(energy_now)):
            print(f"  Step {step:6d} | Λ触发: 能量跳变，回滚并减半dt")
            psi, omega = psi_prev, omega_prev
            dt *= 0.5
            continue
        prev_energy = energy_now
        u = np.gradient(psi, dy, axis=0)
        v = -np.gradient(psi, dx, axis=1)
        omega_new = adi_step(omega, u, v, dx, dy, dt, Re)
        psi_new = poisson_sor(omega_new, psi, dx, dy, tol=1e-5, max_iter=2500)
        for j in range(1,N-1):
            omega_new[0,j] = -2.0*psi_new[1,j]/dy**2 - 2.0/dy
            omega_new[-1,j] = -2.0*psi_new[-2,j]/dy**2
        for i in range(1,N-1):
            omega_new[i,0] = -2.0*psi_new[i,1]/dx**2
            omega_new[i,-1] = -2.0*psi_new[i,-2]/dx**2
        grad_omega = np.gradient(omega_new)
        sigma_local = np.var(grad_omega[0]) + np.var(grad_omega[1])
        sigma = min(0.95, sigma_local/(sigma_local+1.0))
        sigma_history.append(sigma)
        if sigma > 0.4 and N <= 256:
            noise = np.random.randn(N,N)*0.002*sigma
            noise = gaussian_filter(noise, sigma=1.0)
            omega_new += noise
            for j in range(1,N-1):
                omega_new[0,j] = -2.0*psi_new[1,j]/dy**2 - 2.0/dy
        psi, omega = psi_new, omega_new
        if sigma < 0.3 and dt < original_dt:
            dt = min(original_dt, dt*1.005)
        if step % 2000 == 0:
            interior = psi[1:-1,1:-1]
            idx = np.argmin(interior)
            i,j = np.unravel_index(idx, interior.shape)
            i+=1; j+=1
            xc, yc = j/(N-1), i/(N-1)
            print(f"Step {step:6d}: Σ={sigma:.3f} dt={dt:.6f} 主涡≈({xc:.3f},{yc:.3f}) 能量={energy_now:.2e}")
    return psi, omega, energy_history, sigma_history

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--grid-size', type=int, default=128)
    parser.add_argument('--reynolds', type=int, default=1000)
    args = parser.parse_args()
    N = args.grid_size
    Re = args.reynolds
    print(f"🧠 天赐·NS求解器启动 N={N} Re={Re}")
    t0 = time.time()
    psi, omega, energy_hist, sigma_hist = solve_cavity_tianci(N=N, Re=Re)
    elapsed = time.time()-t0
    os.makedirs('output', exist_ok=True)
    np.save(f'output/psi_{N}.npy', psi)
    np.save(f'output/omega_{N}.npy', omega)
    np.save(f'output/energy_{N}.npy', np.array(energy_hist))
    np.save(f'output/sigma_{N}.npy', np.array(sigma_hist))
    interior = psi[1:-1,1:-1]
    idx = np.argmin(interior)
    i,j = np.unravel_index(idx, interior.shape)
    i+=1; j+=1
    xc, yc = j/(psi.shape[1]-1), i/(psi.shape[0]-1)
    report = {
        "grid_size": N, "Re": Re,
        "main_vortex": (round(xc,4), round(yc,4)),
        "final_sigma": float(sigma_hist[-1]),
        "elapsed_sec": round(elapsed,1)
    }
    with open(f'output/report_{N}.json','w') as f:
        json.dump(report, f, indent=2)
    print(f"完成 主涡({xc:.4f},{yc:.4f}) Σ={sigma_hist[-1]:.3f} 耗时{elapsed:.1f}s")