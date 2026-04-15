# Voice commands examples — Techly Assistant

Danh sách câu hỏi mẫu cho từng tool. Dùng để test ESP32 voice assistant qua Xiaozhi.

Mỗi tool có **3-5 cách hỏi** khác nhau — LLM nên gọi đúng tool bất kể cách diễn đạt.

---

## 🏢 Company data (6 tools, always-on)

### `lay_doanh_thu`
- "Doanh thu công ty tháng này"
- "Doanh thu tháng ba bao nhiêu"
- "Công ty lời được bao nhiêu"
- "Cho anh xem doanh số năm nay"
- "Tình hình doanh thu thế nào"

### `lay_don_hang`
- "Hôm nay có bao nhiêu đơn"
- "Đơn hàng thế nào"
- "Đã giao được bao nhiêu đơn rồi"
- "Còn bao nhiêu đơn đang xử lý"
- "Thống kê đơn hàng hôm nay"

### `lay_thong_tin_cong_ty`
- "Công ty mình tên gì"
- "Địa chỉ công ty ở đâu"
- "Cho anh số hotline"
- "Website công ty là gì"
- "Công ty có bao nhiêu nhân viên"

### `lay_khach_hang_vip`
- "Danh sách khách VIP"
- "Ai là khách hàng chi tiêu nhiều nhất"
- "Top 5 khách hàng lớn"
- "Khách hàng quan trọng là ai"

### `lay_san_pham_ban_chay`
- "Sản phẩm nào bán chạy nhất"
- "Mặt hàng hot là gì"
- "Bán được nhiều nhất là sản phẩm nào"
- "Top sản phẩm bestseller"

### `lay_lich_hop`
- "Tuần này có họp gì"
- "Lịch họp của công ty"
- "Thứ hai có họp không"
- "Cuộc họp sắp tới"

---

## ⏰ Time / Weather (2 tools, always-on)

### `lay_thoi_gian_hien_tai`
- "Mấy giờ rồi"
- "Bây giờ là mấy giờ"
- "Hôm nay thứ mấy"
- "Ngày bao nhiêu rồi"

### `lay_thoi_tiet`
- "Thời tiết Hà Nội"
- "Sài Gòn hôm nay có nóng không"
- "Đà Nẵng có mưa không"
- "Nhiệt độ ngoài trời"
- "Thời tiết Huế thế nào"

---

## 📝 Notes / Calculator (4 tools, always-on)

### `ghi_chu`
- "Ghi chú mai họp 9 giờ sáng"
- "Nhắc anh mua sữa"
- "Lưu lại số điện thoại 0901234567"
- "Note là phải gọi cho sếp"

### `doc_ghi_chu`
- "Đọc ghi chú của anh"
- "Anh đã ghi gì rồi"
- "Xem note"
- "Các ghi chú đã lưu"

### `xoa_ghi_chu`
- "Xóa hết ghi chú"
- "Dọn ghi chú đi"
- "Clear note"

### `tinh_toan`
- "100 chia 4 bằng bao nhiêu"
- "2 cộng 3 nhân 4"
- "Tính giúp anh 500 trừ 125"
- "(100 - 20) chia 4 là mấy"

---

## 📰 News (2 tools, always-on)

### `lay_tin_moi_nhat`
- "Tin mới nhất"
- "Có tin gì mới không"
- "Đọc tin thời sự"
- "Tin hôm nay"

### `doc_bao`
- "Đọc báo VnExpress"
- "Tin tức Tuổi Trẻ"
- "Có gì mới trên Thanh Niên"
- "Đọc VietnamNet"

---

## 💰 Finance (4 tools, always-on)

### `lay_ty_gia`
- "Tỷ giá đô hôm nay"
- "1 USD bằng bao nhiêu tiền Việt"
- "Tỷ giá euro"
- "Giá đô la"
- "1 yen nhật bao nhiêu"

### `gia_vang_sjc`
- "Giá vàng hôm nay"
- "Vàng SJC bao nhiêu"
- "Giá vàng SJC bán ra"

### `gia_co_phieu`
- "Giá VCB"
- "Chứng khoán FPT"
- "Mã HPG hôm nay"
- "Cổ phiếu Vingroup"
- "VIC bao nhiêu"

