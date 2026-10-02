# Project notes — Hiulix / Tora Labs LLC

Working state as of **2 October 2026**. Written as a cold-start document: if you
are picking this up with no memory of the conversation, everything you need is
here.

---

## 1. What this is

Marketing site **and** a live AI sales agent for **Hiulix**, the managed
service provider product of Tora Labs LLC (Philadelphia, PA). The agent on the
site is the product doing its own job — it is the demo.

**Two names, deliberately.** Hiulix is the product sold to MSPs and the name on
this site. **SalesmateAI is the platform underneath it** and the name used
throughout the business plan, so it stays — renaming the plan's product would
put the site and the plan in conflict, and the plan is the document that has to
hold up. Section 11 has the reasoning; `config.py` has both names.

Built from the founder's five-year business plan
(`Tora_Labs_Business_Plan — копия.pdf`, 52 pages, gitignored). Visual design
follows a reference screenshot the founder supplied (the Aside browser landing
page): pale sky hero, centred headline, long quiet column of off-white, one
idea per screen.

| | |
|---|---|
| **Live** | https://salesmateai-three.vercel.app |
| (alias) | https://salesmateai-sherzod2.vercel.app |
| **Repo** | https://github.com/sherzodibodullayev/SalesmateAI (public, `main`) |
| **Vercel** | scope `sherzod2`, project `salesmateai` |
| **Stack** | FastAPI + Jinja2 + vanilla JS. No build step, no framework, no npm. |

Status: **deployed and working.** `/health` returns `status: ok`,
`openai_key: set`, `redis: memory-fallback`.

---

## 2. Run it locally

```bash
cd "C:/Users/user/American_projects/Tora_Labs" && .venv/Scripts/python.exe -m uvicorn main:app --reload --port 8010
```

Then http://localhost:8010. The venv already exists. `.env` holds the OpenAI
key.

> The local server is **not** running right now — it was a background process
> and it stopped. The Vercel deployment is unaffected.

Marketing pages work without an API key; only `/api/chat` fails (503).
`/health?deep=1` actually calls OpenAI.

---

## 3. File map

```
main.py                       routes, page context, robots/sitemap, health
config.py                     COMPANY/FOUNDER facts, env helpers, Redis, model
models.py                     request/response shapes
api/index.py                  Vercel entry point — reports startup errors as text
routes/chat_routes.py         /api/chat, /api/audio-question, conversation CRUD
routes/websocket_routes.py    unused; serverless cannot do WebSockets
utils/conversation_utils.py   ← THE AGENT'S SYSTEM PROMPT lives here
utils/redis_utils.py          conversation store; falls back to process memory
utils/rate_limiting.py        40 req/IP/hour; also has a memory fallback
utils/audio_utils.py          Whisper upload handling, file deleted after
templates/                    base, index, demo, pricing, company, privacy, terms
public/static/css/site.css    design system — all tokens in :root
public/static/css/components.css   the ported 21st.dev components
public/static/css/chat.css    the agent panel + /demo console
public/static/js/site.js      masthead, nav, reveal, market chart, chat panel
public/static/js/components.js     the ported components' behaviour
public/static/js/chat.js      the ONE chat client (drives panel and /demo both)
test_prompt.py                prompt checks — run it after touching BASE_PROMPT
vercel.json / .vercelignore   Vercel config
render.yaml                   alternative host, unused
DEPLOY.md                     the Vercel runbook
```

**Pages:** `/` `/demo` `/pricing` `/company` `/privacy` `/terms`

---

## 4. Where to change things

| To change | Edit |
|---|---|
| What the agent says or refuses | `utils/conversation_utils.py` → `BASE_PROMPT` |
| Prices, entity details, contacts | `config.py` → `COMPANY` (or Vercel env) |
| Founder bio items | `config.py` → `FOUNDER` |
| Colours, type, spacing | `public/static/css/site.css` → `:root` |
| Animations | `components.css` + `components.js` |

**If you change a price or ship a feature, change it in BOTH `config.py` and
`BASE_PROMPT`** — otherwise the page and the agent contradict each other in
front of a customer. `test_prompt.py` now enforces that: it fails if a
`price_*` in `COMPANY` is absent from the rendered prompt.

