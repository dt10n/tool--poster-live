# -*- coding: utf-8 -*-
import json
import qrcode
import sys
import os
import urllib.request
from collections import deque
from PIL import Image, ImageDraw, ImageFont
from smart_parser import smart_parse_notice
from template_config import get_template_config

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

def generate_qr(link, output_path, size=535):
    """
    根据链接自动生成二维码。
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=1,
    )
    qr.add_data(link)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img = img.resize((size, size))
    img.save(output_path)
    return output_path

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
            font = ImageFont.truetype(font_path, current_size)
        except:
            font = ImageFont.load_default()
            return font, [text]
            
        lines = wrap_text(text, font, max_width)
        if len(lines) <= max_lines:
            return font, lines
        current_size -= 4 # 步进减小字号
    
    # 最终兜底
    font = ImageFont.truetype(font_path, current_size)
    return font, wrap_text(text, font, max_width)

def create_poster(template_path, output_path, qr_image_path, title, caption_list, live_time, template_id="template_final", date_code=""):
    """
    根据内容生成海报图片。
    """
    # 清洗标题中的重复字符（如"该该"->"该"）
    if title:
        import re
        title = re.sub(r'(.)\1+', r'\1', title)  # 连续重复字符去重
    
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
    
    bold_paths = [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc",
        "SourceHanSansCN-Bold.otf",
        "SourceHanSansCN-Bold.ttf",
        "/System/Library/Fonts/STHeiti Medium.ttc",
        "/System/Library/Fonts/PingFang.ttc"
    ]
    regular_paths = [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc",
        "SourceHanSansCN-Regular.otf",
        "SourceHanSansCN-Regular.ttf",
        "/System/Library/Fonts/STHeiti Light.ttc",
        "/System/Library/Fonts/PingFang.ttc"
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
        
    if not bold_font_path: bold_font_path = "/System/Library/Fonts/STHeiti Medium.ttc"
    if not regular_font_path: regular_font_path = "/System/Library/Fonts/STHeiti Light.ttc"

    # --- 3. 颜色与坐标 ---
    TITLE_COLOR = (26, 59, 142, 255)
    TEXT_COLOR = (26, 59, 142, 255)
    TIME_COLOR = (26, 59, 142, 255)
    BULLET_COLOR = (252, 159, 81, 255) # 橙色
    DATE_CODE_COLOR = (252, 159, 81, 255) # 橙色文字 (252, 159, 81)
    
    title_pos_x, title_pos_y = 220, 2110 + content_y_offset - 20  # 整体上移20px
    bullet_text_start_x = 340
    bullet_dot_x = bullet_dot_x_cfg if bullet_dot_x_cfg is not None else 270
    bullet_area_start_y = (bullet_start_y_cfg if bullet_start_y_cfg is not None else 2585) + content_y_offset - 20
    # 我们设定一个合理的行间距，如果文案多，则自动缩小间距
    default_spacing = 145 
    # 我们设定一个合理的行间距，如果文案多，则自动缩小间距
    default_spacing = 145 
    
    if time_box:
        time_box_coords = [time_box[0], time_box[1], time_box[0] + time_box[2], time_box[1] + time_box[3]]
    else:
        time_box_coords = [981, 3078, 981 + 1130, 3078 + 198]
    
    # --- 4. 绘制 ---
    # 4.0 绘制日期代码 (居中于 box)
    if date_code and date_code_box:
        bx, by, bw, bh = date_code_box
        try:
            bg_sample = base_image.getpixel((max(0, bx - 10), by + bh // 2))
        except Exception:
            bg_sample = (15, 45, 132, 255)

        margin = max(40, int(bw * 0.2))
        draw.rectangle([bx + margin, by, bx + bw - margin, by + bh], fill=bg_sample)
        
        # 绘制日期数字 (橙色)
        date_font_paths = [
            "/System/Library/Fonts/Supplemental/Impact.ttf",
            "/System/Library/Fonts/Supplemental/DIN Alternate Bold.ttf",
            "/System/Library/Fonts/Supplemental/Arial Black.ttf",
            bold_font_path
        ]
        
        date_font = None
        target_font_size = 115 # 饱满字号
        for fp in date_font_paths:
            try:
                date_font = ImageFont.truetype(fp, target_font_size)
                break
            except: continue
        
        if not date_font:
            date_font = ImageFont.truetype(bold_font_path, target_font_size)
        
        text_bbox = draw.textbbox((0, 0), date_code, font=date_font)
        tw = text_bbox[2] - text_bbox[0]
        th = text_bbox[3] - text_bbox[1]
        
        # 精准居中
        tx = bx + (bw - tw) // 2
        ty = by + (bh - th) // 2 - text_bbox[1]
        
        draw.text((tx, ty), date_code, font=date_font, fill=DATE_CODE_COLOR)

    # 4.1 绘制标题 (自适应字号与换行)
    title_font, title_lines = get_best_font_and_lines(title, 161, 1900, 2, bold_font_path)
    current_y = title_pos_y
    for line in title_lines:
        draw.text((title_pos_x, current_y), line, font=title_font, fill=TITLE_COLOR)
        current_y += title_font.size + 20
    
    # 4.2 绘制文案列表 (支持 3 句或 4 句)
    num_captions = len(caption_list)
    
    # 动态调整间距：如果超过 3 句，则缩小间距以防超出
    if bullet_spacing_cfg is not None:
        spacing = bullet_spacing_cfg
    else:
        spacing = default_spacing if num_captions <= 3 else 125
    
    # 统一字号计算 (针对所有文案)
    line_gap = 10
    best_size = 88
    while best_size >= 60:
        try:
            candidate_font = ImageFont.truetype(regular_font_path, best_size)
        except Exception:
            candidate_font = ImageFont.load_default()
            break
        ok = True
        for item in caption_list:
            lines = wrap_text(item, candidate_font, 1800)
            if len(lines) > 2:
                ok = False
                break
            total_h = len(lines) * candidate_font.size + max(0, len(lines) - 1) * line_gap
            if total_h > spacing:
                ok = False
                break
        if ok:
            break
        best_size -= 2
    
    final_item_font = ImageFont.truetype(regular_font_path, best_size)
    
    # 增加标题和上方人像的间隔
    title_bottom_margin = 80  # 标题下方增加间隔
    
    for i, item in enumerate(caption_list):
        # 计算当前文字的 y 坐标 - 考虑标题下方的间隔
        y_center = bullet_area_start_y + i * spacing
        
        # 绘制文字 (垂直居中和换行,最多2行)
        item_lines = wrap_text(item, final_item_font, 1800)
        total_h = len(item_lines) * final_item_font.size + max(0, len(item_lines) - 1) * line_gap
        text_y = y_center - total_h // 2
        # 点点和文案整体居中对齐，再往下挪20px
        dot_y = text_y + total_h // 2 + 20

        should_draw_dot = True
        if use_template_bullets:
            try:
                base_px = base_image.getpixel((bullet_dot_x, int(dot_y)))
                if isinstance(base_px, int):
                    base_px = (base_px, base_px, base_px, 255)
                elif len(base_px) == 3:
                    base_px = (base_px[0], base_px[1], base_px[2], 255)
            except Exception:
                base_px = (0, 0, 0, 0)
            should_draw_dot = not (
                abs(base_px[0] - BULLET_COLOR[0]) <= 20
                and abs(base_px[1] - BULLET_COLOR[1]) <= 20
                and abs(base_px[2] - BULLET_COLOR[2]) <= 20
            )

        if should_draw_dot:
            r = bullet_dot_r_cfg if bullet_dot_r_cfg is not None else 12
            draw.ellipse([bullet_dot_x - r, dot_y - r, bullet_dot_x + r, dot_y + r], fill=BULLET_COLOR)

        temp_y = text_y
        for line in item_lines:
            draw.text((bullet_text_start_x, temp_y), line, font=final_item_font, fill=TEXT_COLOR)
            temp_y += final_item_font.size + line_gap
        
    # 4.3 时间框遮挡与写入
    time_font = ImageFont.truetype(bold_font_path, 108)
    box_w = time_box_coords[2] - time_box_coords[0]
    box_h = time_box_coords[3] - time_box_coords[1]

    text_bbox = draw.textbbox((0, 0), live_time, font=time_font)
    text_w = text_bbox[2] - text_bbox[0]
    text_h = text_bbox[3] - text_bbox[1]

    text_x = time_box_coords[0] + (box_w - text_w) // 2
    text_y = time_box_coords[1] + (box_h - text_h) // 2 - text_bbox[1]

    if template_id == "template_final":
        pad_x = 10
        pad_y = 2
        l = max(time_box_coords[0], text_x - pad_x)
        t = max(time_box_coords[1], text_y + text_bbox[1] - pad_y)
        r = min(time_box_coords[2], text_x + text_w + pad_x)
        b = min(time_box_coords[3], text_y + text_bbox[1] + text_h + pad_y)
        scan_y = int(text_y + text_bbox[1] + max(0, text_h // 2))
        scan_y = max(time_box_coords[1], min(time_box_coords[3] - 1, scan_y))
        stop_x = None
        for x in range(time_box_coords[2] - 1, time_box_coords[0] - 1, -1):
            px = base_image.getpixel((x, scan_y))
            rr, gg, bb = px[0], px[1], px[2]
            if abs(rr - TIME_COLOR[0]) <= 40 and abs(gg - TIME_COLOR[1]) <= 40 and abs(bb - TIME_COLOR[2]) <= 40:
                stop_x = x
                break
            if (bb - rr) >= 60 and bb >= 120 and rr <= 120 and gg <= 140:
                stop_x = x
                break
        if stop_x is not None:
            r = min(r, stop_x - 2)
        draw.rectangle([l, t, r, b], fill=(255, 255, 255, 255))
    else:
        draw.rectangle(time_box_coords, fill=(255, 255, 255, 255))

    draw.text((text_x, text_y), live_time, font=time_font, fill=TIME_COLOR)
    
    # 4.4 绘制二维码
    if qr_image_path and template_id in ("template_final", "template_2", "template_3", "template_4"):
        try:
            qr_img = Image.open(qr_image_path).convert("RGBA")
            # 调整二维码大小以适应 qr_box
            qr_img = qr_img.resize((qr_box_w, qr_box_h), Image.Resampling.LANCZOS)
            
            # 创建圆角遮罩
            mask = Image.new("L", (qr_box_w, qr_box_h), 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.rounded_rectangle((0, 0, qr_box_w, qr_box_h), radius=20, fill=255)
            
            # 粘贴二维码
            base_image.paste(qr_img, (qr_box_x, qr_box_y), mask)
            
        except Exception as e:
            print(f"二维码绘制失败: {e}")
    # 其他模板不绘制二维码

    # 保存
    out = Image.alpha_composite(base_image, txt_layer)
    out.convert("RGB").save(output_path)
    print(f"成功生成海报: {output_path}")

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
