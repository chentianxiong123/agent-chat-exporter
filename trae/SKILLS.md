# SKILLS.md — Trae CN Chat Export

**给 AI 助手读的操作手册。** 这份文件描述如何从 Trae CN（字节跳动 AI IDE）的 SQLCipher 加密数据库导出聊天记录。人类读者请看同目录 [README.md](README.md)。

## 能力

从运行中的 Trae CN 进程内存提取 SQLCipher 密钥 → 解密数据库 → 按工作区分会话导出 JSONL。

- **仅 Windows**（需要进程内存扫描，用了 `pymem`）
- 依赖：`sqlcipher3`、`pymem`、`psutil`、`pycryptodome`

## 前置条件

按顺序确认，**前两条缺一即无法进行**：

```powershell
# 1. Trae CN 正在运行
tasklist /FI "IMAGENAME eq Trae CN.exe"

# 2. ai_agent.dll 已加载（即至少打开过一次 AI 聊天）
tasklist /M /FI "IMAGENAME eq Trae CN.exe" | findstr ai_agent.dll
```

如果第 2 步查不到 `ai_agent.dll`：让用户打开 Trae CN 并用一次 AI 聊天，**然后重新跑**。密钥不存在于磁盘，只存在于这个 DLL 加载后的进程内存里，这是本工具的根本限制，无法绕过。

```powershell
# 3. 数据库存在
dir "%APPDATA%\Trae CN\ModularData\ai-agent\database.db"
```

- 需要 `PROCESS_ALL_ACCESS` 权限，不够的话用管理员身份跑
- 数据库约 1.3GB，解密需要足够内存

## 配置

**本工具不是 argparse，而是 `config.json` 驱动。** 首次运行自动生成，之后用户/AI 直接改这个 JSON 即可：

```json
{
  "db_path": "%APPDATA%\\Trae CN\\ModularData\\ai-agent\\database.db",
  "key": "",
  "proc_name": "Trae CN",
  "dll_name": "ai_agent.dll",
  "output_dir": ""
}
```

- `db_path` 里的 `%APPDATA%` 由脚本 `os.path.expandvars` 展开，换用户自动适配
- `key` 为空时第 1 步会自动提取并回填
- **`config.json` 含密钥，已被 `.gitignore` 忽略，绝不要提交**

## 命令

```powershell
pip install -r requirements.txt
python run.py                       # 一键：取密钥 -> 解密 -> 导出
```

分步执行（只在排查问题时用）：

```powershell
python 1_find_key/find_key.py        # 1. 内存扫描提取 SQLCipher 密钥
python 2_decrypt_db/decrypt.py       # 2. 解密数据库，全部表导出到 tables_json/
python 3_export_chats/export_jsonl.py  # 3. 按工作区分会话导出到 trae_chat_jsonl/
```

## 输出契约

```
trae_chat_jsonl/
└── {工作区名}/
    └── {会话标题}_{YYYYmmdd_HHMMSS}.jsonl
```

每行结构：`{"role": "user"|"assistant", "content": "..."}`

系统提示、工具调用、计划项等内部噪声已被清洗。

## 校验

```powershell
python -c "import json,glob; bad=0
for f in glob.glob('trae_chat_jsonl/**/*.jsonl', recursive=True):
    for i,l in enumerate(open(f,encoding='utf-8'),1):
        if not l.strip(): continue
        try: json.loads(l)
        except: bad+=1; print('  坏行',f,i)
print('坏行',bad)"
```

同时确认中间产物 `tables_json/` 下 `history_v2.json` 有内容，没有说明第 2 步就失败了。

## 常见失败

| 现象 | 原因 | 处理 |
|------|------|------|
| 找不到进程 / DLL 未加载 | 没打开过 AI 聊天 | 打开 Trae 用一次 AI 后再跑，这是最常见原因 |
| `find_key()` 无输出直接返回 | 没扫到密钥 | 重开 Trae，确认 `ai_agent.dll` 已加载，再跑 |
| 密钥提取失败 | `PROCESS_ALL_ACCESS` 权限不足 | 以管理员身份运行 |
| 第 3 步导出 0 会话 | 密钥不匹配，解密出来是空/乱码 | **删掉 `config.json` 的 `key` 字段**，重跑第 1 步 |
| `sqlcipher3` import 失败 | 依赖没装 | `pip install -r requirements.txt` |

## 硬约束

- **不要**把 `config.json`（含密钥）或导出的 `*.jsonl` 提交进 git
- **不要**把密钥外传到公开 gist、issue 或聊天记录
- 本工具仅限处理**用户自己设备上、自己账号下**的数据
- 解密出的 `tables_json/` 含全量表数据（包括 `project.absolute_path` 等本地路径信息），**不要整体外传**，用完即删
