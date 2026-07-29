# -*- coding: utf-8 -*-
import json
try:
    import qrcode
except ImportError:
    qrcode = None
from qr_generator import generate_qr_image as _gen_qr_image
import sys
import os
import urllib.request
from collections import deque
from PIL import Image, ImageDraw, ImageFont
from smart_parser import smart_parse_notice
from template_config import get_template_config

# NotoSansCJK TTC 索引：0=JP, 1=KR, 2=SC(简体中文), 3=TC, 4=HK
# 必须用 index=2 加载简体中文字形，否则默认 JP 字形（如「置」字形不同）
_NOTO_SC_INDEX = 2

def _load_font(font_path, size):
    """加载字体，NotoSansCJK 系列自动使用简体中文字形（index=2）"""
    if font_path and "NotoSansCJK" in font_path:
        return ImageFont.truetype(font_path, size, index=_NOTO_SC_INDEX)
    return ImageFont.truetype(font_path, size)

def _connected_components_bbox(mask, step, x0, y0, min_count=10):
    gh = len(mask)
    gw = len(mask[0]) if gh else 0
    seen = [[False] * gw for _ in range(gh)]
    out = []
    for gy in range(gh):
        for gx in range(gw):
            if not mask[gy][gx] or seen[gy][gx]:
                continue
            q = deque([(gy, gx)])
            seen[gy][gx] = True
            minx = maxx = gx
            miny = maxy = gy
            cnt = 0
            while q:
                cy, cx = q.popleft()
                cnt += 1
                if cx < minx: minx = cx
                if cx > maxx: maxx = cx
                if cy < miny: miny = cy
                if cy > maxy: maxy = cy
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < gh and 0 <= nx < gw and mask[ny][nx] and not seen[ny][nx]:
                        seen[ny][nx] = True
                        q.append((ny, nx))
            if cnt < min_count:
                continue
            x1 = x0 + minx * step
            y1 = y0 + miny * step
            x2 = x0 + (maxx + 1) * step
            y2 = y0 + (maxy + 1) * step
            out.append((cnt, (x1, y1, x2, y2)))
    out.sort(reverse=True, key=lambda t: t[0])
    return [b for _, b in out]

def _detect_white_box(base_image, roi, step=4):
    w, h = base_image.size
    x0, y0, rw, rh = roi
    x0 = max(0, x0)
    y0 = max(0, y0)
    x1 = min(w, x0 + rw)
    y1 = min(h, y0 + rh)
    gw = (x1 - x0 + step - 1) // step
    gh = (y1 - y0 + step - 1) // step
    mask = [[False] * gw for _ in range(gh)]
    for gy in range(gh):
        yy = y0 + gy * step
        for gx in range(gw):
            xx = x0 + gx * step
            px = base_image.getpixel((xx, yy))
            rr, gg, bb = px[0], px[1], px[2]
            if rr > 245 and gg > 245 and bb > 245:
                mask[gy][gx] = True
    boxes = _connected_components_bbox(mask, step, x0, y0, min_count=50)
    return boxes

def _detect_orange_dots(base_image, roi, target=(252, 159, 81), tol=25, step=2):
    w, h = base_image.size
    x0, y0, rw, rh = roi
    x0 = max(0, x0)
    y0 = max(0, y0)
    x1 = min(w, x0 + rw)
    y1 = min(h, y0 + rh)
    gw = (x1 - x0 + step - 1) // step
    gh = (y1 - y0 + step - 1) // step
    mask = [[False] * gw for _ in range(gh)]
    for gy in range(gh):
        yy = y0 + gy * step
        for gx in range(gw):
            xx = x0 + gx * step
            px = base_image.getpixel((xx, yy))
            rr, gg, bb = px[0], px[1], px[2]
            if abs(rr - target[0]) <= tol and abs(gg - target[1]) <= tol and abs(bb - target[2]) <= tol:
                mask[gy][gx] = True
    boxes = _connected_components_bbox(mask, step, x0, y0, min_count=10)
    dots = []
    for (x1b, y1b, x2b, y2b) in boxes:
        bw = x2b - x1b
        bh = y2b - y1b
        if 12 <= bw <= 90 and 12 <= bh <= 90 and 0.6 <= (bw / bh) <= 1.4:
            cx = (x1b + x2b) / 2
            cy = (y1b + y2b) / 2
            r = min(bw, bh) / 2
            dots.append((cx, cy, r))
    dots.sort(key=lambda t: t[1])
    return dots

