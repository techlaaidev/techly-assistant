"""Personal expense tracker using SQLite."""
import re
import sqlite3
from datetime import datetime
from ._common import _reply, EXPENSES_DB, format_vnd


def _get_conn():
    conn = sqlite3.connect(str(EXPENSES_DB))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount INTEGER NOT NULL,
            category TEXT NOT NULL,
            note TEXT,
            created_at TEXT NOT NULL
        )
    """)
    return conn


def _parse_vn_amount(text: str) -> int | None:
    """Parse '50k' → 50000, '2tr' → 2000000, '1 triệu' → 1000000."""
    s = str(text).lower().replace(" ", "").replace(".", "").replace(",", "")
    m = re.search(r"(\d+)", s)
    if not m:
        return None
    num = int(m.group(1))
    if "k" in s or "nghìn" in s or "nghin" in s:
        return num * 1000
    if "tr" in s or "triệu" in s or "trieu" in s:
        return num * 1_000_000
    return num


def register(mcp):
    @mcp.tool()
    def ghi_chi_tieu(so_tien: str, danh_muc: str, ghi_chu: str = "") -> str:
        """Ghi một khoản chi tiêu mới vào sổ cá nhân.

        GỌI TOOL NÀY KHI người dùng nói: "tôi vừa tiêu X cho Y", "ghi chi X cho Y".
        Ví dụ: "hôm nay tiêu 50k ăn trưa" → ghi_chi_tieu("50000", "ăn uống", "ăn trưa")
        Ví dụ: "mua cà phê 35k" → ghi_chi_tieu("35000", "cà phê").

        Args:
            so_tien: số tiền (dạng số nguyên VND, có thể là "50000" hoặc "50k")
            danh_muc: danh mục (ăn uống, cà phê, đi lại, mua sắm, giải trí, ...)
            ghi_chu: ghi chú thêm (tùy chọn)
        """
        amount = _parse_vn_amount(so_tien)
        if amount is None or amount <= 0:
            return f"Số tiền không hợp lệ: '{so_tien}'."
        conn = _get_conn()
        conn.execute(
            "INSERT INTO expenses (amount, category, note, created_at) VALUES (?, ?, ?, ?)",
            (amount, danh_muc.lower().strip(), ghi_chu, datetime.now().isoformat()),
        )
        conn.commit()
        conn.close()
        return f"Đã ghi: {format_vnd(amount)} cho danh mục '{danh_muc}'."

    @mcp.tool()
    def tong_chi_thang(thang: int = 0) -> str:
        """Tổng chi tiêu trong một tháng (mặc định tháng hiện tại).

        GỌI TOOL NÀY KHI người dùng hỏi: "tháng này tiêu bao nhiêu", "tổng chi tháng X".
        Args:
            thang: số tháng (1-12). Mặc định 0 = tháng hiện tại.
        """
        now = datetime.now()
        target_month = thang if 1 <= thang <= 12 else now.month
        target_year = now.year
        conn = _get_conn()
        cur = conn.execute("""
            SELECT COALESCE(SUM(amount), 0), COUNT(*) FROM expenses
            WHERE strftime('%Y', created_at) = ?
            AND strftime('%m', created_at) = ?
        """, (str(target_year), f"{target_month:02d}"))
        total, count = cur.fetchone()
        conn.close()
        if not count:
            return _reply(
                f"Bạn chưa ghi chi tiêu nào trong tháng {target_month}/{target_year}. "
                f"Hãy bắt đầu ghi bằng cách nói 'tiêu X đồng cho Y'."
            )
        return _reply(
            f"Tổng chi tiêu tháng {target_month}/{target_year}: {format_vnd(total)} "
            f"(từ {count} giao dịch)."
        )

    @mcp.tool()
    def bao_cao_chi_tieu() -> str:
        """Báo cáo chi tiêu tháng hiện tại theo từng danh mục.

        GỌI TOOL NÀY KHI người dùng hỏi: "báo cáo chi tiêu", "tiêu nhiều nhất vào gì",
        "thống kê chi tiêu".
        """
        now = datetime.now()
        conn = _get_conn()
        cur = conn.execute("""
            SELECT category, SUM(amount) as total FROM expenses
            WHERE strftime('%Y', created_at) = ?
            AND strftime('%m', created_at) = ?
            GROUP BY category
            ORDER BY total DESC
        """, (str(now.year), f"{now.month:02d}"))
        rows = cur.fetchall()
        conn.close()
        if not rows:
            return _reply(f"Chưa có chi tiêu nào trong tháng {now.month}.")
        total = sum(r[1] for r in rows)
        lines = [f"Báo cáo tháng {now.month}/{now.year} (tổng {format_vnd(total)}):"]
        for cat, amt in rows:
            pct = (amt / total * 100) if total else 0
            lines.append(f"- {cat}: {format_vnd(amt)} ({pct:.0f}%)")
        return _reply("\n".join(lines))