```bash
cd "C:/Users/user/American_projects/Tora_Labs" && .venv/Scripts/python.exe test_prompt.py
```

It also catches a failure the source hides: `BASE_PROMPT` is one long string
held together by backslash continuations, and the space has to come *before*
the backslash. Without it two words fuse in the text the model actually reads
while the file still looks right. That happened once during the Hiulix rewrite.

---

## 5. Claims discipline — the rule the whole site follows

The business plan is careful to separate verified facts from planning
assumptions. The site keeps that separation, and so does the agent:

- Prices are labelled **published planning assumptions**, not quotes.
- "No paying customers, no revenue yet" is stated plainly — on the site and by
  the agent.
- Voice AI and specific CRM integrations are described as **planned**, never
  available.
- Market figures are attributed to the analyst firm that published them, and a
  range is shown rather than one flattering number.
- The founder section lists documented items only. Where the record shows an
  offer or an application rather than a completed qualification, it says so.
- **No stock portrait stands in for the founder** — a monogram is used. A stock
  face captioned with a real person's name is a misrepresentation regardless of
  the licence.
- The agent discloses it is an AI at the start of every conversation.

The system prompt enforces the same rules: it is told exactly which figures it
may state, and to defer to the founder for anything else. Verified live — asked
about HubSpot and voice, it refused to promise either.

---

## 6. The ported components

The founder asked for ten 21st.dev components via `npx shadcn add`. That is a
React/Next mechanism and this site is Jinja + vanilla JS, so each was
**reimplemented from its documented behaviour**, not installed. The source is
behind a login on 21st.dev and could not be fetched.

| Original | Ours | Where |
|---|---|---|
| reveal-text | `.rt` | all big headings, statement block |
| animated-hero | `.rotw` | hero headline noun cycles |
| text-three (typewriter) | `.tw` | intent section, `/demo` aside |
| spotlight-card | `.spot` | cards, pricing plans, pillars |
| flip-button | `.flipbtn` | secondary CTAs |
| liquid-glass-button | `.btn--glass` | buttons on sky / shader |
| glsl-hills | `.hills` | closing CTA — WebGL, CSS fallback |
| pricing | `.switch` + `.num` | monthly/annual, counted figures, confetti |
| faq1 | `.faq` | centred animated accordion |
| light-theme background | `.bg-canvas` | tinted radials behind the page |

House rules, kept throughout: the markup already contains the finished state so
no-JS is fine; `prefers-reduced-motion` skips straight to it; nothing animates
or observes while off screen.

**The hero frame** (`.frame[data-seq]`) plays the conversation typing itself out
over ~3.5s on scroll-in, with the lead record filling in beside it, then holds.
Timeline is read off `data-at` / `data-dur` attributes in the markup.

---

## 7. Bugs found and fixed — do not reintroduce

These were real, and most were only visible because something *else* broke
first. Worth reading before touching the related code.

**Animation that could leave content invisible.** `.rt` splits headings into
word spans at `opacity: 0`. If the IntersectionObserver never fires, the
heading stays blank forever. Same class of problem in the hero frame, where
typed text is removed from the DOM to be typed back in — an empty panel.
Both now have **6-second backstop timers**. Discovered because the preview pane
pauses the document timeline when hidden, which stops both transitions and
IntersectionObserver.

**A wrong price on the pricing page.** The monthly↔annual counter animated with
`requestAnimationFrame`. If that is throttled (background tab, embedded
viewer), the number froze **mid-count** — a wrong figure left on screen. Now
has a guaranteed-landing timer plus a token so a second click cancels the
first.

**The rotating headline word was clipped.** Its container width was measured
once at load — before the web font settled, and the heading is `clamp()` on
`vw`, so it changed again on resize. Container was 122px for a 243px word.
Fixed with a `ResizeObserver` on the heading (catches font load, resize and
browser zoom) plus `box-sizing: content-box` with a padded, negatively-margined
tail that gives ~10px of clip slack regardless.

**FAQ answers indented 20px left of their question.** `site.css` had
`.faq details p` (specificity 0,1,2) which outranked `components.css`'s
`.faq__a p` (0,1,1). The old block is gone; only `components.css` styles the
accordion now.

