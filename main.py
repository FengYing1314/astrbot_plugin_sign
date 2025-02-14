from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from astrbot.api.message_components import Plain
import json
import os
import datetime
import random
from PIL import Image, ImageDraw, ImageFont

@register("sign", "Your Name", "一个功能丰富的签到插件", "1.1.0", "repo url")
class SignPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.data_file = os.path.join(os.path.dirname(__file__), "sign_data.json")
        self.bg_image = os.path.join(os.path.dirname(__file__), "Basemap.png") # 添加底图路径
        self.load_data()

    def load_data(self):
        """加载签到数据"""
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r', encoding='utf-8') as f:
                self.sign_data = json.load(f)
        else:
            self.sign_data = {}
            self.save_data()
        if not self.sign_data:
            self.sign_data = {}
            self.save_data()

    def save_data(self):
        """保存签到数据"""
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.sign_data, f, indent=4, ensure_ascii=False)

    async def create_sign_image(self, text: str) -> str:
        """生成签到图片,使用1640x856的底图,文字区域750x850"""
        # 打开底图
        bg = Image.open(self.bg_image)
        
        # 确保底图尺寸正确
        if bg.size != (1640, 856):
            bg = bg.resize((1640, 856))
        
        # 创建绘图对象
        draw = ImageDraw.Draw(bg)
        
        # 设置字体
        try:
            # 根据文本长度动态调整字体大小
            text_lines = len(text.split('\n'))
            font_size = min(40, int(750 / text_lines))  # 确保文字不会太大
            font = ImageFont.truetype("simhei.ttf", font_size)
        except:
            font = ImageFont.load_default()

        # 计算文本区域
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        # 计算居中位置 (在750x850的区域内居中)
        x = (1640 - text_width) / 2  # 整个图片水平居中
        y = (856 - text_height) / 2   # 整个图片垂直居中

        # 在图片上绘制文字
        draw.text((x, y), text, font=font, fill=(0, 0, 0))

        # 保存为临时文件并返回路径
        temp_path = os.path.join(os.path.dirname(__file__), "temp_sign.png")
        bg.save(temp_path)
        return temp_path

    @filter.command("签到")
    async def sign(self, event: AstrMessageEvent):
        '''每日签到'''
        user_id = event.get_sender_id()
        today = datetime.date.today().strftime('%Y-%m-%d')
        
        if user_id not in self.sign_data:
            self.sign_data[user_id] = {
                "total_days": 0,
                "last_sign": "",
                "continuous_days": 0,
                "coins": 0
            }
        
        user_data = self.sign_data[user_id]
        
        if user_data["last_sign"] == today:
            url = await self.text_to_image("今天已经签到过啦喵~ (。・ω・。)")
            yield event.image_result(url)
            return
            
        if user_data["last_sign"] == (datetime.date.today() - datetime.timedelta(days=1)).strftime('%Y-%m-%d'):
            user_data["continuous_days"] += 1
        else:
            user_data["continuous_days"] = 1
            
        coins_got = random.randint(0, 100)
        user_data["coins"] = user_data.get("coins", 0) + coins_got
        
        user_data["total_days"] += 1
        user_data["last_sign"] = today
        self.save_data()
        
        result = (
            f"签到成功喵~ ヾ(≧▽≦*)o\n"
            f"获得金币：{coins_got} ✧(≖ ◡ ≖✿)\n"
            f"当前金币：{user_data['coins']} (*´∀`*)\n"
            f"累计签到：{user_data['total_days']}天 (◍•ᴗ•◍)\n"
            f"连续签到：{user_data['continuous_days']}天 nyaa~ ฅ(●'◡'●)ฅ"
        )

        # 使用新的图片生成方法
        image_path = await self.create_sign_image(result)
        yield event.image_result(image_path)
        # 删除临时文件
        if os.path.exists(image_path):
            os.remove(image_path)

    @filter.command("查询")
    async def sign_info(self, event: AstrMessageEvent):
        '''查看签到信息'''
        user_id = event.get_sender_id()
        
        if user_id not in self.sign_data:
            image_path = await self.create_sign_image("还没有签到记录呢喵~ (｡•́︿•̀｡)")
            yield event.image_result(image_path)
            if os.path.exists(image_path):
                os.remove(image_path)
            return
            
        user_data = self.sign_data[user_id]
        text = (
            f"签到信息喵~ (๑•̀ㅂ•́)و✧\n"
            f"当前金币：{user_data.get('coins', 0)} (★ ω ★)\n"
            f"累计签到：{user_data['total_days']}天 (◕‿◕✿)\n"
            f"连续签到：{user_data['continuous_days']}天 (｡♥‿♥｡)\n"
            f"上次签到：{user_data['last_sign']} nya~ ₍˄·͈༝·͈˄₎◞ ̑̑"
        )
        image_path = await self.create_sign_image(text)
        yield event.image_result(image_path)
        if os.path.exists(image_path):
            os.remove(image_path)

    @filter.command("排行")
    async def sign_rank(self, event: AstrMessageEvent):
        '''查看签到排行榜'''
        sorted_users = sorted(
            self.sign_data.items(),
            key=lambda x: (x[1]['coins'], x[1]['total_days']), 
            reverse=True
        )[:10]
        
        rank_text = "金币排行榜 TOP 10 ✨\n\n"
        for idx, (user_id, data) in enumerate(sorted_users, 1):
            rank_text += f"第{idx}名: {user_id}\n"
            rank_text += f"金币: {data['coins']} | 累计签到: {data['total_days']}天\n\n"
        
        image_path = await self.create_sign_image(rank_text)
        yield event.image_result(image_path)
        if os.path.exists(image_path):
            os.remove(image_path)

    @filter.command("修改金币")
    @filter.permission_type(filter.PermissionType.ADMIN)
    async def modify_coins(self, event: AstrMessageEvent, user_id: str, amount: int):
        '''修改用户金币数量(仅管理员)'''
        if user_id not in self.sign_data:
            image_path = await self.create_sign_image(f"用户 {user_id} 不存在喵~ (｡•́︿•̀｡)")
            yield event.image_result(image_path)
            if os.path.exists(image_path):
                os.remove(image_path)
            return
            
        self.sign_data[user_id]['coins'] = amount
        self.save_data()
        image_path = await self.create_sign_image(f"已将用户 {user_id} 的金币修改为 {amount} 喵~ (。・∀・)ノ")
        yield event.image_result(image_path)
        if os.path.exists(image_path):
            os.remove(image_path)

    @filter.command("签到帮助")
    async def sign_help(self, event: AstrMessageEvent):
        '''查看签到帮助'''
        help_text = """签到系统帮助喵~ ฅ^•ﻌ•^ฅ
        
发送 签到 - 每日签到
发送 查询 - 查看个人签到信息 
发送 排行 - 查看签到排行榜
发送 签到帮助 - 显示本帮助
管理员指令:
发送 修改金币 <用户id> <金币数> - 修改用户金币数量"""
        
        image_path = await self.create_sign_image(help_text)
        yield event.image_result(image_path)
        if os.path.exists(image_path):
            os.remove(image_path)