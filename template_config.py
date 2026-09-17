# Four active livestream-poster templates, calibrated from the delivered artwork.

TEMPLATES_CONFIG = {
    # Academy poster: QR code is generated from the live link.
    "template_final": {
        "name": "学院",
        "path": "template_new_1.png",
        "qr_box": [916, 3381, 583, 557],
        "time_box": [882, 3078, 1328, 198],
        "date_code_box": None,
        "title_x": 226,
        "title_y": 2122,
        "title_max_width": 2110,
        "caption_max_width": 1950,
        "caption_item_gap_max": 40,
        "caption_item_gap_min": 18,
        "title_caption_gap_min": 90,
        "title_caption_gap_min_two_lines": 120,
        "caption_time_gap_min": 90,
        "content_x": 346,
        "bullet_dot_x": 275,
        "bullet_dot_r": 14,
        "bullet_start_y": 2483,
        "bullet_spacing": 144,
        "time_cover_mode": "full_box",
        "time_cover_x": [1010, 2100],
        "time_cover_top_inset": 24,
        "time_cover_bottom_inset": 24,
        "time_text_box": [882, 2210],
        "time_text_x_offset": 0,
        "suffix": "-学院",
    },

    # Existing poster retained unchanged. It uses Hu Liang's sole QR image.
    "template_5": {
        "name": "有二维码",
        "path": "template_new_5.png",
        "qr_box": [290, 2654, 408, 408],
        "time_box": [882, 2378, 1328, 198],
        "date_code_box": [1065, 2871, 504, 106],
        "title_x": 226,
        "title_y": 1354,
        "title_max_width": 2110,
        "caption_max_width": 1930,
        "caption_item_gap_max": 40,
        "caption_item_gap_min": 18,
        "title_caption_gap_min": 90,
        "title_caption_gap_min_two_lines": 120,
        "caption_time_gap_min": 90,
        "content_x": 346,
        "bullet_dot_x": 275,
        "bullet_dot_r": 14,
        "content_bot": 2367,
        # Issue 475 calibration: move the title and caption group up 20px
        # while preserving the time capsule and QR-code area.
        "t5_content_shift": 10,
        "content_y_offset": -10,
        "content_layout": "template5",
        "time_cover_mode": "none",
        "time_text_x_offset": 0,
        "suffix": "-有二维码",
    },

    # New vertical poster. Its title and caption geometry matches template_5.
    "template_no_qr": {
        "name": "无二维码",
        "path": "template_new_no_qr.png",
        "qr_box": None,
        "time_box": [882, 2304, 1328, 198],
        "date_code_box": None,
        "title_x": 226,
        "title_y": 1354,
        "title_max_width": 2110,
        "caption_max_width": 1930,
        "caption_item_gap_max": 40,
        "caption_item_gap_min": 18,
        "title_caption_gap_min": 90,
        "title_caption_gap_min_two_lines": 120,
        "caption_time_gap_min": 90,
        "content_x": 346,
        "bullet_dot_x": 275,
        "bullet_dot_r": 14,
        "content_bot": 2293,
        "t5_content_shift": 30,
        "content_layout": "template5",
        "time_cover_mode": "none",
        "time_text_x_offset": 0,
        "suffix": "-无二维码",
    },

    # New horizontal poster. It has no QR code or keyword field.
    "template_horizontal": {
        "name": "横版",
        "path": "template_new_horizontal.png",
        "qr_box": None,
        "time_box": [888, 1572, 1328, 198],
        "date_code_box": None,
        "title_font_size": 180,
        "title_x": 190,
        "title_y": 219,
        "title_max_width": 1980,
        "balance_two_line_title": True,
        "caption_max_width": 1900,
        "caption_item_gap_max": 40,
        "caption_item_gap_min": 18,
        "title_caption_gap_min": 90,
        "title_caption_gap_min_two_lines": 120,
        "caption_time_gap_min": 90,
        "content_x": 242,
        "bullet_dot_x": 171,
        "bullet_dot_r": 14,
        "content_bot": 1470,
        "time_cover_mode": "none",
        "time_text_x_offset": 0,
        "suffix": "-横版",
    },
}


def get_template_config(template_id):
    return TEMPLATES_CONFIG.get(template_id)


def get_all_templates():
    return {key: config["name"] for key, config in TEMPLATES_CONFIG.items()}
