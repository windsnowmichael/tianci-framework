import numpy as np
import os
import argparse

def run_ks_solver(init_density=0.1, grid_size=64):
    print(f"[KS Solver] 启动: init_density={init_density}, grid_size={grid_size}")
    os.makedirs('output', exist_ok=True)
    result = np.random.rand(grid_size, grid_size)
    np.save(f'output/result_{init_density}.npy', result)
    print(f"[KS Solver] 完成: 结果已保存至 output/result_{init_density}.npy")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--init-density', type=float, default=0.1)
    parser.add_argument('--grid-size', type=int, default=64)
    args = parser.parse_args()
    run_ks_solver(args.init_density, args.grid_size)
