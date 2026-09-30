# SKILLS.md — OpenCode Chat Export

**给 AI 助手读的操作手册。** 这份文件描述如何从 OpenCode CLI 的本地数据库导出聊天记录。人类读者请看同目录 [README.md](README.md)。

## 能力

从 opencode 的明文 SQLite 数据库导出**顶层会话**的人机对话为统一 JSONL。子代理会话（自主运行、无人类交互）直接掠过，不导出。

- Python 3.8+，**无第三方依赖**，标准库即可
- 数据库是明文 SQLite（无加密），不需要任何解密步骤

## 前置条件

先确认，不要假设：

```bash
ls -la ~/.local/share/opencode/opencode.db    # 存在才能跑
```

- 注意：此路径可能是符号链接（指向实际存储位置），脚本能直接读，不用管
- opencode 必须安装过并跑过至少一次，否则没有数据库
- 数据库可能很大（数 GB 级），磁盘要有足够空间放导出产物（实测 6.4GB 库 → 20MB JSONL）

## 命令

```bash
python3 export_opencode.py                          # 默认输入输出
python3 export_opencode.py --db <path> --out <dir>  # 自定义
python3 export_opencode.py --help
```

- 默认输入：`~/.local/share/opencode/opencode.db`
- 默认输出：`./opencode_chat_jsonl/`（**会先清空重建**，注意别指向重要目录）
- 产物已被 `.gitignore` 的 `*chat_jsonl/` 覆盖，不会误提交

## 输出契约

```
opencode_chat_jsonl/
└── {目录分类}/                    # 按会话的 directory 字段（如 home_a1、tmp）
    └── {会话标题}_{YYYYmmdd_HHMMSS}.jsonl
```

每行结构：`{"role": "user"|"assistant", "content": "..."}`

只含**顶层会话**（`parent_id IS NULL`）里 `type=text` 的 part。子代理、reasoning 思考、工具调用、patch、压缩检查点、折叠残留全部不产出。

## 数据模型（提取依据）

```
session (parent_id IS NULL = 人机会话)          message (role, time, model)
    └── message ──1:N──> part (type=text 才是对话正文)
```

- `part.type` 可选值：`text`（对话正文）/ `reasoning`（思考）/ `tool`（工具调用）/ `step-start`、`step-finish` / `patch` / `compaction`（压缩检查点）
- **只取 `type=text`**，其余全是内部噪声
- 压缩检查点：opencode 压缩上下文时插入 `role=user` + `summary` 的空消息 + `type=compaction` 的 part，**本身无正文，天然跳过**，不会丢对话
- 折叠残留：个别 `text` 里会内嵌 `[Assistant tool call]: ...` 文本（压缩折叠的痕迹），脚本会剥离尾部，保留对话部分

## 校验

```bash
python3 -c "import json,glob; bad=0
for f in glob.glob('opencode_chat_jsonl/**/*.jsonl', recursive=True):
    for i,l in enumerate(open(f,encoding='utf-8'),1):
        if not l.strip(): continue
        try: json.loads(l)
        except: bad+=1; print('  坏行',f,i)
print('坏行',bad)"
```

- 会话数与 `SELECT COUNT(*) FROM session WHERE parent_id IS NULL` 一致（当前数据：68）
- 每行 `role` 只能有 `user` / `assistant` 两种值

## 常见失败

| 现象 | 原因 | 处理 |
|------|------|------|
| `数据库不存在` | opencode 没装/没跑过 | 先 `opencode` 跑一次产生数据库 |
| 导出 0 会话 | 全是子代理会话的库（无顶层会话） | 属正常，报告即可 |
| 查询超时/卡住 | 大库（数 GB）上全表扫 | 脚本已按索引查询；勿自己跑全表 `json_extract` 扫描 |
| 文件名为 `untitled` | 该会话标题为空 | 正常兜底，内容不受影响 |

## 硬约束

- **不要**把导出的 `*.jsonl` 提交进 git（`.gitignore` 已覆盖，别手动 `git add -f`）
- 会话内容可能含**敏感信息**（密码、密钥、路径），产物只留在本地，**不要外传**
- 本工具仅限处理**用户自己设备上、自己账号下**的数据
- 只读模式打开数据库，不会改动原库（但 `--out` 目录会被清空重建，勿指向重要目录）
