---
title: "Phase 01 — Personality Layer"
status: pending
priority: P1
effort: 1h
---

# Phase 01 — Personality Layer

## Context Links

- Research: `plans/260415-jarvis-features-research/research/researcher-260415-1244-jarvis-features.md` § Feature 5
- Existing system prompt file: `docs/xiaozhi-agent-system-prompt.md`
- Dashboard: https://xiaozhi.me (agent settings → system prompt field)

## Overview

**Priority:** P1 — highest impact, zero risk, zero code  
**Status:** pending  
Zero-code change. Configure system prompt in Xiaozhi cloud dashboard to inject Jarvis personality. Immediate demo impact.

## Key Insights (from research)

- Xiaozhi cloud LLM uses system prompt set on dashboard — single source of truth for persona
- Char limit unknown; test 300-char version first before full prompt
- Approach B fallback: extend `tools/company.py` COMPANY_DATA_FILE or add PERSONA constant — only if dashboard is insufficient
- Existing file `docs/xiaozhi-agent-system-prompt.md` already addresses speculative TTS fix; new prompt must preserve that behavior

## Requirements

### Functional
- Assistant calls user "Sir" (English context) or "thưa ngài" (Vietnamese context)
- Dry, confident tone — answer first, caveats last
- Never says "I am just an AI"
- Occasional sardonic one-liner, then moves on
- Responses concise; no unnecessary hedging

### Non-functional
- Zero latency impact (system prompt processed server-side by Xiaozhi cloud)
- Must not break existing tool-call behavior (GPT-5 function calling must still fire)
- Must not conflict with existing TTS speculative-token fix in current system prompt

## Architecture

```
xiaozhi.me dashboard
    └── Agent Settings → System Prompt field
            └── [personality prompt text]
                    ↓ injected into every LLM call on Xiaozhi cloud
                    ↓ no change to server.py / MCP tools
ESP32 → Xiaozhi cloud (LLM with personality) → TTS → ESP32 speaker
```

No MCP server changes unless dashboard char limit is hit (see Fallback below).

### Fallback Architecture (if char limit < prompt length)

```
docs/xiaozhi-agent-system-prompt.md  ← edit here
    → paste truncated version into dashboard
    → full persona context stored in company_data.md under ## Persona section
    → company.py already reads company_data.md via _read_company_section()
```

## Related Code Files

### Modify
- `docs/xiaozhi-agent-system-prompt.md` — add Jarvis personality block at top, preserve existing TTS-fix instructions

### Create
- None (unless fallback needed)

### Fallback only (if dashboard char limit hit)
- `company_data.md` — add `## Persona` section with full prompt text

## Implementation Steps

1. **Draft 300-char prompt** (fits most cloud dashboards):
   ```
   You are Techly, an AI in the style of J.A.R.V.I.S. from Iron Man.
   Call user "Sir" (English) or "thưa ngài" (Vietnamese).
   Dry wit, confident, concise. Answer first, caveats last.
   Never say "I am just an AI."
   ```

2. **Draft full prompt** (~500 chars, for backup):
   ```
   You are Techly, an AI assistant in the style of J.A.R.V.I.S. from Iron Man.
   Personality: brilliant, dry wit, unfailingly polite.
   Always address user as "Sir" in English or "thưa ngài" in Vietnamese.
   Style: concise, confident, occasionally sardonic — one dry line, then move on.
   Answer the question first. Caveats and disclaimers go last, if at all.
   Never say "I am just an AI" or "as an AI language model".
   When uncertain: state it in one word ("Possibly, Sir."), then answer.
   ```

3. **Update `docs/xiaozhi-agent-system-prompt.md`**: prepend personality block above existing TTS-fix block. Add comment separator `# === PERSONALITY ===` and `# === TTS FIX ===`.

4. **Login to xiaozhi.me** → agent settings → paste 300-char prompt first → save.

5. **Test voice trigger**: say "xin chào" or "who are you?" → verify Jarvis tone + "Sir"/"thưa ngài".

6. **If char limit hit**: note exact limit → trim prompt to fit → document limit in `docs/xiaozhi-agent-system-prompt.md` header comment.

7. **Test tool calls still fire**: say "mấy giờ rồi" → verify `hien_thi_gio()` tool is called (not hallucinated in text).

8. **If tool calls break**: the personality prompt is likely overriding the function-call instruction → adjust priority ordering in prompt; move tool-call enforcement lines above personality.

## Todo List

- [ ] Draft 300-char prompt version
- [ ] Draft 500-char full prompt version
- [ ] Update `docs/xiaozhi-agent-system-prompt.md` with both versions + comments
- [ ] Paste 300-char into xiaozhi.me dashboard → save
- [ ] Test: personality tone audible ("Sir" / "thưa ngài")
- [ ] Test: existing tools still fire correctly (time, weather, company data)
- [ ] If char limit hit: document it, trim, re-test
- [ ] If tool calls regress: reorder prompt sections, re-test

## Success Criteria

- Voice response uses Jarvis tone: confident, dry, addresses user as Sir/thưa ngài
- No regression: `hien_thi_gio`, `lay_thoi_tiet`, `lay_doanh_thu` still invoke via function call (not hallucinated)
- Speculative TTS still fires correctly (no "không tìm thấy" before tool returns)

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Dashboard char limit < 300 | Medium | Low | Use absolute minimum 150-char prompt; store full version in docs only |
| Personality prompt overrides function-call behavior | Low | High | Keep function-call enforcement lines first; personality second |
| Non-Vietnamese persona sounds odd in VN responses | Medium | Low | Use bilingual phrasing — "thưa ngài" for VN, "Sir" for EN |
| Xiaozhi dashboard UI changes / system prompt field renamed | Low | Low | Check docs/README on xiaozhi.me before starting |

## Security Considerations

- No secrets involved; system prompt is non-sensitive text
- Do NOT include company data or user PII in system prompt
- Dashboard credentials (xiaozhi.me login) — use existing account, do not store password anywhere

## Next Steps

- After Phase 1: proceed to Phase 2 (Screen Vision) — independent, no dependency on Phase 1
- If fallback to `company_data.md` needed: notify implementer of Phase 3 (no impact expected)

## Unresolved Questions

1. What is the exact char limit of Xiaozhi dashboard system prompt field? (Unknown — must test empirically)
2. Does Xiaozhi inject system prompt before or after its own internal instructions? (Affects prompt priority ordering)
3. Will changing system prompt affect the existing TTS speculative token behavior documented in `docs/xiaozhi-agent-system-prompt.md`?
