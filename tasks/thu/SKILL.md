---
name: live-poster-auto-thu
description: 每周一和每周四 14:00-18:30 自动执行：物料准备→海报生成→通知李菁
---

执行直播海报自动化工作流。代码目录：/Users/fanlili/Downloads/live-poster-tool/

---

# 【阶段一：物料准备】

## 第一步：用户触发

用户手动发送以下信息触发工作流：
- 直播间链接
- 直播大纲飞书文档链接

收到后直接进入第二步，无需自动抓取群消息。

---

## 第二步：解析直播信息

```python
import sys
sys.path.insert(0, '/Users/fanlili/Downloads/live-poster-tool')
from smart_parser import smart_parse_notice
data = smart_parse_notice(通告原文)
```

**直播时间格式固定为 `X月X日（周X）19:00`**（中文全角括号，时间固定19:00），不管群消息原始格式，统一转换。

**【直播日期规则——严格遵守】**
- 直播固定在**周二**或**周五**举行，不会是其他日期
- 物料准备在直播**前一天**执行：
  - 今天周四 → 直播时间是**明天周五**
  - 今天周一 → 直播时间是**明天周二**
- 确定直播日期时，必须基于"今天+1天"推算，不能用今天的日期作为直播日期

---

## 第三步：准备直播物料

参考 /Users/fanlili/Downloads/live-material-prep/SKILL.md 执行：

1. 从大纲文档提取标题、推广文案、期数，**同时提取文章安排**：
   - 查找文档中关于「回放文章」的安排（如"当天"/"直播后X天"/"无"等）→ 记为 `REPLAY_PLAN`
   - 查找文档中关于「翻写文章」的安排（如"直播后一周"/"无"等）→ 记为 `FANXIE_PLAN`
   - **若文档中未找到，不能自行填写默认值，必须暂停并询问用户：「大纲文档中未找到文章安排信息，请告知回放文章安排和翻写文章安排」**
2. 从排期表匹配小助手编号（排期表：https://epndqwwg0a.feishu.cn/sheets/E1UqsTcGfhSRQOtk9VOcBN6RnUd）
3. 按 /Users/fanlili/Downloads/live-material-prep/references/template.md 生成四部分物料
4. 读取物料文档确认上一期标题位置，再插入到飞书物料文档（https://epndqwwg0a.feishu.cn/docx/MXFjdkkkSoGDKTxr5BlcNCXDnjf）

**【飞书文档修改规则】`replace_range` 不支持多段，禁止用它修正内容。已插入内容如需替换，必须先 `delete_range` 再 `insert_before`。**

**【插入飞书文档空行规则——坚决不能违反】**

飞书文档是 block-based 结构，纯空行通过 API 插入时会被忽略导致大段内容堆在一起。
**必须**在插入前调用 `LiveMaterialGenerator._convert_blank_lines_for_feishu()` 将所有空行替换为含零宽空格（U+200B `​`）的行，或直接使用 `generate_material_for_feishu()` 代替 `generate_material()`。

以下 8 处位置必须有零宽空格空行：
1. 排期表链接 之后
2. 直播间链接 之后（序号2结束）
3. 推广文案最后一条 之后（关键词之前）
4. 标签二 之后（序号4之前）
5. 序号4「【学院直播预告帖】」之后
6. #学院专属直播课… 之后
7. 推广文案列表最后一条 之后（【直播时间】之前）
8. 【手机观看】 之后（【直播流程】之前）

---

## 第四步：插入飞书文档后，让用户确认

插入完成后，告知用户插入结果，并附上文档链接：
```
449期物料已插入飞书文档，请确认内容和空行格式是否正确：
https://epndqwwg0a.feishu.cn/docx/MXFjdkkkSoGDKTxr5BlcNCXDnjf
```

**等待用户回复「确认」/「ok」/「好的」后，才能继续下一步。**
**严禁在用户确认之前发送给汤爱学。**

---

## 第五步：发内容小分队 @汤爱学 复核

