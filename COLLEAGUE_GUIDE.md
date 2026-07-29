# 同事安装使用教程

这份教程用于把「直播物料与海报生成 skill」安装到同事自己的 Codex 里，并复用同一个飞书机器人「直播物料小助手」执行群消息流程。

GitHub 地址：

```text
https://github.com/dt10n/tool--poster-live.git
```

## 一、先确认同事要用到哪一档

### 只生成 6 张海报

只需要安装仓库和 Python 依赖。  
不需要飞书机器人，不需要 App Secret，不需要群权限。

### 跑完整直播流程

包括读取/写入飞书物料、读取群二维码、发内容小分队、发 PPT 制作群、发 226 课程群、团队群 17:00 通知等。  
除了安装仓库，还必须配置飞书机器人 profile。

## 二、安装到 Codex skills 目录

在同事电脑终端执行：

```bash
mkdir -p ~/.codex/skills
git clone https://github.com/dt10n/tool--poster-live.git ~/.codex/skills/live-poster-codex
pip install -r ~/.codex/skills/live-poster-codex/requirements.txt
```

如果提示目录已经存在，说明同事之前装过，直接更新：

```bash
cd ~/.codex/skills/live-poster-codex
git pull
pip install -r requirements.txt
```

如果以后要更新到最新版：

```bash
cd ~/.codex/skills/live-poster-codex
git pull
pip install -r requirements.txt
```

安装完成后，重启 Codex。

## 三、在 Codex 里调用

重启后，对 Codex 说：

```text
调用 live-poster-codex skill，开始准备直播物料和海报。
直播链接：xxx
直播大纲文档：xxx
```

如果只从海报生成步骤开始，可以说：

```text
调用 live-poster-codex skill，从生成海报这一步开始。期数是 xxx，二维码已经准备好了。
```

## 四、配置飞书机器人 profile

如果同事要跑完整飞书流程，必须配置本地 `lark-cli` profile。

### 1. profile 名必须固定

必须叫：

```text
live-poster-bot
```

因为 skill 里的发群消息命令固定使用：

```bash
lark-cli --profile live-poster-bot ... --as bot
```

如果同事本地没有这个名字，或者叫成别的名字，Codex 就找不到机器人身份。

### 2. 使用你的机器人信息

机器人名称：

```text
直播物料小助手
```

App ID：

```text
cli_a94b5144b1381cb3
```

App Secret 不要写进文档、不要截图、不要发公开群。  
由你私下安全发给同事，或者现场帮同事配置。

### 3. 添加 profile

在同事电脑终端执行：

```bash
read -s APP_SECRET
printf "%s" "$APP_SECRET" | lark-cli profile add \
  --name live-poster-bot \
  --app-id cli_a94b5144b1381cb3 \
  --app-secret-stdin \
  --brand feishu
unset APP_SECRET
```

执行第一行后，粘贴 App Secret，然后回车。  
终端里不会显示粘贴内容，这是正常的。

如果同事电脑上的 `lark-cli` 不在 PATH 里，可以先确认位置：

```bash
which lark-cli
```

如果没有输出，需要先安装或配置 `lark-cli`，再继续。

### 4. 检查 profile 是否存在

```bash
lark-cli profile list
```

能看到：

```text
live-poster-bot
```

就说明本地 profile 名配置好了。

## 五、飞书后台和群权限检查

同事使用同一个机器人时，需要满足：

1. 「直播物料小助手」已经加入所有相关群。
2. 机器人有发送群消息权限。
3. 机器人有上传/发送图片权限。
4. 机器人有读取群消息权限，用于检查汤爱学/郭凤强回复和胡亮二维码。
5. 如果要读取/写入飞书文档、读取表格、上传共享空间，还需要同事自己的飞书登录或机器人具备对应权限。

常见相关群：

```text
内容小分队
PPT制作群
226课程群
螺丝钉团队群
```

## 六、做一次最小测试

为了避免正式直播当天才发现权限问题，建议先让同事测试机器人能不能发一条消息到测试群或内容小分队。

示例命令，把 `oc_xxx` 换成测试群 chat_id：

```bash
lark-cli --profile live-poster-bot im +messages-send \
  --as bot \
  --chat-id oc_xxx \
  --msg-type post \
  --content '{"zh_cn":{"title":"","content":[[{"tag":"text","text":"直播物料小助手测试消息"}]]}}'
```

发送成功后，群里消息发送者应该显示：

```text
直播物料小助手
```

不能显示为同事本人，也不能显示为范丽丽。

## 七、二维码文件命名

如果不是自动从飞书群下载二维码，而是手动放文件，二维码必须放在 skill 目录下，并按期数命名：

```text
qr_1_465.png
qr_2_465.png
qr_3_465.png
```

规则固定：

```text
第 1 张二维码 = qr_1_期数.png = 翻写、回放
第 2 张二维码 = qr_2_期数.png = 预告+企微、横版预告
第 3 张二维码 = qr_3_期数.png = 新预告+企微
学院海报二维码 = 用直播链接自动生成
```

## 八、输出位置

海报生成后在：

```text
~/.codex/skills/live-poster-codex/output/
```

文件名类似：

```text
465期-学院.png
465期-翻写.png
465期-回放.png
465期-预告+企微朋友圈.png
465期-新预告+企微朋友圈.png
465期-横版预告.png
```

## 九、同事给 Codex 的推荐话术

完整流程：

```text
调用 live-poster-codex skill，开始准备直播物料和海报。
直播链接：https://...
直播大纲文档：https://...

注意：
1. 先在窗口发给我预览，确认后再写入飞书物料文档。
2. 严格保持飞书文档里的换行和空行。
3. 群消息全部用直播物料小助手 bot 身份发送。
```

只生成海报：

```text
调用 live-poster-codex skill，从生成 6 张海报开始。
期数：465
标题：xxx
直播时间：x月x日（周x）19:00
关键词：260xxx
直播链接：https://...
介绍文案：
1. xxx
2. xxx
3. xxx
4. xxx
二维码已经放在 skill 目录下，文件名为 qr_1_465.png、qr_2_465.png、qr_3_465.png。
```

## 十、常见问题

### Codex 说找不到 skill

检查目录是否正确：

```bash
ls ~/.codex/skills/live-poster-codex/SKILL.md
```

如果文件存在，重启 Codex。

### 发群消息显示为本人

说明没有用 bot profile，或命令没有带：

```text
--profile live-poster-bot --as bot
```

正式流程里所有群消息都必须显示为：

```text
直播物料小助手
```

### profile 找不到

重新检查：

```bash
lark-cli profile list
```

必须能看到：

```text
live-poster-bot
```

### 生成海报时报找不到模板

需要在 skill 目录运行，或让脚本先切换目录：

```python
os.chdir("/Users/同事用户名/.codex/skills/live-poster-codex")
```

skill 内置流程已经会处理这个问题，手写脚本时才需要注意。

### 文字出现孤字或间距异常

不要自行缩小字号。  
正确做法是让 Codex 按 `SKILL.md` 里的规则调整标题框/文案框宽度和间距。

## 十一、给同事的一句话版本

```text
先把 https://github.com/dt10n/tool--poster-live.git clone 到 ~/.codex/skills/live-poster-codex，安装 requirements.txt，重启 Codex。只生成海报不用飞书配置；要跑完整流程，就把“直播物料小助手”的 App ID/Secret 配成名为 live-poster-bot 的 lark-cli profile。
```
