直播全流程工作流：物料准备 → 文档更新 → 复核 → 发PPT群 → 生成海报 → 上传 → 通知李菁

脚本目录：/Users/fanlili/Downloads/live-poster-tool/
物料目录：/Users/fanlili/Downloads/live-material-prep/

---

# 【阶段一：物料准备】

## 第一步：用户触发

用户手动发送以下信息触发工作流：
- 直播间链接（小鹅通）
- 直播大纲飞书文档链接

收到后直接进入第二步，无需自动抓取群消息。

---

## 第二步：解析大纲文档

用 lark-cli 或 WebFetch 获取大纲文档内容，提取：
- **期数**：从文件名或文档标题（"第448期"→448）
- **标题**：从【备选标题】部分取第一条非删除线内容
- **推广文案**：从【介绍文案】部分取全部条目（每条一行，最多4条）
- **REPLAY_PLAN**：文档中「直播回放文」相关表格，"是否需要准备"/"公众号发文时间"列
- **FANXIE_PLAN**：文档中「直播翻写文」相关表格，"是否需要准备"/"公众号发文时间"列

**若文档中未找到 REPLAY_PLAN 或 FANXIE_PLAN，不能自行填写默认值，必须暂停询问用户。**

直播时间格式固定为 `X月X日（周X）19:00`（中文全角括号，时间固定19:00）。

**【直播日期规则——严格遵守】**
- 直播固定在**周二**或**周五**举行，不会是其他日期
- 物料准备在直播**前一天**执行：
  - 今天周四 → 直播时间是**明天周五**
  - 今天周一 → 直播时间是**明天周二**
- 确定直播日期时，必须基于"今天+1天"推算，不能用今天的日期作为直播日期

---

## 第三步：匹配小助手

用 WebFetch 获取排期表：https://epndqwwg0a.feishu.cn/sheets/E1UqsTcGfhSRQOtk9VOcBN6RnUd

根据日期列匹配对应的小助手编号（格式如"5号、6号、3号"）。

---

## 第四步：生成四部分物料

关键词规则：日期数字，如5.15→0515。

按以下格式生成（序号用 `1\.` 避免飞书渲染成全1）：

```
## 【AI生成】{日期}（{期数}期）（{星期}）直播：{标题}

1\. 小助手配置：{小助手编号}
[直播小助手排期表](https://epndqwwg0a.feishu.cn/sheets/E1UqsTcGfhSRQOtk9VOcBN6RnUd)

2\. 直播间创建：
直播间链接：{小鹅通链接}

3\. 同步胡亮如下信息：
{星期}（{完整日期}）晚直播（{期数}期），小助手的配置信息如下，辛苦配置～
直播间链接：{小鹅通链接}
直播标题：{标题}
推广文案：
{推广文案全部条目，大纲有几条写几条，不能多也不能少}

关键词：{关键词}
标签一：无
标签二：投资知识科普

4\. 【学院直播预告帖】

#学院专属直播课 螺丝钉直播第{期数}期将在『今晚7点』准时开始，欢迎大家实时互动交流～

【直播主题】：{标题}
【您将了解】：
{推广文案全部条目，大纲有几条写几条，不能多也不能少}

【直播时间】：{完整日期} 晚7-8点
【电脑观看】：{小鹅通链接}
【手机观看】：微信扫描下面二维码即可收看。也可以先把二维码图片保存手机里，微信里点击扫一扫-选择相册-选择二维码图片，即可进入查看。

【直播流程】：
第一环节主题讲解：10-20分钟
第二环节：实时互动交流，解答大家在投资上的困惑。
```

---

## 第五步：展示物料给用户确认

展示四部分物料内容，等待用户回复「确认」/「ok」/「好的」后继续。

---

## 第六步：插入到飞书物料文档

**必须先 fetch 文档，找到上一期标题的完整文字，再执行插入。**

文档：https://epndqwwg0a.feishu.cn/docx/MXFjdkkkSoGDKTxr5BlcNCXDnjf

