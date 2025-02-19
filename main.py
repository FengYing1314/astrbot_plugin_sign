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
import requests

@register("astrbot_plugin_sign", "FengYing", "一个简易的签到插件，目前正在开发新功能，和完善已实现的功能，具体使用请看README.md" "1.0.3", "https://github.com/FengYing1314/astrbot_plugin_sign")
class SignPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.bg_image = os.path.join(os.path.dirname(__file__), "Basemap.png")
        
        # 设置数据库路径
        db_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "plugins_db")
        if not os.path.exists(db_dir):
            os.makedirs(db_dir)
        self.db_path = os.path.join(db_dir, "astrbot_plugin_sign.db")
        
        # 初始化数据库
        self.init_db()

    def init_db(self):
        """初始化数据库连接和表结构"""
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        
        # 创建用户签到表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS sign_data (
                user_id TEXT PRIMARY KEY,
                total_days INTEGER DEFAULT 0,
                last_sign TEXT DEFAULT '',
                continuous_days INTEGER DEFAULT 0,
                coins INTEGER DEFAULT 0,
                total_coins_gift INTEGER DEFAULT 0,
                last_fortune_result TEXT DEFAULT '',
                last_fortune_value INTEGER DEFAULT 0
            )
        ''')
        
        self.conn.commit()

    def get_user_data(self, user_id):
        """获取用户数据"""
        self.cursor.execute('SELECT * FROM sign_data WHERE user_id = ?', (user_id,))
        row = self.cursor.fetchone()
        if not row:
            return None
        
        # 构造用户数据字典
        columns = ['user_id', 'total_days', 'last_sign', 'continuous_days', 'coins', 
                  'total_coins_gift', 'last_fortune_result', 'last_fortune_value']
        return dict(zip(columns, row))

    def update_user_data(self, user_id, **kwargs):
        """更新用户数据"""
        if not self.get_user_data(user_id):
            # 插入新用户
            self.cursor.execute('''
                INSERT INTO sign_data (user_id) VALUES (?)
            ''', (user_id,))
            
        # 构建UPDATE语句
        update_fields = []
        values = []
        for key, value in kwargs.items():
            update_fields.append(f"{key} = ?")
            values.append(value)
        values.append(user_id)
        
        sql = f"UPDATE sign_data SET {', '.join(update_fields)} WHERE user_id = ?"
        self.cursor.execute(sql, values)
        self.conn.commit()

    async def download_font(self, font_path: str) -> bool:
        """下载字体文件"""
        try:
            font_url = "https://github.com/lxgw/LxgwWenKai/releases/download/v1.510/LXGWWenKai-Medium.ttf"
            logger.info(f"正在下载字体文件: {font_url}")
            
            response = requests.get(font_url)
            if response.status_code == 200:
                # 确保目录存在
                os.makedirs(os.path.dirname(font_path), exist_ok=True)
                
                with open(font_path, 'wb') as f:
                    f.write(response.content)
                logger.info(f"字体文件下载成功: {font_path}")
                return True
            else:
                logger.error(f"字体文件下载失败,状态码: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"字体文件下载失败: {str(e)}")
            return False

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
                logger.info("字体文件不存在,尝试下载...")
                if not await self.download_font(font_path):
                    logger.error("字体文件下载失败")
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
            
            user_data = self.get_user_data(user_id) or {}
            
            if user_data.get('last_sign') == today:
                image_path = await self.create_sign_image("今天已经签到过啦喵~")
                if image_path:
                    yield event.image_result(image_path)
                    if os.path.exists(image_path):
                        os.remove(image_path)
                return

            continuous_days = 1
            if user_data.get('last_sign') == (datetime.date.today() - datetime.timedelta(days=1)).strftime('%Y-%m-%d'):
                continuous_days = user_data.get('continuous_days', 0) + 1

            coins_got = random.randint(0, 100)
            coins_gift = min(continuous_days * 10, 200) if continuous_days > 1 else 0
            total_coins = coins_got + coins_gift

            # 生成占卜结果
            fortune_levels = ["凶", "末小吉", "末吉", "小吉", "半吉", "吉", "大吉"]
            fortune_value = random.randint(0, 100)
            fortune_index = min(fortune_value // 15, 6)
            fortune_result = fortune_levels[fortune_index]

            # 更新数据库
            self.update_user_data(
                user_id,
                total_days=user_data.get('total_days', 0) + 1,
                last_sign=today,
                continuous_days=continuous_days,
                coins=user_data.get('coins', 0) + total_coins,
                total_coins_gift=user_data.get('total_coins_gift', 0) + coins_gift,
                last_fortune_result=fortune_result,
                last_fortune_value=fortune_value
            )

            # 生成结果消息
            result = (
                f"签到成功喵~\n"
                f"获得金币：{total_coins}\n"
                f"（基础签到：{coins_got}，连续签到加成：{coins_gift}）\n"
                f"当前金币：{user_data.get('coins', 0) + total_coins}\n"
                f"累计签到：{user_data.get('total_days', 0) + 1}天\n"
                f"连续签到：{continuous_days - 1}天\n"
                f"今日占卜：{fortune_result} ({fortune_value}/100)"
            )

            image_path = await self.create_sign_image(result)
            if image_path:
                yield event.image_result(image_path)
                if os.path.exists(image_path):
                    os.remove(image_path)

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
            f"连续签到：{user_data['continuous_days'] - 1}天\n" #第一天签到不算连续
            f"累计连续签到奖励：{user_data['total_coins_gift']}金币\n"  # 新增：显示累计连续奖励
            f"上次签到：{user_data['last_sign']}\n"
            f"最新占卜：{user_data['last_fortune_result']} ({user_data['last_fortune_value']}/100)"
        )
        image_path = await self.create_sign_image(text, font_size=40)
        yield event.image_result(image_path)
        if os.path.exists(image_path):
            os.remove(image_path)

    @filter.command("排行")
    async def sign_rank(self, event: AstrMessageEvent):
        '''查看签到排行榜'''
        self.cursor.execute('''
            SELECT user_id, coins, total_days FROM sign_data
            ORDER BY coins DESC, total_days DESC LIMIT 10
        ''')
        sorted_users = self.cursor.fetchall()

        rank_text = "金币排行榜 TOP 10\n\n"
        for idx, (user_id, coins, total_days) in enumerate(sorted_users, 1):
            rank_text += f"第{idx}名: {user_id}\n"
            rank_text += f"金币: {coins} | 累计签到: {total_days}天\n\n"

        image_path = await self.create_sign_image(rank_text, font_size=35)
        yield event.image_result(image_path)
        if os.path.exists(image_path):
            os.remove(image_path)

    @filter.command("修改金币")
    @filter.permission_type(filter.PermissionType.ADMIN)
    async def modify_coins(self, event: AstrMessageEvent, user_id: str, amount: int):
        '''修改用户金币数量(仅管理员)'''
        if not self.get_user_data(user_id):
            image_path = await self.create_sign_image(f"用户 {user_id} 不存在喵~", font_size=40)
            yield event.image_result(image_path)
            if os.path.exists(image_path):
                os.remove(image_path)
            return

        self.update_user_data(user_id, coins=amount)
        image_path = await self.create_sign_image(f"已将用户 {user_id} 的金币修改为 {amount} 喵~", font_size=40)
        yield event.image_result(image_path)
        if os.path.exists(image_path):
            os.remove(image_path)

    @filter.command("删除所有记录")
    @filter.permission_type(filter.PermissionType.ADMIN)
    async def delete_all_records(self, event: AstrMessageEvent):
        '''删除所有签到记录（仅管理员）'''
        try:
            # 清空签到数据
            self.cursor.execute('DELETE FROM sign_data')
            self.conn.commit()

            # 返回成功消息
            image_path = await self.create_sign_image("所有签到记录已删除喵~", font_size=40)
            yield event.image_result(image_path)
            if os.path.exists(image_path):
                os.remove(image_path)
        except Exception as e:
            logger.error(f"删除记录失败: {str(e)}")
            yield event.plain_result("删除记录失败喵~请联系开发者检查日志")

    @filter.command("删除用户记录")
    @filter.permission_type(filter.PermissionType.ADMIN)
    async def delete_user_records(self, event: AstrMessageEvent, user_id: str):
        '''删除指定用户的签到记录（仅管理员）'''
        if self.get_user_data(user_id):
            self.cursor.execute('DELETE FROM sign_data WHERE user_id = ?', (user_id,))
            self.conn.commit()
            yield event.plain_result(f"用户 {user_id} 的签到记录已删除喵~")
        else:
            yield event.plain_result(f"用户 {user_id} 不存在喵~")

    @filter.command("签到帮助")
    async def sign_help(self, event: AstrMessageEvent):
        '''查看签到帮助'''
        help_text = """签到系统帮助喵~

发送 签到 - 每日签到
发送 查询 - 查看个人签到信息
发送 排行 - 查看签到排行榜
发送 签到帮助 - 显示本帮助

管理员指令:
发送 修改金币 <用户id> <金币数> - 修改用户金币数量
发送 删除所有记录 - 删除所有签到记录
发送 删除用户记录 <用户id> - 删除指定用户的签到记录"""

        image_path = await self.create_sign_image(help_text, font_size=38)
        yield event.image_result(image_path)
        if os.path.exists(image_path):
            os.remove(image_path)

    def __del__(self):
        """析构函数,确保关闭数据库连接"""
        if hasattr(self, 'conn'):
            self.conn.close()
