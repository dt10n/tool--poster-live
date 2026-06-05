import json

TEMPLATES_CONFIG = {
    "template_final": {
        "name": "模板一",
        "path": "template_new_1.png",
        "qr_box": [928, 3380, 560, 560], # [x, y, width, height]
        "time_box": [700, 3020, 1600, 210], # [x, y, width, height]
        "bullet_dot_x": 276,
        "bullet_dot_r": 16,
        "bullet_start_y": 2598,
        "bullet_spacing": 144,
        "use_template_bullets": True,
        "auto_layout": True,
        "content_y_offset": -50,
        "suffix": "-学院"
    },
    "template_2": {
        "name": "模板二",
        "path": "template_new_2.png",
        "qr_box": [928, 3380, 560, 560], # [x, y, width, height]
        "suffix": "-预告+企微朋友圈",
        "bullet_dot_x": 276,
        "bullet_dot_r": 16,
        "bullet_start_y": 2598,
        "bullet_spacing": 144,
        "use_template_bullets": False,
        "content_y_offset": -60,
        "date_code_box": [813, 4153, 344, 106]
    },
    "template_3": {
        "name": "模板三",
        "path": "template_new_3.png",
        "qr_box": [928, 3380, 560, 560], # [x, y, width, height]
        "suffix": "-回放",
        "bullet_dot_x": 276,
        "bullet_dot_r": 16,
        "bullet_start_y": 2598,
        "bullet_spacing": 144,
        "use_template_bullets": False,
        "content_y_offset": -60,
        "date_code_box": [813, 4153, 344, 106]
    },
    "template_4": {
        "name": "模板四",
        "path": "template_new_4.png",
        "qr_box": [928, 3380, 560, 560], # [x, y, width, height]
        "suffix": "-翻写",
        "bullet_dot_x": 276,
        "bullet_dot_r": 16,
        "bullet_start_y": 2598,
        "bullet_spacing": 144,
        "use_template_bullets": False,
        "content_y_offset": -60,
        "date_code_box": [923, 4153, 344, 106]
    }
}

def get_template_config(template_id):
    return TEMPLATES_CONFIG.get(template_id)

def get_all_templates():
    return {k: v['name'] for k, v in TEMPLATES_CONFIG.items()}
