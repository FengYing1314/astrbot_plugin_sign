from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from astrbot.api.message_components import Plain
import json
import os
import datetime
import random
from PIL import Image, ImageDraw, ImageFont

@register("astrbot_plugin_sign", "FengYing", "一个简易的签到插件(半成品)，推荐自己更改底图，分辨率为1640*856" "", "")
class SignPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.data_file = os.path.join(os.path.dirname(__file__), "sign_data.json")
        self.bg_image = os.path.join(os.path.dirname(__file__), "Basemap.png")  # 添加底图路径
        self.load_data()

    def load_data(self):
        """加载签到数据"""
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r', encoding='utf-8') as f:
                self.sign_data = json.load(f)
            # 数据兼容性处理
            for user_id in self.sign_data:
                user_data = self.sign_data[user_id]
                if "fortune_history" not in user_data:
                    user_data["fortune_history"] = {}
                if "last_fortune" not in user_data:
                    user_data["last_fortune"] = {"result": "", "value": 0}
        else:
            self.sign_data = {}
            self.save_data()

    def save_data(self):
        """保存签到数据"""
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.sign_data, f, indent=4, ensure_ascii=False)

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

            if user_id not in self.sign_data:
                self.sign_data[user_id] = {
                    "total_days": 0,
                    "last_sign": "",
                    "continuous_days": 0,
                    "coins": 0,
                    "fortune_history": {},
                    "last_fortune": {"result": "", "value": 0}
                }

            user_data = self.sign_data[user_id]

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

            # 生成占卜结果
            fortune_levels = ["凶", "末小吉", "末吉", "小吉", "半吉", "吉", "大吉"]
            fortune_value = random.randint(0, 100)
            fortune_index = min(fortune_value // 15, 6)
            fortune_result = fortune_levels[fortune_index]

            # 保存占卜记录
            user_data["fortune_history"][today] = {  # 按日期保存历史
                "result": fortune_result,
                "value": fortune_value
            }
            user_data["last_fortune"] = {  # 保存最后一次结果
                "result": fortune_result,
                "value": fortune_value
            }
            self.save_data()

            result = (
                f"签到成功喵~\n"
                f"获得金币：{coins_got}\n"
                f"当前金币：{user_data['coins']}\n"
                f"累计签到：{user_data['total_days']}天\n"
                f"连续签到：{user_data['continuous_days']}天\n"
                f"今日占卜：{fortune_result} ({fortune_value}/100)"
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

        if user_id not in self.sign_data:
            image_path = await self.create_sign_image("还没有签到记录呢喵~", font_size=40)
            yield event.image_result(image_path)
            if os.path.exists(image_path):
                os.remove(image_path)
            return

        user_data = self.sign_data[user_id]
        text = (
            f"签到信息喵~\n"
            f"当前金币：{user_data.get('coins', 0)}\n"
            f"累计签到：{user_data['total_days']}天\n"
            f"连续签到：{user_data['continuous_days']}天\n"
            f"上次签到：{user_data['last_sign']}\n"
            f"最新占卜：{user_data['last_fortune']['result']} ({user_data['last_fortune']['value']}/100)"
        )
        image_path = await self.create_sign_image(text, font_size=40)
        yield event.image_result(image_path)
        if os.path.exists(image_path):
            os.remove(image_path)

    @filter.command("占卜历史")
    async def fortune_history(self, event: AstrMessageEvent):
        '''查看最近7天占卜记录'''
        user_id = event.get_sender_id()

        if user_id not in self.sign_data:
            image_path = await self.create_sign_image("还没有签到记录呢喵~", font_size=40)
            yield event.image_result(image_path)
            return

        user_data = self.sign_data[user_id]
        history = user_data["fortune_history"]

        # 获取最近7条记录
        sorted_dates = sorted(history.keys(), reverse=True)[:7]
        history_text = "最近占卜记录\n\n"
        for date in sorted_dates:
            entry = history[date]
            history_text += f"{date}: {entry['result']} ({entry['value']}/100)\n"

        image_path = await self.create_sign_image(history_text, font_size=35)
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

        rank_text = "金币排行榜 TOP 10\n\n"
        for idx, (user_id, data) in enumerate(sorted_users, 1):
            rank_text += f"第{idx}名: {user_id}\n"
            rank_text += f"金币: {data['coins']} | 累计签到: {data['total_days']}天\n\n"

        image_path = await self.create_sign_image(rank_text, font_size=35)
        yield event.image_result(image_path)
        if os.path.exists(image_path):
            os.remove(image_path)

    @filter.command("修改金币")
    @filter.permission_type(filter.PermissionType.ADMIN)
    async def modify_coins(self, event: AstrMessageEvent, user_id: str, amount: int):
        '''修改用户金币数量(仅管理员)'''
        if user_id not in self.sign_data:
            image_path = await self.create_sign_image(f"用户 {user_id} 不存在喵~", font_size=40)
            yield event.image_result(image_path)
            if os.path.exists(image_path):
                os.remove(image_path)
            return

        self.sign_data[user_id]['coins'] = amount
        self.save_data()
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
            self.sign_data = {}
            self.save_data()

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
        if user_id in self.sign_data:
            del self.sign_data[user_id]
            self.save_data()
            yield event.plain_result(f"用户 {user_id} 的签到记录已删除喵~")
        else:
            yield event.plain_result(f"用户 {user_id} 不存在喵~")

    @filter.command("签到帮助")
    async def sign_help(self, event: AstrMessageEvent):
        '''查看签到帮助'''
        help_text = """签到系统帮助喵~

发送 签到 - 每日签到
发送 查询 - 查看个人签到信息
发送 占卜历史 - 查看最近7天占卜记录
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
