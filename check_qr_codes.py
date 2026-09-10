#!/usr/bin/env python3
"""
check_qr_codes.py — 检查PPT制作群是否有胡亮或代发机器人发的二维码，并下载

用法：
    python check_qr_codes.py --issue 449
    python check_qr_codes.py --issue 449 --output-dir /Users/fanlili/.codex/skills/live-poster-codex

返回码：
    0 — 找到唯一二维码并下载完成
    1 — 未找到（胡亮或代发机器人还没发）
    2 — 下载失败

【长期规则，勿修改】
    PPT制作群 chat_id : oc_918c9be8ab6950e746bc308c8c32a334
    胡亮 open_id      : ou_5d68d3ab3c26fb8e84287d2521cfc572
    真维斯 app_id     : cli_a9388a10967b9cd5（代胡亮发二维码）

    二维码取用规则：每期只取胡亮或真维斯代发的第1张图片，不依赖文字标注/关键词。
        下载为 qr_1_{期数}.png，供 template_5（有二维码）使用。
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime

PPT_CHAT_ID = "oc_918c9be8ab6950e746bc308c8c32a334"
HULIANG_OPEN_IDS = {
    "ou_5d68d3ab3c26fb8e84287d2521cfc572",  # 2026-08-10 PPT制作群实测
    "ou_0c491c7eb6f52da668fc2ef7264c6255",  # 历史配置，保留兼容
}
QR_SENDER_APP_IDS = {
    "cli_a9388a10967b9cd5",  # 真维斯，2026-09-10 实测由其代胡亮发二维码
}
# 支持同事在不同系统/用户目录下安装 lark-cli；可用 LARK_CLI 显式覆盖。
LARK_CLI = (
    os.environ.get("LARK_CLI")
    or shutil.which("lark-cli")
    or os.path.expanduser("~/.npm-global/bin/lark-cli")
)
LARK_PROFILE = os.environ.get("LARK_PROFILE", "live-poster-bot")


def run_lark(args: list) -> dict:
    """调用 lark-cli，返回解析后的 JSON"""
    if not os.path.isfile(LARK_CLI) and not shutil.which(LARK_CLI):
        return {"ok": False, "error": f"未找到 lark-cli：{LARK_CLI}"}
    cmd = [LARK_CLI, "--profile", LARK_PROFILE] + args
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"ok": False, "error": result.stderr or result.stdout}


def fetch_messages(page_size=50) -> list:
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
    从消息列表中找到胡亮或其代发机器人发的二维码图片。

    规则：按发送时间顺序取胡亮或真维斯代发的第1张图片，不依赖文字标注/关键词。
        该图片下载为 qr_1，供 template_5 使用。

    返回：{"qr_1": {"msg_id": ..., "img_key": ...}}
    """
    result = {}

    # 过滤胡亮或代发机器人的消息（且晚于 since_ts，防止误抓上一期旧二维码），转为时间正序（最早在前）。
    qr_sender_msgs = [
        m for m in messages
        if (
            m.get("sender", {}).get("id") in HULIANG_OPEN_IDS
            or m.get("sender", {}).get("id") in QR_SENDER_APP_IDS
        )
        and (since_ts <= 0 or _msg_timestamp(m) >= since_ts)
    ]
    if not qr_sender_msgs:
        return result
    qr_sender_msgs_asc = list(reversed(qr_sender_msgs))

    # 图片可能是独立 image 消息，也可能嵌在 post 中；两种格式都只取第一张。
    img_order = ["qr_1"]
    img_count = 0
    for msg in qr_sender_msgs_asc:
        if msg.get("msg_type") in {"image", "post"} and img_count < 1:
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
    # 格式3: post Markdown 内嵌图片，例如 ![Image](img_v3_xxx)
    m = re.search(r'!\[Image\]\((img_[^)]+)\)', content)
    if m:
        return m.group(1).strip()
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
    parser = argparse.ArgumentParser(description="检查并下载胡亮或代发机器人发的直播二维码")
    parser.add_argument("--issue", required=True, help="直播期数，如 449")
    parser.add_argument(
        "--output-dir",
        default=os.path.dirname(os.path.abspath(__file__)),
        help="二维码保存目录"
    )
    parser.add_argument("--page-size", type=int, default=50, help="抓取消息数量（最大50）")
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
    print(f"[check_qr_codes] 只认 {datetime.fromtimestamp(since_ts):%Y-%m-%d %H:%M} 之后胡亮或真维斯代发的图片")

    issue = args.issue
    output_dir = args.output_dir
    qr1_path = os.path.join(output_dir, f"qr_1_{issue}.png")

    print(f"[check_qr_codes] 抓取PPT制作群消息（最新{args.page_size}条）...")
    messages = fetch_messages(args.page_size)

    if not messages:
        print("[check_qr_codes] 未获取到消息")
        sys.exit(1)

    print(f"[check_qr_codes] 共获取 {len(messages)} 条消息，正在查找二维码...")
    found = find_qr_messages(messages, since_ts)

    has_qr1 = "qr_1" in found

    if not has_qr1:
        print("[check_qr_codes] 未找到二维码消息，胡亮或真维斯代发机器人还没发")
        sys.exit(1)

    if has_qr1:
        print(f"[check_qr_codes] 找到二维码图片（qr_1），正在下载 → {qr1_path}")
        ok = download_qr(found["qr_1"]["msg_id"], found["qr_1"]["img_key"], qr1_path)
        if ok:
            print(f"[check_qr_codes] ✅ qr_1_{issue}.png 下载完成")
        else:
            print(f"[check_qr_codes] ❌ qr_1 下载失败")
            sys.exit(2)

    print(f"[check_qr_codes] ✅ 二维码已下载完成，可以生成四张海报")
    sys.exit(0)


if __name__ == "__main__":
    main()
