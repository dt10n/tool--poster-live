# ============================================================
#  模板配置 —— 坐标全部从成品海报像素级精确标定
#  成品测量日期：2026-05-07
#
#  关键坐标说明（4张大模板 2416x4398）：
#    时间胶囊白色区：整体 y=3050~3290，右侧胶囊 x=900~2335
#    时间文字实测位置：y=3131~3225, x=1024~2076
#    → time_box（填写区）：x=900, y=3078, w=1435, h=196
#
#    关键词橙色方括号：y=4153~4259
#    → 翻写/回放：x=816, y=4153, w=379, h=107
#    → 直播(预告)：x=916, y=4153, w=379, h=107
# ============================================================

TEMPLATES_CONFIG = {

    # ── 模板一：学院 ──────────────────────────────────────────
    "template_final": {
        "name": "模板一",
        "path": "template_new_1.png",
        "qr_box":        [916, 3381, 583, 557],
        "time_box":      [900, 3078, 1435, 196],   # 右侧白色胶囊
        "date_code_box": None,
        "title_x": 226,  "title_y": 2122,  "title_max_width": 2110,
        "caption_max_width": 1950,
        "caption_item_gap_max": 40,
        "title_caption_gap_min": 90,
        "title_caption_gap_min_two_lines": 120,
        "content_x": 346,
        "bullet_dot_x": 275,  "bullet_dot_r": 14,
        "bullet_start_y": 2483,  "bullet_spacing": 144,
        "use_template_bullets": False,
        "content_y_offset": 0,  "auto_layout": False,
        "suffix": "-学院",
    },

    # ── 模板二：翻写 ──────────────────────────────────────────
    "template_2": {
        "name": "模板二",
        "path": "template_new_2.png",
        "qr_box":        [916, 3381, 583, 557],
        "time_box":      [900, 3078, 1435, 196],
        "date_code_box": [750, 4169, 458, 106],
        "title_x": 226,  "title_y": 2122,  "title_max_width": 2110,
        "caption_max_width": 1950,
        "caption_item_gap_max": 40,
        "title_caption_gap_min": 90,
        "title_caption_gap_min_two_lines": 120,
        "content_x": 346,
        "bullet_dot_x": 275,  "bullet_dot_r": 14,
        "bullet_start_y": 2483,  "bullet_spacing": 144,
        "use_template_bullets": False,
        "content_y_offset": 0,  "auto_layout": False,
        "suffix": "-翻写",
    },

    # ── 模板三：回放 ───────────────────────────────────────────
    "template_3": {
        "name": "模板三",
        "path": "template_new_3.png",
        "qr_box":        [916, 3381, 583, 557],
        "time_box":      [900, 3078, 1435, 196],
        "date_code_box": [750, 4169, 458, 106],
        "title_x": 226,  "title_y": 2122,  "title_max_width": 2110,
        "caption_max_width": 1950,
        "caption_item_gap_max": 40,
        "title_caption_gap_min": 90,
        "title_caption_gap_min_two_lines": 120,
        "content_x": 346,
        "bullet_dot_x": 275,  "bullet_dot_r": 14,
        "bullet_start_y": 2483,  "bullet_spacing": 144,
        "use_template_bullets": False,
        "content_y_offset": 0,  "auto_layout": False,
        "suffix": "-回放",
    },

    # ── 模板四：预告+企微朋友圈 ───────────────────────────────
    "template_4": {
        "name": "模板四",
        "path": "template_new_4.png",
        "qr_box":        [916, 3381, 583, 557],
        "time_box":      [900, 3078, 1435, 196],
        "date_code_box": [876, 4161, 458, 106],
        "title_x": 226,  "title_y": 2122,  "title_max_width": 2110,
        "caption_max_width": 1950,
        "caption_item_gap_max": 40,
        "title_caption_gap_min": 90,
        "title_caption_gap_min_two_lines": 120,
        "content_x": 346,
        "bullet_dot_x": 275,  "bullet_dot_r": 14,
        "bullet_start_y": 2483,  "bullet_spacing": 144,
        "use_template_bullets": False,
        "content_y_offset": 0,  "auto_layout": False,
        "suffix": "-预告+企微朋友圈",
    },

    # ── 模板六：横版预告 (3708x1950) ─────────────────────────
    "template_6": {
        "name": "模板六",
        "path": "template_new_6.png",
        # QR码框（蓝色边框内，正方形）：2026-06-25 新模板实测 外框 x2436~3381,y368~1299
        "qr_box":        [2468, 403, 880, 880],
        # 时间胶囊白色内部文字区：内部白色椭圆 x=900~2160, y=1572~1769（像素精确实测）
        # content_bot=1430 独立控制内容区下界（bullet points 止于此，不与 time_box 耦合）
        "time_box":      [950, 1572, 1140, 196],
        "time_text_x_offset": 50,
        "content_bot":   1340,
        # 关键词橙色括号（2026-06-25 新模板实测）：左「x2511~2538，右」x3012~3039，y1539~1645
        # 填字区：x2538~3012（宽474），居中放6位关键词
        "date_code_box": [2546, 1539, 458, 106],
        "date_code_font_size": 116,
        # title_max_width=2200（2026-07-16加宽）：左侧固定，只向右扩，避免短标题出现单字/标点独占第二行；右侧仍不撞二维码框(2468)
        # caption_max_width=1800：文案区更宽，避免长文案被迫换行
        # title_x=190：与 bullet_dot_x 对齐（点点在x=190）
        "title_font_size": 180,
        "title_x": 190,  "title_y": 280,  "title_max_width": 2200,
        "caption_max_width": 1950,
        "caption_item_gap_max": 40,
        "title_caption_gap_min": 90,
        "title_caption_gap_min_two_lines": 120,
        "content_x": 270,
        "bullet_dot_x": 190,  "bullet_dot_r": 14,
        "bullet_start_y": 500,  "bullet_spacing": 110,
        "use_template_bullets": False,
        "content_y_offset": 0,  "auto_layout": False,
        "suffix": "-横版预告",
    },

    # ── 模板五：新预告+企微朋友圈 (2416x3222) ────────────────
    "template_5": {
        "name": "模板五",
        "path": "template_new_5.png",
        # 二维码：x=292, y=2660, 405×405（2026-06-25 用户要求下移5px：2649→2654）
        "qr_box":        [290, 2654, 408, 408],
        # 时间框：胶囊中心区，实测 y=2400~2558（安全区，不碰弧边）
        # x 从胶囊最宽处左边界+安全偏移：x=1000, w=1180
        "time_box":      [1000, 2400, 1180, 158],
        # 关键词橙色括号：左x=1028~1055，右x=1375~1401
        # 填写区：x=1056~1374, y=2881~2987, h=106
        "date_code_box": [1088, 2871, 458, 106],
        # 内容区实测：y=1154~2367（完全空白，无任何占位文字）
        # 标题从顶部开始
        "title_x": 226,  "title_y": 1354,  "title_max_width": 2110,
        "caption_max_width": 1930,
        "caption_item_gap_max": 40,
        "t5_content_shift": 30,
        "content_x": 346,
        "bullet_dot_x": 275,  "bullet_dot_r": 14,
        # bullet_start_y / spacing 由 _draw_template5_content 动态计算，此处仅备用
        "bullet_start_y": 1520,  "bullet_spacing": 282,
        # 内容区底部边界（时间胶囊顶部上方留60px）
        "content_bot": 2367,
        "use_template_bullets": False,
        "content_y_offset": 0,  "auto_layout": False,
        "suffix": "-新预告+企微朋友圈",
    },
}

def get_template_config(template_id):
    return TEMPLATES_CONFIG.get(template_id)

def get_all_templates():
    return {k: v["name"] for k, v in TEMPLATES_CONFIG.items()}
