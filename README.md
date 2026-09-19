# SalesmateAI — Tora Labs LLC

Marketing site and live AI sales agent for SalesmateAI, the product of
Tora Labs LLC (Philadelphia, PA). FastAPI + Jinja templates + vanilla JS.

The agent on this site is the product doing its own job: it greets the
visitor, classifies intent, answers from approved material, qualifies, and
hands over to the founder when asked. Content comes from the company's
five-year business plan.

## Run it

```bash
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt -r requirements-dev.txt   # Windows
cp .env.example .env                                          # then fill in OPENAI_API_KEY
.venv/Scripts/python.exe -m uvicorn main:app --reload --port 8010
```

Then open http://localhost:8010.

The marketing pages work without an API key; only `/api/chat` fails (503).
`/health` reports whether the key is set, and `/health?deep=1` actually calls
OpenAI.

## Layout

```
main.py                  routes, page context, robots/sitemap
config.py                COMPANY / FOUNDER facts, keys, Redis, model
models.py                request/response shapes
routes/chat_routes.py    /api/chat, /api/audio-question, conversation CRUD
utils/conversation_utils.py   the agent's system prompt  ← edit this to change behaviour
utils/redis_utils.py     conversation store, falls back to process memory
utils/rate_limiting.py   per-IP limit
templates/               base + index, demo, pricing, company, privacy, terms
public/static/           css, js, images  (served by the CDN on Vercel)
api/index.py             Vercel serverless entry point
```

## Where to change things

| To change | Edit |
|---|---|
| What the agent says or refuses to say | `utils/conversation_utils.py` → `BASE_PROMPT` |
| Prices, entity details, contact email | `config.py` → `COMPANY` (or `.env`) |
| Founder bio items | `config.py` → `FOUNDER` |
| Languages the agent answers in | `utils/conversation_utils.py` → `LANGUAGES`, plus the buttons in `templates/base.html` |
| Colours, type, spacing | `public/static/css/site.css` → `:root` tokens |

Contact details are placeholders (`hello@salesmateai.com`, the LinkedIn URL).
Set the real ones in `.env`; every template reads them from `config.py`, so no
template needs touching.

## Claims discipline

The plan the site is built from is careful to separate verified facts from
planning assumptions, and the site keeps that separation. Specifically:

- Prices are labelled as published **planning assumptions**, not quotes.
- "No customers, no revenue yet" is stated plainly, including by the agent.
- Voice AI and specific CRM integrations are described as **planned**.
- Market figures are attributed to the analyst firm that published them, with
  a range shown rather than one flattering number.
- The founder section lists documented items only; where the record shows an
  offer or an application rather than a completed qualification, it says so.
- No stock portrait stands in for the founder; a monogram is used instead.

The system prompt enforces the same rules on the agent — it is told which
figures it may state and to defer to the founder for anything else. If you
change a price or ship a feature, change it in **both** `config.py` and
`BASE_PROMPT`, or the page and the agent will disagree with each other.

## Deploying

See **[DEPLOY.md](DEPLOY.md)** for the Vercel runbook.

Redis is optional there. Without it the pages are unaffected and the agent
still answers; what you lose is a guarantee that it remembers the previous
message, because each request can hit a different instance. Fine for a site
that exists to be seen; add Upstash Redis from the Storage tab before anyone
is actually demoed to.

Rotate the OpenAI key first, then attach the domain and set `SITE_URL` +
`ALLOW_INDEXING=true` together as the last step.

## Notes

- Audio questions are transcribed with Whisper; the uploaded file is deleted
  straight after. On serverless it is written to the temp dir, which is the
  only writable path there.
- `chat.js` is the single chat client — the floating panel and the `/demo`
  console share element ids on purpose.
- The WebSocket route exists for hosts that support it. Nothing in the UI uses
  it; serverless platforms do not support it.
