"""Browser automation via Playwright — semantic clicks by text/role.

Requires:
    pip install playwright
    python -m playwright install chromium
    ENABLE_BROWSER_PLAYWRIGHT=1 in .env

Uses async API (FastMCP runs tools in asyncio loop). Persistent browser
instance shared across tool calls. Each tool gates on PC mode.
"""
import re
from ._common import _reply
from . import pc_control  # for mode check

try:
    from playwright.async_api import async_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False

_browser_state = {
    "playwright": None,
    "browser": None,
    "page": None,
}


def _check() -> str | None:
    if not HAS_PLAYWRIGHT:
        return "Playwright chưa cài. Chạy: pip install playwright && python -m playwright install chromium"
    if not pc_control._is_mode_active():
        return pc_control.PC_MODE_DISABLED_MSG
    return None


async def _ensure_browser():
    """Lazy-init Playwright browser. Reuse if already running."""
    if _browser_state["browser"] is None:
        pw = await async_playwright().start()
        browser = await pw.chromium.launch(
            headless=False,
            args=["--start-maximized"],
        )
        page = await browser.new_page(no_viewport=True)
        _browser_state["playwright"] = pw
        _browser_state["browser"] = browser
        _browser_state["page"] = page
    return _browser_state["page"]


async def _close_browser():
    if _browser_state["browser"]:
        try:
            await _browser_state["browser"].close()
        except Exception:
            pass
    if _browser_state["playwright"]:
        try:
            await _browser_state["playwright"].stop()
        except Exception:
            pass
    _browser_state["browser"] = None
    _browser_state["playwright"] = None
    _browser_state["page"] = None


def register(mcp):
    @mcp.tool()
    async def mo_chrome_playwright(url: str = "https://google.com") -> str:
        """Mở trình duyệt Chromium qua Playwright và truy cập URL.

        GỌI TOOL NÀY KHI người dùng muốn duyệt web có khả năng tự động click,
        điền form, scrape data: "duyệt web", "scrape", "automation web".
        Khác với mo_chrome (chỉ launch), tool này tạo phiên Playwright control được.

        Args:
            url: URL muốn mở (mặc định google.com)
        """
        if err := _check():
            return err
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        try:
            page = await _ensure_browser()
            await page.goto(url, timeout=30000)
            return f"Đã mở Chromium qua Playwright đến {url}."
        except Exception as e:
            return f"Lỗi mở Playwright: {str(e)[:150]}"

    @mcp.tool()
    async def click_chu_trong_browser(text: str) -> str:
        """Click vào element có chứa text này trong trang Playwright đang mở.

        GỌI TOOL NÀY KHI người dùng nói: "click vào X", "nhấn vào Y" trong context
        đang duyệt web. CHỈ work nếu trước đó đã gọi mo_chrome_playwright.
        Ví dụ: "click vào mục giải trí", "nhấn nút đăng nhập".

        Tries multiple locator strategies in order: link role, button role,
        exact text match, partial text match.

        Args:
            text: text hiển thị của element cần click
        """
        if err := _check():
            return err
        page = _browser_state.get("page")
        if not page:
            return "Chưa có browser Playwright. Hãy gọi mo_chrome_playwright trước."

        text_re = re.compile(re.escape(text), re.IGNORECASE)
        text_upper = text.upper()

        # Locator strategies (order: most specific first)
        locator_strategies = [
            ("a:has-text", lambda: page.locator(f'a:has-text("{text}")')),
            ("a:has-text upper", lambda: page.locator(f'a:has-text("{text_upper}")')),
            ("button:has-text", lambda: page.locator(f'button:has-text("{text}")')),
            ("link role regex", lambda: page.get_by_role("link", name=text_re)),
            ("button role regex", lambda: page.get_by_role("button", name=text_re)),
            ("text regex", lambda: page.get_by_text(text_re)),
        ]

        last_error = ""
        for strat_name, get_locator in locator_strategies:
            try:
                locator = get_locator().locator("visible=true").first
                count = await locator.count()
                if count == 0:
                    continue

                # Method 1: normal click (after scroll into view)
                try:
                    await locator.scroll_into_view_if_needed(timeout=2000)
                except Exception:
                    pass
                try:
                    await locator.click(timeout=2000)
                    return f"Đã click '{text}' ({strat_name} → normal click)."
                except Exception as e:
                    last_error = str(e)[:100]

                # Method 2: JavaScript .click() — bypass overlays
                try:
                    await locator.evaluate("el => el.click()")
                    return f"Đã click '{text}' ({strat_name} → JS click)."
                except Exception as e:
                    last_error = str(e)[:100]

                # Method 3: if it's a link, navigate to its href directly
                try:
                    href = await locator.get_attribute("href")
                    if href and href.startswith(("http://", "https://", "/")):
                        if href.startswith("/"):
                            base = page.url.split("/")[0] + "//" + page.url.split("/")[2]
                            href = base + href
                        await page.goto(href, timeout=10000)
                        return f"Đã navigate đến '{text}' qua href: {href}"
                except Exception as e:
                    last_error = str(e)[:100]
            except Exception as e:
                last_error = str(e)[:100]
                continue

        return f"Không click được '{text}'. Lỗi cuối: {last_error}"

    @mcp.tool()
    async def dien_form_browser(label_or_placeholder: str, gia_tri: str) -> str:
        """Điền giá trị vào form input có label hoặc placeholder khớp.

        GỌI TOOL NÀY KHI người dùng nói: "điền X vào Y", "nhập Z vào ô tên".

        Args:
            label_or_placeholder: text label hoặc placeholder
            gia_tri: giá trị cần điền
        """
        if err := _check():
            return err
        page = _browser_state.get("page")
        if not page:
            return "Chưa có browser Playwright."
        try:
            try:
                await page.get_by_label(label_or_placeholder).first.fill(gia_tri, timeout=5000)
            except Exception:
                await page.get_by_placeholder(label_or_placeholder).first.fill(gia_tri, timeout=5000)
            return f"Đã điền '{gia_tri}' vào '{label_or_placeholder}'."
        except Exception as e:
            return f"Không điền được: {str(e)[:150]}"

    @mcp.tool()
    async def lay_noi_dung_trang_browser(max_chars: int = 2000) -> str:
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
            text = await page.evaluate("() => document.body.innerText")
            text = text.strip()
            if len(text) > max_chars:
                text = text[:max_chars] + "..."
            return _reply(f"Nội dung trang ({page.url}):\n\n{text}")
        except Exception as e:
            return f"Lỗi lấy nội dung: {str(e)[:150]}"

    @mcp.tool()
    async def cuon_trang_browser(huong: str = "xuong") -> str:
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
                await page.evaluate("window.scrollBy(0, 800)")
            else:
                await page.evaluate("window.scrollBy(0, -800)")
            return f"Đã cuộn {huong}."
        except Exception as e:
            return f"Lỗi: {str(e)[:100]}"

    @mcp.tool()
    async def dong_browser_playwright() -> str:
        """Đóng phiên trình duyệt Playwright hiện tại.

        GỌI TOOL NÀY KHI người dùng nói: "đóng browser", "tắt Chromium",
        "kết thúc duyệt web".
        """
        if err := _check():
            return err
        await _close_browser()
        return "Đã đóng browser Playwright."
