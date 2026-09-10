# 同事安装与执行教程

这份教程用于把本仓库安装为同事自己的 Codex Skill，并在获得授权后执行完整的直播物料和海报流程。

仓库地址：

```text
https://github.com/dt10n/tool--poster-live.git
```

## 1. 能做什么

安装后，Codex 可以：

1. 从直播大纲文档（含批注）提取标题、介绍文案、期数和文章安排。
2. 生成直播物料，在窗口预览确认后写入飞书物料文档。
3. 用“直播小助理”机器人发内容小分队复核、发送 PPT 制作群配置消息并读取当期二维码。
4. 生成 4 张海报：学院、有二维码、无二维码、横版。
5. 在窗口展示海报，确认后上传共享空间，并用机器人发布课程群和同步群消息。
6. 建立直播当天北京时间 17:00 的团队群通知任务，正文和学院海报均由机器人发送。

所有写入飞书、上传、发群和创建定时任务都必须在用户明确确认对应内容后执行。不要跳过窗口预览。

## 2. 前置条件

同事电脑需要：

- macOS 和 Codex。
- Git、Python 3.8+。
- 可执行的 `lark-cli`。
- 能访问相关飞书文档、排期表和共享空间的个人飞书账号。
- 已加入或有权访问相关群聊的“直播小助理”机器人。

机器人群权限和同事个人文档权限是两回事：机器人负责所有群消息与图片；同事个人身份负责读取/写入云文档、排期表和共享空间。

## 3. 安装 Skill

在终端执行：

```bash
mkdir -p ~/.codex/skills
git clone https://github.com/dt10n/tool--poster-live.git ~/.codex/skills/live-poster-codex
cd ~/.codex/skills/live-poster-codex
python3 -m pip install -r requirements.txt
```

随后重启 Codex，让它重新加载 Skill。

日后更新使用：

```bash
cd ~/.codex/skills/live-poster-codex
git fetch --prune origin
git pull --ff-only
python3 -m pip install -r requirements.txt
```

不要从旧备份目录运行代码；实际运行目录永远是 `~/.codex/skills/live-poster-codex`。

## 4. 配置 lark-cli 和机器人

先确认 CLI 可用：

```bash
command -v lark-cli
lark-cli profile list
```

如果 `command -v lark-cli` 没有输出，先安装并配置公司使用的 lark-cli，再继续。Skill 会自动优先使用 PATH 中的 `lark-cli`；也可显式设置：

```bash
export LARK_CLI="$(command -v lark-cli)"
```

完整流程必须有固定名称的机器人 profile：

```text
live-poster-bot
```

机器人信息：

```text
显示名称：直播小助理
App ID：cli_a94b5144b1381cb3
profile 名：live-poster-bot
```

App Secret 不会、也不应写进 GitHub。由管理员通过私密渠道提供给同事。拿到 Secret 后，在终端执行：

```bash
read -s APP_SECRET
printf "%s" "$APP_SECRET" | lark-cli profile add \
  --name live-poster-bot \
  --app-id cli_a94b5144b1381cb3 \
  --app-secret-stdin \
  --brand feishu
unset APP_SECRET
```

输入 Secret 时终端不会回显字符，这是正常现象。配置完成后再次执行：

```bash
lark-cli profile list
```

必须能看到 `live-poster-bot`。

## 5. 飞书权限检查

管理员需确认“直播小助理”已加入以下群，并有读取消息、发送 post 消息、@ 人员、上传/发送图片的权限：

```text
内容小分队
PPT制作群
226课程群
课程群后同步群（oc_e14b3cdc1aac37eeb1cb6dd23fadb70c）
螺丝钉团队群
```

同事本人还必须拥有以下资源的查看或编辑权限：直播大纲文档、直播物料文档、排期表、海报共享空间文件夹。

先用测试群做一次机器人验证。让 Codex 发送测试 post 后，读取同一条消息确认：

```text
sender.sender_type == app
sender.name == 直播小助理
```

仅看到命令返回 `identity: bot` 不够。若群里显示同事本人，必须停止正式群发，检查是否遗漏 `--profile live-poster-bot --as bot`。

## 6. 标准执行话术

完整流程：

```text
调用 live-poster-codex skill，开始准备直播物料和海报。
直播链接：https://...
直播大纲文档：https://...

要求：
1. 读取大纲正文、表格和全部批注。
2. 物料先在窗口预览，确认后再写飞书文档。
3. 严格保留飞书文档的换行和空行。
4. 所有群消息和图片由直播小助理机器人发送，并逐条核验发送者。
```

若物料已人工完成，只做海报：

```text
调用 live-poster-codex skill，从海报生成步骤开始。
期数：473
直播链接：https://...
二维码已在 PPT 制作群发出。
```

若二维码已手动下载，放到 Skill 根目录并命名：

```text
qr_1_473.png
```

每期只使用这 1 张外部二维码，仅用于 `{期数}期-有二维码.png`。学院图的二维码由直播链接生成；无二维码和横版图不使用二维码或关键词。

## 7. 必须遵守的流程顺序

1. 读取大纲，提取期数、标题、介绍文案、回放/翻写文章安排和小助手编号。
2. 在 Codex 窗口预览物料；用户确认后，插入飞书物料文档。
3. 机器人发内容小分队，@ 汤爱学或用户指定的复核人。
4. 复核通过后，机器人发 PPT 制作群 @ 胡亮配置直播信息。
5. 轮询 PPT 制作群，获取胡亮或“真维斯”当期发出的唯一二维码。
6. 生成并在窗口展示 4 张海报。
7. 用户确认海报后，上传共享空间，通知 PPT 制作群的胡亮和郭凤强。
8. 机器人发送 226 课程群三条消息，再把预告帖正文和学院海报同步到同步群。
9. 创建直播当天北京时间 17:00 的团队群通知，真正 @ 对应小助手并发送学院海报。
10. 更新技能记录并打包完整备份。

## 8. 定时通知要求

团队群定时通知不能只依赖本机时区或 LaunchAgent 的触发时间。发送脚本必须：

1. 用 `Asia/Shanghai` 计算直播当天 17:00 的 epoch。
2. 提前触发时 sleep 到目标时间，不能提前发。
3. 晚于目标 30 分钟以上时不补发，记录日志并由用户决定。
4. 发送文字和图片后，读取群消息确认发件人为“直播小助理”。

## 9. 常见问题

| 现象 | 处理方式 |
|---|---|
| 群里显示同事本人 | 停止后续群发，检查 `live-poster-bot` profile 与 `--as bot`，不要自行用用户身份补发。 |
| 找不到二维码 | 确认机器人在 PPT 制作群，且有读取消息/下载图片权限；二维码来源可以是胡亮本人或“真维斯”。 |
| 无法读写飞书文档或云盘 | 这是同事个人账号权限不足，不是机器人发送权限问题。请管理员给该同事授权。 |
| 海报有孤字或文字过小 | 不缩小字号，按 `SKILL.md` 向右加宽文字框；介绍文案字号最低为 96。 |
| 定时任务已创建却未发消息 | 检查 LaunchAgent 是否加载、脚本 PATH 是否含 `node` 和 `lark-cli`、日志是否报错，以及目标群实际消息发送者。 |

## 10. 安全边界

- 不要把 App Secret、个人登录信息、二维码、群聊天记录或最终海报输出提交到仓库。
- 不要修改群 ID、人员 open_id、文案和模板规则，除非得到业务负责人明确确认。
- GitHub 仓库只能存放代码、模板、通用规则和不敏感教程。
