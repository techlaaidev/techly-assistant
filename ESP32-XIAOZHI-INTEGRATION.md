# ClawX + ESP32 Xiaozhi Integration Plan

> **Mục tiêu**: Biến miniPC ClawX thành "brain" cho ESP32 Xiaozhi - ESP32 là mic/loa/screen, miniPC xử lý AI.
>
> **Kết quả**: Buyer nói chuyện với ESP32 bằng giọng nói tiếng Việt, AI xử lý trên miniPC qua OpenClaw Gateway.

---

## 1. Tổng quan kiến trúc

```
┌──────────────────────────────────────────────────────────────────────┐
│                        MiniPC (4GB RAM)                              │
│                                                                      │
│  ┌─────────────────────┐         ┌──────────────────────────────┐   │
│  │ xiaozhi-esp32-server │         │ OpenClaw Gateway (port 18789)│   │
│  │ (Python, Docker)     │────────►│                              │   │
│  │                      │ OpenAI  │  Claude / DeepSeek / GPT     │   │
│  │ Port 8000: WebSocket │ compat  │  + Skills                    │   │
│  │ Port 8003: HTTP/OTA  │  API    │  + Memory                    │   │
│  │                      │         │  + Channels (WA/TG/Discord)  │   │
│  │ ┌─────────────────┐ │         └──────────────────────────────┘   │
│  │ │ VAD: SileroVAD  │ │                                            │
│  │ │ (local, ~50MB)  │ │         ┌──────────────────────────────┐   │
│  │ ├─────────────────┤ │         │ ClawX-Web (port 2003)        │   │
│  │ │ ASR: Whisper API│ │         │ Dashboard + System Monitor   │   │
│  │ │ (cloud, OpenAI) │ │         └──────────────────────────────┘   │
│  │ ├─────────────────┤ │                                            │
│  │ │ TTS: EdgeTTS    │ │         ┌──────────────────────────────┐   │
│  │ │ (free, Msft)    │ │         │ Cloudflare Tunnel            │   │
│  │ ├─────────────────┤ │         │ (remote access)              │   │
│  │ │ LLM: ───────────┼─┼────────► OpenClaw Gateway             │   │
│  │ └─────────────────┘ │         └──────────────────────────────┘   │
│  └──────▲──────────────┘                                            │
│         │ WebSocket (audio stream)                                   │
└─────────┼────────────────────────────────────────────────────────────┘
          │
    ┌─────┴──────┐
    │   ESP32    │
    │  ┌──────┐  │
    │  │ Mic  │  │  INMP441 (ghi âm)
    │  ├──────┤  │
    │  │ Loa  │  │  MAX98357A + Speaker (phát audio)
    │  ├──────┤  │
    │  │Screen│  │  OLED/LCD (hiển thị trạng thái)
    │  └──────┘  │
    └────────────┘
```

### Luồng xử lý khi user nói

```
User nói "Hôm nay thời tiết thế nào?"
  │
  ▼
ESP32 mic ghi âm (opus, 24kHz)
  │
  ▼ WebSocket ws://[minipc]:8000/xiaozhi/v1/
  │
xiaozhi-esp32-server nhận audio
  │
  ├──► SileroVAD: phát hiện giọng nói (local)
  │
  ├──► OpenAI Whisper API: audio → text (cloud)
  │    "Hôm nay thời tiết thế nào?"
  │
  ├──► OpenClaw Gateway: text → AI response
  │    (qua OpenAI-compatible API tại 127.0.0.1:18789)
  │    "Hôm nay Hà Nội 32°C, trời nắng nhẹ, độ ẩm 65%."
  │
  ├──► EdgeTTS: text → audio (Microsoft, free)
  │    Giọng: vi-VN-HoaiMyNeural (nữ tiếng Việt)
  │
  ▼ WebSocket stream audio
  │
ESP32 loa phát: "Hôm nay Hà Nội 32 độ C, trời nắng nhẹ..."
ESP32 screen hiện text response
```

---

## 2. Yêu cầu hệ thống

### MiniPC

| Thành phần | Yêu cầu | Ghi chú |
|---|---|---|
| RAM | 4GB (đủ vì dùng API) | Nếu 8GB+ có thể dùng FunASR local |
| OS | Ubuntu/Debian (đã cài sẵn) | |
| Docker | Đã cài sẵn | |
| OpenClaw Gateway | Đã chạy port 18789 | |
| ClawX-Web | Đã chạy port 2003 | |
| Internet | Cần (cho Whisper API + EdgeTTS) | |
| Port mở | 8000 (WebSocket), 8003 (HTTP/OTA) | Firewall allow |

