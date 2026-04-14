"""Browser automation via Playwright — semantic clicks by text/role.

Requires:
    pip install playwright
    python -m playwright install chromium
    ENABLE_BROWSER_PLAYWRIGHT=1 in .env

Persistent browser instance shared across tool calls. Auto-launch on first
use. Each tool gates on PC mode (same as pc_control).
"""
import os
from ._common import _reply
from . import pc_control  # for mode check

try:
    from playwright.sync_api import sync_playwright, Browser, Page
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False

_browser_state = {
    "playwright": None,
    "browser": None,
    "page": None,
}


def _check() -> str | None:
    """Check Playwright + PC mode active."""
    if not HAS_PLAYWRIGHT:
        return "Playwright chưa cài. Chạy: pip install playwright && python -m playwright install chromium"
    if not pc_control._is_mode_active():
        return pc_control.PC_MODE_DISABLED_MSG
    return None


def _ensure_browser():
    """Lazy-init Playwright browser. Reuse if already running."""
    if _browser_state["browser"] is None:
        pw = sync_playwright().start()
        browser = pw.chromium.launch(
            headless=False,
            args=["--start-maximized"],
        )
        page = browser.new_page(no_viewport=True)
        _browser_state["playwright"] = pw
        _browser_state["browser"] = browser
        _browser_state["page"] = page
    return _browser_state["page"]


def _close_browser():
    """Cleanup persistent browser instance."""
    if _browser_state["browser"]:
        try:
            _browser_state["browser"].close()
        except Exception:
            pass
    if _browser_state["playwright"]:
        try:
            _browser_state["playwright"].stop()
        except Exception:
            pass
    _browser_state["browser"] = None
    _browser_state["playwright"] = None
    _browser_state["page"] = None


def register(mcp):
    @mcp.tool()
    def mo_chrome_playwright(url: str = "https://google.com") -> str:
        """Mở trình duyệt Chromium qua Playwright và truy cập URL.

        GỌI TOOL NÀY KHI người dùng muốn duyệt web có khả năng tự động click,
        điền form, scrape data: "duyệt web", "scrape", "automation web",
        "mở trang để click sau".
        Khác với mo_chrome (chỉ launch), tool này tạo phiên Playwright control được.

        Args:
            url: URL muốn mở (mặc định google.com)
        """
        if err := _check():
            return err
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        try:
            page = _ensure_browser()
            page.goto(url, timeout=30000)
            return f"Đã mở Chromium qua Playwright đến {url}."
        except Exception as e:
            return f"Lỗi mở Playwright: {str(e)[:150]}"

    @mcp.tool()
    def click_chu_trong_browser(text: str) -> str:
        """Click vào element có chứa text này trong trang Playwright đang mở.

        GỌI TOOL NÀY KHI người dùng nói: "click vào X", "nhấn vào Y" trong context
        đang duyệt web. CHỈ work nếu trước đó đã gọi mo_chrome_playwright.
        Ví dụ: "click vào mục giải trí", "nhấn nút đăng nhập", "chọn link X".

        Args:
            text: text hiển thị của element cần click (vd "Giải trí", "Đăng nhập")
        """
        if err := _check():
            return err
        page = _browser_state.get("page")
        if not page:
            return "Chưa có browser Playwright. Hãy gọi mo_chrome_playwright trước."
        try:
            # Try multiple strategies
            locator = page.get_by_text(text, exact=False).first
            locator.click(timeout=5000)
            return f"Đã click '{text}' trong browser."
        except Exception as e:
            return f"Không click được '{text}': {str(e)[:150]}"

    @mcp.tool()
    def dien_form_browser(label_or_placeholder: str, gia_tri: str) -> str:
        """Điền giá trị vào form input có label hoặc placeholder khớp.

        GỌI TOOL NÀY KHI người dùng nói: "điền X vào Y", "nhập Z vào ô tên".
        Ví dụ: "điền email abc@xyz.com vào ô email" → dien_form_browser("email", "abc@xyz.com")

        Args:
            label_or_placeholder: text label hoặc placeholder của ô (vd "Email", "Tìm kiếm")
            gia_tri: giá trị cần điền
        """
        if err := _check():
            return err
        page = _browser_state.get("page")
        if not page:
            return "Chưa có browser Playwright."
        try:
            try:
                page.get_by_label(label_or_placeholder).first.fill(gia_tri, timeout=5000)
            except Exception:
                page.get_by_placeholder(label_or_placeholder).first.fill(gia_tri, timeout=5000)
            return f"Đã điền '{gia_tri}' vào '{label_or_placeholder}'."
        except Exception as e:
            return f"Không điền được: {str(e)[:150]}"

    @mcp.tool()
    def lay_noi_dung_trang_browser(max_chars: int = 2000) -> str:
        """Lấy nội dung text của trang web đang mở (đã render JS).

        GỌI TOOL NÀY KHI người dùng nói: "lấy nội dung trang", "đọc nội dung",
        "scrape data", "trang này nói gì".

        Args:
            max_chars: giới hạn ký tự (mặc định 2000)
        """
        if err := _check():
            return err
        page = _browser_state.get("page")
        if not page:
            return "Chưa có browser Playwright."
        try:
            text = page.evaluate("() => document.body.innerText")
            text = text.strip()
            if len(text) > max_chars:
                text = text[:max_chars] + "..."
            return _reply(f"Nội dung trang ({page.url}):\n\n{text}")
        except Exception as e:
            return f"Lỗi lấy nội dung: {str(e)[:150]}"

    @mcp.tool()
    def cuon_trang_browser(huong: str = "xuong") -> str:
        """Cuộn trang web đang mở (Playwright).

        GỌI TOOL NÀY KHI người dùng nói: "cuộn xuống", "cuộn lên" trong context browser.
        Args:
            huong: "xuong" hoặc "len"
        """
        if err := _check():
            return err
        page = _browser_state.get("page")
        if not page:
            return "Chưa có browser Playwright."
        try:
            if huong.lower() in ("xuong", "down"):
                page.evaluate("window.scrollBy(0, 800)")
            else:
                page.evaluate("window.scrollBy(0, -800)")
            return f"Đã cuộn {huong}."
        except Exception as e:
            return f"Lỗi: {str(e)[:100]}"

    @mcp.tool()
    def dong_browser_playwright() -> str:
        """Đóng phiên trình duyệt Playwright hiện tại.

        GỌI TOOL NÀY KHI người dùng nói: "đóng browser", "tắt Chromium",
        "kết thúc duyệt web".
        """
        if err := _check():
            return err
        _close_browser()
        return "Đã đóng browser Playwright."
