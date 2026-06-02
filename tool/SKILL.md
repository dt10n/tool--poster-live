---
name: 直播海报制作
description: 直播海报生成工具。根据飞书群消息自动读取直播信息，匹配二维码，生成5种格式的海报（学院、预告+企微朋友圈、回放、翻写、螺丝钉上（预告））。支持自动检测新直播消息并触发生成。
metadata:
  {
    "openclaw":
      {
        "requires": { "files": ["/Users/fanlili/Downloads/live-poster-tool/generate_image.py", "/Users/fanlili/Downloads/live-poster-tool/template_config.py", "/Users/fanlili/Downloads/live-poster-tool/smart_parser.py", "/Users/fanlili/Downloads/live-poster-tool/check_new_broadcast.py"] },
      },
  }
---

# 直播海报制作

根据飞书群消息自动读取直播信息，生成5种格式的海报。支持自动检测新直播消息。

## 自动化工作流

### 定时检测

通过 Cron 定时任务自动检测群内新直播消息：

- **执行时间**：周一、周四 13:00-18:00，每30分钟检查一次
- **具体时间**：13:00, 13:30, 14:00, 14:30, 15:00, 15:30, 16:00, 16:30, 17:00, 17:30
- **其他时间**：不执行检查

### 手动触发

当用户在群里发布新直播通告时，自动执行以下流程：

## 完整流程

### 1. 检测新直播消息

从飞书群"内容|PPT制作群"（群ID: oc_918c9be8ab6950e746bc308c8c32a334）读取最新直播通告消息。

与已记录的最近期数对比，如果更新则继续。

### 2. 读取群消息获取直播信息

消息特征：
- 包含"直播标题"字段
- 包含"直播间链接"
- 包含"推广文案"
- 包含"关键词"

### 3. 使用 smart_parser 解析直播信息

```python
import sys
sys.path.insert(0, '/Users/fanlili/Downloads/live-poster-tool')
from smart_parser import smart_parse_notice

# 解析
data = smart_parse_notice(text)
# 返回: title, captions, live_time, link, date_code, issue_number
```

### 4. 下载二维码

从群里下载两个二维码：
- 直播预告二维码（群里最新的预告二维码）
- 翻写文二维码（群里最新的翻写文二维码）

保存为：
- qr_1_yugao_{期数}.png（直播预告）
- qr_2_fanxie_{期数}.png（翻写文）

如需从链接生成二维码：
```python
import qrcode
link = "https://xxx"
qr = qrcode.QRCode(box_size=10, border=1)
qr.add_data(link)
qr.make(fit=True)
img = qr.make_image(fill_color="black", back_color="white")
img.save("qr_link.png")
```

### 5. 生成海报（5张）

```python
import sys
sys.path.insert(0, '/Users/fanlili/Downloads/live-poster-tool')
from generate_image import create_poster
from template_config import get_template_config

# 解析后的数据
title = data['title']           # 直播标题
live_time = data['live_time']   # 直播时间
date_code = data['date_code']   # 关键词/日期码
captions = data['captions']     # 推广文案（4句）
issue = data['issue_number']    # 期数

# 二维码映射（长期规则，勿修改）
qr_map = {
    "template_final": "qr_link_{}.png".format(issue),      # 学院：用直播链接生成的二维码
    "template_2": "qr_2_fanxie_{}.png".format(issue),     # 回放：用群里第二个二维码
    "template_3": "qr_1_yugao_{}.png".format(issue),      # 预告+企微朋友圈：用群里第一个二维码
    "template_4": "qr_1_yugao_{}.png".format(issue),      # 翻写：用群里第一个二维码
    "template_5": "qr_1_yugao_{}.png".format(issue),      # 新预告：用群里第一个二维码
}

# 生成所有海报
templates = ["template_final", "template_2", "template_3", "template_4", "template_5"]

for tmpl_id in templates:
    config = get_template_config(tmpl_id)
    qr_file = qr_map[tmpl_id]
    output_file = "{}{}.png".format(issue, config['suffix'])
    
    create_poster(
        template_path=config["path"],
        qr_image_path=qr_file,
        output_path=output_file,
        title=title,
        caption_list=captions,
        live_time=live_time,
        template_id=tmpl_id,
        date_code=date_code
    )
```

### 6. 发送海报给你确认

1. 先发送一条文字消息确认信息：
```
📺 {期数}期直播海报已生成！
📅 直播时间：{时间}
🔗 链接：{链接}
🔑 关键词：{关键词}

请回复「1」或「确认」或「ok」继续后续操作～
```

2. 然后依次发送5张海报图片：
   - 学院（template_final）
   - 预告+企微朋友圈（template_2）
   - 回放（template_3）
   - 翻写（template_4）
   - 螺丝钉上（template_5）

3. **等待你确认** - 收到你的回复（1/确认/ok）后，继续执行下一步

### 7. 你确认后

