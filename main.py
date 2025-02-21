from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
import os
import datetime

from .database import SignDatabase
from .image_generator import ImageGenerator
from .sign_manager import SignManager

@register("astrbot_plugin_sign", "FengYing", "一个签到插件，具体使用请看README.md", "1.0.5", "https://github.com/FengYing1314/astrbot_plugin_sign")
class SignPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.db = SignDatabase(os.path.dirname(__file__))
        self.img_gen = ImageGenerator(os.path.dirname(__file__))
        
    @filter.command("签到")
    async def sign(self, event: AstrMessageEvent):
        '''每日签到'''
        try:
            user_id = event.get_sender_id()
            today = datetime.date.today().strftime('%Y-%m-%d')
            
            user_data = self.db.get_user_data(user_id) or {}
            
            if user_data.get('last_sign') == today:
                image_path = await self.img_gen.create_sign_image("今天已经签到过啦喵~")
                if image_path:
                    yield event.image_result(image_path)
                    if os.path.exists(image_path):
                        os.remove(image_path)
                return

            # 计算连续天数
            continuous_days = 1
            if user_data.get('last_sign') == (datetime.date.today() - datetime.timedelta(days=1)).strftime('%Y-%m-%d'):
                continuous_days = user_data.get('continuous_days', 0) + 1

            # 计算奖励
            coins_got, coins_gift = SignManager.calculate_sign_rewards(continuous_days)
            fortune_result, fortune_value = SignManager.get_fortune()

            # 更新数据
            self.db.update_user_data(
                user_id,
                total_days=user_data.get('total_days', 0) + 1,
                last_sign=today,
                continuous_days=continuous_days,
                coins=user_data.get('coins', 0) + coins_got + coins_gift,
                total_coins_gift=user_data.get('total_coins_gift', 0) + coins_gift,
                last_fortune_result=fortune_result,
                last_fortune_value=fortune_value
            )

            # 记录历史
            self.db.log_coins(user_id, coins_got, "基础签到")
            if coins_gift > 0:
                self.db.log_coins(user_id, coins_gift, "连续签到奖励")
            self.db.log_fortune(user_id, fortune_result, fortune_value)

            # 生成结果消息
            result = SignManager.format_sign_result(
                user_data, coins_got, coins_gift, 
                fortune_result, fortune_value
            )

            image_path = await self.img_gen.create_sign_image(result)
            if image_path:
                yield event.image_result(image_path)
                if os.path.exists(image_path):
                    os.remove(image_path)

        except Exception as e:
            logger.error(f"签到失败: {str(e)}")
            yield event.plain_result("签到失败了喵~请联系管理员检查日志")

    # ... 其他命令处理方法 ...
    # 为了简洁,其他命令处理方法的实现逻辑类似,
    # 都是通过调用 db、img_gen 和 SignManager 的方法来完成功能
