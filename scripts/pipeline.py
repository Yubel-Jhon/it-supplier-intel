"""一键跑脚本层:fetch -> parse -> verify -> diff。纯标准库,零第三方依赖。
等价于依次手动跑 4 个脚本,任一步失败即中止(别跳步,文件有依赖链)。
"""
import os
import subprocess
import sys

# Windows 下 Python 默认 stdout 是 GBK,终端是 UTF-8,中文会乱码。统一改成 UTF-8。
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

STEPS = [
    ("fetch", "fetch.py"),
    ("parse", "parse.py"),
    ("verify", "verify.py"),
    ("diff", "diff.py"),
]


def main():
    for name, script in STEPS:
        print(f"\n=== [{name}] python scripts/{script} ===")
        p = subprocess.run(
            [sys.executable, os.path.join(HERE, script)],
            cwd=ROOT,
        )
        if p.returncode != 0:
            print(f"[pipeline] {name} 失败(code={p.returncode}),中止。"
                  f"多半是缺上一步产出,别跳步。")
            sys.exit(p.returncode)
    print("\n[pipeline] 脚本层跑完。看上面 diff 的输出:")
    print("  - 无增量 -> 静默结束")
    print("  - 有增量 -> 进判断层(verify 语义 -> update 合成 -> notify 推送)")


if __name__ == "__main__":
    main()
