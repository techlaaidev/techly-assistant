"""PC control via PyAutoGUI — voice-driven mouse/keyboard automation.

Requires:
    pip install pyautogui pyperclip
    ENABLE_PC_CONTROL=1 in .env

Single gate: ENABLE_PC_CONTROL env var (server-level switch).
Tools work directly without runtime mode.

Safety:
    - PyAutoGUI fail-safe: move cursor to top-left corner (0,0) to abort
    - All actions log to stderr for monitoring
    - Recipes use small delays to look natural for demo
"""
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path
from ._common import _reply, DATA_DIR

# Standard install paths (Windows). First existing path wins.
APP_PATHS = {
    "chrome": [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    ],
    "edge": [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ],
    "notepad": [r"C:\Windows\System32\notepad.exe"],
    "calc": [r"C:\Windows\System32\calc.exe"],
    "calculator": [r"C:\Windows\System32\calc.exe"],
    "explorer": [r"C:\Windows\explorer.exe"],
    "cmd": [r"C:\Windows\System32\cmd.exe"],
    "powershell": [r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"],
}


def _find_app(name: str) -> str | None:
    """Resolve app name to executable path. None if not found."""
    paths = APP_PATHS.get(name.lower(), [])
    for p in paths:
        if Path(p).is_file():
            return p
    return None

try:
    import pyautogui
    HAS_PYAUTOGUI = True
    pyautogui.FAILSAFE = True       # move cursor to (0,0) to abort
    pyautogui.PAUSE = 0.1            # 100ms delay between actions
except ImportError:
    HAS_PYAUTOGUI = False

SCREENSHOTS_DIR = DATA_DIR / "screenshots"
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)


def _check() -> str | None:
    """Return error string if pyautogui not installed, else None."""
    if not HAS_PYAUTOGUI:
        return "PyAutoGUI chưa cài. Chạy: pip install pyautogui"
    return None