1. **上传到飞书共享文档**：
   - 飞书共享文档目录：`https://epndqwwg0a.feishu.cn/drive/folder/MplmffLghlQ17Rd7blbcL6Umnhe`
   - 在该目录下找到对应期数的文件夹（如 `441-20260324`）
   - 上传5张海报到该文件夹

2. **发送通知**：
   - 发给你确认
   - 发到群里艾特@胡亮，格式：
   ```
   {月}.{日}直播海报已上传至共享文档了哈，请知悉～
   附：文件夹链接
   @胡亮
   ```

## 代码规则（已封装）

生成代码已按以下规则优化：

1. **标题**：字号自适应，字数多则自动调小，最多2行
2. **介绍文案**：字号根据字数多少自适应，字数多字号小，最多2行
3. **点点位置**：和文案整体居中对齐，再往下挪20px
4. **模板配置**：template_config.py 中已配置好5个模板的位置参数
5. **标题去重**：自动去除标题中连续重复字符（如"该该"->"该"）

## 模板五（预告）视觉规范（2026-04-20固化，长期复用）

**这是模板五的标准样式，以444期为基准确认。后续生成必须严格遵循此规范。**

### 布局结构

从上到下依次为：
1. **左上角**：主讲人头像（圆形裁剪） + 右侧个人介绍（姓名、奖项、书籍）
2. **中部居中**：直播主题标题（深蓝色粗体，居中对齐）
3. **标题下方**：3个核心问题（橙色圆点前缀，竖排）
4. **问题下方**：时间按钮（蓝色圆角矩形，白底白字，带图标）
5. **底部**：二维码（左侧） + 参与指引（右侧，含"长按识别"和橙色"回复「0414」"）

### 文字填充规则

| 元素 | 位置参数 | 颜色 | 字号 | 说明 |
|------|----------|------|------|------|
| 标题 | 居中，中心x=1459，y=440，最大宽度1125px | 深蓝色（#1F3864） | 自适应（字数多则小） | 最多2行，居中对齐 |
| 3句文案 | 固定y=[520, 580, 640]，左侧橙色圆点（x=116, r=6），文字x=145，最大宽度700px | 深蓝色 | 常规 | 竖排，带橙色圆点 |
| 时间按钮 | x=80, y=2340，框宽701x146 | 按钮内白底蓝字 | 加粗 | 格式："4月14日（周二）19:00" |
| 关键词 | x=80, y=2486，框147x114 | 橙色（#FC8414） | 加粗 | 纯日期码，如"0414" |
| 二维码 | x=294, y=2620，尺寸398x395 | — | — | 群里第一个预告二维码 |
| 二维码旁文字 | 二维码右侧 | 白字+橙色关键词 | 常规 | "长按识别二维码 回复「0414」" |

### 配色参考

- 主色（背景）：深蓝色 `#1F3864`
- 内容区背景：白色
- 强调色：橙色 `#FC8414`
- 正文：深蓝色
- 装饰：浅蓝色圆点 + 半透明"LUO SI DING"文字水印

### 二维码规则（重要，必须遵守）

| 模板 | 用途 | 二维码来源 |
|------|------|-----------|
| template_final (模板1) | 学院 | 链接生成的二维码 (qr_link_{期数}.png) |
| template_2 (模板2) | 预告+企微朋友圈 | 第二个二维码 (qr_2_fanxie_{期数}.png) |
| template_3 (模板3) | 回放 | 第一个二维码 (qr_1_yugao_{期数}.png) |
| template_4 (模板4) | 翻写 | 第一个二维码 (qr_1_yugao_{期数}.png) |
| template_5 (模板5) | 预告 | 第一个二维码 (qr_1_yugao_{期数}.png) |

**关键规则**：模板2/3/5 用第一个二维码（预告二维码），模板4用第二个二维码（翻写二维码）。

## 模板文件位置

- 模板1: /Users/fanlili/Downloads/live-poster-tool/template_1_latest.png
- 模板2: /Users/fanlili/Downloads/live-poster-tool/template_2_latest.png
- 模板3: /Users/fanlili/Downloads/live-poster-tool/template_3_latest.png
- 模板4: /Users/fanlili/Downloads/live-poster-tool/template_4_latest.png
- 模板5: /Users/fanlili/Downloads/live-poster-tool/template_5_latest.png（预告风格，螺丝钉上）

## 字体配置

- 优先使用思源黑体（Source Han Sans SC）：
  - 粗体：`/tmp/fonts/shs/OTF/SimplifiedChinese/SourceHanSansSC-Bold.otf`
  - 常规：`/tmp/fonts/shs/OTF/SimplifiedChinese/SourceHanSansSC-Regular.otf`
- 兜底字体：Noto Sans CJK（`/usr/share/fonts/opentype/noto/NotoSansCJK-*.ttc`）
- generate_image.py 中已配置自动回退逻辑

