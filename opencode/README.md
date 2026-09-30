# OpenCode Chat Export

从 OpenCode CLI 的本地数据库导出聊天记录为 JSONL 格式。

> 🤖 AI 助手请看同目录 [SKILLS.md](SKILLS.md)

## 状态

✅ 已实现。实测 6.4GB 库 → 68 会话 / 51141 行 / 20MB JSONL。

## 快速开始

```bash
cd opencode
python3 export_opencode.py                          # 默认输入输出
python3 export_opencode.py --db <path> --out <dir>  # 自定义
```

无第三方依赖，Python 3.8+ 标准库即可。

## 导出什么

- **只导顶层会话**（人机对话，`parent_id IS NULL`），子代理会话（自主运行、无人类交互）直接掠过
- **只取 `type=text` 的 part**（对话正文），reasoning / tool / step-* / patch / compaction 等内部噪声全部过滤
- 压缩检查点（无正文的空摘要消息）天然跳过，对话内容零丢失
- 折叠残留（`[Assistant tool call]:` 内嵌文本）自动剥离

## 输出契约

```
opencode_chat_jsonl/
└── {目录分类}/              # 按会话工作目录分类（home_a1、tmp 等）
    └── {会话标题}_{YYYYmmdd_HHMMSS}.jsonl
```

每行：`{"role": "user"|"assistant", "content": "..."}`，与 trae / hermes 输出格式一致。

## 数据库

```
~/.local/share/opencode/opencode.db   （可能是符号链接，指向实际位置）
```

明文 SQLite（无加密），核心表：`session` / `message` / `part`。内容在 `part.data`（`type=text`），元数据在 `message.data`（role / 模型 / token）。

## 已知问题

- 数据库可能很大（数 GB 级），必须只读模式打开，按索引查询
- `auto_vacuum = OFF`，体积膨胀是 opencode 自身行为，与导出无关
- `--out` 目录会先清空重建

## 参考

- **[ocgc](https://github.com/ocgc)** — OpenCode Garbage Collector（第三方清理工具，针对 opencode 数据库膨胀问题）
