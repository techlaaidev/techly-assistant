---
title: "Jarvis Phase 1 — Personality, Screen Vision, Spotify Music"
description: "3 features to transform Techly into a Jarvis-style assistant with personality, screen awareness, and music control."
status: pending
priority: P1
effort: 7h
branch: main
tags: [jarvis, personality, vision, spotify, mcp, tools]
created: 2026-04-15
---

# Jarvis Phase 1 — Personality / Vision / Music

**Research:** `plans/260415-jarvis-features-research/research/researcher-260415-1244-jarvis-features.md`

## Phases

| # | Phase | File | Effort | Status | Blocker |
|---|-------|------|--------|--------|---------|
| 1 | Personality Layer | [phase-01-personality-layer.md](phase-01-personality-layer.md) | 1h | pending | None — verify dashboard char limit first |
| 2 | Screen Vision | [phase-02-screen-vision.md](phase-02-screen-vision.md) | 2-3h | pending | `OPENAI_API_KEY` must exist |
| 3 | Spotify Control | [phase-03-spotify-control.md](phase-03-spotify-control.md) | 3h | pending | Spotify Premium + Developer App creds |

## Dependency Order

```
Phase 1 (no code) → can run in parallel with Phase 2 or 3
Phase 2 → requires OPENAI_API_KEY (already in .env for pc_control)
Phase 3 → requires new Spotify Developer App + Premium account
```

## Files Changed (total)

| File | Action | Phase |
|------|--------|-------|
| `docs/xiaozhi-agent-system-prompt.md` | modify | 1 |
| `tools/screen_vision.py` | create | 2 |
| `server.py` | modify | 2, 3 |
| `.env.example` | modify | 2, 3 |
| `tools/spotify_control.py` | create | 3 |
| `scripts/spotify_oauth_setup.py` | create | 3 |
| `data/spotify_token.json` | runtime (gitignored) | 3 |

## Success Criteria

- Phase 1: Jarvis personality audible in voice responses — calls user "Sir" / "thưa ngài"
- Phase 2: `nhin_man_hinh("đây là gì?")` returns Vietnamese description of screen content
- Phase 3: `phat_nhac("lo-fi")` starts Spotify playback; `tam_dung_nhac()` pauses
