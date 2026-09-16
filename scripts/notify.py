"""第 4 步(可选):推送简报。默认 stdout;可配 wechat_push 走 git push 触发微信。"""
import os
import subprocess
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import DATA_DIR  # noqa: E402

MODE = os.environ.get("DAILY_BRIEFING_NOTIFY", "local_file")  # local_file(默认) | wechat_push | stdout(调试)


def main():
    today = date.today().isoformat()
    brief_path = os.path.join(DATA_DIR, today, "brief.md")
    if not os.path.exists(brief_path):
        print("无简报(brief.md 不存在),今日可能无增量")
        sys.exit(0)
    content = open(brief_path, encoding="utf-8").read()

    if MODE == "local_file":
        print(f"[local_file] 简报已落在 {brief_path}")
    elif MODE == "wechat_push":
        # 接已有的 wechatauto-replica:把简报追加到触发微信的仓库文件,再 commit+push。
        # 依你现有 wechat-notify 配置,设 DAILY_BRIEFING_PUSH_FILE 为那个触发文件路径。
        push_file = os.environ.get("DAILY_BRIEFING_PUSH_FILE", "")
        if not push_file:
            print("[wechat_push] 未设 DAILY_BRIEFING_PUSH_FILE,回退 stdout 打印")
            print(content)
            sys.exit(0)
        with open(push_file, "a", encoding="utf-8") as f:
            f.write("\n" + content)
        subprocess.run(["git", "add", push_file], check=False)
        subprocess.run(["git", "commit", "-m", f"daily-agent-briefing 情报 {today}"], check=False)
        subprocess.run(["git", "push"], check=False)
        print("[wechat_push] 已 push,微信通知链路应已触发")
    else:
        print(content)


if __name__ == "__main__":
    main()
