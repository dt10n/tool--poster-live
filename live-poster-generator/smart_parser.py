# -*- coding: utf-8 -*-
import re
from datetime import datetime

def smart_parse_notice(text):
    """
    智能解析直播通告文本
    """
    data = {
        "title": "",
        "captions": [],
        "live_time": "",
        "link": "",
        "output_name": "poster_auto_generated.png",
        "date": None
    }

    # 1. 提取链接 (过滤 ` 符号)
    link_match = re.search(r'https?://[^\s`]+', text)
    if link_match:
        data["link"] = link_match.group(0).strip('`')

    # 2. 提取直播时间 - 支持多种格式
    # 格式1: 周五（3月20日）晚直播
    time_match = re.search(r'(周[一二三四五六日])（(\d+)月(\d+)日）', text)
    if time_match:
        week = time_match.group(1)
        month = time_match.group(2)
        day = time_match.group(3)
        data["live_time"] = f"{week}（{month}月{day}日）"
    
    # 格式2: 【直播时间】：
    time_match2 = re.search(r'【直播时间】：(.*?)(?:\n|$)', text)
    if time_match2 and not data["live_time"]:
        data["live_time"] = time_match2.group(1).strip()
    
    # 格式3: 具体时间 3月20日周五晚上19：00-20:00
    time_match3 = re.search(r'(\d+)月(\d+)日(周[一二三四五六日])[晚上午后夜]+(\d{1,2})[：:](\d{2})\s*[-~]\s*(\d{1,2})[：:](\d{2})', text)
    if time_match3:
        month = time_match3.group(1)
        day = time_match3.group(2)
        week = time_match3.group(3)
        hour1 = time_match3.group(4)
        min1 = time_match3.group(5)
        hour2 = time_match3.group(6)
        min2 = time_match3.group(7)
        data["live_time"] = f"{week}（{month}月{day}日）{hour1}:{min1}-{hour2}:{min2}"
    
    # 格式4: 晚直播 + 具体时间
    time_match4 = re.search(r'(周[一二三四五六日])（(\d+)月(\d+)日）晚直播\s*(\d{1,2})[：:](\d{2})\s*[-~]\s*(\d{1,2})[：:](\d{2})', text)
    if time_match4 and not data["live_time"]:
        week = time_match4.group(1)
        month = time_match4.group(2)
        day = time_match4.group(3)
        hour1 = time_match4.group(4)
        min1 = time_match4.group(5)
        hour2 = time_match4.group(6)
        min2 = time_match4.group(7)
        data["live_time"] = f"{week}（{month}月{day}日）{hour1}:{min1}-{hour2}:{min2}"
    
    # 如果没有具体时间，默认添加晚上19:00-20:00
    if data["live_time"] and "-" not in data["live_time"]:
        data["live_time"] = data["live_time"] + "晚7-8点"

    # 3. 提取关键词/日期代码
    kw_match = re.search(r'关键词[：:]\s*(\d+)', text)
    if kw_match:
        data["date_code"] = kw_match.group(1)

    # 4. 提取标题 - 支持多种格式
    # 格式1: 直播标题：
    title_match = re.search(r'直播标题[：:]\s*(.+?)(?:\n|$)', text)
    if title_match:
        data["title"] = title_match.group(1).strip()
    # 格式2: 【直播主题】：
    if not data["title"]:
        title_match = re.search(r'【直播主题】[：:]\s*(.+)', text)
        if title_match:
            data["title"] = title_match.group(1).strip()

    # 5. 提取推广文案 - 支持多种格式
    # 格式1: 推广文案： 后面多行
    captions_match = re.search(r'推广文案[：:]\s*(.*?)(?:\n关键词|\n标签|$)', text, re.DOTALL)
    if captions_match:
        section_text = captions_match.group(1).strip()
        lines = [l.strip() for l in section_text.split("\n") if l.strip()]
        for line in lines:
            cleaned_line = re.sub(r'^(\d[\.、\s]*|[①②③④\-\*]\s*)', '', line).strip()
            if cleaned_line:
                data["captions"].append(cleaned_line)
    
    # 格式2: 【您将了解】：
    if not data["captions"]:
        captions_match = re.search(r'【您将了解】[：:]\s*(.*?)\s*(?=【|$)', text, re.DOTALL)
        if captions_match:
            section_text = captions_match.group(1).strip()
            lines = [l.strip() for l in section_text.split("\n") if l.strip()]
            for line in lines:
                cleaned_line = re.sub(r'^(\d[\.、\s]*|[①②③④\-\*]\s*)', '', line).strip()
                if cleaned_line:
                    data["captions"].append(cleaned_line)

    # 限制文案数量
    data["captions"] = data["captions"][:4]

    # 6. 提取期数
    # 格式: 440期 或 （440期）
    issue_match = re.search(r'[（(](\d{2,4})期[）)]', text)
    if not issue_match:
        issue_match = re.search(r'(\d{2,4})期直播', text)
    if not issue_match:
        issue_match = re.search(r'第(\d{2,4})期', text)
    
    if issue_match:
        data["issue_number"] = issue_match.group(1)

    # 兜底
    if not data["title"]:
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        for line in lines:
            if "链接" not in line and "关键词" not in line and "标签" not in line:
                data["title"] = line
                break

    return data
