import sqlite3
import os
import json
from typing import Dict, Any, Optional
from datetime import datetime

class SignDatabase:
    def __init__(self, plugin_dir: str):
        db_dir = os.path.join(os.path.dirname(os.path.dirname(plugin_dir)), "plugins_db")
        if not os.path.exists(db_dir):
            os.makedirs(db_dir)
        self.db_path = os.path.join(db_dir, "astrbot_plugin_sign.db")
        self.init_db()
        
    def init_db(self):
        """初始化数据库连接和表结构"""
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        
        # 创建所需的表
        tables = [
            '''CREATE TABLE IF NOT EXISTS sign_data (
                user_id TEXT PRIMARY KEY,
                total_days INTEGER DEFAULT 0,
                last_sign TEXT DEFAULT '',
                continuous_days INTEGER DEFAULT 0,
                coins INTEGER DEFAULT 0,
                total_coins_gift INTEGER DEFAULT 0,
                last_fortune_result TEXT DEFAULT '',
                last_fortune_value INTEGER DEFAULT 0
            )''',
            '''CREATE TABLE IF NOT EXISTS coins_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                user_id TEXT,
                amount INTEGER,
                reason TEXT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP
            )''',
            '''CREATE TABLE IF NOT EXISTS fortune_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                result TEXT,
                value INTEGER, 
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP
            )'''
        ]
        
        for table in tables:
            self.cursor.execute(table)
        self.conn.commit()

    def get_user_data(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取用户数据"""
        self.cursor.execute('SELECT * FROM sign_data WHERE user_id = ?', (user_id,))
        row = self.cursor.fetchone()
        if not row:
            return None
        
        columns = ['user_id', 'total_days', 'last_sign', 'continuous_days', 'coins', 
                  'total_coins_gift', 'last_fortune_result', 'last_fortune_value']
        return dict(zip(columns, row))

    def update_user_data(self, user_id: str, **kwargs):
        """更新用户数据"""
        if not self.get_user_data(user_id):
            self.cursor.execute('INSERT INTO sign_data (user_id) VALUES (?)', (user_id,))
            
        update_fields = []
        values = []
        for key, value in kwargs.items():
            update_fields.append(f"{key} = ?")
            values.append(value)
        values.append(user_id)
        
        sql = f"UPDATE sign_data SET {', '.join(update_fields)} WHERE user_id = ?"
        self.cursor.execute(sql, values)
        self.conn.commit()

    def log_coins(self, user_id: str, amount: int, reason: str):
        """记录金币变动"""
        self.cursor.execute(
            'INSERT INTO coins_history (user_id, amount, reason) VALUES (?, ?, ?)',
            (user_id, amount, reason)
        )
        self.conn.commit()

    def log_fortune(self, user_id: str, result: str, value: int):
        """记录占卜记录"""
        self.cursor.execute(
            'INSERT INTO fortune_history (user_id, result, value) VALUES (?, ?, ?)',
            (user_id, result, value)
        )
        self.conn.commit()

    def get_ranking(self, limit: int = 10):
        """获取排行榜数据"""
        self.cursor.execute('''
            SELECT user_id, coins, total_days FROM sign_data
            ORDER BY coins DESC, total_days DESC LIMIT ?
        ''', (limit,))
        return self.cursor.fetchall()

    def close(self):
        """关闭数据库连接"""
        self.conn.close()
