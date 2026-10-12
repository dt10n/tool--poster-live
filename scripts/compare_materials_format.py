#!/usr/bin/env python3
"""Compare fixed format of two single-issue DocxXML/section-fetch JSON files."""
import argparse
import difflib
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def signature(path):
    raw = Path(path).read_text().strip()
    if raw.startswith('{'):
        raw = json.loads(raw)['data']['document']['content']
    root = ET.fromstring('<root>' + raw + '</root>')
    result = []
    caption_mode = False
    for e in root.iter():
        if e.tag not in ('p', 'li', 'h2'):
            continue
        s = ''.join(e.itertext()).replace('\u200b', '').strip()
        if e.tag == 'li' and s.startswith('小助手配置：'):
            s = '1. ' + s
        s = re.sub(r'^([1-4])[.、．]\s*', r'\1. ', s)
        if s.startswith('【AI生成】'):
            s = '{本期标题}'
        elif '小助手配置：' in s:
            s = re.sub(r'配置：.*', '配置：{编号}', s)
        elif s.startswith(('直播名称：', '直播标题：', '【直播主题】：')):
            s = s.split('：')[0] + '：{标题}'
        elif s.startswith('直播简介：'):
            s = re.sub(r'\d+月\d+日', '{日期}', s)
        elif s.startswith('周') and '信息如下，辛苦配置～' in s:
            s = '周{星期}（{日期}）晚直播（{期数}期）信息如下，辛苦配置～'
        elif s.startswith('#学院专属直播课'):
            s = re.sub(r'第\d+期', '第{期数}期', s)
        elif s.startswith('【直播时间】：'):
            s = re.sub(r'\d+年\d+月\d+日', '{日期}', s)
        elif s.startswith('关键词：'):
            s = '关键词：{日期码}'
            caption_mode = False
        elif s.startswith('直播间链接：'):
            s = '直播间链接：{链接}'
        else:
            s = re.sub(r'https://\S+', '{链接}', s)
        if s.startswith(('推广文案：', '【您将了解】：')):
            caption_mode = True
            result.append(s)
            result.append('{推广文案逐条换行}')
            continue
        if s.startswith('【直播时间】：'):
            caption_mode = False
        if caption_mode and s and not s.startswith('关键词：'):
            continue
        result.append(s)
    # Leading/trailing spacer blocks do not define section layout.
    while result and not result[0]:
        result.pop(0)
    while result and not result[-1]:
        result.pop()
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('previous')
    p.add_argument('current')
    args = p.parse_args()
    before, after = signature(args.previous), signature(args.current)
    diff = list(difflib.unified_diff(before, after, fromfile='前一期固定格式', tofile='本期固定格式', lineterm=''))
    if diff:
        print('\n'.join(diff))
        print('FAIL: 存在格式差异；须按当前 Skill 逐项解释或修正，禁止照抄前一期错误。')
        return 1
    print('PASS: 与前一期固定结构、正文及空行一致（动态字段已归一化）。')
    return 0


if __name__ == '__main__':
    sys.exit(main())