插入位置：在上一期标题行**之前**（整块插在上一期章节的上方），且在置顶内容**之后**。

**【飞书文档插入格式规则——严格遵守，经实测验证】**：
1. **每行独立成段**：每一行内容之间必须用 `\n\n` 分隔，单个 `\n` 会被飞书合并成同一段
2. **空行用零宽空格 `​`（U+200B）占位**：纯空行需在空行位置插入零宽空格字符单独成段
3. **零宽空格空行位置**（固定8处）：
   - 排期表链接之后
   - 直播间链接之后（序号2结束处）
   - 推广文案最后一条之后（关键词之前）
   - 标签二之后（序号4之前）
   - 序号4标题之后
   - #学院开场句之后
   - 推广文案列表最后一条之后（【直播时间】之前）
   - 【手机观看】之后（【直播流程】之前）

**【插入操作规则】`replace_range` 不支持多段落，禁止用它修正内容；已插入内容如需替换，必须先 `delete_range` 再 `insert_before`：**
```bash
# 步骤1：删除旧内容
~/.npm-global/bin/lark-cli docs +update \
  --doc https://epndqwwg0a.feishu.cn/docx/MXFjdkkkSoGDKTxr5BlcNCXDnjf \
  --mode delete_range \
  --selection-with-ellipsis "## 【AI生成】{本期标题}...{本期最后一行}"

# 步骤2：重新插入
~/.npm-global/bin/lark-cli docs +update \
  --doc https://epndqwwg0a.feishu.cn/docx/MXFjdkkkSoGDKTxr5BlcNCXDnjf \
  --mode insert_before \
  --selection-by-title "## 【AI生成】{上一期完整标题}" \
  --markdown @物料文件.md
```

---

## 第七步：发内容小分队 @汤爱学 复核

发送到内容小分队群（chat_id: oc_d49775cef6a606b893cdec743875be02），艾特汤爱学（open_id: ou_e9a6dd9bd4ab1b8d65452635ef70c953）：

**必须用 post 格式 + at 标签，才能触发飞书@通知，纯文字 @名字 无效：**
```bash
lark-cli im +messages-send \
  --chat-id oc_d49775cef6a606b893cdec743875be02 \
  --msg-type post \
  --content '{
    "zh_cn": {
      "title": "",
      "content": [[
        {"tag": "at", "user_id": "ou_e9a6dd9bd4ab1b8d65452635ef70c953", "user_name": "汤爱学"},
        {"tag": "text", "text": " {星期}（{完整日期}）{期数}期直播物料，辛苦复核～\nhttps://epndqwwg0a.feishu.cn/docx/MXFjdkkkSoGDKTxr5BlcNCXDnjf"}
      ]]
    }
  }'
```

**只发固定话术+文档链接，不发物料内容。**

等待汤爱学回复「OK」/「ok」/「没问题」后继续。

---

## 第八步：发 PPT制作群 @胡亮（只艾特胡亮）

汤爱学复核OK后，发到PPT制作群（chat_id: oc_918c9be8ab6950e746bc308c8c32a334），**只**艾特胡亮（ou_0c491c7eb6f52da668fc2ef7264c6255），不艾特郭凤强。

**必须用 post 格式 + at 标签触发@通知：**
```bash
lark-cli im +messages-send \
  --chat-id oc_918c9be8ab6950e746bc308c8c32a334 \
  --msg-type post \
  --content '{
    "zh_cn": {
      "title": "",
      "content": [[
        {"tag": "at", "user_id": "ou_0c491c7eb6f52da668fc2ef7264c6255", "user_name": "胡亮"},
        {"tag": "text", "text": " {星期}（{完整日期}）晚直播（{期数}期），小助手的配置信息如下，辛苦配置～\n\n直播间链接：{直播链接}\n\n直播标题：{标题}\n\n推广文案：\n{推广文案全部条目每条一行}\n\n关键词：{关键词}\n标签一：无\n标签二：投资知识科普"}
      ]]
    }
  }'
```

