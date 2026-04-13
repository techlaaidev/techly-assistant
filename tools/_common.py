"""Shared helpers for all tool modules."""
import re
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
COMPANY_DATA_FILE = BASE_DIR / "company_data.md"
NOTES_FILE = DATA_DIR / "notes.txt"
REMINDERS_FILE = DATA_DIR / "reminders.json"
EXPENSES_DB = DATA_DIR / "expenses.db"
KB_DIR = DATA_DIR / "knowledge_base"

DATA_DIR.mkdir(parents=True, exist_ok=True)
KB_DIR.mkdir(parents=True, exist_ok=True)

# Ack prefix forces the LLM to speak a natural intro instead of guessing
# "không tìm thấy" during cloud speculative TTS.
_ACK_PREFIX = "Đã lấy thông tin thành công, chờ trong giây lát để phân tích.\n\n"


def _reply(data: str) -> str:
    """Wrap a data-fetch tool response with the acknowledgment prefix."""
    return _ACK_PREFIX + data


def _read_company_section(section_title: str) -> str:
    """Extract a section from company_data.md by heading name."""
    if not COMPANY_DATA_FILE.exists():
        return "Không tìm thấy file dữ liệu công ty."
    text = COMPANY_DATA_FILE.read_text(encoding="utf-8")
    pattern = rf"## {re.escape(section_title)}\n(.*?)(?=\n## |\Z)"
    match = re.search(pattern, text, re.DOTALL)
    return match.group(1).strip() if match else f"Không tìm thấy mục '{section_title}'."


def format_vnd(amount: int) -> str:
    """Format integer as Vietnamese currency (e.g. 50000 -> '50.000đ')."""
    return f"{amount:,.0f}đ".replace(",", ".")
