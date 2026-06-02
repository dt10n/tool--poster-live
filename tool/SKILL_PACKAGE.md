# 直播全流程自动化技能包

> 适用于：螺丝钉投资研究院 每周直播物料准备 + 海报生成 + 通知流程
> 版本：2026-05-18 更新版

---

## 触发方式

用户发送以下内容时启动本工作流：
- 直播间链接（小鹅通，格式如 `https://n6o8y.xetslk.com/sl/xxxx`）
- 直播大纲飞书文档链接（格式如 `https://epndqwwg0a.feishu.cn/docx/xxxx`）

---

## 工具依赖

- `lark-cli`：路径 `~/.npm-global/bin/lark-cli`，用于飞书消息发送、文档读写、文件上传
- `Python 3`：用于生成海报图片
- 海报生成脚本目录：`/Users/fanlili/Downloads/live-poster-tool/`

---

## 关键参数

| 角色/群组 | ID |
|---------|-----|
| PPT制作群 | chat_id: `oc_918c9be8ab6950e746bc308c8c32a334` |
| 内容小分队群 | chat_id: `oc_d49775cef6a606b893cdec743875be02` |
| 226课程群 | chat_id: `oc_ad278b7a15d31ab7a5ced19569769db8` |
| 胡亮 | open_id: `ou_0c491c7eb6f52da668fc2ef7264c6255` |
| 郭凤强 | open_id: `ou_ac59bb01b7e830ae90f51515e0b54a07` |
| 汤爱学 | open_id: `ou_e9a6dd9bd4ab1b8d65452635ef70c953` |
| 李菁 | open_id: `ou_93a19e195953359b82d943d7dff11b87` |
| 物料文档 | `https://epndqwwg0a.feishu.cn/docx/MXFjdkkkSoGDKTxr5BlcNCXDnjf` |
| 排期表 | `https://epndqwwg0a.feishu.cn/sheets/E1UqsTcGfhSRQOtk9VOcBN6RnUd` |
| 海报共享文件夹 | `https://epndqwwg0a.feishu.cn/drive/folder/MplmffLghlQ17Rd7blbcL6Umnhe` |

---

# 【阶段一：物料准备】

## 第一步：解析大纲文档

用 lark-cli 或 WebFetch 获取用户提供的大纲飞书文档，提取以下信息：

| 字段 | 提取位置 | 说明 |
|------|---------|------|
| `issue` | 文件名或文档标题 | "第449期"→449 |
| `title` | 【备选标题】部分 | 取第一条非删除线内容 |
| `captions` | 【介绍文案】部分 | 每条一行，条数按实际为准（可能3条或4条） |
| `REPLAY_PLAN` | 「直播回放文」相关表格 | "是否需要准备"/"公众号发文时间"列 |
| `FANXIE_PLAN` | 「直播翻写文」相关表格 | "是否需要准备"/"公众号发文时间"列 |

**⚠️ 重要：若文档中未找到 REPLAY_PLAN 或 FANXIE_PLAN，不能自行填写默认值，必须暂停并询问用户。**

直播时间格式固定：`X月X日（周X）19:00`（中文全角括号，时间固定19:00）

---

## 第二步：匹配小助手

用 lark-cli sheets +read 获取排期表，根据直播日期匹配对应小助手编号（格式如"5、6、7"）。

排期表：`https://epndqwwg0a.feishu.cn/sheets/E1UqsTcGfhSRQOtk9VOcBN6RnUd`（sheet_id: `8c44f7`）

---

## 第三步：生成四部分物料

**变量说明：**
- `{日期}`：简写，如 `5.19`
- `{完整日期}`：如 `2026年5月19日`
- `{星期}`：如 `周二`
- `{关键词}`：日期数字，如5.19→`0519`
- `{推广文案}`：条数与大纲介绍文案一致，不固定为3或4条

**物料格式（序号用 `1\.` 避免飞书渲染成全1）：**

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
{推广文案第一条}
...（按实际条数）

关键词：{关键词}
标签一：无
标签二：投资知识科普

4\. 【学院直播预告帖】

#学院专属直播课 螺丝钉直播第{期数}期将在『今晚7点』准时开始，欢迎大家实时互动交流～

【直播主题】：{标题}
【您将了解】：
{推广文案第一条}
...（与大纲介绍文案条数完全一致）