**Invisible button label.** `.hills-wrap .btn--glass` was given white text for
"the dark shader" — but the closing CTA's content sits over the shader's *pale
sky*. White on white. Now ink, with solider glass.

**Deploy: 276 MB bundle vs a 225 MB limit.** `.vercelignore` was already keeping
the source to ~2 MB; the weight was `uvicorn[standard]` (uvloop, watchfiles,
httptools, websockets, PyYAML — all compiled) and `pytest`. Neither is used by
the serverless function: Vercel invokes the ASGI app directly. Both moved to
`requirements-dev.txt`.

**Deploy: 500 on every page, `int('')` at `config.py:37`.** `REDIS_PORT` had
been added in the Vercel dashboard and left **blank**. `os.getenv` returns `''`
for a variable that exists but is empty, so the default never applied. Config
now has `env()` / `env_int()` helpers treating blank as unset everywhere, and a
malformed integer logs and falls back rather than taking the site down.

---

## 8. Deployment state

**Env vars set in Vercel (Production):** `OPENAI_API_KEY`, `ENV=production`,
`SESSION_SECRET`, `ALLOW_INDEXING=false`, `CHAT_MODEL=gpt-4.1`.
The blank `REDIS_PORT` / `REDIS_DB` / `REDIS_HOST` / `REDIS_PASSWORD` were
deleted.

**Redis: deliberately not used.** The founder's call — the site exists to be
seen rather than to sell. Without it the pages are unaffected and the agent
answers normally; what is lost is a *guarantee* that it remembers the previous
message, since each request can hit a different instance. Tested live and it
did remember ("12 people, Chicago"), because Vercel keeps routing a visitor to
the same warm instance. Adding Upstash Redis from the Storage tab is ~2 minutes
and needs no code change — `config.py` already reads `KV_URL`.

**`robots.txt` currently blocks everything** (`Disallow: /`). Intentional: it
stops Google indexing the `.vercel.app` address and then competing with the
real domain. Flip `ALLOW_INDEXING=true` and set `SITE_URL` **together**, as the
last step after the domain is attached.

**Deploy command:**
```bash
cd "C:/Users/user/American_projects/Tora_Labs" && vercel deploy --prod --yes --scope sherzod2
```

Full runbook in `DEPLOY.md`.

---

## 9. Repo hygiene

Public repo, so this was checked hard before and after pushing. Not tracked,
and must stay that way:

- `.env` — holds a live OpenAI key
- `Tora_Labs_Business_Plan — копия.pdf` — founder's personal educational
  records, financial projections, capital allocation. The site was the thing to
  publish; the plan was not.
- `chatbot ( 1 ).zip` — contains the original `config.py` with the key hardcoded
- `.venv/`, `__pycache__/`, `app.log`, `chatbot_extracted/`, `pdf_text.txt`,
  `.vercel/`, `.env.local`

Content was scanned, not just filenames — zero matches for `sk-`, private keys,
or credentialled URLs.

**Still outstanding: the OpenAI key has never been rotated.** It came from the
zip, which has been passed around, so treat it as public. It is in use on
production right now. Rotate it at platform.openai.com/api-keys and set a
monthly spend limit — the serverless rate limit is soft (per warm instance), so
the spend cap is the only hard protection.

---

## 10. Contacts (updated by the founder, commit `0e1fcdd`)

Now real, in `config.py` → `COMPANY`:
email `Toralabs@outlook.com`, phone `(804) 719-1159`, Facebook, Instagram,
LinkedIn. No longer the `hello@salesmateai.com` placeholder.

That commit missed one: `chat.js` had the old placeholder hardcoded in its
network-failure message, because it is a static file and does not read
`COMPANY`. Fixed during the Hiulix rewrite. It is the only contact detail
outside `config.py`, so it is the one that will go stale again.

---

## 11. The vertical — decided, and shipped

**Chosen: managed service providers. Brand: Hiulix.** Done on 2 October 2026;
this section now records what was decided and what it changed rather than
proposing it.

