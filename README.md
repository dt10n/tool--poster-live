# 直播物料与海报生成 Skill

银行螺丝钉直播物料准备与海报生成工具。输入直播链接和飞书大纲文档后，可完成物料预览与写入、群内复核、二维码检测、四张海报生成、共享空间上传、课程群发布、同步群发布和团队群定时通知。

同事安装、飞书授权和完整执行步骤见 [COLLEAGUE_GUIDE.md](COLLEAGUE_GUIDE.md)。Codex 执行约束见 [SKILL.md](SKILL.md)。

## 当前交付物

每期只生成以下 4 张图：

| 模板 | 输出文件 | 二维码 | 关键词 |
|---|---|---|---|
| 学院 | `{期数}期-学院.png` | 由直播链接自动生成 | 无 |
| 有二维码 | `{期数}期-有二维码.png` | 胡亮或“真维斯”当期唯一二维码 | 有 |
| 无二维码 | `{期数}期-无二维码.png` | 无 | 无 |
| 横版 | `{期数}期-横版.png` | 无 | 无 |

“无二维码”和“横版”使用 2026-09-10 更新的底图。两图只填标题、介绍文案和直播时间，不绘制二维码或关键词；横版底图中的示例文字会在生成时自动清除。具体版式规则以 `SKILL.md` 顶部“当前四图定版”为准。

## 本地生成

环境：Python 3.8+，安装依赖：

```bash
pip install -r requirements.txt
```

生成前进入本仓库目录，二维码文件命名为 `qr_1_{期数}.png`。学院图不需要本地二维码；有二维码图使用这一张二维码。

```python
import os
from generate_image import create_poster
from template_config import TEMPLATES_CONFIG

issue = "473"
title = "社保基金，是如何获得7%-8%的年化的？"
captions = [
    "社保基金的钱从哪里来，规模有多大？",
    "社保基金，是如何投资的，收益如何？",
    "普通投资者，该如何学习社保基金投资？",
]
live_time = "9月11日（周五）19:00"
date_code = "260911"
live_link = "https://n6o8y.xetslk.com/sl/xxxx"

qr_map = {
    "template_final": None,
    "template_5": f"qr_1_{issue}.png",
    "template_no_qr": None,
    "template_horizontal": None,
}

os.makedirs("output", exist_ok=True)
for template_id, config in TEMPLATES_CONFIG.items():
    create_poster(
        template_path=config["path"],
        output_path=f"output/{issue}期{config['suffix']}.png",
        qr_image_path=qr_map[template_id],
        title=title,
        caption_list=captions,
        live_time=live_time,
        template_id=template_id,
        date_code=date_code,
        live_link=live_link,
    )
```

## 关键约束

- 竖版标题字号 148，横版标题字号 180；介绍文案最小字号 96。未经用户明确许可，不得压缩字号。
- 出现孤字或孤标点时，只向右加宽文字框，左侧保持固定；不要缩小字号。
- 所有群消息和图片必须由“直播小助理”机器人发出，发送后逐条核验 `sender_type=app` 且名称为“直播小助理”。
- 物料必须先在 Codex 窗口给用户确认，再写入飞书文档；海报也必须先给用户确认，再上传和群发。
- 团队群通知必须在直播当天北京时间 17:00 发送，并用北京时间 epoch 守门，不能仅依赖本机时区。

## 仓库内容

- `SKILL.md`：完整流程、消息文案和强制规则。
- `generate_image.py`：海报绘制逻辑。
- `template_config.py`：四张活动模板的配置。
- `check_qr_codes.py`：从 PPT 制作群识别并下载当期唯一二维码。
- `template_new_*.png`：活动模板图。
- `memory/`：已固化的版式与流程复盘。

本仓库不包含任何飞书 App Secret、用户登录信息、群消息内容、历史二维码或海报输出。