### ESP32

| Thành phần | Yêu cầu |
|---|---|
| Board | ESP32-S3-DevKitC-1 (N16R8) |
| Mic | INMP441 (đã gắn sẵn) |
| Amp + Loa | MAX98357A + Speaker 3W 8Ω (đã gắn sẵn) |
| Screen | OLED/LCD (đã gắn sẵn) |
| Firmware | Xiaozhi prebuilt hoặc custom build |

### API Keys cần có

| Service | Dùng cho | Cách lấy | Chi phí |
|---|---|---|---|
| OpenAI API Key | Whisper STT | platform.openai.com | ~$0.006/phút |
| OpenClaw Gateway Token | LLM | `~/.openclaw/openclaw.json` | Free (đã có) |
| EdgeTTS | Text-to-Speech | Không cần key | Free |

### Chi phí API ước tính

| Service | Usage/tháng | Cost |
|---|---|---|
| Whisper STT | 300 phút | ~$1.80 |
| LLM (qua OpenClaw) | Tuỳ provider | ~$0.50-2.00 |
| EdgeTTS | Unlimited | Free |
| **Tổng** | | **~$2-4/tháng** |

---

## 3. Hướng dẫn triển khai

### Phase 1: Cài xiaozhi-esp32-server trên MiniPC

#### Bước 1.1: Clone repository

```bash
ssh user@[MINIPC_IP]
cd ~
git clone https://github.com/xinnan-tech/xiaozhi-esp32-server.git
cd xiaozhi-esp32-server
```

#### Bước 1.2: Tạo file config

```bash
mkdir -p data
nano data/.config.yaml
```

Nội dung `data/.config.yaml`:

```yaml
# ============================================================
# Xiaozhi ESP32 Server - Config cho ClawX MiniPC (4GB RAM)
# LLM → OpenClaw Gateway | TTS → EdgeTTS (free) | ASR → API
# ============================================================

server:
  ip: 0.0.0.0
  port: 8000
  http_port: 8003

log:
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  level: INFO

# ── Module Selection ──────────────────────────────────────
selected_module:
  VAD: SileroVAD
  ASR: OpenAIWhisperASR
  LLM: OpenAILLM
  TTS: EdgeTTS
  Memory: nomem
  Intent: intent_llm

# ── LLM: Trỏ về OpenClaw Gateway ──────────────────────────
# OpenClaw Gateway expose OpenAI-compatible API tại port 18789
# Dùng --network host nên truy cập qua 127.0.0.1
LLM:
  OpenAILLM:
    base_url: "http://127.0.0.1:18789/v1"
    api_key: "THAY_BANG_GATEWAY_TOKEN"
    model: "default"

# ── ASR: OpenAI Whisper API ────────────────────────────────
# Chi phí: $0.006/phút (~$1.80/tháng với 300 phút)
ASR:
  OpenAIWhisperASR:
    api_key: "THAY_BANG_OPENAI_API_KEY"
    model: "whisper-1"
    language: "vi"

# ── TTS: Microsoft Edge TTS (free, không cần API key) ─────
# Giọng tiếng Việt: vi-VN-HoaiMyNeural (nữ), vi-VN-NamMinhNeural (nam)
TTS:
  EdgeTTS:
    voice: "vi-VN-HoaiMyNeural"

# ── VAD: Voice Activity Detection (local, nhẹ) ────────────
VAD:
  SileroVAD:
    threshold: 0.5
    min_silence_duration_ms: 700

# ── Prompt: Nhân cách AI ──────────────────────────────────
prompt: |
  Bạn là ClawX, trợ lý AI thông minh chạy trên miniPC.
  Bạn trả lời ngắn gọn, thân thiện, bằng tiếng Việt.
  Khi được hỏi bạn là ai, hãy nói "Tôi là ClawX, trợ lý AI cá nhân của bạn."
  Bạn có khả năng điều khiển thiết bị IoT, trả lời câu hỏi, và hỗ trợ công việc.
```

#### Bước 1.3: Lấy Gateway Token