def _auto_layout_template_final(base_image):
    w, h = base_image.size
    time_boxes = _detect_white_box(base_image, (500, 2900, 1900, 500))
    time_box = None
    for (x1, y1, x2, y2) in time_boxes[:10]:
        bw = x2 - x1
        bh = y2 - y1
        if bw >= 900 and 140 <= bh <= 320 and (bw / max(1, bh)) >= 3.0:
            time_box = (x1, y1, bw, bh)
            break

    qr_boxes = _detect_white_box(base_image, (600, 3300, 1400, 900))
    qr_box = None
    for (x1, y1, x2, y2) in qr_boxes[:20]:
        bw = x2 - x1
        bh = y2 - y1
        if 380 <= bw <= 800 and 380 <= bh <= 800 and 0.8 <= (bw / max(1, bh)) <= 1.25:
            qr_box = (x1, y1, bw, bh)
            break

    dots = _detect_orange_dots(base_image, (150, 2400, 400, 900))
    bullet = None
    if dots:
        xs = [d[0] for d in dots]
        ys = [d[1] for d in dots]
        rs = [d[2] for d in dots]
        xs.sort()
        rs.sort()
        ys_sorted = sorted(ys)
        x_med = xs[len(xs) // 2]
        r_med = rs[len(rs) // 2]
        spacings = [ys_sorted[i + 1] - ys_sorted[i] for i in range(len(ys_sorted) - 1)]
        sp = int(round(sorted(spacings)[len(spacings) // 2])) if spacings else 144
        bullet = {
            "dot_x": int(round(x_med)),
            "dot_r": int(round(r_med)),
            "start_y": int(round(ys_sorted[0])),
            "spacing": sp,
        }

    return {"qr_box": qr_box, "time_box": time_box, "bullet": bullet}

def fetch_url_content(url):
    """
    尝试从 URL 获取文本内容。
    """
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            content = response.read().decode('utf-8')
            # 如果包含飞书/Lark 的关键词且很短，通常是登录页
            if "feishu.cn" in url or "larksuite.com" in url:
                if "登录" in content or "Login" in content:
                    print("警告：飞书文档需要登录权限，无法直接抓取内容。")
                    return None
            return content
    except Exception as e:
        print(f"URL 抓取失败: {e}")
        return None

def generate_qr(link, output_path, size=532):
    """
    根据链接生成二维码并保存。
    优先用本地纯 Python 实现，兜底用 qrcode 库。
    """
    try:
        img = _gen_qr_image(link, target_size=size)
        img.save(output_path)
        return output_path
    except Exception as e:
        print(f"本地 QR 生成失败: {e}")
    # 兜底
    if qrcode:
        qr = qrcode.QRCode(version=1,
                           error_correction=qrcode.constants.ERROR_CORRECT_L,
                           box_size=10, border=2)
        qr.add_data(link); qr.make(fit=True)
        img = qr.make_image(fill_color='black', back_color='white')
        img = img.resize((size, size), Image.NEAREST)
        img.save(output_path)
        return output_path
    raise RuntimeError("无法生成二维码，请安装 qrcode 库")

def wrap_text(text, font, max_width):
    """
    根据最大宽度对文本进行自动换行，并包含避头尾（Kinsoku Shori）逻辑。
    """
    NOT_AT_START = "，。！？；：”）》】」』"
    lines = []

    if "\n" in text:
        for section in text.split("\n"):
            lines.extend(wrap_text(section, font, max_width))
        return lines

    current_line = ""
    for char in text:
        if font.getlength(current_line + char) > max_width:
            # 检查导致换行的字符是否是行首禁则字符
            if char in NOT_AT_START:
                # 如果是，则将该字符强制追加到当前行，然后换行
                lines.append(current_line + char)
                current_line = ""
            else:
                # 否则，正常换行
                lines.append(current_line)
                current_line = char
        else:
            current_line += char
    
    if current_line:
        lines.append(current_line)

    return lines

def get_best_font_and_lines(text, initial_size, max_width, max_lines, font_path):
    """
    动态计算最合适的字号，确保文本在限定行数内显示。
    """
    current_size = initial_size
    while current_size >= 60: # 设置最小字号兜底
        try:
            font = _load_font(font_path, current_size)
        except:
            font = ImageFont.load_default()
            return font, [text]
            
        lines = wrap_text(text, font, max_width)
        if len(lines) <= max_lines:
            return font, lines
        current_size -= 4 # 步进减小字号
    
    # 最终兜底
    font = _load_font(font_path, current_size)
    return font, wrap_text(text, font, max_width)

def create_poster(template_path, output_path, qr_image_path, title, caption_list, live_time, template_id="template_final", date_code="", live_link=None, feishu_qr_images=None, title_max_lines=2):
    """
    根据内容生成海报图片。
    """
    # 清洗标题中的重复字符（如"该该"->"该"）
    if title:
        import re
        title = re.sub(r'(.)\1+', r'\1', title)  # 连续重复字符去重
    
    # ── QR 图片选择规则 ──
    # template_final（模板1/学院）: 用 live_link 自动生成真实二维码
    # template_2/3/5: 用 feishu_qr_images[0]（群里第一个二维码）
    # template_4: 用 feishu_qr_images[1]（群里第二个二维码）
    # 以上均优先于传入的 qr_image_path
    _qr_path = qr_image_path
    if template_id == "template_final" and live_link:
        _auto_qr = output_path + "_auto_qr.png"
        try:
            generate_qr(live_link, _auto_qr, size=532)
            _qr_path = _auto_qr
        except Exception as e:
            print(f"自动生成二维码失败: {e}")
    elif template_id in ("template_2", "template_3", "template_5") and feishu_qr_images and len(feishu_qr_images) >= 1:
        _qr_path = feishu_qr_images[0]
    elif template_id == "template_4" and feishu_qr_images and len(feishu_qr_images) >= 2:
        _qr_path = feishu_qr_images[1]
    elif template_id == "template_4" and feishu_qr_images and len(feishu_qr_images) >= 1:
        _qr_path = feishu_qr_images[0]  # 如果只有1个，退回第一个
    qr_image_path = _qr_path  # 覆盖原参数

    # 自动从 live_time 推导 date_code（YYMMDD格式，如2026"7月9日" → "260709"；年份用当前年后两位）
    if not date_code and live_time:
        import re as _re, datetime as _dt
        m = _re.search(r'(\d{1,2})[月](\d{1,2})', live_time)
        if m:
            _yy = _dt.datetime.now().strftime('%y')
            date_code = f"{_yy}{int(m.group(1)):02d}{int(m.group(2)):02d}"

    # --- 1. 加载模板 ---
    try:
        # 优先使用 template_id 获取配置
        config = get_template_config(template_id)
        date_code_box = None
        time_box = None
        bullet_dot_x_cfg = None
        bullet_dot_r_cfg = None
        bullet_start_y_cfg = None
        bullet_spacing_cfg = None
        use_template_bullets = False
        content_y_offset = 0
        auto_layout = False
        if config:
            template_path = config['path']
            qr_box_x, qr_box_y, qr_box_w, qr_box_h = config['qr_box']
            date_code_box = config.get('date_code_box')
            time_box = config.get('time_box')
            bullet_dot_x_cfg = config.get('bullet_dot_x')
            bullet_dot_r_cfg = config.get('bullet_dot_r')
            bullet_start_y_cfg = config.get('bullet_start_y')
            bullet_spacing_cfg = config.get('bullet_spacing')
            use_template_bullets = bool(config.get('use_template_bullets', False))
            content_y_offset = int(config.get('content_y_offset', 0) or 0)
            auto_layout = bool(config.get('auto_layout', False))
        else:
            # 兼容旧逻辑
            qr_box_x, qr_box_y, qr_box_w, qr_box_h = 948, 3380, 520, 560
            
        base_image = Image.open(template_path).convert("RGBA")
        template_img = base_image.copy().convert("RGB")  # 保留模板原像素用于还原

        if template_id == "template_final" and auto_layout:
            layout = _auto_layout_template_final(base_image)
            if layout.get("qr_box"):
                qx, qy, qw, qh = layout["qr_box"]
                qr_box_x, qr_box_y, qr_box_w, qr_box_h = qx, qy, qw, qh
            if layout.get("time_box"):
                time_box = list(layout["time_box"])
            if layout.get("bullet"):
                bullet = layout["bullet"]
                bullet_dot_x_cfg = bullet.get("dot_x", bullet_dot_x_cfg)
                bullet_dot_r_cfg = bullet.get("dot_r", bullet_dot_r_cfg)
                bullet_start_y_cfg = bullet.get("start_y", bullet_start_y_cfg)
                bullet_spacing_cfg = bullet.get("spacing", bullet_spacing_cfg)
                use_template_bullets = True
        txt_layer = Image.new("RGBA", base_image.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(txt_layer)

    except FileNotFoundError:
        print(f"错误：找不到模板文件 '{template_path}'。")
        return

    # --- 2. 设置字体 ---
    bold_font_path = None
    regular_font_path = None
    
    # 字体查找：优先用项目目录内字体，再找系统字体
    # 如需换字体，把 .ttc/.ttf 文件放到代码同目录，加在列表最前面
    _base = os.path.dirname(os.path.abspath(__file__))
    bold_paths = [
        # 项目目录内（优先，放这里可确保各环境一致）
        os.path.join(_base, "NotoSansCJK-Bold.ttc"),
        os.path.join(_base, "fonts", "NotoSansCJK-Bold.ttc"),
        # 飞书小龙虾 Linux 环境
        "/home/gem/workspace/agent/media/inbound/NotoSansCJK-Bold.ttc",
        "/home/gem/workspace/agent/media/inbound/fonts/NotoSansCJK-Bold.ttc",
        # 标准 Linux
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/noto-cjk/NotoSansCJK-Bold.ttc",
        # macOS
        "/System/Library/Fonts/STHeiti Medium.ttc",
        "/System/Library/Fonts/PingFang.ttc",
    ]
    regular_paths = [
        os.path.join(_base, "NotoSansCJK-Regular.ttc"),
        os.path.join(_base, "fonts", "NotoSansCJK-Regular.ttc"),
        "/home/gem/workspace/agent/media/inbound/NotoSansCJK-Regular.ttc",
        "/home/gem/workspace/agent/media/inbound/fonts/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
        "/System/Library/Fonts/PingFang.ttc",
    ]

    for p in bold_paths:
        try:
            ImageFont.truetype(p, 10)
            bold_font_path = p
            break
        except: continue
    for p in regular_paths:
        try:
            ImageFont.truetype(p, 10)
            regular_font_path = p
            break
        except: continue

    # 找不到任何字体时报错（不要用空字体，会导致文字乱）
    if not bold_font_path or not regular_font_path:
        raise RuntimeError(
            "找不到中文字体！请把 NotoSansCJK-Bold.ttc 和 "
            "NotoSansCJK-Regular.ttc 放到代码同目录下。\n"
            f"已搜索路径: {bold_paths[:4]}"
        )
    print(f"[字体] 粗体: {bold_font_path}")
    print(f"[字体] 常规: {regular_font_path}")

    # --- 3. 颜色与坐标 ---
    TITLE_COLOR     = (26, 59, 142, 255)
    TEXT_COLOR      = (26, 59, 142, 255)
    TIME_COLOR      = (26, 59, 142, 255)
    BULLET_COLOR    = (252, 159, 81, 255)   # 橙色
    DATE_CODE_COLOR = (252, 159, 81, 255)   # 橙色

    title_vis_bot = None   # 标题视觉底部y，4.1绘制后赋值，用于4.2计算文案起点
    # 从 config 读取坐标（全部基于成品海报像素级测量）
    title_pos_x         = (config.get("title_x")        if config else None) or 226
    title_pos_y         = (config.get("title_y")        if config else None) or 2222
    title_max_width     = (config.get("title_max_width") if config else None) or 2050
    # caption_max_width：独立控制文案换行宽度（默认等于 title_max_width）
    # 横版模板等宽内容区更大，可单独设更大宽度，避免与标题换行互相制约
    caption_max_width   = (config.get("caption_max_width") if config else None) or title_max_width
    # title_font_size：标题最大字号（自动缩小保证≤max_lines行），默认148
    title_font_size_cfg = (config.get("title_font_size") if config else None) or 148
    bullet_text_start_x = (config.get("content_x")      if config else None) or 346
    bullet_dot_x        = bullet_dot_x_cfg if bullet_dot_x_cfg is not None else 275
    # 优先使用 config 的 bullet_spacing 作为初始间距，否则默认 144
    default_spacing     = bullet_spacing_cfg if bullet_spacing_cfg is not None else 144

    if time_box:
        time_box_coords = [time_box[0], time_box[1], time_box[0] + time_box[2], time_box[1] + time_box[3]]
    else:
        time_box_coords = [448, 3081, 448 + 1751, 3081 + 198]

    # content_bot：内容区下边界（bullet points 不超过此 y 值）
    # 若 config 有 content_bot 则用它（与 time_box 的 y1 解耦），否则回退到 time_box 顶部
    _content_bot = (config.get("content_bot") if config else None) or time_box_coords[1]

    # --- 4. 绘制 ---
    # 4.0 绘制日期代码（关键词）——精确填入两个括号之间
    if date_code and date_code_box:
        bx, by, bw, bh = date_code_box
        # bx = 左括号右边界+1，bw = 到右括号左边界-1，精确不碰括号

        # ① 逐行从右括号右侧50px采样纯背景色，填满填写区
        sample_x = bx + bw + 50
        for ey in range(by, by + bh):
            try:
                bg_px = base_image.getpixel((sample_x, ey))
                bg_color = bg_px[:3] + (255,) if len(bg_px) == 4 else bg_px + (255,)
            except Exception:
                bg_color = (22, 58, 154, 255)
            draw.rectangle([bx, ey, bx + bw, ey], fill=bg_color)

        # ② 字号：默认116（与周围文字高度匹配），可由 config 覆盖。
        #    整串一次性绘制（与时间数字"19:00"完全同方式），不逐字、不压缩。
        #    新模板括号空隙够宽（469px），6位116号(408px)放得下，正常满格。
        #    仅当超宽时才自动缩小字号兜底（防溢出）。
        target_size = (config.get("date_code_font_size") if config else None) or 116
        date_font = _load_font(bold_font_path, target_size)
        tb = draw.textbbox((0, 0), date_code, font=date_font)
        tw = tb[2] - tb[0]; th = tb[3] - tb[1]
        while tw > bw - 4 and target_size > 80:
            target_size -= 2
            date_font = _load_font(bold_font_path, target_size)
            tb = draw.textbbox((0, 0), date_code, font=date_font)
            tw = tb[2] - tb[0]; th = tb[3] - tb[1]

        # ③ 水平居中、垂直居中
        tx = bx + (bw - tw) // 2 - tb[0]
        ty = by + (bh - th) // 2 - tb[1]
        draw.text((tx, ty), date_code, font=date_font, fill=DATE_CODE_COLOR)

    title_vis_bot = None   # 标题视觉底部y，绘制后赋值

    # 4.1 绘制标题（自适应字号与换行）
    # template_5 使用专用函数 _draw_template5_content，此处跳过
    if template_id != "template_5":
        title_font, title_lines = get_best_font_and_lines(title, title_font_size_cfg, title_max_width, title_max_lines, bold_font_path)

        # 测量标题视觉高度
        _title_vis_h = 0
        for _ln in title_lines:
            _tb = draw.textbbox((0, 0), _ln, font=title_font)
            _title_vis_h += (_tb[3] - _tb[1]) + 20
        _title_vis_h = max(0, _title_vis_h - 20)

        # ── 动态间距（所有模板长期规则）──
        # 公式：gap = (可用区 - 标题高 - 文案高) / 2，上下对称
        # 文案越多越长 → gap 自动缩小；文案越少越短 → gap 自动增大
        # 最小 60px 保底，确保三者之间肉眼可见留白
        _n_caps = len(caption_list) if caption_list else 0
        _captions_h = default_spacing * _n_caps
        _time_top = _content_bot
        _avail = _time_top - title_pos_y
        _CAP_OFFSET = 74   # 圆点中心到文字顶部的偏移（lh//2+top_offset）
        _gap = (_avail - _title_vis_h - _captions_h - _CAP_OFFSET) // 2

        # 若 gap < 60，缩小文案行间距直到 gap≥60
        # 缩小后的间距写回 default_spacing，后续绘制循环中 spacing 变量会读取
        # 动态压缩 spacing，确保所有文案都能放进内容区
        # 目标：gap >= 40px（标题→文案和文案→时间条都留40px）
        # 压缩下限：spacing >= 80px（换行文案也能显示）
        _sp = default_spacing
        while _gap < 40 and _sp > 80:
            _sp -= 2
            _captions_h = _sp * _n_caps
            _gap = (_avail - _title_vis_h - _captions_h - 74) // 2
        default_spacing = _sp
        # 标题到介绍文案的外部间隙需要明显大于文案内部间距，并与模板5保持一致。
        _title_caption_gap_min = (config.get("title_caption_gap_min") if config else None) or 90
        if len(title_lines) >= 2:
            _title_caption_gap_min = max(
                _title_caption_gap_min,
                (config.get("title_caption_gap_min_two_lines") if config else None) or 120
            )
        _gap = max(_gap, _title_caption_gap_min)

        # 绘制标题
        current_y = title_pos_y
        for line in title_lines:
            tb = draw.textbbox((0, 0), line, font=title_font)
            draw.text((title_pos_x, current_y - tb[1]), line, font=title_font, fill=TITLE_COLOR)
            current_y += (tb[3] - tb[1]) + 20
        title_vis_bot = current_y - 20

    # 文案起点计算：
    # _gap = 标题视觉底 → 文案第一行文字顶部 的距离
    # bullet_area_start_y（圆点中心）= 文案文字顶 + lh//2 + top_offset ≈ 文字顶 + 74px
    # 所以: bullet_area_start_y = title_vis_bot + _gap + 74
    _cap_text_offset = 74   # 圆点中心距文字顶部的固定偏移（lh//2≈48 + top_offset≈26）
    if title_vis_bot is not None:
        bullet_area_start_y = title_vis_bot + _gap + _cap_text_offset + content_y_offset
    else:
        bullet_area_start_y = (bullet_start_y_cfg if bullet_start_y_cfg is not None else 2583) + content_y_offset

    # 4.2 绘制文案列表 (支持 3 句或 4 句) - template_5 跳过，由专用函数处理
    if template_id == "template_5":
        num_captions = 0  # 跳过通用文案绘制
    else:
        num_captions = len(caption_list)
    
    # 间距由动态逻辑确定（default_spacing 已在 4.1 中根据内容调整）
    # bullet_spacing_cfg 是 config 的初始值，仅作参考，不覆盖动态结果
    spacing = default_spacing
    
    # 统一字号计算 (针对所有文案)
    line_gap = 10
    min_caption_size = (config.get("caption_min_font_size") if config else None) or 96
    best_size = (config.get("caption_font_size") if config else None) or min_caption_size

    # 先检测是否有文案需要换2行，若有则扩大 spacing 让2行放得下
    _detect_font = _load_font(regular_font_path, best_size)
    _has_2lines = any(
        len(wrap_text(item, _detect_font, caption_max_width - 80)) > 1
        for item in caption_list
    )
    if _has_2lines:
        _tb_tmp = draw.textbbox((0, 0), '中', font=_detect_font)
        _lh_tmp = _tb_tmp[3] - _tb_tmp[1]
        _spacing_2line = _lh_tmp * 2 + line_gap + 30   # 2行 + 上下各15px
        if spacing < _spacing_2line:
            spacing = _spacing_2line
            # 重新用扩大后的 spacing 计算 bullet_area_start_y（保持 gap 对称）
            if title_vis_bot is not None:
                _tt = _content_bot
                _av = _tt - title_pos_y
                _th = sum(
                    (draw.textbbox((0,0), ln, font=title_font)[3]
                     - draw.textbbox((0,0), ln, font=title_font)[1]) + 20
                    for ln in (title_lines or [])
                ) - 20 if title_lines else 0
                _nc = len(caption_list) if caption_list else 0
                _gap_new = max((_av - _th - spacing * _nc - 74) // 2, 60)
                bullet_area_start_y = title_vis_bot + _gap_new + 74 + content_y_offset

    # 字号自适应：确保所有文案块加上句间留白能放进内容区
    # 可用高度 = 时间框顶 - bullet_area_start_y - 首行高/2 - 20px边距
    _time_top_for_cap = _content_bot
    _cap_avail = _time_top_for_cap - bullet_area_start_y - 20

    while best_size >= min_caption_size:
        try:
            candidate_font = _load_font(regular_font_path, best_size)
        except Exception:
            candidate_font = ImageFont.load_default()
            break
        ok = True
        _blocks_test = []
        for item in caption_list:
            lines = wrap_text(item, candidate_font, caption_max_width - 80)
            if len(lines) > 2:
                ok = False; break
            _tb0 = draw.textbbox((0, 0), lines[0], font=candidate_font)
            _lh0 = _tb0[3] - _tb0[1]
            _bh = len(lines) * _lh0 + max(0, len(lines) - 1) * line_gap
            _blocks_test.append((_bh, _lh0, _tb0[1]))
        if not ok:
            best_size -= 2; continue

        # 预算总高度：所有文案块 + 句间留白(最小20px×(n-1))
        _total_test = sum(b[0] for b in _blocks_test)
        _n_test = len(_blocks_test)
        _first_lh_test = _blocks_test[0][1] if _blocks_test else 0
        _min_total = _total_test + max(0, _n_test - 1) * 20 + _first_lh_test // 2
        if _min_total <= _cap_avail:
            break  # 放得下
        best_size -= 2
    if best_size < min_caption_size:
        best_size = min_caption_size

    final_item_font = _load_font(regular_font_path, best_size)
    
    # 增加标题和上方人像的间隔
    title_bottom_margin = 80  # 标题下方增加间隔

    # template_5 由 _draw_template5_content 专用函数处理，跳过通用循环
    _caption_list_to_draw = [] if template_id == "template_5" else caption_list

    # ── 预计算各条文案的块高，确定句间留白 ──
    _cap_blocks = []
    for item in _caption_list_to_draw:
        lines = wrap_text(item, final_item_font, caption_max_width - 80)
        tb0 = draw.textbbox((0, 0), lines[0], font=final_item_font)
        _lh = tb0[3] - tb0[1]
        _to = tb0[1]
        _block_h = len(lines) * _lh + max(0, len(lines)-1) * line_gap
        _cap_blocks.append((lines, _block_h, _lh, _to))

    # 计算句间留白：均匀分配可用空间
    _total_cap_h = sum(b[1] for b in _cap_blocks)
    _n_draw = len(_cap_blocks)
    _time_top_draw = _content_bot

    # 可用区 = 时间框顶部 - 文案起点 - 首行偏移
    _first_lh = _cap_blocks[0][2] if _cap_blocks else 0
    _avail_draw = _time_top_draw - 20 - bullet_area_start_y - _first_lh // 2

    if _n_draw > 1:
        # 介绍文案内部行间距必须小于标题→文案、文案→时间的外部间隙。
        # 图1-4与图5统一：文案之间最多40px，不再按剩余空间拉大。
        _caption_gap_max = (config.get("caption_item_gap_max") if config else None) or 40
        _gap_between = max((_avail_draw - _total_cap_h) // (_n_draw - 1), 20)
        _gap_between = min(_gap_between, _caption_gap_max)
    else:
        _gap_between = 0

    # ── 逐条绘制 ──
    _cur_y = bullet_area_start_y   # 第一条圆点中心y

    # 时间框顶部（文案不能超过这里，留20px安全边距）
    _time_top_limit = _content_bot - 20

    for i, (item_lines, block_h, first_lh, top_off) in enumerate(_cap_blocks):
        dot_y = _cur_y
        # 如果本条文案超出时间框才跳过（用时间框顶部作为硬边界）
        _vis_top = dot_y - top_off - first_lh // 2
        _vis_bot = _vis_top + top_off + block_h
        if _vis_bot > _time_top_limit:
            # 文案超出，不绘制这一条及后续
            break

        # 正确公式：
        # 视觉中心 = draw_y + top_off + first_lh//2 = dot_y
        # → draw_y = dot_y - top_off - first_lh//2
        draw_y = dot_y - top_off - first_lh // 2

        # 画圆点
        r = bullet_dot_r_cfg if bullet_dot_r_cfg is not None else 12
        draw.ellipse([bullet_dot_x - r, dot_y - r, bullet_dot_x + r, dot_y + r],
                     fill=BULLET_COLOR)

        # 画文字
        temp_y = draw_y
        for line in item_lines:
            tb = draw.textbbox((0, 0), line, font=final_item_font)
            draw.text((bullet_text_start_x, temp_y), line, font=final_item_font, fill=TEXT_COLOR)
            temp_y += (tb[3] - tb[1]) + line_gap

        # 下一条圆点起点：本条视觉底部 + 句间留白 + 下条第一行视觉高度的一半
        if i < len(_cap_blocks) - 1:
            _next_lh, _next_off = _cap_blocks[i+1][2], _cap_blocks[i+1][3]
            # 本条视觉底部 = draw_y + top_off + block_h（block_h已是视觉高）
            _vis_bot = draw_y + top_off + block_h
            # 下条圆点 = 下条第一行视觉中心 = 视觉底 + gap + next_lh//2
            _cur_y = _vis_bot + _gap_between + _next_lh // 2
        
    # 4.3 时间框：①先白色精确覆盖占位文字 ②再写真实时间
    box_x1, box_y1, box_x2, box_y2 = time_box_coords
    box_w = box_x2 - box_x1
    box_h = box_y2 - box_y1

    # ① 用白色精确覆盖胶囊内的占位文字
    # 对模板1-4: 占位文字实测 x=1030~2150，左边留130px不碰圆弧
    # 对模板5:  time_box已精确到文字区，直接用 box_x1
    if template_id in ("template_5", "template_6"):
        # template_5/6: time_box 已精确到文字区，直接用 box 边界
        cover_x1 = box_x1
        cover_x2 = box_x2
    else:
        cover_x1 = 1030
        cover_x2 = 2150
    cover_y1 = box_y1 + 4
    cover_y2 = box_y2 - 4
    draw.rectangle([cover_x1, cover_y1, cover_x2, cover_y2],
                   fill=(255, 255, 255, 255))

    # ② 字号自适应，确保不超胶囊宽度
    max_text_w = cover_x2 - cover_x1 - 20
    time_font_size = max(60, min(110, int(box_h * 0.70)))
    time_font = _load_font(bold_font_path, time_font_size)
    text_bbox_t = draw.textbbox((0, 0), live_time, font=time_font)
    text_w = text_bbox_t[2] - text_bbox_t[0]
    text_h = text_bbox_t[3] - text_bbox_t[1]
    while text_w > max_text_w and time_font_size > 60:
        time_font_size -= 4
        time_font = _load_font(bold_font_path, time_font_size)
        text_bbox_t = draw.textbbox((0, 0), live_time, font=time_font)
        text_w = text_bbox_t[2] - text_bbox_t[0]
        text_h = text_bbox_t[3] - text_bbox_t[1]

    # ③ 在胶囊内水平居中（相对 cover 区）、垂直居中
    # time_text_x_offset: 正数=向右偏移，负数=向左偏移，默认-50（垂直模板右偏补偿）
    _tx_off = (config.get("time_text_x_offset") if config else None)
    if _tx_off is None:
        _tx_off = -50
    text_x = cover_x1 + ((cover_x2 - cover_x1) - text_w) // 2 + _tx_off
    text_y = box_y1 + (box_h - text_h) // 2 - text_bbox_t[1]
    draw.text((text_x, text_y), live_time, font=time_font, fill=TIME_COLOR)
    
    # 4.4 绘制二维码
    if qr_image_path and template_id in ("template_final", "template_2", "template_3", "template_4", "template_5", "template_6"):
        try:
            qr_img = Image.open(qr_image_path).convert("RGBA")
            # 保持正方形：取短边，居中裁剪后填满 qr_box
            src_w, src_h = qr_img.size
            side = min(src_w, src_h)
            if src_w != src_h:
                # 居中裁剪成正方形
                left = (src_w - side) // 2
                top  = (src_h - side) // 2
                qr_img = qr_img.crop((left, top, left+side, top+side))
            # resize 到 qr_box 的短边（填满白色框）
            target = min(qr_box_w, qr_box_h)
            qr_img = qr_img.resize((target, target), Image.Resampling.LANCZOS)
            # 粘贴时居中对齐到 qr_box
            paste_x = qr_box_x + (qr_box_w - target) // 2
            paste_y = qr_box_y + (qr_box_h - target) // 2
            mask = Image.new("L", (target, target), 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.rounded_rectangle((0, 0, target, target), radius=10, fill=255)
            base_image.paste(qr_img, (paste_x, paste_y), mask)
        except Exception as e:
            print(f"二维码绘制失败: {e}")

    # 4.5 模板五专用内容绘制（独立布局，覆盖前面通用逻辑的空白区域）
    if template_id == "template_5":
        _draw_template5_content(
            base_image, txt_layer, draw,
            title, caption_list, date_code,
            bold_font_path, regular_font_path, config,
            title_max_lines
        )

    # 保存
    out = Image.alpha_composite(base_image, txt_layer)
    out.convert("RGB").save(output_path)
    print(f"成功生成海报: {output_path}")

def _draw_template5_content(base_image, txt_layer, draw,
                             title, caption_list, date_code,
                             bold_font_path, regular_font_path, config,
                             title_max_lines=2):
    """
    模板五自动布局（长期规则，所有情况通用）：

    可用区：y=1154~2350（白色空白区 ~ 时间胶囊顶部）
    布局原则（与模板1-4完全一致）：
      - 可用区 = 时间框顶部 - 标题起始y
      - 总内容高 = 标题高 + 文案高（144px × 条数）
      - gap = (可用区 - 总内容高) / 2，上下对称
      - 文案越多/越长 → gap 自动缩小；文案越少/越短 → gap 自动增大
      - 最小 gap = 60px（绝不挤在一起）
    """
    TITLE_COLOR  = (26, 59, 142, 255)
    TEXT_COLOR   = (26, 59, 142, 255)
    BULLET_COLOR = (252, 159, 81, 255)

    title_x     = config.get("title_x",        150)
    title_max_w = config.get("title_max_width", 2116)
    caption_max_w = config.get("caption_max_width", title_max_w)  # 文案框宽度，可独立于标题
    content_shift = config.get("t5_content_shift", 0)             # 标题+文案整体垂直偏移
    content_x   = config.get("content_x",       280)
    dot_x       = config.get("bullet_dot_x",    195)
    dot_r       = config.get("bullet_dot_r",    14)

    AREA_TOP = 1220   # 白色内容区顶部（下移让标题不太靠上）
    TIME_TOP = 2350   # 时间胶囊顶部
    SPACING  = 144    # 文案行间距（与图1~4一致）
    MIN_GAP  = 60     # 最小间距保底

    # ── Step1：标题字号和视觉高度 ──
    title_font = None
    title_lines = []
    title_vis_h = 0
    if title:
        title_font, title_lines = get_best_font_and_lines(
            title, 148, title_max_w, title_max_lines, bold_font_path)
        for line in title_lines:
            tb = draw.textbbox((0, 0), line, font=title_font)
            title_vis_h += (tb[3] - tb[1]) + 20
        title_vis_h = max(0, title_vis_h - 20)

    # ── Step2：文案字号（单条≤2行）──
    # 若有2行文案，SPACING 自动扩大为能容纳2行的最小值
    n = len(caption_list) if caption_list else 0
    item_font = None
    lh = top_offset = 0
    line_gap_t5 = 10
    if n > 0:
        min_caption_size = (config.get("caption_min_font_size") if config else None) or 96
        best_size = (config.get("caption_font_size") if config else None) or min_caption_size
        _df = _load_font(regular_font_path, best_size)
        _has2 = any(len(wrap_text(it, _df, caption_max_w - 60)) > 1 for it in caption_list)
        if _has2:
            _tb_tmp = draw.textbbox((0, 0), '中', font=_df)
            _lh_tmp = _tb_tmp[3] - _tb_tmp[1]
            _sp2 = _lh_tmp * 2 + line_gap_t5 + 30
            if SPACING < _sp2:
                SPACING = _sp2

        while best_size >= min_caption_size:
            try:
                f = _load_font(regular_font_path, best_size)
            except Exception:
                f = ImageFont.load_default(); break
            fits = True
            for item in caption_list:
                lines = wrap_text(item, f, caption_max_w - 60)
                tb0 = draw.textbbox((0, 0), lines[0], font=f)
                lh_c = tb0[3] - tb0[1]
                block_h = len(lines)*lh_c + max(0,len(lines)-1)*line_gap_t5
                if len(lines) > 2 or block_h > SPACING - 20:
                    fits = False; break
            if fits:
                item_font = f; break
            best_size -= 2
        if item_font is None:
            item_font = _load_font(regular_font_path, min_caption_size)
        tb0 = draw.textbbox((0, 0), caption_list[0], font=item_font)
        lh = tb0[3] - tb0[1]
        top_offset = tb0[1]

    # ── Step3：动态 gap（与模板1-4完全一致的公式）──
    captions_h = SPACING * n
    avail = TIME_TOP - AREA_TOP
    total_content = title_vis_h + captions_h
    gap = min(max((avail - total_content) // 2, MIN_GAP), 200)

    # 标题起始y：AREA_TOP + gap（上方留 gap）；content_shift 让标题+文案整体下移
    title_start = AREA_TOP + gap + content_shift

    # ── Step4：绘制标题 ──
    cur_y = title_start
    title_vis_bot = title_start
    if title and title_font:
        for line in title_lines:
            tb = draw.textbbox((0, 0), line, font=title_font)
            draw.text((title_x, cur_y - tb[1]), line, font=title_font, fill=TITLE_COLOR)
            cur_y += (tb[3] - tb[1]) + 20
        title_vis_bot = cur_y - 20

    # ── Step5：绘制文案，起点 = 标题底 + gap（最少120px留白）──
    if n > 0 and item_font:
        line_gap = 10
        first_dot_y = title_vis_bot + max(gap, 120)

        # 预计算各条文案块高
        _t5_blocks = []
        for item in caption_list:
            lines = wrap_text(item, item_font, caption_max_w - 60)
            tb0 = draw.textbbox((0, 0), lines[0], font=item_font)
            _lh5 = tb0[3] - tb0[1]
            _to5 = tb0[1]
            _bh5 = len(lines) * _lh5 + max(0, len(lines)-1) * line_gap
            _t5_blocks.append((lines, _bh5, _lh5, _to5))

        # 计算句间留白（均匀分配剩余空间）
        _total_h5 = sum(b[1] for b in _t5_blocks)
        _n5 = len(_t5_blocks)
        if _n5 > 1:
            _avail5 = TIME_TOP - first_dot_y - _t5_blocks[0][2] // 2
            _gap5 = max((_avail5 - _total_h5) // (_n5 - 1), 40)
            _gap5 = min(_gap5, 40)
        else:
            _gap5 = 0

        _cur5 = first_dot_y
        for i, (lines, bh, first_lh, top_off) in enumerate(_t5_blocks):
            dot_cy = _cur5
            # 正确公式：draw_y = dot_cy - top_off - first_lh//2
            draw_y5 = dot_cy - top_off - first_lh // 2

            draw.ellipse([dot_x-dot_r, dot_cy-dot_r, dot_x+dot_r, dot_cy+dot_r],
                         fill=BULLET_COLOR)
            ty = draw_y5
            for line in lines:
                tb = draw.textbbox((0, 0), line, font=item_font)
                draw.text((content_x, ty), line, font=item_font, fill=TEXT_COLOR)
                ty += (tb[3] - tb[1]) + line_gap

            if i < len(_t5_blocks) - 1:
                _next_lh = _t5_blocks[i+1][2]
                _next_off = _t5_blocks[i+1][3]
                _vis_bot5 = draw_y5 + top_off + bh
                _cur5 = _vis_bot5 + _gap5 + _next_lh // 2


def run_batch_posters(data_file):
    """
    根据数据文件批量生成海报。
    """
    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            posters_data = json.load(f)
    except Exception as e:
        print(f"无法读取数据文件: {e}")
        return

    for i, data in enumerate(posters_data):
        print(f"正在处理第 {i+1} 张海报: {data.get('title', '未命名')}")
        
        # 1. 生成二维码
        qr_path = f"temp_qr_{i}.png"
        generate_qr(data['link'], qr_path)
        
        # 2. 生成海报
        output_path = data.get('output_name', f"poster_batch_{i}.png")
        create_poster(
            template_path="template_final.png",
            output_path=output_path,
            qr_image_path=qr_path,
            title=data['title'],
            caption_list=data['captions'],
            live_time=data['live_time']
        )

def generate_from_notice_file(notice_file="input_notice.txt"):
    """
    从指定文本文件读取并生成海报。
    """
    if os.path.exists(notice_file):
        with open(notice_file, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if content:
                print(f"检测到 {notice_file}，正在进行智能解析...")
                data = smart_parse_notice(content)
                if data and data.get("link"):
                    print(f"解析成功！主题：{data['title']}")
                    qr_temp_path = "temp_qr.png"
                    generate_qr(data['link'], qr_temp_path)
                    create_poster(
                        template_path="template_final.png",
                        output_path=data.get("output_name", "poster_auto_generated.png"),
                        qr_image_path=qr_temp_path,
                        title=data['title'],
                        caption_list=data['captions'],
                        live_time=data['live_time']
                    )
                    return True
    return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="自动海报生成器")
    parser.add_argument("--text", type=str, help="粘贴直播通告文本进行自动解析生成")
    parser.add_argument("--url", type=str, help="传入公开网页链接进行自动抓取解析")
    parser.add_argument("--file", type=str, help="指定 JSON 数据文件进行批量生成")
    
    args = parser.parse_args()
    
    # 自动化工作流：
    input_text = None
    
    # 方式 A: 检查是否存在 input_notice.txt (最简单的粘贴方式)
    if not args.text and not args.url and not args.file:
        if generate_from_notice_file("input_notice.txt"):
            sys.exit(0)

    # 方式 B: 命令行参数 --url 或 --text
    if args.url:
        print(f"正在尝试抓取 URL: {args.url}")
        input_text = fetch_url_content(args.url)
    elif args.text:
        input_text = args.text
    
    if input_text:
        # 解析并生成
        print("检测到原始文本，正在进行智能解析...")
        data = smart_parse_notice(input_text)
        if data and data.get("link"):
            print(f"解析成功！主题：{data['title']}")
            qr_temp_path = "temp_qr.png"
            generate_qr(data['link'], qr_temp_path)
            create_poster(
                template_path="template_final.png",
                output_path=data.get("output_name", "poster_auto_generated.png"),
                qr_image_path=qr_temp_path,
                title=data['title'],
                caption_list=data['captions'],
                live_time=data['live_time']
            )
        else:
            print("解析失败，未在文本中找到有效的直播链接。请检查文本格式。")
            
    elif args.file or os.path.exists("posters_data.json"):
        data_file = args.file if args.file else "posters_data.json"
        print(f"检测到 {data_file}，进入批量自动生成模式...")
        run_batch_posters(data_file)
        
    else:
        print("未检测到文本或数据文件，使用默认配置生成单张海报...")
        # (下方的默认单张生成代码保持不变)
        data = {
            "title": "养老金投资指南：\n如何规划你的退休生活？",
            "captions": [
                "第一步：了解个人养老金账户的政策优惠",
                "第二步：根据风险偏好选择适合的基金产品",
                "第三步：坚持长期投资，享受复利增长",
                "第四步：定期审视组合，根据年龄动态调整"
            ],
            "live_time": "3月6日 (周五) 19:00",
            "link": "https://n6o8y.xetslk.com/sl/JDfgI", 
            "output_name": "poster_default.png"
        }

        qr_temp_path = "temp_qr.png"
        generate_qr(data['link'], qr_temp_path)
        create_poster(
            template_path="template_final.png",
            output_path=data['output_name'],
            qr_image_path=qr_temp_path,
            title=data['title'],
            caption_list=data['captions'],
            live_time=data['live_time']
        )