### `vnindex_hien_tai`
- "VN-Index hôm nay"
- "Chỉ số chứng khoán"
- "Thị trường hôm nay thế nào"

---

## 🌐 Wiki / Translate (2 tools, always-on)

### `tim_wiki`
- "Hồ Chí Minh là ai"
- "Einstein là ai"
- "Thuyết tương đối là gì"
- "Nói về Việt Nam"
- "Giải thích photosynthesis"

### `dich`
- "Dịch 'chào buổi sáng' sang tiếng Anh"
- "Dịch 'good morning' sang tiếng Việt"
- "'Cám ơn' trong tiếng Anh là gì"
- "Dịch 'how are you' nghĩa là gì"

---

## ⏱️ Reminder (3 tools, always-on)

### `them_nhac`
- "Nhắc anh 3 giờ chiều họp với sếp"
- "Nhắc 20 phút nữa uống nước"
- "Nhắc 9 giờ sáng mai gọi khách hàng"
- "Nhắc anh thứ 6 đi gặp đối tác"

### `xem_nhac_sap_toi`
- "Có nhắc gì không"
- "Xem các lời nhắc"
- "Sắp tới có gì"
- "Nhắc sắp tới"

### `xoa_nhac`
- "Xóa nhắc số 1"
- "Bỏ lời nhắc số 3"

---

## 💸 Expense (3 tools, always-on)

### `ghi_chi_tieu`
- "Tiêu 50 nghìn cà phê"
- "Hôm nay tiêu 100 nghìn ăn trưa"
- "Mua đồ 200 nghìn"
- "Chi 500 nghìn đổ xăng"

### `tong_chi_thang`
- "Tháng này tiêu bao nhiêu"
- "Tổng chi tháng 3"
- "Em đã tiêu bao nhiêu tiền"

### `bao_cao_chi_tieu`
- "Báo cáo chi tiêu"
- "Tiêu nhiều nhất vào gì"
- "Thống kê chi tiêu"
- "Phân tích chi tiêu tháng này"

---

## 📚 Knowledge base (2 tools, always-on)

### `tim_trong_tai_lieu`
- "Chính sách nghỉ phép thế nào"
- "Quy trình onboarding nhân viên mới"
- "Công ty cho nghỉ bao nhiêu ngày phép"
- "Ngày đầu đi làm phải làm gì"
- "Cách xin nghỉ ốm"

### `liet_ke_tai_lieu`
- "Có những tài liệu gì"
- "List tài liệu nội bộ"
- "Kho tri thức có gì"

---

## 🧠 Memory — persistent (4 tools, always-on)

### `nho_thong_tin`
- "Nhớ là anh thích cà phê đen"
- "Ghi nhớ là dự án X sẽ launch ngày 15/5"
- "Đặc điểm của sếp là thích đúng giờ"
- "Nhớ giúp anh rằng con của anh tên Minh"

### `nho_lai`
- "Anh đã nói gì về cà phê"
- "Nhớ lại về dự án X"
- "Trước đây anh nói gì về sếp"

### `liet_ke_thuc_the`
- "Đã nhớ những gì"
- "List memory"
- "Biết những ai"

### `quen_thuc_the`
- "Quên thông tin về X"
- "Xóa bộ nhớ về dự án cũ"

---

## 📁 File ops (4 tools, always-on)

### `liet_ke_file`
- "Có file gì trong thư mục"
- "List file của anh"
- "Xem file đã lưu"

### `doc_file`
- "Đọc file ghi_chu.txt"
- "Nội dung của file notes.md"

### `viet_file`
- "Lưu vào file test.txt nội dung 'Hello'"
- "Tạo file meeting-note với nội dung X"

### `xoa_file`
- "Xóa file test.txt"
- "Delete file cũ"

---

## 🔗 URL fetch (1 tool, always-on)

### `doc_trang_web`
- "Đọc trang https://vnexpress.net"
- "Lấy nội dung URL https://example.com"
- "Tóm tắt bài viết tại [URL]"

---

## 🗄️ Database (2 tools, always-on)

### `truy_van_db`
- "SELECT * FROM customers LIMIT 5"
- "Query database lấy top 10 đơn hàng"
- "Chạy câu SELECT name FROM users"

### `liet_ke_bang_db`
- "Database có những bảng gì"
- "List tables"
- "Schema của DB"

---