```bash
# Lấy token từ OpenClaw config
cat ~/.openclaw/openclaw.json | grep -i token

# HOẶC từ biến môi trường ClawX
cat /path/to/clawx-web/.env | grep GATEWAY_TOKEN
```

Thay `THAY_BANG_GATEWAY_TOKEN` trong config bằng giá trị token này.

#### Bước 1.4: Chạy Docker container

```bash
cd ~/xiaozhi-esp32-server

docker run -d \
  --name xiaozhi-server \
  --restart always \
  --network host \
  -e TZ=Asia/Ho_Chi_Minh \
  -v $(pwd)/data:/opt/xiaozhi-esp32-server/data \
  ghcr.nju.edu.cn/xinnan-tech/xiaozhi-esp32-server:server_latest
```

> **Quan trọng**: Dùng `--network host` để container truy cập được OpenClaw Gateway ở `127.0.0.1:18789`

#### Bước 1.5: Mở firewall

```bash
sudo ufw allow 8000/tcp comment "Xiaozhi WebSocket"
sudo ufw allow 8003/tcp comment "Xiaozhi HTTP/OTA"
```

#### Bước 1.6: Verify

```bash
# Check container đang chạy
docker ps | grep xiaozhi

# Check logs
docker logs xiaozhi-server --tail 30

# Test OTA endpoint
curl http://localhost:8003/xiaozhi/ota/
# → Phải trả về JSON response

# Test OpenClaw Gateway vẫn hoạt động
curl http://localhost:18789/v1/models
# → Phải trả về danh sách models
```

**Kết quả mong đợi**: Server log hiện `Server started on 0.0.0.0:8000` và OTA endpoint trả về response.

---

### Phase 2: Config ESP32 trỏ về MiniPC

#### Bước 2.0: Xác định IP LAN của miniPC

```bash
hostname -I
# Ghi lại IP, ví dụ: 192.168.1.100
```

#### Cách A: Đổi OTA URL không cần reflash (thử trước)

1. **Reset ESP32** → giữ nút BOOT → nhấn RST → thả BOOT
2. ESP32 vào **AP mode**, phát WiFi `XIAOZHI_XXXX`
3. Kết nối điện thoại vào WiFi `XIAOZHI_XXXX`
4. Mở trình duyệt → `http://192.168.4.1`
5. Cấu hình:
   - **WiFi SSID**: tên WiFi nhà
   - **WiFi Password**: mật khẩu WiFi nhà
   - **OTA URL**: `http://192.168.1.100:8003/xiaozhi/ota/`
6. Save → ESP32 tự restart → kết nối WiFi → gọi OTA → nhận WebSocket URL

#### Cách B: Build firmware custom (nếu Cách A không work)

**Yêu cầu**: Máy dev (Windows/Mac/Linux) có cài ESP-IDF 5.3+

```bash
# 1. Cài ESP-IDF (1 lần duy nhất)
# Windows: https://docs.espressif.com/projects/esp-idf/en/latest/esp32s3/get-started/windows-setup.html
# Linux/Mac: https://docs.espressif.com/projects/esp-idf/en/latest/esp32s3/get-started/linux-macos-setup.html

# 2. Clone firmware
git clone https://github.com/78/xiaozhi-esp32.git
cd xiaozhi-esp32

# 3. Sửa server URL
# File: main/Kconfig.projbuild
# Tìm và đổi:
```

Sửa file `main/Kconfig.projbuild`:

```kconfig
config WEBSOCKET_URL
    string "WebSocket URL"
    default "ws://192.168.1.100:8000/xiaozhi/v1/"
    help
        WebSocket URL of xiaozhi-esp32-server on miniPC

config OTA_URL
    string "OTA URL"
    default "http://192.168.1.100:8003/xiaozhi/ota/"
    help
        OTA check URL of xiaozhi-esp32-server on miniPC
```

```bash
# 4. Build
idf.py set-target esp32s3
idf.py build

# 5. Flash (cắm ESP32 qua USB, tìm COM port)
# Windows: check Device Manager → COM3, COM4, ...
# Linux: /dev/ttyUSB0 hoặc /dev/ttyACM0
idf.py -p COM3 flash

# 6. Monitor log (optional, debug)
idf.py -p COM3 monitor
# Ctrl+] để thoát monitor
```

#### Cách C: Flash firmware prebuilt (không cần ESP-IDF)

Nếu không muốn cài ESP-IDF, dùng Flash Download Tool:

1. Tải [Flash Download Tool](https://www.espressif.com/en/support/download/other-tools)
2. Tải firmware `.bin` từ [xiaozhi-esp32 Releases](https://github.com/78/xiaozhi-esp32/releases)
3. Chọn file phù hợp board (ví dụ: `bread-compact-wifi-n16r8-oled12864`)
4. Mở Flash Download Tool:
   - ChipType: **ESP32-S3**
   - WorkMode: **Develop**
   - LoadMode: **UART**
5. Chọn file `.bin` → Address: `0x0` → Chọn COM port → **START**
6. Đợi "FINISH" → rút USB → cắm lại
7. Sau đó dùng **Cách A** ở trên để đổi OTA URL

---

### Phase 3: Test & Verify

#### Test 1: Kết nối

```bash
# Trên miniPC, xem log xiaozhi-server
docker logs -f xiaozhi-server

# Khi ESP32 kết nối thành công, log sẽ hiện:
# "New WebSocket connection from 192.168.1.xxx"
```

#### Test 2: Nói chuyện

1. Nói wake word (mặc định: "Hi, Xiaozhi" hoặc nhấn nút trên ESP32)
2. Nói: **"Xin chào"**
3. Chờ 2-3 giây
4. ESP32 phát loa: **"Xin chào! Tôi là ClawX, trợ lý AI cá nhân của bạn."**

#### Test 3: Kiểm tra pipeline

```bash
# Xem log chi tiết
docker logs xiaozhi-server --tail 50

# Phải thấy:
# [ASR] Transcribed: "Xin chào"
# [LLM] Requesting OpenClaw Gateway...
# [LLM] Response: "Xin chào! Tôi là ClawX..."
# [TTS] Generating audio with EdgeTTS...
# [TTS] Audio sent to client
```

#### Checklist verify

```
[ ] docker ps | grep xiaozhi → container running
[ ] curl localhost:8003/xiaozhi/ota/ → có response
[ ] curl localhost:18789/v1/models → OpenClaw trả về models
[ ] ESP32 đèn sáng, kết nối WiFi thành công
[ ] docker logs xiaozhi-server → "New WebSocket connection"
[ ] Nói "Xin chào" → ESP32 phát loa trả lời
[ ] Nói câu hỏi dài → AI trả lời đúng context
```

---

### Phase 4: Cloudflare Tunnel (truy cập từ xa)

Để ESP32 hoạt động khi ở ngoài nhà (qua 4G/WiFi khác), cần expose xiaozhi-server qua Cloudflare Tunnel.

#### Bước 4.1: Thêm route trong tunnel config

Thêm ingress rule cho Cloudflare Tunnel (trong config tunnel trên miniPC):

```yaml
# Thêm vào cloudflared config
ingress:
  # ... existing rules ...
  - hostname: xiaozhi-SUBDOMAIN.veoforge.ggff.net
    service: http://localhost:8000
  - hostname: xiaozhi-ota-SUBDOMAIN.veoforge.ggff.net
    service: http://localhost:8003
```

Hoặc qua Cloudflare Dashboard → Zero Trust → Tunnels → Public Hostname → Add:
- `xiaozhi-SUBDOMAIN.veoforge.ggff.net` → `http://localhost:8000`
- `xiaozhi-ota-SUBDOMAIN.veoforge.ggff.net` → `http://localhost:8003`

#### Bước 4.2: Đổi ESP32 firmware URL

Build lại firmware với URL public:

```kconfig
config WEBSOCKET_URL
    default "wss://xiaozhi-SUBDOMAIN.veoforge.ggff.net/xiaozhi/v1/"

config OTA_URL
    default "https://xiaozhi-ota-SUBDOMAIN.veoforge.ggff.net/xiaozhi/ota/"
```

> **Lưu ý**: Dùng `wss://` (secure WebSocket) và `https://` vì qua Cloudflare Tunnel.

#### Bước 4.3: Test từ xa

1. ESP32 kết nối WiFi/4G ở ngoài nhà
2. ESP32 gọi OTA qua internet → Cloudflare Tunnel → miniPC
3. Nói chuyện bình thường - audio đi qua tunnel về miniPC xử lý

---

### Phase 5: Tích hợp ClawX Dashboard (tương lai)

> **Ghi chú**: Phase này build sau khi Phase 1-4 ổn định.

#### 5.1 Thêm xiaozhi vào docker-compose.yml

```yaml
# Thêm vào docker-compose.yml của ClawX-Web
services:
  clawx:
    # ... existing config ...

  xiaozhi-server:
    image: ghcr.nju.edu.cn/xinnan-tech/xiaozhi-esp32-server:server_latest
    container_name: xiaozhi-server
    restart: always
    network_mode: host
    environment:
      - TZ=Asia/Ho_Chi_Minh
    volumes:
      - ./xiaozhi-data:/opt/xiaozhi-esp32-server/data
```

#### 5.2 Backend: Health check route

Thêm vào `server/routes/system.ts`:

```typescript
// GET /api/system/xiaozhi-status
router.get('/xiaozhi-status', async (_req, res) => {
  try {
    const resp = await fetch('http://127.0.0.1:8003/xiaozhi/ota/');
    const data = await resp.json();
    res.json({ online: true, ...data });
  } catch {
    res.json({ online: false });
  }
});
```

#### 5.3 Frontend: Dashboard card

Thêm card "Voice Assistant" trên Dashboard hiển thị:
- Xiaozhi server status (online/offline)
- Số ESP32 devices đang kết nối
- ASR/TTS/LLM provider đang dùng
- Nút "Test Voice" (record audio từ browser → gửi test)

#### 5.4 Settings page

Thêm section "Voice Assistant" trong Settings:
- Config voice (giọng nam/nữ, ngôn ngữ)
- Config ASR provider (Whisper/Xunfei/Doubao)
- Config wake word
- Config AI prompt/personality

---

## 4. Sơ đồ chân nối ESP32 (tự ráp thêm)

> **Ghi chú**: Nếu ESP32 đã gắn sẵn loa/mic/screen thì BỎ QUA phần này.
> Phần này dùng khi muốn ráp thêm ESP32 mới cho buyer.

### Linh kiện

| Linh kiện | Model | Giá ước tính |
|---|---|---|
| Board | ESP32-S3-DevKitC-1 (N16R8) | ~$4 |
| Microphone | INMP441 MEMS | ~$1 |
| Amplifier | MAX98357A I2S | ~$1 |
| Speaker | 3W 8Ω cavity speaker | ~$0.50 |
| Display | SSD1306 OLED 128x64 | ~$2 |
| Breadboard | 830 holes | ~$1 |
| Jumper wires | Male-to-male | ~$0.50 |
| **Tổng** | | **~$10** |

### Sơ đồ nối dây

```
ESP32-S3 (N16R8)                 INMP441 (Microphone)
═══════════════                  ════════════════════
GPIO4  ─────────────────────────► WS   (Word Select)
GPIO5  ─────────────────────────► SCK  (Serial Clock)
GPIO6  ─────────────────────────► SD   (Serial Data)
3V3    ─────────────────────────► VDD  (Power 3.3V)
GND    ─────────────────────────► GND  (Ground)
                                  L/R → nối về GND


ESP32-S3                         MAX98357A (Amplifier)
═══════════════                  ════════════════════
GPIO7  ─────────────────────────► DIN  (Data In)
GPIO15 ─────────────────────────► BCLK (Bit Clock)
GPIO16 ─────────────────────────► LRC  (Left/Right Clock)
3V3    ─────────────────────────► VCC  (Power)
GND    ─────────────────────────► GND  (Ground)
                                  SD & GAIN → nối về GND
                                  Audio+ ──► Loa (+)
                                  Audio- ──► Loa (-)


ESP32-S3                         SSD1306 OLED 128x64
═══════════════                  ════════════════════
GPIO41 ─────────────────────────► SDA  (Data)
GPIO42 ─────────────────────────► SCK  (Clock)
3V3    ─────────────────────────► VCC  (Power)
GND    ─────────────────────────► GND  (Ground)
```

### Sơ đồ trực quan (breadboard)

```
    ┌──────────────────────────────────────────────┐
    │              BREADBOARD                       │
    │                                              │
    │  ┌─────────┐   ┌─────────┐   ┌──────────┐  │
    │  │ INMP441 │   │MAX98357A│   │  SSD1306  │  │
    │  │  (MIC)  │   │  (AMP)  │   │  (OLED)   │  │
    │  │         │   │     ┌───┤   │           │  │
    │  │ WS  ●───┼───┼──── │GPIO4 │           │  │
    │  │ SCK ●───┼───┼──── │GPIO5 │ SDA ●─────┼──┼── GPIO41
    │  │ SD  ●───┼───┼──── │GPIO6 │ SCK ●─────┼──┼── GPIO42
    │  │ VDD ●───┼───┼──── │3V3   │ VCC ●─────┼──┼── 3V3
    │  │ GND ●───┼───┼──── │GND   │ GND ●─────┼──┼── GND
    │  │ L/R→GND │   │ DIN ●─────┼──┼── GPIO7 │  │
    │  └─────────┘   │BCLK ●─────┼──┼── GPIO15│  │
    │                 │ LRC ●─────┼──┼── GPIO16│  │
    │                 │ VCC ●─────┼──┼── 3V3   │  │
    │                 │ GND ●─────┼──┼── GND   │  │
    │                 │           │  └──────────┘  │
    │                 │  Audio+───┼──► Loa (+)     │
    │                 │  Audio-───┼──► Loa (-)     │
    │                 └───────────┘                 │
    │                                              │
    │        ┌──────────────────────┐              │
    │        │    ESP32-S3-N16R8    │              │
    │        │    (DevKitC-1)       │              │
    │        │                      │              │
    │        │  USB-C (flash/power) │              │
    │        └──────────────────────┘              │
    └──────────────────────────────────────────────┘
```

---

## 5. Cách flash firmware ESP32

### Cách 1: Flash qua trình duyệt (KHÔNG cần cài tool)

1. Mở **Chrome** hoặc **Edge** (Firefox không hỗ trợ)
2. Vào: https://espressif.github.io/esp-launchpad/
3. Cắm ESP32 qua USB-C
4. Chọn COM port → Chọn file firmware `.bin` → Flash
5. Đợi xong → rút USB → cắm lại

### Cách 2: Flash Download Tool (Windows, GUI)

1. Tải [Flash Download Tool](https://www.espressif.com/en/support/download/other-tools) từ Espressif
2. Tải firmware `.bin` từ [xiaozhi-esp32 Releases](https://github.com/78/xiaozhi-esp32/releases)
   - Chọn file phù hợp board (ví dụ: `bread-compact-wifi-n16r8-oled12864_en.bin`)
3. Mở Flash Download Tool:

```
┌─────────────────────────────────────────┐
│  ChipType:  [ESP32-S3 ▼]               │
│  WorkMode:  [Develop  ▼]               │
│  LoadMode:  [UART     ▼]               │
│                                         │
│  [✓] firmware.bin          @ 0x0        │
│                                         │
│  COM:  [COM3 ▼]    Baud: [460800 ▼]    │
│                                         │
│            [ START ]                    │
│                                         │
│  Progress: [████████████████] 100%      │
│  Status:   FINISH                       │
└─────────────────────────────────────────┘
```

4. Click **START** → đợi **FINISH** → rút USB → cắm lại

### Cách 3: Build từ source (cho custom server URL)

```bash
# Yêu cầu: ESP-IDF 5.3+
# Cài 1 lần: https://docs.espressif.com/projects/esp-idf/en/latest/esp32s3/get-started/

git clone https://github.com/78/xiaozhi-esp32.git
cd xiaozhi-esp32

# Sửa main/Kconfig.projbuild → đổi OTA_URL và WEBSOCKET_URL

idf.py set-target esp32s3
idf.py build
idf.py -p COM3 flash       # Windows
idf.py -p /dev/ttyUSB0 flash  # Linux
```

### Sau khi flash: Cấu hình WiFi cho ESP32

1. ESP32 khởi động → vào **AP mode** → phát WiFi `XIAOZHI_XXXX`
2. Kết nối điện thoại vào WiFi `XIAOZHI_XXXX` (không có mật khẩu)
3. Mở trình duyệt → `http://192.168.4.1`
4. Nhập:
   - **WiFi SSID**: tên WiFi nhà
   - **WiFi Password**: mật khẩu WiFi nhà
   - **OTA URL** (nếu có): `http://[MINIPC_IP]:8003/xiaozhi/ota/`
5. Save → ESP32 restart → kết nối WiFi → sẵn sàng

---

## 6. Troubleshooting

| Triệu chứng | Nguyên nhân | Cách fix |
|---|---|---|
| ESP32 không kết nối WebSocket | IP sai hoặc firewall chặn | `sudo ufw allow 8000/tcp` và check IP bằng `hostname -I` |
| Log: "LLM error" | OpenClaw Gateway chưa chạy hoặc token sai | `curl http://127.0.0.1:18789/v1/models` để verify |
| Không có tiếng phát | EdgeTTS cần internet | Check miniPC có internet: `ping google.com` |
| ASR trả về rỗng | OpenAI key sai hoặc hết quota | Check key tại https://platform.openai.com |
| ESP32 không vào AP mode | Firmware lỗi | Flash lại firmware bằng Flash Download Tool |
| Latency cao (>5 giây) | Network chậm hoặc LLM chậm | Đổi LLM sang model nhẹ hơn (DeepSeek-V3-0324) |
| Docker container crash | Thiếu RAM | `docker logs xiaozhi-server` để xem lỗi cụ thể |
| ESP32 nghe nhưng không trả lời | VAD threshold quá cao | Giảm `VAD.SileroVAD.threshold` xuống 0.3 |

### Lệnh debug hữu ích

```bash
# Xem log real-time
docker logs -f xiaozhi-server

# Restart server
docker restart xiaozhi-server

# Check RAM usage
free -h

# Check tất cả ports đang listen
ss -tlnp | grep -E "8000|8003|18789|2003"

# Test OpenClaw Gateway
curl -X POST http://127.0.0.1:18789/v1/chat/completions \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"model":"default","messages":[{"role":"user","content":"test"}]}'
```

---

## 7. Timeline

```
Tuần 1: Phase 1 + 2
├── [ ] Cài xiaozhi-esp32-server trên miniPC (Docker)
├── [ ] Config: LLM → OpenClaw, TTS → EdgeTTS, ASR → Whisper API
├── [ ] Mở firewall port 8000, 8003
├── [ ] Flash ESP32 firmware (prebuilt hoặc custom)
├── [ ] Config ESP32 WiFi + OTA URL trỏ về miniPC
└── [ ] Test: nói chuyện với ESP32 → AI trả lời qua loa ✓

Tuần 2: Phase 3
├── [ ] Thêm Cloudflare Tunnel routes cho xiaozhi
├── [ ] Build firmware ESP32 với URL public (wss://)
├── [ ] Test: ESP32 ở ngoài nhà (4G) → vẫn hoạt động ✓
└── [ ] Test: latency qua tunnel < 3 giây ✓

Tuần 3+: Phase 4 + 5 (khi sẵn sàng)
├── [ ] Thêm xiaozhi-server vào docker-compose.yml ClawX
├── [ ] ClawX Dashboard: card "Voice Assistant"
├── [ ] ClawX Settings: config voice/ASR/TTS
├── [ ] Cron → ESP32 (đọc tin buổi sáng qua loa)
└── [ ] Channel bridge (WhatsApp/Telegram → đọc qua ESP32 loa)
```

---

## 8. Selling Point cho Buyer

> **Package bán**: MiniPC ClawX + ESP32 Voice Kit
>
> **Giá trị**:
> - Trợ lý AI riêng, nói tiếng Việt, chạy private
> - Cùng AI engine: chat web = chat voice = WhatsApp/Telegram
> - Truy cập từ xa qua điện thoại (Cloudflare Tunnel)
> - Đọc tin tức buổi sáng, nhắc lịch, điều khiển smart home
> - Không phụ thuộc cloud AI (dùng model nào tuỳ ý)
> - ESP32 kit giá chỉ ~$10, plug & play
>
> **Tagline**: *"Mua 1 miniPC + 1 ESP32 = Trợ lý AI cho cả nhà"*

---

## Tài liệu tham khảo

- [xiaozhi-esp32 (firmware)](https://github.com/78/xiaozhi-esp32)
- [xiaozhi-esp32-server (backend)](https://github.com/xinnan-tech/xiaozhi-esp32-server)
- [OpenClaw Gateway docs](https://docs.openclaw.ai/)
- [ESP-IDF Getting Started](https://docs.espressif.com/projects/esp-idf/en/latest/esp32s3/get-started/)
- [Flash Download Tool](https://www.espressif.com/en/support/download/other-tools)
- [EdgeTTS voices list](https://speech.platform.bing.com/consumer/speech/synthesize/readaloud/voices/list?trustedclienttoken=6A5AA1D4EAFF4E9FB37E23D68491D6F4)
- [Xiaozhi Hardware Guide](https://xiaozhi.dev/en/docs/usage/hardware-guide/)
