"""Export opencode chat sessions to JSONL.

仅导出顶层会话（parent_id IS NULL，子代理会话直接跳过），
仅取 type=text 的 part（reasoning / tool / step-* / patch / compaction 等内部噪声全部跳过）。

输出契约与 trae 一致:
    opencode_chat_jsonl/{目录分类}/{会话标题}_{YYYYmmdd_HHMMSS}.jsonl
    每行: {"role": "user"|"assistant", "content": "..."}
"""
import argparse
import json
import os
import re
import shutil
import sqlite3
from datetime import datetime

DEFAULT_DB = os.path.expanduser("~/.local/share/opencode/opencode.db")
DEFAULT_OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "opencode_chat_jsonl")


def safe(s, maxlen=80):
    s = re.sub(r'[<>:"/\\|?*\x00-\x1F]', '_', str(s))
    s = re.sub(r'\s+', '_', s).strip('_')[:maxlen].rstrip('. ')
    return s or 'untitled'


def fmt_ts(ts):
    if isinstance(ts, (int, float)):
        if ts > 1e12:
            ts /= 1000
        try:
            return datetime.fromtimestamp(ts).strftime('%Y%m%d_%H%M%S')
        except Exception:
            pass
    return 'unknown'


def export(db_path=None, out_dir=None):
    db_path = db_path or DEFAULT_DB
    out_dir = out_dir or DEFAULT_OUT

    if not os.path.exists(db_path):
        print(f"[-] 数据库不存在: {db_path}")
        print("    提示: opencode 默认在 ~/.local/share/opencode/opencode.db")
        return

    conn = sqlite3.connect(f'file:{db_path}?mode=ro', uri=True)

    # 只取顶层会话（子代理 parent_id 非空，直接掠过）
    sessions = conn.execute(
        "SELECT id, title, slug, directory, time_updated FROM session "
        "WHERE parent_id IS NULL ORDER BY time_updated"
    ).fetchall()

    if os.path.exists(out_dir):
        shutil.rmtree(out_dir)
    os.makedirs(out_dir, exist_ok=True)

    total_sessions = 0
    total_lines = 0
    for sid, title, slug, directory, updated in sessions:
        # 该会话全部 text part, 关联 message 拿 role, 按创建时间排序
        parts = conn.execute(
            "SELECT m.data, p.data FROM part p "
            "JOIN message m ON p.message_id = m.id "
            "WHERE p.session_id = ? AND json_extract(p.data, '$.type') = 'text' "
            "ORDER BY p.time_created",
            (sid,),
        ).fetchall()

        lines = []
        for mdata, pdata in parts:
            try:
                role = json.loads(mdata).get('role', '')
                text = json.loads(pdata).get('text', '')
            except Exception:
                continue
            if role not in ('user', 'assistant') or not text:
                continue
            # 压缩折叠残留: 折叠后的工具调用记录不属于对话, 剥掉文本尾部的记录
            text = re.sub(r'\n*\[Assistant tool call\]: .*$', '', text, flags=re.DOTALL)
            if not text or text.startswith('diff --git'):
                continue
            lines.append(json.dumps({"role": role, "content": text}, ensure_ascii=False))

        if not lines:
            continue  # 无对话内容的会话（如纯工具会话）不产出文件

        ws = safe(directory or slug or '_unknown')
        wd = os.path.join(out_dir, ws)
        os.makedirs(wd, exist_ok=True)

        fn = f"{safe(title or slug or 'untitled')}_{fmt_ts(updated)}.jsonl"
        fp = os.path.join(wd, fn)
        with open(fp, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines) + '\n')

        total_sessions += 1
        total_lines += len(lines)
        print(f"  {ws}/{fn}  ({len(lines)} 行)")

    conn.close()
    print(f"\n[+] {total_sessions} 个会话, {total_lines} 行对话 -> {out_dir}")
    return out_dir


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="导出 opencode 顶层会话对话为 JSONL")
    ap.add_argument("--db", default=DEFAULT_DB, help="opencode.db 路径 (默认 ~/.local/share/opencode/opencode.db)")
    ap.add_argument("--out", default=DEFAULT_OUT, help="输出目录 (默认 opencode_chat_jsonl/, 会先清空重建)")
    args = ap.parse_args()
    export(args.db, args.out)