**【艾特规则】必须用 post 格式 + at 标签，纯文字 @名字 不会触发飞书通知：**
```bash
lark-cli im +messages-send --msg-type post --content '{"zh_cn":{"content":[[{"tag":"at","user_id":"open_id"},{"tag":"text","text":" 消息内容"}]]}}'
```


用户确认后，发送到内容小分队群（chat_id: oc_d49775cef6a606b893cdec743875be02），艾特汤爱学（open_id: ou_e9a6dd9bd4ab1b8d65452635ef70c953）：

```bash
lark-cli im +messages-send \
  --chat-id oc_d49775cef6a606b893cdec743875be02 \
  --msg-type post \
  --content '{"zh_cn":{"title":"","content":[[{"tag":"at","user_id":"ou_e9a6dd9bd4ab1b8d65452635ef70c953","user_name":"汤爱学"},{"tag":"text","text":" {星期}（{完整日期}）{期数}期直播物料，辛苦复核～\nhttps://epndqwwg0a.feishu.cn/docx/MXFjdkkkSoGDKTxr5BlcNCXDnjf"}]]}}'
```

**等待汤爱学回复「OK」/「ok」/「没问题」后继续。**

---

## 第六步：发 PPT制作群 @胡亮

汤爱学复核OK后，发到PPT制作群（chat_id: oc_918c9be8ab6950e746bc308c8c32a334），艾特胡亮（ou_0c491c7eb6f52da668fc2ef7264c6255）。

**必须用 post 格式 + at 标签触发@通知：**
```bash
lark-cli im +messages-send \
  --chat-id oc_918c9be8ab6950e746bc308c8c32a334 \
  --msg-type post \
  --content '{"zh_cn":{"title":"","content":[[{"tag":"at","user_id":"ou_0c491c7eb6f52da668fc2ef7264c6255","user_name":"胡亮"},{"tag":"text","text":" {星期}（{完整日期}）晚直播（{期数}期），小助手的配置信息如下，辛苦配置～\n\n直播间链接：{直播链接}\n\n直播标题：{标题}\n\n推广文案：\n{推广文案全部条目每条\\n分隔}\n\n关键词：{关键词}\n标签一：无\n标签二：投资知识科普"}]]}}'
```

---

# 【阶段二：海报生成】

## 第七步：下载群内三张二维码

发完胡亮配置信息后，**立即启动 15 分钟轮询**，使用 `check_qr_codes.py` 自动检测并下载：

```bash
python3 /Users/fanlili/Downloads/live-poster-tool/check_qr_codes.py --issue {期数}
```

**返回码说明：**
- `0` → 三张二维码已全部下载，继续下一步
- `1` → 胡亮还未发，15 分钟后重试（通过 ScheduleWakeup 延迟 900 秒）
- `2` → 只找到部分，检查异常

**二维码规则（长期规则，勿修改）：**
- `qr_1_{期数}.png` = 胡亮发的**第1张图片**（按发送时间顺序，不依赖文字标注）
- `qr_2_{期数}.png` = 胡亮发的**第2张图片**
- `qr_3_{期数}.png` = 胡亮发的**第3张图片**

**ScheduleWakeup prompt 模板（每次轮询复用此 prompt）：**
```
python3 /Users/fanlili/Downloads/live-poster-tool/check_qr_codes.py --issue {期数}
- 返回 0：下载完成，告知用户「胡亮已发二维码，已下载，准备生成6张海报」，继续第八步
- 返回 1：告知用户「胡亮还未发二维码，15分钟后再次检查」，再次 ScheduleWakeup 900秒
- 超时（18:00后）：停止轮询，告知用户「今日未收到胡亮二维码，请手动确认」
```

---

## 第八步：生成6张海报

