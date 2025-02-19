from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from astrbot.api.message_components import Plain
import json
import os
import datetime
import random
import sqlite3
from PIL import Image, ImageDraw, ImageFont

@register("astrbot_plugin_sign", "FengYing", "一个简易的签到插件(半成品)，推荐自己更改底图，分辨率为1640*856" "", "")
class SignPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        # 数据库路径和名称
        db_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "plugins_db")
        self.db_file = os.path.join(db_dir, "astrbot_plugin_sign.db")
        self.bg_image = os.path.join(os.path.dirname(__file__), "Basemap.png")
        
        # 确保数据库目录存在
        if not os.path.exists(db_dir):
            try:
                os.makedirs(db_dir)
                logger.info(f"Created database directory: {db_dir}")
            except Exception as e:
                logger.error(f"Failed to create database directory: {str(e)}")
        
        self.init_db()

    def init_db(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS sign_data
            (user_id TEXT PRIMARY KEY,
             total_days INTEGER,
             last_sign TEXT,
             continuous_days INTEGER,
             coins INTEGER)''')
        conn.commit()
        conn.close()

    def get_user_data(self, user_id: str) -> dict:
        """获取用户数据"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM sign_data WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                "user_id": row[0],
                "total_days": row[1],
                "last_sign": row[2],
                "continuous_days": row[3],
                "coins": row[4]
            }
        return None

    def save_user_data(self, user_data: dict):
        """保存用户数据"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('''INSERT OR REPLACE INTO sign_data 
            (user_id, total_days, last_sign, continuous_days, coins)
            VALUES (?, ?, ?, ?, ?)''',
            (user_data["user_id"],
             user_data["total_days"],
             user_data["last_sign"],
             user_data["continuous_days"],
             user_data["coins"]))
        conn.commit()
        conn.close()

    def get_all_users(self) -> list:
        """获取所有用户数据"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM sign_data')
        rows = cursor.fetchall()
        conn.close()
        
        return [{
            "user_id": row[0],
            "total_days": row[1],
            "last_sign": row[2],
            "continuous_days": row[3],
            "coins": row[4]
        } for row in rows]

    async def create_sign_image(self, text: str, font_size: int = 40) -> str:
        """生成签到图片,使用1640x856的底图,文字区域750x850"""
        try:
            if not os.path.exists(self.bg_image):
                logger.error(f"底图不存在: {self.bg_image}")
                return None
                
            bg = Image.open(self.bg_image)
            if bg.size != (1640, 856):
                bg = bg.resize((1640, 856))
            
            draw = ImageDraw.Draw(bg)
            
            font_path = os.path.join(os.path.dirname(__file__), "LXGWWenKai-Medium.ttf")
            if not os.path.exists(font_path):
                logger.error(f"字体文件不存在: {font_path}")
                return None
                
            font = ImageFont.truetype(font_path, font_size)

            text_bbox = draw.textbbox((0, 0), text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            
            x = (1640 - text_width) / 2
            y = (856 - text_height) / 2

            draw.text((x, y), text, font=font, fill=(0, 0, 0))

            temp_path = os.path.join(os.path.dirname(__file__), "temp_sign.png")
            bg.save(temp_path)
            logger.info(f"生成签到图片成功: {temp_path}")
            return temp_path
        except Exception as e:
            logger.error(f"生成签到图片失败: {str(e)}")
            return None

    @filter.command("签到")
    async def sign(self, event: AstrMessageEvent):
        '''每日签到'''
        try:
            user_id = event.get_sender_id()
            today = datetime.date.today().strftime('%Y-%m-%d')
            
            user_data = self.get_user_data(user_id)
            if not user_data:
                user_data = {
                    "user_id": user_id,
                    "total_days": 0,
                    "last_sign": "",
                    "continuous_days": 0,
                    "coins": 0
                }
            
            if user_data["last_sign"] == today:
                image_path = await self.create_sign_image("今天已经签到过啦喵~", font_size=40)
                if image_path:
                    yield event.image_result(image_path)
                    if os.path.exists(image_path):
                        os.remove(image_path)
                else:
                    yield event.plain_result("今天已经签到过啦喵~")
                return
                
            if user_data["last_sign"] == (datetime.date.today() - datetime.timedelta(days=1)).strftime('%Y-%m-%d'):
                user_data["continuous_days"] += 1
            else:
                user_data["continuous_days"] = 1
                
            coins_got = random.randint(0, 100)
            user_data["coins"] = user_data.get("coins", 0) + coins_got
            
            user_data["total_days"] += 1
            user_data["last_sign"] = today
            
            self.save_user_data(user_data)
            
            result = (
                f"签到成功喵~\n"
                f"获得金币：{coins_got}\n"
                f"当前金币：{user_data['coins']}\n"
                f"累计签到：{user_data['total_days']}天\n"
                f"连续签到：{user_data['continuous_days']}天"
            )

            image_path = await self.create_sign_image(result, font_size=45)
            if image_path:
                yield event.image_result(image_path)
                if os.path.exists(image_path):
                    os.remove(image_path)
            else:
                yield event.plain_result(result)
        except Exception as e:
            logger.error(f"签到失败: {str(e)}")
            yield event.plain_result("签到失败了喵~请联系管理员检查日志")

    @filter.command("查询")
    async def sign_info(self, event: AstrMessageEvent):
        '''查看签到信息'''
        user_id = event.get_sender_id()
        user_data = self.get_user_data(user_id)
        
        if not user_data:
            image_path = await self.create_sign_image("还没有签到记录呢喵~", font_size=40)
            yield event.image_result(image_path)
            if os.path.exists(image_path):
                os.remove(image_path)
            return
            
        text = (
            f"签到信息喵~\n"
            f"当前金币：{user_data.get('coins', 0)}\n"
            f"累计签到：{user_data['total_days']}天\n"
            f"连续签到：{user_data['continuous_days']}天\n"
            f"上次签到：{user_data['last_sign']}"
        )
        image_path = await self.create_sign_image(text, font_size=40) 
        yield event.image_result(image_path)
        if os.path.exists(image_path):
            os.remove(image_path)

    @filter.command("排行")
    async def sign_rank(self, event: AstrMessageEvent):
        '''查看签到排行榜'''
        all_users = self.get_all_users()
        sorted_users = sorted(
            all_users,
            key=lambda x: (x['coins'], x['total_days']), 
            reverse=True
        )[:10]
        
        rank_text = "金币排行榜 TOP 10\n\n"
        for idx, data in enumerate(sorted_users, 1):
            rank_text += f"第{idx}名: {data['user_id']}\n"
            rank_text += f"金币: {data['coins']} | 累计签到: {data['total_days']}天\n\n"
        
        image_path = await self.create_sign_image(rank_text, font_size=35)  
        yield event.image_result(image_path)
        if os.path.exists(image_path):
            os.remove(image_path)

    @filter.command("修改金币")
    @filter.permission_type(filter.PermissionType.ADMIN)
    async def modify_coins(self, event: AstrMessageEvent, user_id: str, amount: int):
        '''修改用户金币数量(仅管理员)'''
        user_data = self.get_user_data(user_id)
        if not user_data:
            image_path = await self.create_sign_image(f"用户 {user_id} 不存在喵~", font_size=40)
            yield event.image_result(image_path)
            if os.path.exists(image_path):
                os.remove(image_path)
            return
            
        user_data['coins'] = amount
        self.save_user_data(user_data)
        image_path = await self.create_sign_image(f"已将用户 {user_id} 的金币修改为 {amount} 喵~", font_size=40)
        yield event.image_result(image_path)
        if os.path.exists(image_path):
            os.remove(image_path)

    @filter.command("签到帮助")
    async def sign_help(self, event: AstrMessageEvent):
        '''查看签到帮助'''
        help_text = """签到系统帮助喵~
        
发送 签到 - 每日签到
发送 查询 - 查看个人签到信息 
发送 排行 - 查看签到排行榜
发送 签到帮助 - 显示本帮助
管理员指令:
发送 修改金币 <用户id> <金币数> - 修改用户金币数量"""
        
        image_path = await self.create_sign_image(help_text, font_size=38) 
        yield event.image_result(image_path)
        if os.path.exists(image_path):
            os.remove(image_path)
