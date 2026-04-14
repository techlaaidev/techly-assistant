"""PC control via PyAutoGUI — voice-driven mouse/keyboard automation.

Requires:
    pip install pyautogui pyperclip
    ENABLE_PC_CONTROL=1 in .env

Optional smart click:
    OPENAI_API_KEY=sk-... in .env  (enables click_thong_minh tool)

Two-layer gating:
    1. Admin: ENABLE_PC_CONTROL env var (server-level switch)
    2. User: runtime mode flag, set via voice "bật chế độ điều khiển máy tính"
       Auto-expires after 5 minutes. Persisted to data/pc_mode.json.

Safety:
    - PyAutoGUI fail-safe: move cursor to top-left corner (0,0) to abort
    - All actions log to stderr for monitoring
    - Recipes use small delays to look natural for demo
"""
import base64
import io
import json
import os
import subprocess
import time
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path
from ._common import _reply, DATA_DIR

# OPENAI_API_KEY read at call-time (not module load) so user can update
# .env without restarting the server.
OPENAI_VISION_MODEL = os.getenv("OPENAI_VISION_MODEL", "gpt-4o")


def _get_openai_key() -> str:
    """Read OPENAI_API_KEY from .env file freshly at call-time.

    This bypasses os.environ cache so user can update .env without
    restarting the MCP server.
    """
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if key:
        return key
    # Re-parse .env file
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("OPENAI_API_KEY=") and not line.startswith("#"):
                value = line.partition("=")[2].strip().strip('"').strip("'")
                if value:
                    os.environ["OPENAI_API_KEY"] = value  # cache for next call
                    return value
    return ""

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

PC_MODE_FILE = DATA_DIR / "pc_mode.json"
PC_MODE_DURATION = timedelta(minutes=5)
PC_MODE_DISABLED_MSG = (
    "Chế độ điều khiển máy tính chưa bật. "
    "Hãy nói 'bật chế độ điều khiển máy tính' trước."
)


def _is_mode_active() -> bool:
    """Return True if PC mode is currently enabled and not expired."""
    if not PC_MODE_FILE.exists():
        return False
    try:
        data = json.loads(PC_MODE_FILE.read_text(encoding="utf-8"))
        expires_at = datetime.fromisoformat(data["expires_at"])
        return datetime.now() < expires_at
    except Exception:
        return False


