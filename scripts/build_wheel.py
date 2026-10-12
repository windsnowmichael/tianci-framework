# -*- coding: utf-8 -*-
"""
build_wheel.py —— 构建 wheel 并注入来源 commit（v0.3.0 起的发布真源机制）。

为什么需要它：
  "我装的是不是 v0.3.0" 不应靠版本号猜。本脚本在构建时把
  `git rev-parse HEAD` 的完整 commit 写入 `tianci/_build_info.py`，
  随 wheel 分发；安装后 `import tianci; tianci.__commit__` 即可自报
  来源 commit，与发布 tag（v0.3.0 → 某 commit）逐字符对齐。

用法（仓库根目录）：
  python scripts/build_wheel.py            # 缺省构建到 dist/
  python scripts/build_wheel.py -o out/    # 指定输出目录

行为：
  1. 校验当前工作树处于 git 仓库且无未提交改动（构建前后一致，
     避免"装到的代码 ≠ tag 代码"再次漂移）；
  2. 生成 tianci/_build_info.py（__commit__="<40位hex>"）；
  3. python -m build --wheel 出包；
  4. 无论成败均清理 _build_info.py（源码树保持只读原样，._build_info.py
     已入 .gitignore）。

依赖：python -m pip install build
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD_INFO = os.path.join(REPO_ROOT, "tianci", "_build_info.py")


def _git(args: list[str]) -> str:
    out = subprocess.run(
        ["git"] + args, cwd=REPO_ROOT, capture_output=True, text=True)
    if out.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} 失败：{out.stderr.strip()}")
    return out.stdout.strip()


def main() -> int:
    ap = argparse.ArgumentParser(description="构建 wheel 并注入来源 commit")
    ap.add_argument("-o", "--output", default=os.path.join(REPO_ROOT, "dist"),
                    help="wheel 输出目录（默认 dist/）")
    args = ap.parse_args()

    # 1) 真源校验：HEAD 有效 + 工作树干净（防止构建时源码漂移）
    head = _git(["rev-parse", "HEAD"])
    if len(head) != 40:
        raise RuntimeError(f"非预期 HEAD：{head!r}")
    dirty = _git(["status", "--porcelain"])
    if dirty:
        raise RuntimeError(
            "工作树有未提交改动，拒绝构建（构建产物必须与 tag 代码一致）：\n"
            + dirty[:800])

    # 2) 注入 __commit__
    os.makedirs(os.path.dirname(BUILD_INFO), exist_ok=True)
    with open(BUILD_INFO, "w", encoding="utf-8") as f:
        f.write(f'# -*- coding: utf-8 -*-\n__commit__ = "{head}"\n')
    print(f"[build_wheel] 注入 __commit__={head}")

    # 3) 构建
    rc = 1
    try:
        os.makedirs(args.output, exist_ok=True)
        proc = subprocess.run(
            [sys.executable, "-m", "build", "--wheel", "--outdir", args.output],
            cwd=REPO_ROOT, capture_output=True, text=True,
        )
        if proc.returncode != 0:
            print(proc.stdout[-3000:])
            print(proc.stderr[-3000:], file=sys.stderr)
            raise RuntimeError("wheel 构建失败")
        rc = 0
    finally:
        # 4) 清理：源码树恢复原样（_build_info.py 是构建期产物）
        if os.path.exists(BUILD_INFO):
            os.remove(BUILD_INFO)
            print("[build_wheel] 已清理 _build_info.py（构建期产物）")

        # 防呆：dist 里残留的旧包清理由构建工具负责，但绝不允许
        # 已安装的 site-packages 里存在 stale _build_info（不会发生）。
    if rc == 0:
        wheels = sorted(
            p for p in os.listdir(args.output) if p.endswith(".whl"))
        print(f"[build_wheel] 完成：{args.output}/{wheels[-1] if wheels else '?'}")
    return rc


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # noqa: BLE001 —— 构建失败要显式暴露
        print(f"[build_wheel] 失败：{type(exc).__name__}: {exc}", file=sys.stderr)
        sys.exit(1)