【直播时间】：{完整日期} 晚7-8点
【电脑观看】：{小鹅通链接}
【手机观看】：微信扫描下面二维码即可收看。也可以先把二维码图片保存手机里，微信里点击扫一扫-选择相册-选择二维码图片，即可进入查看。

【直播流程】：
第一环节主题讲解：10-20分钟
第二环节：实时互动交流，解答大家在投资上的困惑。
```

---

## 第四步：展示物料给用户确认

展示上述四部分内容，**等待用户回复「确认」/「ok」/「好的」后继续。**

---

## 第五步：插入到飞书物料文档

### 5.1 执行前必须先读取文档

```bash
lark-cli docs +fetch --doc https://epndqwwg0a.feishu.cn/docx/MXFjdkkkSoGDKTxr5BlcNCXDnjf --scope outline --format pretty
```

找到上一期标题的完整文字（格式如 `## 【AI生成】5.15（448期）...`），作为插入锚点。

### 5.2 飞书文档空行规则（严格遵守，实测验证）

**⚠️ 飞书文档是 block-based 结构，纯空行通过 API 插入时会被忽略，必须在空行位置插入零宽空格 U+200B（`​`）才能显示为可见空行。**

插入前必须调用：
```python
from live_material_generator import LiveMaterialGenerator
content = LiveMaterialGenerator._convert_blank_lines_for_feishu(raw_content)
# 或直接使用 generate_material_for_feishu() 代替 generate_material()
```

**8处必须有零宽空格空行的固定位置：**
1. 排期表链接之后
2. 直播间链接之后（序号2结束处）
3. 推广文案最后一条之后（关键词之前）
4. 标签二之后（序号4之前）
5. `4\. 【学院直播预告帖】`之后
6. `#学院专属直播课…`开场句之后
7. 推广文案列表最后一条之后（【直播时间】之前）
8. 【手机观看】之后（【直播流程】之前）

**每行之间用 `\n\n` 分隔**（单个 `\n` 会被飞书合并成同一段）。

### 5.3 插入命令

将处理好的内容保存为本地文件（相对路径），再执行：

```bash
lark-cli docs +update \
  --doc https://epndqwwg0a.feishu.cn/docx/MXFjdkkkSoGDKTxr5BlcNCXDnjf \
  --mode insert_before \
  --selection-by-title "## 【AI生成】{上一期完整标题}" \
  --markdown "@{物料文件名}.md"
```

插入位置：上一期标题行**之前**（整块插在上一期章节的上方），置顶内容**之后**。

### 5.4 插入后让用户确认

插入完成后，告知用户并附文档链接：
```
物料已插入飞书文档，请确认内容和空行格式是否正确：
https://epndqwwg0a.feishu.cn/docx/MXFjdkkkSoGDKTxr5BlcNCXDnjf
```
**⚠️ 等待用户确认后才能继续，严禁在用户确认前发汤爱学。**

---

## 第六步：发内容小分队 @汤爱学 复核

用户确认后，发送到内容小分队群：

```
@汤爱学 {星期}（{完整日期}）{期数}期直播物料，辛苦复核～
https://epndqwwg0a.feishu.cn/docx/MXFjdkkkSoGDKTxr5BlcNCXDnjf
```

**等待汤爱学回复「OK」/「ok」/「没问题」/「没有发现问题」后继续。**
需启动15分钟轮询检测回复：每15分钟抓取一次内容小分队群最新消息。

---

## 第七步：发PPT制作群 @胡亮（只艾特胡亮，不艾特郭凤强）

汤爱学复核OK后，**只**艾特胡亮：

```
{星期}（{完整日期}）晚直播（{期数}期），小助手的配置信息如下，辛苦配置～

直播间链接：{直播链接}

直播标题：{标题}

推广文案：
{推广文案第一条}
...（按实际条数）

关键词：{关键词}
标签一：无
标签二：投资知识科普
```

发完后立即启动15分钟轮询，等待胡亮发二维码。

---

# 【阶段二：海报生成】

## 第八步：自动检测并下载二维码

发完胡亮配置信息后，**立即启动15分钟轮询**：

```bash
python3 /Users/fanlili/Downloads/live-poster-tool/check_qr_codes.py --issue {期数}
```

