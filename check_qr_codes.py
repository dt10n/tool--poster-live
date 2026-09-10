#!/usr/bin/env python3
"""
check_qr_codes.py — 检查PPT制作群是否有胡亮发的二维码，并下载

用法：
    python check_qr_codes.py --issue 449
    python check_qr_codes.py --issue 449 --output-dir /Users/fanlili/.codex/skills/live-poster-codex

返回码：
    0 — 找到第3张二维码并下载完成
    1 — 未找到（胡亮还没发）
    2 — 只找到部分（尚未发到第3张）

【长期规则，勿修改】
    PPT制作群 chat_id : oc_918c9be8ab6950e746bc308c8c32a334
    胡亮 open_id      : ou_5d68d3ab3c26fb8e84287d2521cfc572

    二维码取用规则：按胡亮发送顺序识别前3张图片，不依赖文字标注/关键词。
        现行四图流程仅保留 qr_3：胡亮发的第3张图片 → template_5（新预告+企微朋友圈）。
        前两张只用于确定第3张的发送顺序，不下载、不生成海报。
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime

PPT_CHAT_ID = "oc_918c9be8ab6950e746bc308c8c32a334"
HULIANG_OPEN_IDS = {
    "ou_5d68d3ab3c26fb8e84287d2521cfc572",  # 2026-08-10 PPT制作群实测
    "ou_0c491c7eb6f52da668fc2ef7264c6255",  # 历史配置，保留兼容
}
LARK_CLI = os.path.expanduser("~/.npm-global/bin/lark-cli")
LARK_PROFILE = os.environ.get("LARK_PROFILE", "live-poster-bot")


def run_lark(args: list) -> dict:
    """调用 lark-cli，返回解析后的 JSON"""
    cmd = [LARK_CLI, "--profile", LARK_PROFILE] + args
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"ok": False, "error": result.stderr or result.stdout}


def fetch_messages(page_size=30) -> list:
    """抓取PPT制作群最新消息，按时间倒序"""
    data = run_lark([
        "im", "+chat-messages-list",
        "--as", "bot",
        "--chat-id", PPT_CHAT_ID,
        "--page-size", str(page_size),
        "--sort", "desc",
    ])
    if not data.get("ok"):
        print(f"[ERROR] 抓取消息失败: {data.get('error')}", file=sys.stderr)
        return []
    return data.get("data", {}).get("messages", [])


def _msg_timestamp(msg) -> float:
    """解析消息 create_time（兼容毫秒/秒时间戳和 'YYYY-MM-DD HH:MM:SS' 字符串），失败返回0"""
    raw = msg.get("create_time", "")
    s = str(raw).strip()
    if s.isdigit():
        ts = int(s)
        return ts / 1000 if ts > 1e12 else ts
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(s, fmt).timestamp()
        except ValueError:
            pass
    return 0


def find_qr_messages(messages: list, since_ts: float = 0) -> dict:
    """
    从消息列表中找到胡亮发的二维码图片。

    规则：按发送时间顺序取胡亮发的前3张图片，不依赖文字标注/关键词。
        仅第3张图片会下载为 qr_3，供 template_5 使用。

    返回：{"qr_1": {"msg_id": ..., "img_key": ...}, "qr_2": {...}, "qr_3": {...}}
    """
    result = {}

    # 过滤胡亮的消息（且晚于 since_ts，防止误抓上一期旧二维码），转为时间正序（最早在前）
    huliang_msgs = [
        m for m in messages
        if m.get("sender", {}).get("id") in HULIANG_OPEN_IDS
        and (since_ts <= 0 or _msg_timestamp(m) >= since_ts)
    ]
    if not huliang_msgs:
        return result
    huliang_msgs_asc = list(reversed(huliang_msgs))

    # 按顺序收集胡亮发的图片消息
    img_order = ["qr_1", "qr_2", "qr_3"]
    img_count = 0
    for msg in huliang_msgs_asc:
        if msg.get("msg_type") == "image" and img_count < 3:
            img_key = _extract_img_key(msg.get("content", ""))
            if img_key:
                key = img_order[img_count]
                result[key] = {"msg_id": msg["message_id"], "img_key": img_key}
                img_count += 1

    return result


def _extract_img_key(content: str):
    """从消息 content 中提取 img_key"""
    # 格式1: [Image: img_v3_xxx]
    m = re.search(r'\[Image:\s*(img_[^\]]+)\]', content)
    if m:
        return m.group(1).strip()
    # 格式2: JSON 中的 image_key 字段
    m = re.search(r'"image_key"\s*:\s*"([^"]+)"', content)
    if m:
        return m.group(1)
    return None


def download_qr(msg_id: str, img_key: str, output_path: str) -> bool:
    """下载图片到指定路径"""
    output_dir = os.path.dirname(output_path)
    filename = os.path.basename(output_path)

    # lark-cli 要求使用相对路径
    orig_dir = os.getcwd()
    try:
        os.chdir(output_dir)
        data = run_lark([
            "im", "+messages-resources-download",
            "--as", "bot",
            "--message-id", msg_id,
            "--file-key", img_key,
            "--type", "image",
            "--output", filename,
        ])
        return data.get("ok", False)
    finally:
        os.chdir(orig_dir)


def main():
    parser = argparse.ArgumentParser(description="检查并下载胡亮发的直播二维码")
    parser.add_argument("--issue", required=True, help="直播期数，如 449")
    parser.add_argument(
        "--output-dir",
        default=os.path.dirname(os.path.abspath(__file__)),
        help="二维码保存目录"
    )
    parser.add_argument("--page-size", type=int, default=30, help="抓取消息数量")
    parser.add_argument(
        "--since",
        default=None,
        help="只认该时间之后的二维码消息，格式 'YYYY-MM-DD HH:MM'（防止误抓上一期旧码）；默认今天0点"
    )
    args = parser.parse_args()

    if args.since:
        since_ts = datetime.strptime(args.since, "%Y-%m-%d %H:%M").timestamp()
    else:
        since_ts = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
    print(f"[check_qr_codes] 只认 {datetime.fromtimestamp(since_ts):%Y-%m-%d %H:%M} 之后胡亮发的图片")

    issue = args.issue
    output_dir = args.output_dir
    qr3_path = os.path.join(output_dir, f"qr_3_{issue}.png")

    print(f"[check_qr_codes] 抓取PPT制作群消息（最新{args.page_size}条）...")
    messages = fetch_messages(args.page_size)

    if not messages:
        print("[check_qr_codes] 未获取到消息")
        sys.exit(1)

    print(f"[check_qr_codes] 共获取 {len(messages)} 条消息，正在查找胡亮的二维码...")
    found = find_qr_messages(messages, since_ts)

    has_qr1 = "qr_1" in found
    has_qr2 = "qr_2" in found
    has_qr3 = "qr_3" in found

    if not has_qr1 and not has_qr2 and not has_qr3:
        print("[check_qr_codes] 未找到二维码消息，胡亮还没发")
        sys.exit(1)

    if not has_qr3:
        found_count = int(has_qr1) + int(has_qr2)
        print(f"[check_qr_codes] ⚠️ 目前只识别到 {found_count}/3 张，等待胡亮第3张二维码")
        sys.exit(2)

    if has_qr3:
        print(f"[check_qr_codes] 找到第3张图片（qr_3），正在下载 → {qr3_path}")
        ok = download_qr(found["qr_3"]["msg_id"], found["qr_3"]["img_key"], qr3_path)
        if ok:
            print(f"[check_qr_codes] ✅ qr_3_{issue}.png 下载完成")
        else:
            print(f"[check_qr_codes] ❌ qr_3 下载失败")
            sys.exit(2)

    print(f"[check_qr_codes] ✅ 第3张二维码已下载完成，可以生成四张海报")
    sys.exit(0)


if __name__ == "__main__":
    main()
