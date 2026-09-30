# agent-chat-exporter

[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> **从本地 AI 编程助手和 QQ Android 提取聊天记录，解密后统一导出为 JSONL。**
> Export chat history from local AI coding assistants (Trae CN, Hermes, OpenCode) and QQ Android into clean JSONL — decrypt SQLCipher and XOR databases, normalize into one format.

---

各 AI 工具的聊天记录都被锁在各自的本地数据库里，格式互不兼容、有的还加密。这个工具集把数据库解密、读取、清洗成统一的 JSONL，方便你备份、迁移、分析或做训练数据。

- **跨工具统一** — 四个工具的聊天数据落到同一种 `{role, content}` 结构
- **本地处理** — 全部在你自己的机器上跑，数据不上传任何服务器
- **噪声清洗** — 系统提示、工具回调、上下文压缩摘要等内部噪声已过滤，输出是干净的可读对话

## 支持的工具

| 工具 | 数据库 | 加密 | 平台 | 状态 |
|------|--------|------|------|------|
| [Trae CN](trae/) | SQLCipher 4 | 密钥需从进程内存中提取 | Windows | ✅ 完成 |
| [Hermes](hermes/) | 明文 SQLite | 无 | 跨平台 | ✅ 完成 |
| [OpenCode](opencode/) | 明文 SQLite | 无 | 跨平台 | ✅ 完成 |
| [QQ Android](qq-phone/) | SQLite + XOR | 两套 XOR 密钥 | 需 root 提机，脚本跨平台 | ✅ 完成 |

## 输出格式

每个会话一个 `.jsonl` 文件，文件名 `{会话标题}_{时间戳}.jsonl`：

```jsonl
{"role": "user", "content": "帮我创建一个项目"}
{"role": "assistant", "content": "好的，项目已创建..."}
```

## 快速开始

```bash
# Trae CN（Windows，需先打开 Trae 让 ai_agent.dll 加载到内存）
cd trae && pip install -r requirements.txt && python run.py

# Hermes（跨平台，无需额外依赖）
cd hermes && python export_hermes.py

# QQ Android（需先从 root 手机 adb pull 数据库到本地）
cd qq-phone && python3 export_chats.py

# OpenCode（跨平台，无需额外依赖）
cd opencode && python export_opencode.py
```

> 🤖 **用 AI 跑？** 每个工具目录（`trae/` `hermes/` `qq-phone/` `opencode/`）都自带一份 `SKILLS.md` —— 给 AI 助手读的操作手册：前置条件、命令、失败模式对照表、校验方式。把对应子目录丢给任意 AI 编程助手，它能自己判断前置条件、跑命令、校验结果。

每个子目录都是独立工具，有各自的 README 说明原理和数据库结构。

## 项目结构

```
agent-chat-exporter/
├── trae/         # Trae CN — SQLCipher 4，三步流水线：取密钥 → 解密 → 导出
├── hermes/       # Hermes — 明文 SQLite
├── opencode/     # OpenCode CLI — 明文 SQLite，只导顶层会话，子代理自动跳过
├── qq-phone/     # QQ Android — XOR 加密，含密钥推导分析
├── README.md
├── LICENSE       # MIT
└── .gitignore
```

每个工具目录内还有一份 `SKILLS.md`，给 AI 助手读（每份自包含前置条件/命令/输出契约/校验/失败模式）。

## 技术栈

- Python 3.8+
- `sqlite3` / `sqlcipher3` — 明文与加密数据库读写
- `pymem` + `psutil` — 进程枚举与内存扫描（仅 Trae，仅 Windows）
- `pycryptodome` — HMAC-SHA512 / PBKDF2 校验（仅 Trae）
- Python 标准库 — Hermes、QQ Android 无第三方依赖

## 适用场景

| 场景 | 说明 |
|------|------|
| **数据备份** | 聊天记录只存在本地，换机 / 重装前导出，避免丢失 |
| **跨工具迁移** | 统一格式后可对比、汇总不同工具的对话 |
| **数据分析** | 统计提问习惯、模型表现、token 消耗 |
| **训练数据** | 清洗后的对话可直接用于微调或评估集 |

## 使用须知

- 本工具只处理**你自己设备上、你自己账号下**的数据，用途限于个人数据备份与迁移
- 请勿用于绕过他人软件的保护、批量采集数据或任何违反相关软件用户协议 / 地方法律的用途
- 本项目按 MIT 协议提供，作者不对使用行为承担任何责任
- 密钥与加密细节请参见各子目录 README，均为对公开版本的逆向分析

## License

[MIT](LICENSE) © 2026 chentianxiong123