**返回码：**
- `0` → 两张二维码已下载，继续下一步
- `1` → 未找到，15分钟后重试
- `2` → 只找到部分，检查异常

**二维码规则（长期固定，勿修改）：**
- `qr_1_{期数}.png` = 胡亮发「直播预告二维码👆」的紧前一条图片
- `qr_2_{期数}.png` = 胡亮发「翻写文二维码👆」的紧前一条图片

超时（当天18:00后）：停止轮询，告知用户「今日未收到胡亮二维码，请手动确认」。

---

## 第九步：生成5张海报

### 二维码映射规则（长期固定，不得修改）

| 模板ID | 海报名称 | 使用的二维码 |
|--------|---------|------------|
| template_final | 学院 | 由 `live_link` 自动生成（不用群里的） |
| template_2 | 翻写 | `qr_2_{期数}.png`（群里第二个） |
| template_3 | 回放 | `qr_1_{期数}.png`（群里第一个） |
| template_4 | 预告+企微朋友圈 | `qr_1_{期数}.png`（群里第一个） |
| template_5 | 新预告+企微朋友圈 | `qr_1_{期数}.png`（群里第一个） |

### 字体规则（必须遵守）

NotoSansCJK TTC 文件包含多语言字形，**必须用 index=2 加载简体中文（SC）字形**，否则默认加载日文（JP）字形，导致「置」「直」等汉字字形异常。代码中已通过 `_load_font()` 函数固化此规则，勿改动。

### 标题和介绍文案自动调整规则

生成海报时 `create_poster` 会自动处理：
1. **标题自动换行+字号缩小**：初始148，超宽时换行（最多2行），仍超则每次-4缩小，最小60
2. **介绍文案自动折行**：超宽自动折为多行，并扩大行间距
3. **整体太多时压缩间距**：默认144px，超出可用区域时自动压缩，下限80px
4. **不与直播时间叠加**：文案底部留白≥时间框顶部上方20px

### 生成代码

```python
import sys
sys.path.insert(0, '/Users/fanlili/Downloads/live-poster-tool')
from generate_image import create_poster
from template_config import TEMPLATES_CONFIG
import os

issue     = "449"  # 替换为实际期数
qr_first  = f'/Users/fanlili/Downloads/live-poster-tool/qr_1_{issue}.png'
qr_second = f'/Users/fanlili/Downloads/live-poster-tool/qr_2_{issue}.png'

qr_map = {
    'template_final': None,
    'template_2':     qr_second,
    'template_3':     qr_first,
    'template_4':     qr_first,
    'template_5':     qr_first,
}

os.makedirs('/Users/fanlili/Downloads/live-poster-tool/output', exist_ok=True)
for tpl_id, cfg in TEMPLATES_CONFIG.items():
    output = f'/Users/fanlili/Downloads/live-poster-tool/output/{issue}期{cfg["suffix"]}.png'
    create_poster(
        template_path=cfg['path'], output_path=output,
        qr_image_path=qr_map[tpl_id],
        title=title, caption_list=captions,
        live_time=live_time_formatted,
        template_id=tpl_id, date_code=date_code,
        live_link=live_link,
    )
```

### 输出命名规则

`output/{期数}期{suffix}.png`，suffix：`-学院` / `-翻写` / `-回放` / `-预告+企微朋友圈` / `-新预告+企微朋友圈`

---

## 第十步：在窗口展示海报给用户确认

**⚠️ 必须用 Read 工具在对话窗口逐张显示图片，不能只告知路径让用户自己去找。**

发文字摘要：
```
第{期数}期直播海报已生成，请确认：
标题：{title}
直播时间：{live_time}
关键词：{date_code}
```

依次展示5张：学院 → 翻写 → 回放 → 预告+企微朋友圈 → 新预告+企微朋友圈。

**等待用户回复「确认」/「ok」/「好的」后继续。**

---

## 第十一步：上传飞书共享文档

目标文件夹：`https://epndqwwg0a.feishu.cn/drive/folder/MplmffLghlQ17Rd7blbcL6Umnhe`

找对应期数子文件夹（如 `449`），不存在则用 `lark-cli drive files create_folder` 创建。上传5张海报：

```bash
lark-cli drive +upload --folder-token {子文件夹token} --file "output/{期数}期-学院.png"
# ...依次上传5张
```