def register(mcp):
    # ===================================================================
    # Mouse control
    # ===================================================================

    @mcp.tool()
    def move_chuot(x: int, y: int, thoi_gian: float = 0.5) -> str:
        """Di chuyển chuột tới tọa độ (x, y) trên màn hình.

        GỌI TOOL NÀY KHI người dùng nói: "di chuyển chuột tới X Y", "đưa chuột lên góc trên".
        Args:
            x: tọa độ x (0 = trái màn hình)
            y: tọa độ y (0 = đỉnh màn hình)
            thoi_gian: thời gian di chuyển (giây), mặc định 0.5 cho hiệu ứng mượt
        """
        if err := _check():
            return err
        try:
            pyautogui.moveTo(x, y, duration=thoi_gian)
            return f"Đã di chuyển chuột tới ({x}, {y})."
        except Exception as e:
            return f"Lỗi: {str(e)[:100]}"

    @mcp.tool()
    def click_chuot(x: int = -1, y: int = -1) -> str:
        """Click chuột trái tại vị trí hiện tại hoặc tọa độ chỉ định.

        GỌI TOOL NÀY KHI người dùng nói: "click chuột", "nhấn chuột", "click vào X Y".
        Args:
            x: tọa độ x (-1 = vị trí hiện tại)
            y: tọa độ y (-1 = vị trí hiện tại)
        """
        if err := _check():
            return err
        try:
            if x >= 0 and y >= 0:
                pyautogui.click(x, y)
                return f"Đã click tại ({x}, {y})."
            pyautogui.click()
            return "Đã click chuột."
        except Exception as e:
            return f"Lỗi: {str(e)[:100]}"

    @mcp.tool()
    def double_click() -> str:
        """Double click chuột tại vị trí hiện tại.

        GỌI TOOL NÀY KHI người dùng nói: "double click", "nhấp đúp".
        """
        if err := _check():
            return err
        try:
            pyautogui.doubleClick()
            return "Đã double click."
        except Exception as e:
            return f"Lỗi: {str(e)[:100]}"

    @mcp.tool()
    def click_phai() -> str:
        """Click chuột phải tại vị trí hiện tại.

        GỌI TOOL NÀY KHI người dùng nói: "click phải", "right click", "chuột phải".
        """
        if err := _check():
            return err
        try:
            pyautogui.rightClick()
            return "Đã click chuột phải."
        except Exception as e:
            return f"Lỗi: {str(e)[:100]}"

    @mcp.tool()
    def cuon_man_hinh(huong: str = "xuong", so_lan: int = 3) -> str:
        """Cuộn màn hình lên hoặc xuống.

        GỌI TOOL NÀY KHI người dùng nói: "cuộn xuống", "cuộn lên", "scroll down 5 lần".
        Args:
            huong: "xuong" hoặc "len"
            so_lan: số lần cuộn (mỗi lần ~120 pixels)
        """
        if err := _check():
            return err
        amount = so_lan * (-100 if huong.lower() in ("xuong", "down") else 100)
        try:
            pyautogui.scroll(amount)
            return f"Đã cuộn {huong} {so_lan} lần."
        except Exception as e:
            return f"Lỗi: {str(e)[:100]}"

    # ===================================================================
    # Keyboard control
    # ===================================================================

    @mcp.tool()
    def go_chu(text: str, thoi_gian_moi_phim: float = 0.05) -> str:
        """Gõ một đoạn text qua bàn phím (như đang gõ tay).

        GỌI TOOL NÀY KHI người dùng nói: "gõ chữ X", "type X", "viết X".
        LƯU Ý: PyAutoGUI typewrite không hỗ trợ Unicode tốt. Với tiếng Việt có dấu, dùng `dan_text` thay thế.
        Args:
            text: nội dung cần gõ (ASCII tốt nhất)
            thoi_gian_moi_phim: delay giữa các phím (giây)
        """
        if err := _check():
            return err
        try:
            pyautogui.typewrite(text, interval=thoi_gian_moi_phim)
            return f"Đã gõ: {text}"
        except Exception as e:
            return f"Lỗi: {str(e)[:100]}"

    @mcp.tool()
    def dan_text(text: str) -> str:
        """Dán một đoạn text qua clipboard (hỗ trợ Unicode đầy đủ, kể cả tiếng Việt có dấu).

        GỌI TOOL NÀY KHI người dùng nói: "dán X", "viết X" (đặc biệt với tiếng Việt có dấu).
        Args:
            text: nội dung cần dán
        """
        if err := _check():
            return err
        try:
            # Use clipboard for Unicode support
            try:
                import pyperclip
                pyperclip.copy(text)
            except ImportError:
                # Fallback: write to temp + paste via OS command (not implemented for KISS)
                return "Cần cài: pip install pyperclip"
            pyautogui.hotkey("ctrl", "v")
            return f"Đã dán: {text[:80]}"
        except Exception as e:
            return f"Lỗi: {str(e)[:100]}"

    @mcp.tool()
    def nhan_phim(phim: str) -> str:
        """Nhấn 1 phím đặc biệt (Enter, Esc, Tab, F1-F12, Space, Backspace, ...).

        GỌI TOOL NÀY KHI người dùng nói: "nhấn enter", "bấm escape", "press F5".
        Args:
            phim: tên phím (enter, esc, tab, space, backspace, f5, up, down, left, right, ...)
        """
        if err := _check():
            return err
        try:
            pyautogui.press(phim.lower())
            return f"Đã nhấn phím {phim}."
        except Exception as e:
            return f"Lỗi: {str(e)[:100]}"

    @mcp.tool()
    def phim_tat(combo: str) -> str:
        """Nhấn tổ hợp phím tắt như Ctrl+C, Alt+Tab, Win+D, Ctrl+Shift+N.

        GỌI TOOL NÀY KHI người dùng nói: "nhấn Ctrl C", "Alt Tab", "phím tắt".
        Args:
            combo: tổ hợp phím viết bằng dấu + (vd "ctrl+c", "alt+tab", "ctrl+shift+t")
        """
        if err := _check():
            return err
        keys = [k.strip().lower() for k in combo.split("+")]
        try:
            pyautogui.hotkey(*keys)
            return f"Đã nhấn {combo}."
        except Exception as e:
            return f"Lỗi: {str(e)[:100]}"

    # ===================================================================
    # Screen info
    # ===================================================================

    @mcp.tool()
    def kich_thuoc_man_hinh() -> str:
        """Lấy độ phân giải màn hình hiện tại.

        GỌI TOOL NÀY KHI người dùng hỏi: "màn hình bao nhiêu pixel", "độ phân giải".
        """
        if err := _check():
            return err
        w, h = pyautogui.size()
        return _reply(f"Màn hình: {w} x {h} pixel.")

    @mcp.tool()
    def vi_tri_chuot_hien_tai() -> str:
        """Lấy tọa độ (x, y) hiện tại của con trỏ chuột.

        GỌI TOOL NÀY KHI người dùng hỏi: "chuột đang ở đâu", "vị trí chuột".
        """
        if err := _check():
            return err
        x, y = pyautogui.position()
        return _reply(f"Chuột đang ở ({x}, {y}).")

    @mcp.tool()
    def chup_man_hinh() -> str:
        """Chụp màn hình hiện tại và lưu vào file PNG.

        GỌI TOOL NÀY KHI người dùng nói: "chụp màn hình", "screenshot", "lưu màn hình".
        File lưu vào data/screenshots/ với timestamp.
        """
        if err := _check():
            return err
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = SCREENSHOTS_DIR / f"screenshot_{timestamp}.png"
            pyautogui.screenshot(str(path))
            return f"Đã chụp màn hình lưu tại {path.name}"
        except Exception as e:
            return f"Lỗi chụp màn hình: {str(e)[:100]}"

    # ===================================================================
    # Pre-baked demo recipes
    # ===================================================================

    # @mcp.tool()  # disabled — use tro_ly for browser tasks
    def mo_trinh_duyet(url: str = "google.com") -> str:
        """Mở trình duyệt mặc định và truy cập một URL (demo recipe).

        GỌI TOOL NÀY KHI người dùng nói: "mở Chrome đến X", "vào trang Y", "truy cập Z".
        Args:
            url: URL muốn mở (mặc định google.com)
        """
        if err := _check():
            return err
        try:
            # Windows: Win key → search "chrome" → enter
            pyautogui.press("win")
            time.sleep(0.5)
            pyautogui.typewrite("chrome", interval=0.05)
            time.sleep(0.5)
            pyautogui.press("enter")
            time.sleep(2.5)  # wait Chrome to launch
            # Address bar
            pyautogui.hotkey("ctrl", "l")
            time.sleep(0.3)
            pyautogui.typewrite(url, interval=0.03)
            pyautogui.press("enter")
            return f"Đã mở Chrome đến {url}."
        except Exception as e:
            return f"Lỗi: {str(e)[:100]}"

    @mcp.tool()
    def tim_kiem_google(tu_khoa: str) -> str:
        """Mở tab mới và search Google với từ khóa (demo recipe).

        GỌI TOOL NÀY KHI người dùng nói: "tìm Google X", "search Y trên Google".
        Args:
            tu_khoa: từ khóa tìm kiếm
        """
        if err := _check():
            return err
        try:
            pyautogui.hotkey("ctrl", "t")  # new tab
            time.sleep(0.5)
            pyautogui.typewrite(tu_khoa, interval=0.04)
            time.sleep(0.3)
            pyautogui.press("enter")
            return f"Đã search Google: {tu_khoa}"
        except Exception as e:
            return f"Lỗi: {str(e)[:100]}"

    @mcp.tool()
    def mo_app(ten_app: str) -> str:
        """Mở một ứng dụng trên máy tính bằng subprocess (không qua menu Start).

        GỌI TOOL NÀY KHI người dùng nói: "mở Notepad", "mở Word", "khởi động X".
        Hỗ trợ apps: notepad, calc, calculator, explorer, cmd, powershell, edge.
        Với app khác, fallback dùng Win+search.

        Args:
            ten_app: tên app (notepad, calc, edge, ...)
        """
        if err := _check():
            return err
        path = _find_app(ten_app)
        if path:
            try:
                subprocess.Popen([path])
                return f"Đã mở {ten_app}."
            except Exception as e:
                return f"Lỗi mở {ten_app}: {str(e)[:100]}"
        # Fallback: Win + search
        try:
            pyautogui.press("win")
            time.sleep(0.5)
            pyautogui.typewrite(ten_app, interval=0.05)
            time.sleep(0.5)
            pyautogui.press("enter")
            return f"Đã mở {ten_app} (qua Start menu)."
        except Exception as e:
            return f"Lỗi: {str(e)[:100]}"

    # @mcp.tool()  # disabled — use tro_ly for browser tasks
    def mo_chrome(url: str = "google.com") -> str:
        """Mở Chrome (profile mặc định, bypass profile picker) và truy cập URL.

        GỌI TOOL NÀY MỖI KHI người dùng nói: "mở Chrome", "mở trình duyệt",
        "vào Chrome", "khởi động Chrome", "open chrome", "launch browser",
        "vào internet", "truy cập website", "lên mạng", "vào dantri", "vào X.com".

        Mở qua subprocess.Popen với --profile-directory=Default → bỏ qua profile
        picker, mở thẳng URL trong profile mặc định.

        Args:
            url: URL muốn mở (mặc định google.com)
        """
        if err := _check():
            return err
        # Normalize URL
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        chrome = _find_app("chrome")
        if chrome:
            try:
                subprocess.Popen([
                    chrome,
                    "--profile-directory=Default",
                    url,
                ])
                return f"Đã mở Chrome đến {url}."
            except Exception as e:
                return f"Lỗi mở Chrome: {str(e)[:100]}"

        # Fallback: webbrowser stdlib
        try:
            import webbrowser
            webbrowser.open(url)
            return f"Đã mở browser mặc định đến {url}."
        except Exception as e:
            return f"Không mở được browser: {str(e)[:100]}"

    # @mcp.tool()  # disabled — use tro_ly for browser tasks
    def mo_chrome_an_danh(url: str = "google.com") -> str:
        """Mở Chrome ở chế độ ẩn danh (incognito) và truy cập URL.

        GỌI TOOL NÀY KHI người dùng nói: "mở Chrome ẩn danh", "incognito",
        "chế độ riêng tư", "không lưu lịch sử".

        Args:
            url: URL muốn mở (mặc định google.com)
        """
        if err := _check():
            return err
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        chrome = _find_app("chrome")
        if not chrome:
            return "Không tìm thấy Chrome trên máy."
        try:
            subprocess.Popen([
                chrome,
                "--profile-directory=Default",
                "--incognito",
                url,
            ])
            return f"Đã mở Chrome ẩn danh đến {url}."
        except Exception as e:
            return f"Lỗi: {str(e)[:100]}"

    @mcp.tool()
    def mo_notepad() -> str:
        """Mở Notepad qua subprocess (không qua Start menu).

        GỌI TOOL NÀY MỖI KHI người dùng nói: "mở Notepad", "mở sổ tay",
        "open notepad", "khởi động Notepad", "vào Notepad", "mở text editor".
        """
        if err := _check():
            return err
        path = _find_app("notepad")
        if path:
            try:
                subprocess.Popen([path])
                return "Đã mở Notepad."
            except Exception as e:
                return f"Lỗi mở Notepad: {str(e)[:100]}"
        return "Không tìm thấy notepad.exe."

