# Top 10 MCP Servers/Integrations cho Techly Assistant

Research date: 2026-04-13. Curated theo ROI cho Vietnamese voice assistant + business use.

## Approach options

3 cách integrate MCP server bên ngoài vào Techly:
- **A. Spawn subprocess** — trong `mcp_pipe.py` thay thế hoặc thêm process spawn
- **B. Multi-server bridge** — viết custom bridge route messages tới nhiều MCP servers
- **C. Reimplement as tool** — copy logic vào `tools/<name>.py` (đơn giản nhất, ít moving parts)

→ Recommend **C** cho hầu hết cases. **A** chỉ khi server quá phức tạp (Apify, Notion).

---

## 🏆 Tier 1 — Highest ROI

### 1. Apify MCP — Web scraping bất kỳ website nào
- **URL:** https://github.com/apify/apify-mcp-server, hosted at https://mcp.apify.com
- **Value:** ⭐⭐⭐⭐⭐ — 4000+ Actors có sẵn (Facebook, Instagram, Google Maps, Amazon, Shopee, scraping, RAG web browser)
- **Use case voice:** "tìm 10 nhà hàng top ở Sài Gòn", "tin mới về Vingroup từ Google", "scrape danh sách shop mỹ phẩm trên Shopee"
- **Setup:** API key Apify (free tier có credits)
- **Integration:** Spawn subprocess hoặc HTTP call trực tiếp tới Apify Actor API
- **Effort:** 🔨 Medium — cần Apify token + tool wrapper

### 2. Brave Search MCP — Web search realtime
- **URL:** https://github.com/modelcontextprotocol/servers/tree/main/src/brave-search
- **Value:** ⭐⭐⭐⭐⭐ — Voice search nhanh, không bias quảng cáo như Google
- **Use case voice:** "tìm thông tin về X trên web", "search tin mới về Y"
- **Setup:** Brave Search API key (2000 queries/tháng free)
- **Integration:** Simple HTTP call → wrap thành `tim_kiem_web(query)` tool
- **Effort:** ⚡ Easy

### 3. Memory MCP — Persistent knowledge graph
- **URL:** https://github.com/modelcontextprotocol/servers/tree/main/src/memory
- **Value:** ⭐⭐⭐⭐⭐ — LLM nhớ user preferences/history qua sessions
- **Use case voice:** "nhớ là tôi thích cà phê đen", "tôi từng nói gì về dự án X"
- **Setup:** None — local JSON storage
- **Integration:** Reimplement as `tools/memory.py` với JSON store + entity-relation graph
- **Effort:** 🔨 Medium

---

## 🥈 Tier 2 — High value cho business

### 4. Notion MCP — Workspace knowledge base
- **URL:** https://github.com/makenotion/notion-mcp-server
- **Value:** ⭐⭐⭐⭐⭐ — Tích hợp wiki Techla AI nội bộ qua voice
- **Use case voice:** "tìm trong Notion về OKR Q2", "thêm task vào Notion project X"
- **Setup:** Notion integration token + workspace permissions
- **Integration:** Spawn subprocess (official server tốt) hoặc dùng Notion API trực tiếp
- **Effort:** 🔨 Medium

### 5. GitHub MCP — Repo / Issues / PRs
- **URL:** https://github.com/github/github-mcp-server
- **Value:** ⭐⭐⭐⭐ — Dev team daily use
- **Use case voice:** "PR nào đang chờ review", "issue mới trong techly-assistant", "ai vừa commit"
- **Setup:** GitHub Personal Access Token (đã có nếu dùng `gh` CLI)
- **Integration:** Reimplement bằng `gh api` calls trong `tools/github.py`
- **Effort:** ⚡ Easy

### 6. Slack/Discord MCP — Team comms
- **URL:** Slack official MCP / discord.py
- **Value:** ⭐⭐⭐⭐ — Đọc/post messages bằng voice
- **Use case voice:** "Slack có gì mới trong channel #general", "post 'họp 3h chiều' vào team"
- **Setup:** Slack bot token / Discord bot
- **Integration:** Reimplement bằng requests + Slack/Discord API trong `tools/`
- **Effort:** 🔨 Medium

---

## 🥉 Tier 3 — Niche nhưng useful

### 7. Filesystem MCP — Local file ops
- **URL:** https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem
- **Value:** ⭐⭐⭐ — Read/write local files via voice (limited use cho voice)
- **Use case voice:** "đọc file README", "tạo file note mới"
- **Setup:** Configurable path whitelist
- **Integration:** Reimplement đơn giản với `pathlib`
- **Effort:** ⚡ Easy

