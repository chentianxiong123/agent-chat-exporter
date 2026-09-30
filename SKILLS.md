# SKILLS.md

**给 AI 助手读的操作手册。** 把这个仓库和本文件一起丢给任意 AI 编程助手，它就能自己判断前置条件、跑通导出、校验结果。

> 面向人类读者的说明请看 [README.md](README.md)。这里只写"该怎么操作"。

---

## 一句话能力

把 AI 编程助手（Trae CN / Hermes / OpenCode）和 QQ Android 的**本地聊天记录**解密、清洗，导出为统一 JSONL。全部在用户本地机器上跑，不联网上传。

## 决策流程

用户说「帮我导出聊天记录 / 备份对话」时：

1. **确认工具** — 按顺序探测：
   - `~/.hermes/state.db` 存在 → **Hermes**
   - 用户在 Windows 且装了 Trae CN → **Trae CN**
   - 用户提 QQ / 有 root 手机 → **QQ Android**
   - 都不满足 → 直接问用户
2. **核对前置条件** — 见各节「前置条件」，缺什么先补齐，不要硬跑
3. **执行命令** — 见各节「命令」，参数不猜，缺就问
4. **校验输出** — 用「通用校验」确认成功，别只看进程没报错

## 输出契约（三种工具一致）

- 每个会话一个文件：`{会话标题}_{YYYYmmdd_HHMMSS}.jsonl`
- 每行一个 JSON 对象，JSONL 格式（行间无逗号）
- Hermes / Trae CN 每行：`{"role": "user"|"assistant", "content": "..."}`
- QQ Android 每行：`{"t": "YYYY-MM-DD HH:MM:SS", "from": "...", "qq": "...", "self": bool, "type": "text", "text": "..."}`
- 系统提示、工具回调、日志、上下文压缩摘要等噪声已被脚本过滤，**输出是干净对话，不要再去清理**

---

## Hermes

### 前置条件

- Hermes 装过、跑过至少一次
- `~/.hermes/state.db` 存在（明文 SQLite，无加密，**无需额外依赖**，Python 3.8+ 标准库即可）

### 命令

```bash
python3 hermes/export_hermes.py                      # 默认输入输出
python3 hermes/export_hermes.py --help               # 看参数
python3 hermes/export_hermes.py --db <path> --out <dir>
```

| 参数 | 默认 | 说明 |
|------|------|------|
| `--db` | `~/.hermes/state.db` | state.db 路径 |
| `--out` | `./hermes_chat_jsonl` | 输出目录，**会先清空重建** |

### 常见失败

| 现象 | 原因 | 处理 |
|------|------|------|
| `unable to open database file` | DB 路径不对 | `ls ~/.hermes/` 确认真实位置，用 `--db` 指定 |
| `no such table: sessions` | `--db` 指到了非 Hermes 数据库 | 换正确文件 |
| `[+] 0 sessions exported` | 会话里没有 user/assistant 消息，或全是噪声 | 正常结果，不是错误 |

---

## QQ Android

### 前置条件

- **root 手机** + 电脑装好 `adb`
- 数据库已 pull 到本地某个目录
- Python 3 标准库即可，无第三方依赖

### 第一步：提取数据库

```bash
adb root
adb pull /data/data/com.tencent.mobileqq/databases/ ./databases/
```

每个账号一个 `{QQ号}.db`。数据库是 SQLite + XOR 加密，脚本内置密钥，不需要额外步骤。

### 命令

```bash
python3 qq-phone/export_chats.py                                # 默认 ./databases -> ./exports
python3 qq-phone/export_chats.py --db-dir ./databases --out ./exports
python3 qq-phone/export_chats.py --help
```

| 参数 | 默认 | 说明 |
|------|------|------|
| `--db-dir` | `./databases` | 数据库目录，目录不存在会打印提取命令并退出 |
| `--out` | `./exports` | 输出目录 |

输出按账号分层：`{out}/account_{QQ号}/private/` 与 `{out}/account_{QQ号}/group/`。

### 常见失败

| 现象 | 原因 | 处理 |
|------|------|------|
| `[!] 找不到数据库目录` | 还没 pull | 先跑上面的 adb 命令 |
| `数据库: 0个` | 目录里没 `*.db` | 确认 pull 的路径层级，可能多套了一层 `databases/` |
| `昵称表: 0人` | DB 里没有 Friends/CardProfilev4 表 | 拉到了错误文件，或 QQ 版本不符 |

---

## Trae CN

### 前置条件（最容易踩坑）

- **仅 Windows**（需要进程内存扫描）
- **Trae CN 必须正在运行，且至少打开过一次 AI 聊天** —— 否则 `ai_agent.dll` 没加载，密钥取不到
- 当前进程需要 `PROCESS_ALL_ACCESS` 权限
- 数据库约 1.3GB，解密需要足够内存

### 命令

```powershell
cd trae
pip install -r requirements.txt
python run.py                       # 一键：取密钥 -> 解密 -> 导出
```

分步执行（只在排查问题时用）：

```powershell
python 1_find_key/find_key.py       # 1. 从进程内存提取 SQLCipher 密钥
python 2_decrypt_db/decrypt.py      # 2. 解密数据库，导出全部表为 JSON
python 3_export_chats/export_jsonl.py  # 3. 按工作区分会话导出 JSONL
```

路径与密钥缓存在 `trae/config.json`（首次运行自动生成，**已被 .gitignore 忽略，不要提交**）。

### 常见失败

| 现象 | 原因 | 处理 |
|------|------|------|
| 找不到进程 / DLL 未加载 | 没打开过 AI 聊天 | 打开 Trae 并用一次 AI 后再跑 |
| 密钥提取失败 | 权限不足 | 以管理员身份运行 |
| 解密 0 行 | 密钥不匹配 | 删掉 `config.json` 缓存重跑第 1 步 |

---

## OpenCode

🚧 **未实现**。`opencode/` 目录只有 README，没有可运行脚本。用户问起就如实说，不要假装能跑。

已知该工具数据库很大（5.9GB+），需只读模式打开，`PRAGMA integrity_check` 会超时。

---

## 通用校验

导出成功后跑这段，确认输出真的可用：

```bash
python3 - <<'PY'
import json, glob, sys
files = sorted(glob.glob(sys.argv[1] if len(sys.argv)>1 else '**/*.jsonl', recursive=True))
bad = 0
for f in files:
    for i, line in enumerate(open(f, encoding='utf-8'), 1):
        line = line.strip()
        if not line: continue
        try:
            o = json.loads(line)
            assert isinstance(o, dict) and o
        except Exception as e:
            bad += 1
            if bad <= 5: print(f"  坏行 {f}:{i} -> {e}")
print(f"文件 {len(files)} 个, 坏行 {bad} 条")
sys.exit(1 if bad else 0)
PY
```

全 JSON 可解析、坏行 0 条才算成功。

## 硬性约束

- **不要**把导出的聊天记录、`*.db`、`config.json` 提交进 git —— 已被 `.gitignore` 覆盖
- **不要**改脚本里的噪声过滤正则来「救」空结果，那是有意过滤
- 密钥与加密细节见各子目录 README，**不要外传到公开 gist 或 issue**
