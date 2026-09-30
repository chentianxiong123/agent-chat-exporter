# SKILLS.md — QQ Android Chat Export

**给 AI 助手读的操作手册。** 这份文件描述如何从 QQ Android 的本地数据库导出聊天记录。人类读者请看同目录 [README.md](README.md)。

## 能力

从 root 手机提取的 `{QQ号}.db`（SQLite + XOR 加密）中解密导出聊天记录。两套 XOR 密钥已内置在脚本里，不需要额外推导。

- Python 3 标准库即可，**无第三方依赖**
- 脚本跨平台，**提数据库需要 root 手机 + adb**

## 前置条件

```bash
adb devices                 # 手机已连接并授权
adb root                    # 需要 root 权限
```

**这一步是硬门槛。** 手机没 root，后面全是空谈。遇到用户没 root，直接告知无法进行，不要试图绕。

## 第一步：提取数据库

```bash
adb pull /data/data/com.tencent.mobileqq/databases/ ./databases/
```

每个账号一个 `{QQ号}.db`，另有 `slowtable_{QQ号}.db`。

## 第二步：导出

```bash
python3 export_chats.py                                # 默认 ./databases -> ./exports
python3 export_chats.py --db-dir <path> --out <path>
python3 export_chats.py --help
```

| 参数 | 默认 | 说明 |
|------|------|------|
| `--db-dir` | `./databases` | 数据库目录。目录不存在会打印 adb 提取命令并退出 |
| `--out` | `./exports` | 输出目录 |

## 输出契约

按账号分层：

```
exports/
└── account_{QQ号}/
    ├── private/
    │   └── {备注}-{对方QQ}.jsonl
    └── group/
        └── {群号}.jsonl
```

每行结构（注意：与 Hermes 不同，字段名不一样）：

```jsonl
{"t": "2022-10-04 11:48:00", "from": "你", "qq": "1026044893", "self": true, "type": "text", "text": "帮我创建一个项目"}
```

- `t` 时间为 UTC+8
- `self` 为 true 表示自己发的
- 图片消息只提取 UUID，**不含实际图片文件**
- 昵称约 27% 含 emoji，是用户真实昵称，**不要清洗**

## 校验

```bash
python3 - <<'PY'
import json, glob, sys
bad = 0
for f in sorted(glob.glob('exports/**/**/*.jsonl', recursive=True)):
    for i, line in enumerate(open(f, encoding='utf-8'), 1):
        if not line.strip(): continue
        try:
            o = json.loads(line)
            assert 't' in o and 'qq' in o
        except Exception as e:
            bad += 1
            if bad <= 5: print(f"  坏行 {f}:{i} -> {e}")
print(f"坏行 {bad} 条")
sys.exit(1 if bad else 0)
PY
```

## 常见失败

| 现象 | 原因 | 处理 |
|------|------|------|
| `[!] 找不到数据库目录` | 还没 pull | 先跑上面的 adb 命令 |
| `数据库: 0个` | 目录里没有 `*.db` | 多半是 pull 时多套了一层 `databases/`，进一层再看 |
| `昵称表: 0人` | DB 里没有 Friends / CardProfilev4 表 | 拉到了错误文件，或 QQ 版本与本工具分析的不一致 |
| `昵称全是乱码` | 密钥二不适用于该版本 | 对照 README 的"密钥发现过程"重新推导，不要猜 |

## 硬约束

- **不要**把提取的 `*.db` 和导出的 `*.jsonl` 提交进 git（已被 `.gitignore` 覆盖）
- **不要**把 XOR 密钥外传到公开 gist、issue 或聊天记录
- 本工具仅限处理**用户自己设备上、自己账号下**的数据
- 群聊昵称需跨表关联，同一用户在不同表里的昵称可能不一致（更新时机不同），**不要当成 bug 修**