### 8. Fetch/Firecrawl MCP — URL → Markdown
- **URL:** https://github.com/mendableai/firecrawl-mcp-server
- **Value:** ⭐⭐⭐⭐ — Đọc bất kỳ trang web nào sạch sẽ
- **Use case voice:** "đọc bài viết tại URL X", "tóm tắt trang Y"
- **Setup:** Firecrawl API key (500 pages free) hoặc dùng `requests + html2text` self-host
- **Integration:** Self-host = reimplement với `urllib + readabilipy`. Hoặc Firecrawl API
- **Effort:** ⚡ Easy (self-host) hoặc 🔨 Medium (Firecrawl)

### 9. PostgreSQL/Supabase MCP — Database queries
- **URL:** https://github.com/modelcontextprotocol/servers/tree/main/src/postgres
- **Value:** ⭐⭐⭐⭐ — Query DB business bằng voice (cẩn thận read-only!)
- **Use case voice:** "doanh thu tháng này", "khách hàng có chi tiêu cao nhất"
- **Setup:** Postgres connection string + read-only user
- **Integration:** `psycopg2` + safe query templates trong `tools/db.py`
- **Effort:** 🔨 Medium

### 10. Telegram Bot MCP — Notifications + interactive
- **URL:** Custom bằng `python-telegram-bot`
- **Value:** ⭐⭐⭐⭐ — Voice notifications + remote control
- **Use case voice:** "gửi tin nhắn Telegram cho team 'meeting đang bắt đầu'", "kiểm tra Telegram có gì mới"
- **Setup:** BotFather → bot token
- **Integration:** Reimplement bằng `requests` tới Telegram Bot API trong `tools/telegram.py`
- **Effort:** ⚡ Easy

---

## Bonus — Đáng chú ý

| # | MCP | Use case | Effort |
|---|---|---|---|
| 11 | **Sentry** MCP | Track errors production | Easy |
| 12 | **Linear** MCP | Project management | Medium |
| 13 | **Stripe** MCP | Payments / revenue tracking | Easy |
| 14 | **Sequential Thinking** MCP | LLM reasoning (built-in) | Easy |
| 15 | **Playwright** MCP | Browser automation | Hard |
| 16 | **Vectara/Chroma** MCP | Vector RAG search | Medium |
| 17 | **Time** MCP (built-in) | Timezone conversions | Trivial |
| 18 | **Rube** | 500+ apps via Zapier-like | Easy |
| 19 | **Sequential Thinking** | LLM reasoning trace | Easy |
| 20 | **MCP Inspector** | Debug tool | Trivial |

---

## Top 3 đề xuất ưu tiên cho Techly

Nếu chỉ implement **3 cái tiếp theo**, tôi recommend:

### 🥇 #1: Brave Search (Easy, ⭐⭐⭐⭐⭐)
- Voice search là killer feature
- 30 phút implement
- Free tier 2000/tháng đủ dùng

### 🥈 #2: Apify (Medium, ⭐⭐⭐⭐⭐)
- Khả năng scrape mọi site
- Đặc biệt useful cho VN sites (Shopee, Tiki, Lazada, Foody, ...)
- ROI cao nhất nhưng cần Apify subscription

### 🥉 #3: Memory (Medium, ⭐⭐⭐⭐⭐)
- Personalization → assistant nhớ user
- "Hôm trước anh nói thích cà phê đen, em đề xuất..."
- Privacy-friendly (local JSON)

## Architecture decision

| Pattern | When to use |
|---|---|
| **Reimplement as `tools/<name>.py`** | API đơn giản, ít endpoints, 1 process |
| **Spawn subprocess** | MCP server quá phức tạp tự implement (Apify, Notion, GitHub) |
| **Multi-MCP bridge** | Cần nhiều MCP servers song song → cần rewrite mcp_pipe.py |

→ Cho 3 đề xuất trên: **Brave** + **Memory** = reimplement (Easy). **Apify** = spawn subprocess (Medium).

---

## Sources

- [Official MCP Servers](https://github.com/modelcontextprotocol/servers)
- [Awesome MCP Servers (wong2)](https://github.com/wong2/awesome-mcp-servers)
- [Apify MCP GitHub](https://github.com/apify/apify-mcp-server)
- [Builder.io Best MCP Servers 2026](https://www.builder.io/blog/best-mcp-servers-2026)
- [Pomerium Best MCP 2025](https://www.pomerium.com/blog/best-model-context-protocol-mcp-servers-in-2025)

## Unresolved questions

1. Apify free tier có đủ cho voice use case daily không? (Cần test)
2. Vietnamese sites có cần custom Actor riêng hay Apify Generic Web Scraper đủ?
3. Notion workspace của Techla AI đã setup chưa? Có data nội bộ ở Notion không?
4. Brave Search có rate limit theo IP không khi voice query nhiều?
