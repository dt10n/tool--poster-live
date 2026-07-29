# 直播海报生成工具 — Codex 操作说明（自包含）

银行螺丝钉直播海报生成器。输入标题/介绍文案/关键词/直播链接/二维码，输出 6 张海报。
本包自带全部代码、模板图、字体，**离线可跑**，无需联网、无需飞书。

给同事安装和配置飞书机器人的详细教程见：[COLLEAGUE_GUIDE.md](COLLEAGUE_GUIDE.md)

---

## 一、环境

```bash
pip install pillow        # 唯一依赖（PIL）
```
Python 3.8+。字体（NotoSansCJK-Bold/Regular.ttc）已随包，放在与 generate_image.py 同目录，自动加载。

## 二、6 张海报是什么

| template_id | 输出后缀 | 用途 | 关键词 | 二维码 |
|---|---|---|---|---|
| template_final | -学院 | 学院预告 | 无 | 由直播链接自动生成 |
| template_2 | -翻写 | 翻写文 | 有 | 群里第1张 |
| template_3 | -回放 | 回放 | 有 | 群里第1张 |
| template_4 | -预告+企微朋友圈 | 预告 | 有 | 群里第2张 |
| template_5 | -新预告+企微朋友圈 | 新预告 | 有 | 群里第3张 |
| template_6 | -横版预告 | 横版 | 有 | 群里第2张 |

（学院那张不含关键词，二维码由 `live_link` 自动生成；其余 5 张需传入二维码图片路径。）

## 三、快速生成 6 张（复制即用）

```python
import sys, os
TOOL = os.path.dirname(os.path.abspath(__file__))   # 本包目录
os.chdir(TOOL)                                       # 必须！模板是相对路径
sys.path.insert(0, TOOL)
from generate_image import create_poster
from template_config import TEMPLATES_CONFIG

issue     = "459"
title     = "螺丝钉红利星级来啦，该怎么用？"          # 一句话标题
captions  = [                                        # 4 句介绍文案
    "近期，红利品种和大盘的相关性为啥变小？",
    "螺丝钉红利星级是啥，如何查询？",
    "红利指数经历了几轮跑输跑赢，长期表现如何？",
    "红利品种，该如何投资呢？",
]
live_time = "7月7日（周二）19:00"                     # 固定这个格式
date_code = "260707"                                 # 关键词：2位年+2位月+2位日（见规则）
link      = "https://n6o8y.xetslk.com/sl/xxxx"       # 小鹅通直播链接

# 二维码：胡亮发的 3 张，命名 qr_1_{issue}.png / qr_2 / qr_3，放在本包目录
qr1 = f"{TOOL}/qr_1_{issue}.png"
qr2 = f"{TOOL}/qr_2_{issue}.png"
qr3 = f"{TOOL}/qr_3_{issue}.png"
qr_map = {
    "template_final": None,   # 学院：链接自动生成
    "template_2": qr1, "template_3": qr1,
    "template_4": qr2, "template_6": qr2,
    "template_5": qr3,
}

os.makedirs(f"{TOOL}/output", exist_ok=True)
for tpl, cfg in TEMPLATES_CONFIG.items():
    out = f"{TOOL}/output/{issue}期{cfg['suffix']}.png"
    create_poster(
        template_path=cfg["path"], output_path=out,
        qr_image_path=qr_map[tpl],
        title=title, caption_list=captions,
        live_time=live_time, template_id=tpl,
        date_code=date_code, live_link=link,
    )
    print("done:", out)
```

## 四、关键规则（必须遵守，别踩坑）

**1. 关键词 6 位**：格式 = **2位年 + 2位月 + 2位日**，如 2026年7月7日 → `260707`。旧的 4 位（月+日）已废弃。此关键词是小鹅通后台的"回复关键词"，海报上显示的必须和后台配置一致。

**2. 标题 / 文案字号 —— 不许擅自缩小（最高优先级）**
- 设计字号：**竖版标题 148、横版标题 180、介绍文案默认 96 且最小 96（横竖版都不低于 96）**。
- **后续没有用户特殊说明时，不压缩字体；要改最小字号，必须先经人工同意。**
- **遇到"单行只剩一个字"（孤字）：优先加宽该行行宽**（标题改模板配置 `title_max_width`、文案改 `caption_max_width`），**绝不靠缩字号解决**。
- **介绍文案内部间距最多 40px**，且必须小于或等于标题到第一条文案、最后一条文案到直播时间的外部间隙。
- `title_max_lines=1`（强制标题压成一行、字号骤减）**默认不要传**；只有用户当期明确说"标题压一行"时才传，且不得延续到其它期。

**3. 模板配置已像素级校准，勿擅改**：`template_config.py` 里的 `date_code_box`（关键词框）、`qr_box`（二维码框）、`caption_max_width`、`title_max_width` 等都是逐张实测校准的，不要动。若更换模板图（template_new_*.png），必须重新校准 `date_code_box` 和 `qr_box` 两项（检测橙色括号得关键词框、检测浅色边框得二维码框）。

**4. 标题可手动换行**：`title` 里插 `\n` 可强制换行。默认不用，让它自动两行大字号。

**5. 二维码静默区**：如需用 `qr_generator.generate_qr_image(url)` 生成二维码，其内部 `quiet=1`（不是默认 4），勿改，否则二维码视觉偏小。

## 五、文件清单

- `generate_image.py`   海报绘制核心（create_poster）
- `template_config.py`  6 个模板的坐标/字号配置（已校准）
- `qr_generator.py`     从链接生成二维码（quiet=1）
- `check_qr_codes.py`   （可选）从飞书群下载胡亮发的二维码，需飞书环境，Codex 一般用不到
- `smart_parser.py`     （可选）解析群通告文本
- `template_new_1~6.png`  6 张模板图
- `NotoSansCJK-Bold/Regular.ttc`  字体
- `SKILL.md`            完整技能文档（更详细的规则、历史坑、校准脚本）
- `output/`             生成结果目录

## 六、更详细的规则

见 `SKILL.md` 顶部「🔴 最新定版」区块（关键词、模板校准、字号规则、横版二维码框、颜色等逐条说明）。
