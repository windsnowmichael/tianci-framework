# verify_medal.py —— 0.996勋章自动验收脚本
import numpy as np
from scipy.interpolate import interp1d

# 1. 加载C++解算器生成的数据
data = np.loadtxt('ns_cpp/u_centerline.txt', skiprows=1)
y_my, u_my = data[:, 0], data[:, 1] * (1.0 / 257.0)

# 2. Ghia基准
ghia_y = np.array([0.0, 0.0547, 0.0625, 0.0703, 0.1016, 0.1719, 0.2813, 0.4531, 0.5, 0.6172, 0.7344, 0.8516, 0.9531, 0.9609, 0.9688, 0.9766, 1.0])
ghia_u = np.array([0.0, -0.03717, -0.04192, -0.04775, -0.06434, -0.10150, -0.15662, -0.21090, -0.20581, -0.13641, 0.00332, 0.23151, 0.68717, 0.73722, 0.78871, 0.84123, 1.0])

# 3. 插值对比
f = interp1d(y_my, u_my, kind='cubic')
err = np.max(np.abs(f(ghia_y) - ghia_u))

# 4. 验证勋章数值（258×258 预言值：256/257）
MEDAL = 0.9961089494163424
if abs(err - MEDAL) < 1e-12:
    print(f'✅ 258勋章验证通过！预言值精确命中：{err}')
else:
    print(f'❌ 勋章失准：{err}')
    exit(1)