```python
import sys
sys.path.insert(0, '/Users/fanlili/Downloads/live-poster-tool')
import os
os.chdir('/Users/fanlili/Downloads/live-poster-tool')  # 必须！模板路径为相对路径，否则报"找不到模板文件"
from generate_image import create_poster
from template_config import TEMPLATES_CONFIG

issue     = data['issue_number']
qr_first  = f'/Users/fanlili/Downloads/live-poster-tool/qr_1_{issue}.png'
qr_second = f'/Users/fanlili/Downloads/live-poster-tool/qr_2_{issue}.png'
qr_third  = f'/Users/fanlili/Downloads/live-poster-tool/qr_3_{issue}.png'

# 二维码映射规则（长期规则，勿修改）：
# 按胡亮发图顺序：第1张=qr_1，第2张=qr_2，第3张=qr_3，不依赖文字标注
# template_final（学院）：用直播链接自动生成
# 图2（翻写）、图3（回放）：用第1张（qr_1）
# 图4（预告+企微）、图6（横版预告）：用第2张（qr_2）
# 图5（新预告）：用第3张（qr_3）
qr_map = {
    'template_final': None,        # 由 live_link 自动生成
    'template_2':     qr_first,    # 图2 翻写：第1张
    'template_3':     qr_first,    # 图3 回放：第1张
    'template_4':     qr_second,   # 图4 预告+企微：第2张
    'template_5':     qr_third,    # 图5 新预告：第3张
    'template_6':     qr_second,   # 图6 横版预告：第2张
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

**【布局参数说明（2026-06-01 更新，已写入 template_config.py，勿手动修改）】**
- 模板1-4：`title_y=2122`（标题上移100px）、`bullet_start_y=2483`、`bullet_spacing=160`
- 模板5：`title_y=1354`，间距由 `_draw_template5_content` 动态计算（SPACING=144，gap上限40px），不修改
- 模板6（横版）：`title_font_size=180`、`title_y=280`、`content_bot=1340`、`bullet_spacing=110`、`date_code_font_size=116`

---

## 第九步：展示海报给用户确认

先发文字：
```
📺 第{期数}期直播海报已生成，请确认：
标题：{title}
直播时间：{live_time}
关键词：{date_code}

确认无误请回复「确认」或「ok」，我会上传到飞书共享文档并通知李菁。
```

然后用 Read 工具依次展示6张海报（**必须在对话窗口里逐张显示图片**，不能只告知路径让用户自己去找）：
1. output/{期数}期-学院.png
2. output/{期数}期-翻写.png
3. output/{期数}期-回放.png
4. output/{期数}期-预告+企微朋友圈.png
5. output/{期数}期-新预告+企微朋友圈.png
6. output/{期数}期-横版预告.png

**等待用户回复「确认」/「ok」/「好的」后继续。**

---

## 第十步：上传飞书 + 通知胡亮和郭凤强

### 10.1 上传到飞书共享文档
目标文件夹：https://epndqwwg0a.feishu.cn/drive/folder/MplmffLghlQ17Rd7blbcL6Umnhe

找对应期数子文件夹（命名如 `448-20260515`），不存在则创建。上传6张海报。

### 10.2 通知胡亮和郭凤强（PPT制作群，同时艾特两人）
艾特胡亮（ou_0c491c7eb6f52da668fc2ef7264c6255）和郭凤强（ou_ac59bb01b7e830ae90f51515e0b54a07），**必须附上飞书文件夹链接**：
```
{月}.{日}直播（第{期数}期）海报已上传至共享文档，请知悉～
https://epndqwwg0a.feishu.cn/drive/folder/{子文件夹token}
```

---

## 第十一步：发226课程群通知李菁

发两条消息到226课程群（chat_id: oc_ad278b7a15d31ab7a5ced19569769db8）：

**第一条**（只发文字，艾特李菁 open_id: ou_93a19e195953359b82d943d7dff11b87，**不附图片**）：
```
菁宝@李菁 ，{星期}（{月.日}）晚直播【{标题}】，物料及直播发文安排（根据钉大回复）如下，请查收（小助手配置：{小助手编号}）：
1、直播链接：{直播链接}
2、学院预告帖子
3、直播回放文章安排：{回放安排}；直播翻写文章：{翻写安排}
```
- `{月.日}` 格式：不带前导零，如 `5.15`
- `{回放安排}` 填入第三步从大纲文档提取的 `REPLAY_PLAN`；`{翻写安排}` 填入 `FANXIE_PLAN`
- **第一条只发文字，不附任何图片**

**第二条**（预告帖正文 + 学院海报图片）：
```
【学院直播预告帖】