## 🏠 Home Assistant (env-gated, 5 tools)

Cần `HA_URL` + `HA_TOKEN` trong `.env`.

### `dieu_khien_thiet_bi`
- "Bật đèn phòng khách"
- "Tắt quạt"
- "Mở điều hoà phòng ngủ"
- "Tắt TV"

### `trang_thai_thiet_bi`
- "Đèn phòng khách đang bật hay tắt"
- "Nhiệt độ điều hoà"
- "Quạt đang ở chế độ gì"

### `dat_nhiet_do`
- "Điều hoà phòng ngủ 25 độ"
- "Hạ lạnh xuống 22 độ"
- "Nhiệt độ AC 26"

### `dat_do_sang`
- "Đèn phòng khách 50%"
- "Giảm đèn còn 30%"
- "Tăng đèn lên max"

### `liet_ke_thiet_bi`
- "Nhà có thiết bị gì"
- "List đèn"
- "Có bao nhiêu thiết bị smart home"

---

## 📅 Google Calendar (env-gated, 3 tools)

Cần `GOOGLE_ACCESS_TOKEN` trong `.env`.

### `xem_lich_hom_nay`
- "Lịch hôm nay"
- "Có cuộc hẹn nào hôm nay"
- "Meeting hôm nay"
- "Hôm nay có gì không"

### `xem_lich_trong_tuan`
- "Lịch tuần này"
- "Tuần này có gì"
- "Các sự kiện sắp tới"

### `them_su_kien`
- "Thêm meeting 3 giờ chiều mai"
- "Lên lịch họp với team 9 giờ sáng thứ 6"
- "Schedule meeting với khách hàng 2 giờ chiều"

---

## 🔍 Brave Search (env-gated)

Cần `BRAVE_API_KEY`.

### `tim_kiem_web`
- "Tìm trên web về Vingroup"
- "Search Google về AI 2026"
- "Tra cứu thông tin về Elon Musk"
- "Tìm trên mạng về Python 3.13"

---

## 🕷️ Apify scraper (env-gated)

Cần `APIFY_TOKEN`.

### `tim_kiem_google_apify`
- "Scrape Google tìm top quán phở Hà Nội"
- "Search Google chi tiết về X"

### `chay_apify_actor`
- "Chạy actor scrape Instagram của user abc"
- "Run apify để scrape Facebook posts"

---

## 📖 Notion (env-gated)

Cần `NOTION_TOKEN`.

### `tim_trong_notion`
- "Tìm trong Notion về OKR Q2"
- "Notion có gì về dự án X"
- "Search Notion từ khóa meeting"

---

## 🐙 GitHub (env-gated)

Cần `GITHUB_TOKEN` + `GITHUB_REPO`.

### `lay_pull_request_dang_mo`
- "PR nào đang chờ review"
- "Có PR mới không"
- "Danh sách pull request"

### `lay_issue_moi_nhat`
- "Issue mới trên GitHub"
- "Có bug nào không"
- "List issue đang mở"

### `lay_commit_gan_day`
- "Ai vừa commit"
- "Commit mới nhất"
- "Thay đổi gần đây trên repo"

---

## 💬 Slack (env-gated)

Cần `SLACK_BOT_TOKEN`.

### `gui_tin_nhan_slack`
- "Gửi Slack 'meeting 3 giờ chiều'"
- "Post vào channel general rằng sắp họp"
- "Thông báo team qua Slack"

### `doc_tin_nhan_slack_gan_day`
- "Slack có gì mới"
- "Tin nhắn mới trong channel"
- "Đọc Slack"

---

## ✈️ Telegram (env-gated)

Cần `TELEGRAM_BOT_TOKEN`.

### `gui_telegram`
- "Gửi Telegram 'đang về nhà'"
- "Nhắn Telegram cho vợ rằng sắp về"
- "Thông báo qua Telegram"

### `doc_tin_nhan_telegram`
- "Telegram có gì mới"
- "Tin nhắn bot mới"
- "Đọc Telegram"

---

## ⏰ Scheduler — proactive Telegram notifications (env-gated, 3 tools)

Cần `ENABLE_SCHEDULER=1` + `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID`. Khác `reminder` thường: tool này **đẩy thông báo chủ động** xuống điện thoại qua Telegram bot, không cần hỏi lại.