## 模板五布局参数（template_config.py 中已配置，直接复用）

**这是模板五的标准样式，以444期为基准确认。后续生成必须严格遵循此规范。**

### 布局结构

从上到下依次为：
1. **左上角**：主讲人头像（椭圆形） + 右侧个人介绍（姓名、头衔、作品）
2. **中部居中**：直播主题标题（深蓝色粗体，居中对齐）
3. **标题下方**：3个核心问题（橙色圆点前缀，竖排）
4. **问题下方**：时间按钮（蓝色圆角矩形，白底蓝字，带图标）
5. **底部**：二维码（左侧） + 参与指引（右侧，含"长按识别"和橙色"回复「0414」"）

### 文字填充规则

| 元素 | 位置参数 | 颜色 | 字号 | 说明 |
|------|----------|------|------|------|
| 标题 | 居中，中心x=1200，y=420，最大宽度2200px | 深蓝色（#1A3B8E） | 自适应（字数多则小） | 最多2行，居中对齐 |
| 3句文案 | 固定y=[600, 820, 1040]，左侧橙色圆点（x=200，r=10），文字x=240，最大宽度1900px | 深蓝色 | 常规 | 竖排，带橙色圆点 |
| 时间按钮 | x=80, y=1900，宽2219×449 | 按钮内白底蓝字 | 108pt | 格式："4月14日（周二）19:00" |
| 关键词 | x=80, y=2550，框147×114 | 橙色（#FC9F51） | 115pt | 纯日期码，如"0414" |
| 二维码 | x=80, y=2400，尺寸569×641 | — | — | 群里第一个预告二维码 |
| 二维码旁文字 | 二维码右侧 | 白字+橙色关键词 | 常规 | "长按识别二维码 回复「0414」" |

### 配色参考

- 主色（背景）：深蓝色 `#1A3B8E`
- 内容区背景：白色
- 强调色：橙色 `#FC9F51`
- 正文：深蓝色
- 装饰：半透明装饰元素

### 二维码规则（重要）

| 模板 | 用途 | 二维码来源 |
|------|------|-----------|
| template_final (模板1) | 学院 | 链接生成的二维码 (qr_link_{期数}.png) |
| template_2 (模板2) | 预告+企微朋友圈 | 第二个二维码 (qr_2_fanxie_{期数}.png) |
| template_3 (模板3) | 回放 | 第一个二维码 (qr_1_yugao_{期数}.png) |
| template_4 (模板4) | 翻写 | 第一个二维码 (qr_1_yugao_{期数}.png) |
| template_5 (模板5) | 预告 | 第一个二维码 (qr_1_yugao_{期数}.png) |

**关键规则**：模板2/3/5 用第一个二维码（预告二维码），模板4用第二个二维码（翻写二维码）。

## 模板文件位置

- 模板1: /Users/fanlili/Downloads/live-poster-tool/template_1_latest.png
- 模板2: /Users/fanlili/Downloads/live-poster-tool/template_2_latest.png
- 模板3: /Users/fanlili/Downloads/live-poster-tool/template_3_latest.png
- 模板4: /Users/fanlili/Downloads/live-poster-tool/template_4_latest.png
- 模板5: /Users/fanlili/Downloads/live-poster-tool/template_5_latest.png（螺丝钉上预告风格，2026-04-22更新）

## 关键词位置

- template_2: date_code_box = [945, 4153, 344, 106]，无白色背景
- template_3: date_code_box = [823, 4153, 344, 106]
- template_4: date_code_box = [833, 4153, 344, 106]
- template_5: date_code_box = [80, 2486, 147, 114]（位于时间按钮下方，橙色）

## content_y_offset（文案垂直位置偏移）

- template_final: -30
- template_2: -40
- template_3: -40
- template_4: -40
- template_5: 0（固定y位置）

## 已确认期数记录

- 452期（6月2日）- 已确认
- 451期（5月26日）- 已确认
- 450期（5月22日）- 已确认
- 445期（4月17日）- 已确认
- 444期（4月14日）- 已确认（含模板五预告）
- 443期（4月10日）- 已确认
- 441期（3月24日）- 已确认
- 440期（3月20日）- 已测试确认流程

**当前最新期数：452**
- 检测到比 452 更高的期数才触发生成（如 453、454...）
- 低于或等于 452 的期数不重复生成

**⚠️ 暂停记录：**
- 5月29日（周四）定时任务暂停——老板出差不直播
- 下次执行：6月1日（周一），准备6月3日（周二）452期直播

**模板五更新记录**：
- 2026-04-22：用新参考图替换模板五，更新了参数配置

（每次确认后更新此记录）

## 模板更新流程

如果用户给了新模板：
1. 保存为 template_1_latest.png ~ template_5_latest.png
2. 更新 template_config.py 中的路径配置
3. 更新 SKILL.md 中的模板文件位置
4. 记录到 memory/YYYY-MM-DD.md
