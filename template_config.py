# Four active livestream-poster templates, calibrated from the delivered artwork.

TEMPLATES_CONFIG = {
    # Academy poster: QR code is generated from the live link.
    "template_final": {
        "name": "学院",
        "path": "template_new_1.png",
        "qr_box": [916, 3381, 583, 557],
        "time_box": [900, 3078, 1435, 196],
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
        "time_cover_mode": "legacy",
        "suffix": "-学院",
    },

    # Existing poster retained unchanged. It uses Hu Liang's sole QR image.
    "template_5": {
        "name": "有二维码",
        "path": "template_new_5.png",
        "qr_box": [290, 2654, 408, 408],
        "time_box": [1000, 2400, 1180, 158],
        "date_code_box": [1088, 2871, 458, 106],
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
        "t5_content_shift": 30,
        "content_layout": "template5",
        "time_cover_mode": "full_box",
        "suffix": "-有二维码",
    },

    # New vertical poster. Its title and caption geometry matches template_5.
    "template_no_qr": {
        "name": "无二维码",
        "path": "template_new_no_qr.png",
        "qr_box": None,
        "time_box": [1000, 2400, 1180, 158],
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
        "content_bot": 2367,
        "t5_content_shift": 30,
        "content_layout": "template5",
        "time_cover_mode": "full_box",
        "suffix": "-无二维码",
    },

    # New horizontal poster. It has no QR code or keyword field.
    "template_horizontal": {
        "name": "横版",
        "path": "template_new_horizontal.png",
        "qr_box": None,
        "time_box": [950, 1572, 1140, 196],
        "date_code_box": None,
        "title_font_size": 180,
        "title_x": 190,
        "title_y": 219,
        "title_max_width": 1980,
        "balance_two_line_title": True,
        # The 2026-09-10 supplied horizontal background retains sample text.
        # Clear only those two left-side sample-text areas before drawing live data.
        "clear_placeholder_text_regions": [
            [120, 120, 2050, 540],
            [120, 670, 1850, 570],
        ],
        "restore_template_regions": [[2050, 50, 190, 160]],
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
        "time_cover_mode": "full_box",
        "time_text_x_offset": 0,
        "suffix": "-横版",
    },
}


def get_template_config(template_id):
    return TEMPLATES_CONFIG.get(template_id)


def get_all_templates():
    return {key: config["name"] for key, config in TEMPLATES_CONFIG.items()}
