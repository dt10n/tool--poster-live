# 直播海报生成工具

银行螺丝钉直播海报生成器。输入直播标题、介绍文案、直播时间、直播链接和胡亮的二维码消息，输出 4 张海报。

给同事安装并配置飞书机器人的完整流程，见 [COLLEAGUE_GUIDE.md](COLLEAGUE_GUIDE.md)。

## 环境

```bash
pip install pillow
```

Python 3.8+。包内自带 NotoSansCJK 字体，离线生成海报不需要联网。

## 四张海报

| template_id | 输出后缀 | 动态内容 | 二维码 | 关键词 |
|---|---|---|---|---|
| `template_final` | `-学院` | 标题、介绍文案、直播时间 | 由直播链接自动生成 | 无 |
| `template_5` | `-有二维码` | 标题、介绍文案、直播时间 | 胡亮第 3 张图 | 有 |
| `template_no_qr` | `-无二维码` | 标题、介绍文案、直播时间 | 无 | 无 |
| `template_horizontal` | `-横版` | 标题、介绍文案、直播时间 | 无 | 无 |

“有二维码”沿用原“新预告+企微朋友圈”模板。新竖版“无二维码”的标题和介绍文案位置与它完全一致。横版模板已去除交付样图中的示例标题和文案，保留主讲人、直播时间和获取链接等固定设计元素。

## 快速生成四张

```python
import os
import sys

TOOL = os.path.dirname(os.path.abspath(__file__))
os.chdir(TOOL)
sys.path.insert(0, TOOL)

from generate_image import create_poster
from template_config import TEMPLATES_CONFIG

issue = "469"
title = "成长、价值风格轮动，我们该如何投资？"
captions = [
    "成长、价值，为啥会有风格轮动？",
    "不同风格，各自有啥特点和代表品种？",
    "成长、价值风格的长期表现如何？",
    "风格轮动下，我们该如何投资？",
]
live_time = "9月15日（周二）19:00"
date_code = "260915"
live_link = "https://n6o8y.xetslk.com/sl/xxxx"

# 只需要胡亮发的第3张二维码。check_qr_codes.py 会按顺序识别它。
qr_map = {
    "template_final": None,
    "template_5": f"{TOOL}/qr_3_{issue}.png",  # 输出：{期数}期-有二维码.png
    "template_no_qr": None,
    "template_horizontal": None,
}

os.makedirs(f"{TOOL}/output", exist_ok=True)
for template_id, config in TEMPLATES_CONFIG.items():
    output_path = f"{TOOL}/output/{issue}期{config['suffix']}.png"
    create_poster(
        template_path=config["path"],
        output_path=output_path,
        qr_image_path=qr_map[template_id],
        title=title,
        caption_list=captions,
        live_time=live_time,
        template_id=template_id,
        date_code=date_code,
        live_link=live_link,
    )
```

## 版式规则

- 标题设计字号：竖版 148，横版 180；默认最多两行。
- 介绍文案字号：96，最小也是 96；不得为了排版自行缩小字体。
- 遇到孤字或孤标点，先向右加宽标题/文案框，左侧固定，不缩小字号。
- 介绍文案内部间距范围 18-40px，且小于标题到文案、文案到直播时间的外部留白。
- 标题、介绍文案、直播时间的两处外部留白由生成代码按实际文字高度自动计算。
- 两张新图不绘制二维码和关键词；直播时间仍填入模板的时间栏。

## 文件清单

- `generate_image.py`: 海报绘制核心。
- `template_config.py`: 4 张活动模板的坐标与样式配置。
- `template_new_1.png`: 学院模板。
- `template_new_5.png`: 有二维码模板（沿用原新预告+企微朋友圈设计）。
- `template_new_no_qr.png`: 新无二维码竖版模板。
- `template_new_horizontal.png`: 新横版模板。
- `check_qr_codes.py`: 在 PPT 制作群按发送顺序识别胡亮第 3 张二维码。
- `SKILL.md`: 完整工作流和飞书发送规则。
