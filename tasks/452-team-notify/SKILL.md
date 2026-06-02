---
name: live-poster-452-team-notify
description: 452期直播当天17:00 给螺丝钉团队群发小助手安排+学院海报
---

给螺丝钉团队群（chat_id: oc_fcace7d6268518d54ed1998b29764543）发452期直播小助手安排消息和学院海报。

本期小助手编号：5号、6号、3号
直播日期：6月2日（周二）

**第一步：发小助手文字消息（post格式含@mentions）**

```bash
LARK_CLI_NO_PROXY=1 ~/.npm-global/bin/lark-cli im +messages-send \
  --chat-id "oc_fcace7d6268518d54ed1998b29764543" \
  --msg-type post \
  --content '{"zh_cn":{"title":"","content":[[{"tag":"text","text":"晚上7-8点直播小助手安排如下：其他同学，用自己账户回复～"},{"tag":"at","user_id":"all"},{"tag":"text","text":"\n\n6.2周二直播小助手\n李菁 螺丝钉小助手1号 红色（发PPT图片，控场，回复用户提问）\n亚芳 "},{"tag":"at","user_id":"ou_edb1b102186805f9e1d0a41dd2eae6e8","user_name":"杜亚芳"},{"tag":"text","text":" 螺丝钉小助手5号 绿色（回复用户提问）\n伞伞 "},{"tag":"at","user_id":"ou_d62113f91cb152e6424966002d9a96ed","user_name":"食米马伞"},{"tag":"text","text":" 螺丝钉小助手6号 粉色（回复用户提问）\n汤 "},{"tag":"at","user_id":"ou_e9a6dd9bd4ab1b8d65452635ef70c953","user_name":"汤爱学"},{"tag":"text","text":" 螺丝钉小助手3号 西柚色（回复用户提问）"}]]}}'
```

**第二步：上传并发送学院海报**

```bash
cd /Users/fanlili/Downloads/live-poster-tool/output
IMAGE_KEY=$(LARK_CLI_NO_PROXY=1 ~/.npm-global/bin/lark-cli im images create --as bot \
  --data '{"image_type":"message"}' \
  --file "image=452期-学院.png" 2>&1 | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['image_key'])")
LARK_CLI_NO_PROXY=1 ~/.npm-global/bin/lark-cli im +messages-send \
  --chat-id "oc_fcace7d6268518d54ed1998b29764543" \
  --image "$IMAGE_KEY"
```

执行完后输出结果确认（ok 或失败原因）。