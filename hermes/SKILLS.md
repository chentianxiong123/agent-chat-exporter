# SKILLS.md — Hermes Chat Export

**给 AI 助手读的操作手册。** 这份文件描述如何从 Hermes 本地数据库导出聊天记录。人类读者请看同目录 [README.md](README.md)。

## 能力

从 `~/.hermes/state.db`（明文 SQLite，无加密）读取会话，过滤系统噪声，导出统一 JSONL。

- Python 3.8+，**无第三方依赖**，标准库即可
- 跨平台（Windows / macOS / Linux）

## 前置条件

先确认，不要假设：

```bash
ls -la ~/.hermes/state.db      # 存在才能跑
```

- Hermes 必须安装过并跑过至少一次，否则没有数据库
- 数据库可能被 Hermes 进程占用，脚本已按只读模式打开，通常无需干预

## 命令

```bash
python3 export_hermes.py                          # 默认输入输出
python3 export_hermes.py --db <path> --out <dir>  # 自定义
python3 export_hermes.py --help
```

| 参数 | 默认 | 说明 |
|------|------|------|
| `--db` | `~/.hermes/state.db` | state.db 路径 |
| `--out` | `./hermes_chat_jsonl` | 输出目录，**会先清空重建** |

## 输出契约

- 每个会话一个文件：`{会话标题}_{YYYYmmdd_HHMMSS}.jsonl`
- 每行一个 JSON 对象（JSONL，行间无逗号）
- 每行结构固定：`{"role": "user"|"assistant", "content": "..."}`
- 文件名中的 `< > : " / \ | ? *` 和控制字符已替换为 `_`
- **噪声已被脚本过滤**：工具回调、系统提示、日志、traceback、`[CONTEXT COMPACTION]` 压缩摘要。输出是干净对话，**不要再去二次清理**

## 校验

```bash
python3 - <<'PY'
import json, glob, sys
bad = 0
for f in sorted(glob.glob('hermes_chat_jsonl/*.jsonl')):
    for i, line in enumerate(open(f, encoding='utf-8'), 1):
        if not line.strip(): continue
        try:
            o = json.loads(line)
            assert o.get('role') in ('user', 'assistant') and o.get('content')
        except Exception as e:
            bad += 1
            if bad <= 5: print(f"  坏行 {f}:{i} -> {e}")
print(f"坏行 {bad} 条")
sys.exit(1 if bad else 0)
PY
```

只看退出码 0 不算成功，必须跑上面这段确认 JSON 全可解析。

## 常见失败

| 现象 | 原因 | 处理 |
|------|------|------|
| `unable to open database file` | `--db` 路径不对 | `ls ~/.hermes/` 确认真实位置后重跑 |
| `no such table: sessions` | `--db` 指到了非 Hermes 数据库 | 换正确文件 |
| `[+] 0 sessions exported` | 会话里没有 user/assistant 消息，或全是噪声 | 正常结果，不是错误 |
| 文件数为 0 但无报错 | 同上 | 不要改脚本去"救" |

## 硬约束

- **不要**把导出的 `*.jsonl` 提交进 git（已被 `.gitignore` 覆盖）
- **不要**修改 `NOISE_PATTERNS` / `is_noise` / `clean_text` 来"救"空结果，那是有意的过滤
- **不要**把导出的聊天记录贴到公开 gist、issue 或聊天记录里