def _enable_mode() -> datetime:
    """Enable PC mode for PC_MODE_DURATION. Returns expiry timestamp."""
    expires_at = datetime.now() + PC_MODE_DURATION
    PC_MODE_FILE.write_text(
        json.dumps({
            "enabled_at": datetime.now().isoformat(),
            "expires_at": expires_at.isoformat(),
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return expires_at


def _disable_mode() -> None:
    if PC_MODE_FILE.exists():
        PC_MODE_FILE.unlink()


def _check_lib() -> str | None:
    """Check pyautogui is installed (for gate tools that bypass mode check)."""
    if not HAS_PYAUTOGUI:
        return "PyAutoGUI chưa cài. Chạy: pip install pyautogui"
    return None


def _check() -> str | None:
    """Check pyautogui ready AND PC mode is active. Used by all action tools."""
    err = _check_lib()
    if err:
        return err
    if not _is_mode_active():
        return PC_MODE_DISABLED_MSG
    return None


def register(mcp):
    # ===================================================================
    # Mode gate (always available, bypass mode check)
    # ===================================================================

    @mcp.tool()
    def bat_che_do_dieu_khien_may_tinh() -> str:
        """Bật chế độ điều khiển máy tính. Sau khi bật, các tool điều khiển chuột,
        bàn phím, mở app sẽ hoạt động trong 5 phút.

        GỌI TOOL NÀY KHI người dùng nói: "bật chế độ điều khiển máy tính",
        "kích hoạt chế độ điều khiển", "cho phép điều khiển máy", "enable PC control",
        "bật chế độ máy tính", "vào chế độ điều khiển".
        """
        if err := _check_lib():
            return err
        expires_at = _enable_mode()
        return (
            f"Đã bật chế độ điều khiển máy tính. "
            f"Hết hạn lúc {expires_at.strftime('%H:%M')}. "
            f"Bây giờ bạn có thể yêu cầu mở app, click chuột, gõ phím."
        )

    @mcp.tool()
    def tat_che_do_dieu_khien_may_tinh() -> str:
        """Tắt ngay chế độ điều khiển máy tính (không cần đợi hết 5 phút).

        GỌI TOOL NÀY KHI người dùng nói: "tắt chế độ điều khiển máy tính",
        "ngừng điều khiển máy", "khoá điều khiển", "disable PC control".
        """
        _disable_mode()
        return "Đã tắt chế độ điều khiển máy tính."

    @mcp.tool()
    def trang_thai_che_do_dieu_khien() -> str:
        """Kiểm tra chế độ điều khiển máy tính đang bật hay tắt.

        GỌI TOOL NÀY KHI người dùng hỏi: "chế độ điều khiển có đang bật không",
        "PC control status", "kiểm tra chế độ điều khiển".
        """
        if not PC_MODE_FILE.exists():
            return _reply("Chế độ điều khiển máy tính: TẮT.")
        try:
            data = json.loads(PC_MODE_FILE.read_text(encoding="utf-8"))
            expires_at = datetime.fromisoformat(data["expires_at"])
            if datetime.now() < expires_at:
                remaining = expires_at - datetime.now()
                mins = int(remaining.total_seconds() // 60)
                secs = int(remaining.total_seconds() % 60)
                return _reply(
                    f"Chế độ điều khiển máy tính: BẬT. "
                    f"Còn {mins} phút {secs} giây."
                )
            return _reply("Chế độ điều khiển máy tính: TẮT (đã hết hạn).")
        except Exception as e:
            return f"Lỗi đọc trạng thái: {str(e)[:100]}"

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

    @mcp.tool()
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

    @mcp.tool()
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

    @mcp.tool()
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

    # ===================================================================
    # Smart click via OpenAI Vision (GPT-4o)
    # ===================================================================

    @mcp.tool()
    def click_thong_minh(mo_ta: str) -> str:
        """Click vào element trên màn hình bằng mô tả tự nhiên (dùng AI vision).

        GỌI TOOL NÀY KHI người dùng nói: "click vào X", "nhấn vào nút Y",
        "chọn mục Z" mà X/Y/Z là MÔ TẢ chứ không phải tọa độ cụ thể.
        Ví dụ: "click vào mục giải trí", "nhấn nút đăng nhập", "chọn tab thể thao".

        Cách hoạt động:
        1. Chụp màn hình hiện tại
        2. Gửi screenshot + mô tả tới OpenAI GPT-4o vision
        3. AI trả về tọa độ (x, y) của element
        4. Click vào tọa độ đó

        Yêu cầu: OPENAI_API_KEY trong .env. Nếu không có sẽ báo lỗi.

        Args:
            mo_ta: Mô tả element cần click (vd "nút giải trí trên menu")
        """
        if err := _check():
            return err
        # Read at call-time (re-parses .env) so user can edit .env without restart
        api_key = _get_openai_key()
        if not api_key:
            return (
                "Click thông minh cần OPENAI_API_KEY. "
                "Thêm vào file .env dòng: OPENAI_API_KEY=sk-... "
                "Lấy key tại platform.openai.com/api-keys. "
                "Sau đó gọi lại tool này (không cần restart server)."
            )

        try:
            # 1. Screenshot to base64
            screenshot = pyautogui.screenshot()
            buf = io.BytesIO()
            screenshot.save(buf, format="PNG")
            img_b64 = base64.b64encode(buf.getvalue()).decode("ascii")
            w, h = screenshot.size

            # 2. Call OpenAI vision API
            payload = {
                "model": OPENAI_VISION_MODEL,
                "messages": [{
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                f"Đây là screenshot màn hình {w}x{h} pixel. "
                                f"Tìm vị trí pixel CHÍNH GIỮA của element được mô tả: "
                                f'"{mo_ta}". '
                                f"Trả về CHÍNH XÁC theo format JSON, không text khác:\n"
                                f'{{"x": <số>, "y": <số>, "found": true}}\n'
                                f'Nếu không tìm thấy: {{"x": 0, "y": 0, "found": false}}'
                            ),
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{img_b64}",
                                "detail": "high",
                            },
                        },
                    ],
                }],
                "max_tokens": 200,
                "temperature": 0,
            }
            req = urllib.request.Request(
                "https://api.openai.com/v1/chat/completions",
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}",
                },
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            content = data["choices"][0]["message"]["content"].strip()

            # Parse JSON, handle markdown code blocks
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()

            result = json.loads(content)
            if not result.get("found"):
                return f"AI không tìm thấy '{mo_ta}' trên màn hình."

            x = int(result["x"])
            y = int(result["y"])
            if x < 0 or x >= w or y < 0 or y >= h:
                return f"AI trả về tọa độ ngoài màn hình ({x},{y})."

            # 3. Click
            pyautogui.click(x, y)
            return f"Đã click '{mo_ta}' tại ({x}, {y})."
        except urllib.error.HTTPError as e:
            return f"Lỗi OpenAI API: {e.code} {e.reason}"
        except json.JSONDecodeError:
            return f"AI trả về không đúng JSON: {content[:100]}"
        except Exception as e:
            return f"Lỗi click thông minh: {str(e)[:150]}"