#学院专属直播课 螺丝钉直播第{期数}期将在『今晚7点』准时开始，欢迎大家实时互动交流～

【直播主题】：{标题}
【您将了解】：
{推广文案全部条目，大纲有几条写几条，不能多也不能少}

【直播时间】：{完整年月日} 晚7-8点
【电脑观看】：{直播链接}
【手机观看】：微信扫描下面二维码即可收看。也可以先把二维码图片保存手机里，微信里点击扫一扫-选择相册-选择二维码图片，即可进入查看。

【直播流程】：
第一环节主题讲解：10-20分钟
第二环节：实时互动交流，解答大家在投资上的困惑。
```
- `{完整年月日}` 格式：如 `2026年5月15日`
- **【您将了解】条数与大纲介绍文案保持一致**：大纲有几条就写几条，不能多也不能少
- 发完文字后，紧接着发学院海报图片（两步，缺一不可）：
  ```bash
  # 第一步：用 bot 上传获取 image_key
  lark-cli im images create --as bot --data '{"image_type":"message"}' --file "image=output/{期数}期-学院.png"
  # 第二步：用 user 发送图片消息
  lark-cli im +messages-send --chat-id oc_ad278b7a15d31ab7a5ced19569769db8 --image "{image_key}"
  ```

---

## 第十二步：给螺丝钉团队群设置定时通知

发完李菁消息后，立即用 `mcp__scheduled-tasks__create_scheduled_task` 创建一个**一次性定时任务**，在**直播当天17:00**发送小助手安排+学院海报。

**小助手人员对照表（长期规则，勿修改）：**
| 编号 | 昵称 | 飞书名 | open_id | 颜色 | 职责 |
|------|------|--------|---------|------|------|
| 1号 | 李菁 | 李菁 | ou_93a19e195953359b82d943d7dff11b87 | 红色 | 发PPT图片，控场，回复用户提问（不需要@） |
| 5号 | 亚芳 | 杜亚芳 | ou_edb1b102186805f9e1d0a41dd2eae6e8 | 绿色 | 回复用户提问 |
| 6号 | 伞伞 | 食米马伞 | ou_d62113f91cb152e6424966002d9a96ed | 粉色 | 回复用户提问 |
| 3号 | 汤 | 汤爱学 | ou_e9a6dd9bd4ab1b8d65452635ef70c953 | 西柚色 | 回复用户提问 |
| 7号 | 范丽丽 | 范丽丽 | ou_2bd618ee347cc81fe4f1832ef1f35c91 | 青色 | 回复用户提问 |

**规则：**
- 每期必有 1号、5号、6号
- 3号和7号轮换（看本期小助手配置决定）
- 1号不需要@，其余需要@

**消息格式（post格式，以小助手5、6、3为例）：**
```
晚上7-8点直播小助手安排如下：其他同学，用自己账户回复～@所有人

{月.日}{周X}直播小助手
李菁 螺丝钉小助手1号 红色（发PPT图片，控场，回复用户提问）
亚芳 @杜亚芳 螺丝钉小助手5号 绿色（回复用户提问）
伞伞 @食米马伞 螺丝钉小助手6号 粉色（回复用户提问）
汤 @汤爱学 螺丝钉小助手3号 西柚色（回复用户提问）
```

**创建定时任务示例（task_id命名：live-poster-{期数}-team-notify）：**
- `taskId`: `live-poster-{期数}-team-notify`
- `fireAt`: `{直播日期}T17:00:00+08:00`（直播当天北京时间17:00）
- `prompt` 中包含：
  1. 发 post 格式文字消息到 `oc_fcace7d6268518d54ed1998b29764543`，根据本期小助手编号按对照表组装@mentions
  2. 上传 `output/{期数}期-学院.png` 获取 image_key，再发送到同群

---

## 第十三步：更新 SKILL.md

将「当前最新期数」改为本期期数，在「已确认期数记录」添加本期。
**更新后，当天后续的30分钟轮询将自动跳过（第一步期数检查不通过）。**