import random
from datetime import datetime, timedelta
from typing import Tuple, Dict, Any

class SignManager:
    @staticmethod
    def calculate_sign_rewards(continuous_days: int) -> Tuple[int, int]:
        """计算签到奖励
        Returns:
            Tuple[基础奖励, 连续签到奖励]
        """
        base_coins = random.randint(0, 100)
        bonus_coins = min(continuous_days * 10, 200) if continuous_days > 1 else 0
        return base_coins, bonus_coins

    @staticmethod
    def get_fortune() -> Tuple[str, int]:
        """获取每日运势
        Returns:
            Tuple[运势结果, 运势值]
        """
        fortune_levels = ["凶", "末小吉", "末吉", "小吉", "半吉", "吉", "大吉"]
        fortune_value = random.randint(0, 100)
        fortune_index = min(fortune_value // 15, 6)
        return fortune_levels[fortune_index], fortune_value

    @staticmethod
    def format_sign_result(user_data: Dict[str, Any], coins_got: int, 
                          coins_gift: int, fortune_result: str, 
                          fortune_value: int) -> str:
        """格式化签到结果"""
        return (
            f"签到成功喵~\n"
            f"获得金币：{coins_got + coins_gift}\n"
            f"（基础签到：{coins_got}，连续签到加成：{coins_gift}）\n"
            f"当前金币：{user_data.get('coins', 0) + coins_got + coins_gift}\n"
            f"累计签到：{user_data.get('total_days', 0) + 1}天\n"
            f"连续签到：{user_data.get('continuous_days', 0)}天\n"
            f"今日占卜：{fortune_result} ({fortune_value}/100)"
        )