---

## 第十二步：通知胡亮和郭凤强（同时艾特两人 + 附文件夹链接）

**⚠️ 必须附飞书文件夹链接，不能只发文字。**

```
{月}.{日}直播（第{期数}期）海报已上传至共享文档，请知悉～
https://epndqwwg0a.feishu.cn/drive/folder/{子文件夹token}
```

---

## 第十三步：发226课程群通知李菁

发两条消息到226课程群（chat_id: `oc_ad278b7a15d31ab7a5ced19569769db8`）：

### 第一条（只发文字，艾特李菁，不附图片）

```
菁宝@李菁 ，{星期}（{月.日}）晚直播【{标题}】，物料及直播发文安排（根据钉大回复）如下，请查收（小助手配置：{小助手编号}）：
1、直播链接：{直播链接}
2、学院预告帖子
3、直播回放文章安排：{REPLAY_PLAN}；直播翻写文章：{FANXIE_PLAN}
```

- `{月.日}` 不带前导零，如 `5.19`
- **第一条只发文字，不附任何图片**

### 第二条（预告帖正文）+ 紧接着发学院海报图片

**⚠️ 以下4处空行必须保留：**

```
【学院直播预告帖】
                            ← 空行1
#学院专属直播课 螺丝钉直播第{期数}期将在『今晚7点』准时开始，欢迎大家实时互动交流～
                            ← 空行2
【直播主题】：{标题}
【您将了解】：
{推广文案第一条}
{推广文案第二条}
...（条数与大纲介绍文案完全一致，不固定为3或4条）
                            ← 空行3
【直播时间】：{完整年月日} 晚7-8点
【电脑观看】：{直播链接}
【手机观看】：微信扫描下面二维码即可收看。也可以先把二维码图片保存手机里，微信里点击扫一扫-选择相册-选择二维码图片，即可进入查看。
                            ← 空行4
【直播流程】：
第一环节主题讲解：10-20分钟
第二环节：实时互动交流，解答大家在投资上的困惑。
```

发完第二条文字后，紧接着发学院海报图片（两步）：

```bash
# 第一步：bot 上传获取 image_key
lark-cli im images create --as bot --data '{"image_type":"message"}' --file "image=output/{期数}期-学院.png"
# 第二步：user 发送图片
lark-cli im +messages-send --chat-id oc_ad278b7a15d31ab7a5ced19569769db8 --image "{image_key}"
```

---

## 第十四步：更新期数记录

将 SKILL.md 底部「当前最新期数」改为本期期数，在「已确认期数记录」中添加本期。

---

# 核心规则汇总（每次执行必须遵守）

| 规则 | 内容 |
|------|------|
| 字体索引 | NotoSansCJK 必须用 index=2（SC简体中文），默认JP字形部分汉字字形异常 |
| 飞书文档空行 | 插入前必须用 `_convert_blank_lines_for_feishu()` 将空行替换为U+200B，8处固定位置 |
| 飞书文档每行\n\n | 单个\n会被飞书合并成同一段 |
| 插入后用户确认 | 用户确认飞书文档内容OK后，才能发汤爱学，严禁跳步 |
| 二维码自动检测 | `check_qr_codes.py --issue {期数}`，15分钟轮询，返回0才继续 |
| 海报必须窗口展示 | 用Read工具逐张在窗口显示，不能只告知路径 |
| 第七步只@胡亮 | 发配置信息时不艾特郭凤强 |
| 第十二步@两人+链接 | 海报上传通知必须同时艾特胡亮+郭凤强，且附飞书文件夹链接 |
| 李菁第一条无图 | 第一条只发文字，不附图片 |
| 李菁第二条介绍文案 | 【您将了解】条数与大纲一致，不固定为3或4条 |
| 李菁第二条4处空行 | 预告帖后、开场句后、介绍文案后、手机观看后 |
| 图片发送方式 | bot上传获取image_key → user发送，不能直接发本地文件 |
| 文章安排不默认 | REPLAY_PLAN/FANXIE_PLAN必须从大纲文档提取，未找到则暂停询问 |
| 二维码映射固定 | template_final自动生成；template_2用qr_2；其余用qr_1 |
| 海报命名规则 | output/{期数}期{suffix}.png |