### `dat_lich_nhac_chu_dong`
- "Nhắc tôi uống nước sau 30 phút"
- "Thông báo cho tôi đi họp sau 15 phút"
- "Đặt lịch nhắc 2 tiếng nữa gọi khách hàng"
- "Nhắc anh sau 1 tuần kiểm tra báo cáo"

### `xem_lich_nhac_chu_dong`
- "Có nhắc nhở nào không"
- "Xem các thông báo đã đặt"
- "Lịch nhắc chủ động đang chờ"

### `xoa_lich_nhac_chu_dong`
- "Hủy lịch nhắc a1b2c3d4"
- "Xóa thông báo 12345678"
- "Bỏ lịch nhắc [mã]"

---

## 🖥️ PC Control — PyAutoGUI automation (env-gated, 18 tools)

Cần `ENABLE_PC_CONTROL=1` + `pip install pyautogui pyperclip`. Fail-safe: chuột về (0,0) để abort.

### Mouse / Keyboard
- "Click chuột" → `click_chuot`
- "Click đúp" / "Double click" → `double_click`
- "Click phải" → `click_phai`
- "Di chuột sang 500 300" → `move_chuot`
- "Cuộn xuống" / "Cuộn lên 5 lần" → `cuon_man_hinh`
- "Gõ chữ hello world" → `go_chu`
- "Dán chữ: chào buổi sáng" (tiếng Việt có dấu) → `dan_text`
- "Nhấn enter" / "Nhấn tab" → `nhan_phim`
- "Ctrl C" / "Ctrl V" / "Alt Tab" → `phim_tat`

### Screen info
- "Kích thước màn hình" → `kich_thuoc_man_hinh`
- "Vị trí chuột hiện tại" → `vi_tri_chuot_hien_tai`
- "Chụp màn hình" → `chup_man_hinh`

### Launch apps
- "Mở Chrome" / "Mở Chrome vào youtube.com" → `mo_chrome`
- "Mở Chrome ẩn danh" → `mo_chrome_an_danh`
- "Mở Notepad" → `mo_notepad`
- "Mở app Spotify" / "Mở Zalo" → `mo_app`
- "Mở trình duyệt google.com" → `mo_trinh_duyet`
- "Tìm Google về Vingroup" → `tim_kiem_google`

---

## 🌐 Browser Playwright (env-gated, 6 tools)

Cần `ENABLE_BROWSER_PLAYWRIGHT=1` + `pip install playwright` + `python -m playwright install chromium`. Dùng Chromium thật (không phải PyAutoGUI). Hỗ trợ semantic click bằng text.

### `mo_chrome_playwright`
- "Vào trang vnexpress.net"
- "Mở https://google.com bằng Playwright"

### `click_chu_trong_browser`
- "Click vào chữ 'Tin mới nhất'"
- "Bấm nút Đăng nhập"
- "Click link Liên hệ"

### `dien_form_browser`
- "Điền email 'abc@gmail.com'"
- "Điền ô tìm kiếm 'Python tutorial'"

### `lay_noi_dung_trang_browser`
- "Đọc nội dung trang này"
- "Lấy text trang hiện tại"

### `cuon_trang_browser`
- "Cuộn trang xuống"
- "Cuộn lên đầu trang"

### `dong_browser_playwright`
- "Đóng trình duyệt"
- "Đóng Playwright"

---

## 🎯 Tips để test hiệu quả

1. **Hỏi natural** — không cần nhớ đúng tên tool, nói tự nhiên
2. **Kiểm tra log `mcp_pipe.py`** để thấy LLM có gọi đúng tool không
3. **Nếu LLM gọi sai tool** → thêm trigger phrase vào docstring
4. **Nếu LLM không gọi tool** → tool description chưa đủ rõ
5. **Câu ngắn gọn** dễ trigger hơn câu dài lòng vòng

## 🔧 Debug

Nếu câu hỏi không trigger tool đúng:

1. Xem log `📨 Xiaozhi → MCP: {"method":"tools/call","params":{"name":"???"}}`
2. Nếu không thấy `tools/call` → LLM không chọn tool nào → cần verbose description hơn
3. Nếu chọn sai tool → cần thêm trigger phrases cụ thể
4. Nếu tool trả data nhưng LLM nói "không tìm thấy" → cần fix data format (empty vs explicit message)
