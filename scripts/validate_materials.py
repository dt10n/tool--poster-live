#!/usr/bin/env python3
"""Validate one issue's DocxXML draft or section-fetch JSON before proceeding."""
import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def validate(source):
    errors = []
    raw = source.strip()
    if raw.startswith('{'):
        raw = json.loads(raw)['data']['document']['content']
    root = ET.fromstring('<root>' + raw + '</root>')
    lines = []
    for e in root.iter():
        if e.tag not in ('p', 'li', 'h2'):
            continue
        value = ''.join(e.itertext()).strip()
        if e.tag == 'li' and value.startswith('小助手配置：'):
            value = '1. ' + value
        lines.append(value)
    lines = [s for s in lines if s and s != '\u200b']
    text = '\n'.join(lines)
    heading = re.search(r'【AI生成】(\d+)月(\d+)日（(\d+)期）（周[一二三四五六日天]）直播：(.+)', text)
    if not heading:
        return ['缺少或无法识别本期标题；输入必须是单期完整正文']
    month, day, issue, title = heading.groups()
    sections = []
    for line in lines:
        m = re.match(r'([1-4])[.、．]\s*(.*)', line)
        if m:
            sections.append((m.group(1), m.group(2)))
    expected = ['小助手配置：', '直播间创建：', '同步胡亮如下信息：', '【学院直播预告帖】']
    if [n for n, _ in sections] != ['1', '2', '3', '4'] or any(
            not value.startswith(prefix) for (_, value), prefix in zip(sections, expected)):
        errors.append('四项名称、顺序或编号不符合固定格式')
    assistant = next((s for s in lines if '小助手配置：' in s), '')
    if not re.fullmatch(r'1[.、．]\s*小助手配置：[356789]、[356789]、[356789]', assistant):
        errors.append('第一项必须仅列三个小助手编号')
    if re.search(r'\d号\s*.+[：:]', text):
        errors.append('物料不得展开小助手姓名、颜色或职责')
    if any(s in text for s in ['文章安排', '直播回放文章', '直播翻写文章']):
        errors.append('物料不得包含文章安排段落')
    required = [
        f'直播名称：{title}｜螺丝钉专属直播课第{issue}期',
        f'直播简介：{month}月{day}日晚7点，螺丝钉来跟大家详细分析一下',
        f'#学院专属直播课 螺丝钉直播第{issue}期将在『今晚7点』准时开始，欢迎大家实时互动交流～',
        f'【直播主题】：{title}', '【您将了解】：', '【电脑观看】：',
        '【手机观看】：微信扫描下面二维码即可收看。也可以先把二维码图片保存手机里，微信里点击扫一扫-选择相册-选择二维码图片，即可进入查看。',
        '【直播流程】：', '第一环节主题讲解：10-20分钟',
        '第二环节：实时互动交流，解答大家在投资上的困惑。',
    ]
    for value in required:
        if value not in text:
            errors.append('缺少或改写固定字段：' + value)
    if not re.search(r'关键词：\d{6}(?:\n|$)', text):
        errors.append('缺少六位关键词')
    if not re.search(r'【直播时间】：\d{4}年' + month + '月' + day + '日 晚7-8点', text):
        errors.append('学院预告日期或时段不一致')
    if len(re.findall(r'直播间链接：https://\S+', text)) != 2:
        errors.append('直播间创建和胡亮配置均须包含直播间链接')
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('file', help='单期 XML 或 docs +fetch --scope section 的 JSON 文件')
    args = parser.parse_args()
    try:
        errors = validate(Path(args.file).read_text())
    except (ValueError, KeyError, ET.ParseError) as exc:
        errors = ['无法读取单期物料：' + str(exc)]
    if errors:
        print('\n'.join('FAIL: ' + e for e in errors))
        return 1
    print('PASS: 四项结构及固定正文检查通过；仍须核对来源字段、排期、链接和视觉空行。')
    return 0


if __name__ == '__main__':
    sys.exit(main())