---

# 【阶段二：海报生成】

## 第九步：下载群内**三张**二维码

等待胡亮在PPT制作群发3张二维码，每张图片后紧跟标注文字。用 `check_qr_codes.py` 自动检测下载：

```bash
python3 /Users/fanlili/Downloads/live-poster-tool/check_qr_codes.py --issue {期数}
```

**二维码规则（2026-06-01 更新，452期确认关键词）：**
- `qr_1_{期数}.png` = 头条预告二维码（"头条预告二维码👆"紧前的图片）
- `qr_2_{期数}.png` = 翻写文二维码（"翻写文二维码👆"紧前的图片）
- `qr_3_{期数}.png` = 图文预告二维码（"图文预告二维码👆"紧前的图片）

---

## 第十步：生成**6张**海报

**二维码映射规则（2026-06-01 更新，长期固定）：**
- template_final（学院）：由 live_link 自动生成，不用群里的二维码
- template_2（翻写）：用 qr_1_{期数}.png（群里第一个）
- template_3（回放）：用 qr_1_{期数}.png（群里第一个）
- template_4（预告+企微朋友圈）：用 qr_2_{期数}.png（群里第二个）
- template_5（新预告+企微朋友圈）：用 qr_3_{期数}.png（群里第三个）
- template_6（横版预告）：用 qr_2_{期数}.png（群里第二个）

**输出命名规则**：`output/{期数}期{suffix}.png`，suffix 来自 TEMPLATES_CONFIG：
- -学院
- -翻写
- -回放
- -预告+企微朋友圈
- -新预告+企微朋友圈

**【海报生成注意事项】**
1. **必须先 `os.chdir` 到工具目录**：模板路径是相对路径，若当前目录不是工具目录会报"找不到模板文件"错误
2. **标题支持手动换行**：在 `title` 字符串中插入 `\n` 可强制换行，例如 `"定投宽基指数，该如何做：\n螺丝钉指数增强组合定投复盘"`
3. **布局参数（2026-05-25 更新，已写入 template_config.py）**：
   - 模板1-4：`title_y=2122`（标题上移100px）、`bullet_start_y=2483`、`bullet_spacing=160`
   - 模板5：`title_y=1354`，间距由 `_draw_template5_content` 动态计算（SPACING=144，gap上限40px），不修改

```python
import sys, os
os.chdir('/Users/fanlili/Downloads/live-poster-tool')  # 必须！否则找不到模板
sys.path.insert(0, '/Users/fanlili/Downloads/live-poster-tool')
from generate_image import create_poster
from template_config import TEMPLATES_CONFIG

issue      = data['issue_number']
qr_first   = f'/Users/fanlili/Downloads/live-poster-tool/qr_1_{issue}.png'
qr_second  = f'/Users/fanlili/Downloads/live-poster-tool/qr_2_{issue}.png'
qr_third   = f'/Users/fanlili/Downloads/live-poster-tool/qr_3_{issue}.png'

# 二维码映射规则（2026-06-01 更新，长期固定）
qr_map = {
    'template_final': None,        # 学院：live_link 自动生成
    'template_2':     qr_first,    # 翻写：第1个
    'template_3':     qr_first,    # 回放：第1个
    'template_4':     qr_second,   # 预告+企微：第2个
    'template_5':     qr_third,    # 新预告：第3个
    'template_6':     qr_second,   # 横版预告：第2个
}

for tpl_id, cfg in TEMPLATES_CONFIG.items():
    suffix = cfg.get('suffix', '')
    output = f'/Users/fanlili/Downloads/live-poster-tool/output/{issue}期{suffix}.png'
    create_poster(
        template_path=cfg['path'], output_path=output,
        qr_image_path=qr_map[tpl_id],
        title=data['title'], caption_list=data['captions'],
        live_time=live_time_formatted,
        template_id=tpl_id, date_code=data['date_code'],
        live_link=data['link'],
    )
```

---

## 第十一步：展示海报给用户确认

