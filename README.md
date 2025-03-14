## 📝 AstrBot 签到插件

一个简单（有点简陋）的签到插件，支持每日签到、查询签到信息、排行榜、占卜以及删除记录等功能.  
目前正在开发新功能中ing


如果发现无法正常调用请查看插件目录文件是否齐全，不齐全请自己再git clone本插件一次

## 🧪 测试平台

| 平台     | 框架           | 状态     | 版本     |
| -------- | -------------- | -------- | -------- |
| QQ       | NapCat (AIOCQHTTP) | ✅ 已测试 | v1.0.1 |
| 企业微信 | WeCom          | ✅ 已测试 | v1.0.1 |

## ✨ 功能特点

- 🎯 每日签到获取随机金币 (0-100)
- 💰 连续签到额外奖励 (最高200金币)
- 🏆 签到排行榜查看
- 📊 个人签到数据查询
- 🎨 签到结果图片生成
- 🔮 每日运势占卜系统
- 📈 完整的签到统计系统
- 💾 数据持久化存储

## 💰 金币系统说明

### 获取金币

- ✅ 基础签到：随机获得 0-100 金币
- 🔄 连续签到：每天额外获得 (连续天数 × 10) 金币，上限200
- 📊 所有收支都会被记录在数据库中


## 📖 使用方法

### 👥 普通用户指令

- 📝 `签到` - 进行每日签到
- 🔍 `查询` - 查看个人签到信息和金币
- 📊 `排行` - 查看签到排行榜
- ❓ `签到帮助` - 显示帮助信息
- 🔮 `运势历史` - 查看历史运势记录

### 👑 管理员指令

- 💎 `修改金币 <用户id> <金币数>` - 修改指定用户的金币数量

## ⚙️ 自定义设置

1.  🖼️ 底图要求：
    -   文件名：`Basemap.png`
    -   分辨率：1640x856
    -   位置：插件目录下

2.  📝 字体文件：
    -   使用 `LXGWWenKai-Medium.ttf` 字体
    -   需放置在插件目录下

## ⚠️ 注意事项

- 💾 所有数据存储在SQLite数据库中,数据库目录为"AstrBot/data/plugins_db/strbot_plugin_sign.db"
- 📊 支持完整的金币和运势历史记录
- 🖼️ 签到结果会以图片形式展示
- ⚡ 插件依赖PIL库进行图片生成

## 👨‍💻 作者

-   作者：[FengYing](https://github.com/FengYing1314/)
-   仓库：[GitHub](https://github.com/FengYing1314/astrbot_plugin_sign)

## 🤝 感谢

- 感谢 [孤灯照镜上](https://github.com/Gorden-86) 对本项目做出的贡献，特别是占卜,删除记录,连续签到功能的实现!)
