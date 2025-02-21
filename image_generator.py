import os
from PIL import Image, ImageDraw, ImageFont
from typing import Union

class ImageGenerator:
    def __init__(self, plugin_dir: str):
        self.bg_image = os.path.join(plugin_dir, "Basemap.png")
        self.font_path = os.path.join(plugin_dir, "LXGWWenKai-Medium.ttf")

    async def create_sign_image(self, text: str, font_size: int = 40) -> Union[str, None]:
        """生成签到图片"""
        try:
            if not os.path.exists(self.bg_image):
                return None

            bg = Image.open(self.bg_image)
            if bg.size != (1640, 856):
                bg = bg.resize((1640, 856))

            draw = ImageDraw.Draw(bg)

            try:
                if os.path.exists(self.font_path):
                    font = ImageFont.truetype(self.font_path, font_size)
                else:
                    font = ImageFont.load_default()
                    font_size = 16
            except Exception:
                font = ImageFont.load_default()
                font_size = 16

            text_bbox = draw.textbbox((0, 0), text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]

            x = (1640 - text_width) / 2
            y = (856 - text_height) / 2

            draw.text((x, y), text, font=font, fill=(0, 0, 0))

            temp_path = os.path.join(os.path.dirname(self.bg_image), "temp_sign.png")
            bg.save(temp_path)
            return temp_path
        except Exception:
            return None
