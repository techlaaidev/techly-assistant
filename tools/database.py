"""SQL database queries via SQLite (default) or Postgres (if psycopg2 installed).

Requires env:
    DB_TYPE     = "sqlite" or "postgres" (default "sqlite")
    DB_PATH     = sqlite file path (sqlite mode)
    DB_DSN      = postgres connection string (postgres mode, requires psycopg2)

Read-only by design. Only SELECT statements allowed.
"""
import os
import re
import sqlite3
from ._common import _reply, DATA_DIR

DB_TYPE = os.getenv("DB_TYPE", "sqlite").lower()
DB_PATH = os.getenv("DB_PATH", str(DATA_DIR / "user.db"))
DB_DSN = os.getenv("DB_DSN", "")


def _is_safe_select(query: str) -> bool:
    """Allow only SELECT queries, block writes/DDL."""
    q = query.strip().lower()
    if not q.startswith("select"):
        return False
    forbidden = ["insert", "update", "delete", "drop", "alter", "create",
                 "truncate", "grant", "revoke", "attach", "pragma"]
    return not any(re.search(rf"\b{w}\b", q) for w in forbidden)


def _query(sql: str) -> list:
    if DB_TYPE == "postgres":
        try:
            import psycopg2
        except ImportError:
            raise RuntimeError("psycopg2 chưa cài. Chạy: pip install psycopg2-binary")
        with psycopg2.connect(DB_DSN) as conn:
            cur = conn.cursor()
            cur.execute(sql)
            cols = [d[0] for d in cur.description] if cur.description else []
            rows = cur.fetchall()
        return [dict(zip(cols, r)) for r in rows]
    # SQLite default
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.execute(sql)
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


def register(mcp):
    @mcp.tool()
    def truy_van_db(sql: str) -> str:
        """Chạy 1 câu SELECT trên database. CHỈ chấp nhận SELECT (read-only).

        GỌI TOOL NÀY KHI người dùng nói: "query DB", "select X", "lấy data từ database".
        Ví dụ: truy_van_db("SELECT name, total FROM customers ORDER BY total DESC LIMIT 5")

        Args:
            sql: câu SELECT (KHÔNG dùng INSERT/UPDATE/DELETE/DROP/...)
        """
        if not _is_safe_select(sql):
            return "Chỉ cho phép câu SELECT, không dùng INSERT/UPDATE/DELETE/DROP."
        try:
            rows = _query(sql)
        except Exception as e:
            return f"Lỗi DB: {str(e)[:200]}"
        if not rows:
            return _reply("Câu query trả về 0 dòng (không có dữ liệu khớp).")
        # Format max 10 rows for voice
        preview = rows[:10]
        lines = []
        for i, row in enumerate(preview, 1):
            parts = ", ".join(f"{k}={v}" for k, v in row.items())
            lines.append(f"{i}. {parts}")
        more = f"\n... và {len(rows) - 10} dòng nữa." if len(rows) > 10 else ""
        return _reply(f"Kết quả ({len(rows)} dòng):\n" + "\n".join(lines) + more)

    @mcp.tool()
    def liet_ke_bang_db() -> str:
        """Liệt kê các bảng trong database hiện tại.

        GỌI TOOL NÀY KHI người dùng hỏi: "DB có bảng gì", "list tables", "schema".
        """
        try:
            if DB_TYPE == "postgres":
                rows = _query(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema = 'public' ORDER BY table_name"
                )
                names = [r["table_name"] for r in rows]
            else:
                rows = _query(
                    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
                )
                names = [r["name"] for r in rows]
        except Exception as e:
            return f"Lỗi DB: {str(e)[:200]}"
        if not names:
            return "Database không có bảng nào."
        return _reply(f"Có {len(names)} bảng:\n" + "\n".join(f"- {n}" for n in names))