**Why MSPs, not HVAC.** HVAC was raised as an example of *narrowness*, not as a
target. The business plan's Section 9 names **Technology** (SaaS, software, *IT
service providers*, cybersecurity, technology consultancies, digital platforms)
and **Professional Services**. If that plan is being used for immigration or
investment, the site must not contradict it. MSPs are already a line in Section
9 and are HVAC-shaped anyway: an emergency story, $3–10k/mo contract value,
dense around Philadelphia, and a first sales conversation that is genuinely
standardised. Narrower still: *MSPs serving 20–250 seat SMBs*.

**The five questions** — now the spine of the whole site and of the product's
qualification logic:

1. How many users / endpoints?
2. Internal IT person, or none?
3. Current provider, and when does the agreement end?
4. Compliance driver? (SOC 2, HIPAA, CMMC, cyber insurance)
5. **Why now?** — breach, outage, provider failing, growth, audit

The fifth is the one no web form asks and the one that decides lead quality.

**Two conversations, and they are easy to confuse.** On *this* site the visitor
is an MSP owner being sold Hiulix, so the live agent qualifies MSPs: headcount
and seats under management, the MSP's own inbound volume, who answers after
hours, timeline. On a *customer's* site Hiulix talks to that MSP's prospect, and
that is where the five questions get asked. The hero frame illustrates the
second; the chat panel and `/demo` run the first. `BASE_PROMPT` says this
explicitly, because a model given both roles will start interviewing the MSP
owner as if he were the prospect.

**What changed:** content only, as predicted. Name and mark, headline, hero
conversation and lead-record fields (Company/Inbound/Handled-by → *Seats,
Internal IT, Agreement ends, Why now*), `BASE_PROMPT`, FAQ (two new entries:
"Why only MSPs?" and "Can we resell it to our own clients?"), intent examples,
pricing plan names and copy, footer, legal pages. Design, components, backend
and deploy untouched. Plan tiers keep their exact figures — only the names
changed: Small business → **Solo & small MSP**, Mid-market → **Established
MSP**, Enterprise → **MSP group & MSSP**.

**Honest limits held, and verified live against the model:**

- ConnectWise / Autotask / HaloPSA — refused as not live.
- White-label and reselling — refused as not built, not priced, *and not on the
  published roadmap*. The first draft of the prompt let the model soften this to
  "it's on the roadmap"; the wording now forbids that phrase by name. This is
  the one claim an MSP audience will push hardest on, because one MSP reaching
  40 SMBs is distribution a one-founder company cannot buy. It is still worth
  building — it just is not built.
- A non-MSP visitor is told plainly the product is not for them.
- Pricing is stated as **per MSP, not per client site**, in `config.py`, on
  `/pricing` and in the prompt.

Two places were deliberately *not* made to sound MSP-specific: the market
section still shows the five analyst estimates for conversational AI with their
attributions, because inventing an "~40,000 US MSPs" figure would break the
claims discipline in section 5 for no gain; and the privacy pillars are generic
because they are accurate.

**The name: `hiulix.com` is the founder's**, registered 2026-09-26 at NameCheap
and confirmed by him on 2 October. Checked by RDAP below rather than taken on
trust, because the registration predates the decision to use the name and an
unexplained registration would have been a reason to stop. Nothing in the code
depends on the domain yet: `SITE_URL` is still unset and `robots.txt` still
blocks everything — flip those two together, as the last step after the domain
is attached (section 8).

```bash
curl -s -o /dev/null -w "%{http_code}\n" https://rdap.verisign.com/com/v1/domain/hiulix.com
```

## 12. Other open items

- [ ] Rotate the OpenAI key, set a spend cap (section 9)
- [x] ~~Confirm who owns `hiulix.com`~~ — the founder's, confirmed 2 October 2026
- [ ] Attach `hiulix.com`, then `SITE_URL` + `ALLOW_INDEXING=true` together
- [x] ~~Decide the vertical~~ — MSPs, as Hiulix, 2 October 2026 (section 11)
- [ ] Vercel Hobby is non-commercial; Pro ($20/mo) once the site is selling
- [ ] Add Upstash Redis before anyone is seriously demoed to
- [ ] The business plan PDF still describes the product only as SalesmateAI. If
      the plan is ever revised, add Hiulix as the MSP go-to-market name rather
      than replacing SalesmateAI in it