先发文字：
```
📺 第{期数}期直播海报已生成，请确认：
标题：{title}
直播时间：{live_time}
关键词：{date_code}

确认无误请回复「确认」或「ok」，我会上传到飞书共享文档并通知李菁。
```

然后用 Read 工具依次展示5张海报。等待用户回复「确认」/「ok」/「好的」后继续。

---

## 第十二步：上传飞书 + 通知胡亮和郭凤强

### 12.1 上传到飞书共享文档
目标文件夹：https://epndqwwg0a.feishu.cn/drive/folder/MplmffLghlQ17Rd7blbcL6Umnhe

找对应期数子文件夹（命名如 `448-20260515`），不存在则创建。上传5张海报。

### 12.2 通知胡亮和郭凤强（PPT制作群，同时艾特两人）

艾特胡亮（ou_0c491c7eb6f52da668fc2ef7264c6255）和郭凤强（ou_ac59bb01b7e830ae90f51515e0b54a07）：
```
{月}.{日}直播（第{期数}期）海报已上传至共享文档，请知悉～
```

---

## 第十三步：发226课程群通知李菁

发两条消息到226课程群（chat_id: oc_ad278b7a15d31ab7a5ced19569769db8）：

**第一条**（只发文字，艾特李菁 open_id: ou_93a19e195953359b82d943d7dff11b87，**不附图片**）：
```
菁宝@李菁 ，{星期}（{月.日}）晚直播【{标题}】，物料及直播发文安排（根据钉大回复）如下，请查收（小助手配置：{小助手编号}）：
1、直播链接：{直播链接}
2、学院预告帖子
3、直播回放文章安排：{REPLAY_PLAN}；直播翻写文章：{FANXIE_PLAN}
```
- `{月.日}` 不带前导零，如 `5.15`
- `{REPLAY_PLAN}` 和 `{FANXIE_PLAN}` 从第二步大纲文档提取，不能默认填写
- **第一条只发文字，不附任何图片**

**第二条**（预告帖正文 + 附学院海报图片），注意4处空行必须保留：
```
【学院直播预告帖】
（空行）
#学院专属直播课 螺丝钉直播第{期数}期将在『今晚7点』准时开始，欢迎大家实时互动交流～
（空行）
【直播主题】：{标题}
【您将了解】：
{推广文案全部条目，大纲有几条写几条，不能多也不能少}
（空行）
【直播时间】：{完整年月日} 晚7-8点
【电脑观看】：{直播链接}
【手机观看】：微信扫描下面二维码即可收看。也可以先把二维码图片保存手机里，微信里点击扫一扫-选择相册-选择二维码图片，即可进入查看。
（空行）
【直播流程】：
第一环节主题讲解：10-20分钟
第二环节：实时互动交流，解答大家在投资上的困惑。
```
- `{完整年月日}` 格式：如 `2026年5月15日`
- **只有第二条消息附学院海报图片**：output/{期数}期-学院.png（两步：先 bot 上传取 image_key，再 user 发图）

---

## 第十四步：更新 SKILL.md

将 /Users/fanlili/Downloads/live-poster-tool/SKILL.md 底部「当前最新期数」改为本期期数，在「已确认期数记录」添加本期。

---

# 关键参数速查

| 角色 | chat_id / open_id |
|------|-------------------|
| PPT制作群 | chat_id: oc_918c9be8ab6950e746bc308c8c32a334 |
| 内容小分队群 | chat_id: oc_d49775cef6a606b893cdec743875be02 |
| 226课程群 | chat_id: oc_ad278b7a15d31ab7a5ced19569769db8 |
| 胡亮 | open_id: ou_0c491c7eb6f52da668fc2ef7264c6255 |
| 郭凤强 | open_id: ou_ac59bb01b7e830ae90f51515e0b54a07 |
| 汤爱学 | open_id: ou_e9a6dd9bd4ab1b8d65452635ef70c953 |
| 李菁 | open_id: ou_93a19e195953359b82d943d7dff11b87 |
