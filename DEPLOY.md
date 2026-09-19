# Deploying SalesmateAI to Vercel

The repo is configured for Vercel: `vercel.json` sends `public/**` to the CDN
and everything else to the Python function in `api/index.py`.

You can ship without Redis. Step 3 says exactly what you give up.

---

## 0. Rotate the OpenAI key first

The key in `.env` came from the chatbot zip, which has been passed around.
Treat it as public.

1. <https://platform.openai.com/api-keys> → revoke the old key, create a new one.
2. While you are there, set a **monthly spend limit** on the project. The agent
   is about to be reachable by anyone on the internet, and every visitor
   message is a paid request.
3. The new key goes into Vercel's environment variables (step 4), never into
   the repo.

`.env` is already covered by both `.gitignore` and `.vercelignore`.

---

## 1. The repo

Already done — <https://github.com/sherzodibodullayev/SalesmateAI>, `main`.

`.env`, the business-plan PDF, the chatbot zip and the virtualenv are all
excluded, and the pushed tree was scanned for credential patterns before it
went up. For future pushes, the same check:

```bash
git ls-files | grep -E "^\.env$|\.pdf$|\.zip$" && echo "STOP" || echo "clean"
```

---

## 2. Import the project

<https://vercel.com/new> → import the repo → **Deploy**. Leave every build
setting alone: `vercel.json` overrides them.

That is enough to get the site live. The agent needs `OPENAI_API_KEY` before
it will answer — step 4.

### What actually gets uploaded

`vercel.json` uses `includeFiles: "**"` so the function can read `templates/`
at runtime. That is a blunt instrument, so `.vercelignore` does the trimming:
it keeps out the 95 MB virtualenv, the 6 MB chatbot archive, the business-plan
PDF and `chatbot_extracted/`. Roughly 2 MB is uploaded instead of ~102 MB. If
you add large files later, add them to `.vercelignore` too.

---

## 3. Redis — optional, and what skipping it costs

Vercel runs the app as serverless functions: each request can land on a
different instance with its own memory. Two things depend on shared state.

**Rate limiting — fine without it.** `utils/rate_limiting.py` falls back to a
per-process counter, 40 requests per IP per hour. On serverless that cap is
per warm instance rather than global, so it is a soft limit, not an exact one.
It is still real protection, and your OpenAI spend cap (step 0) is the hard
backstop either way.

**Conversation memory — this is what you lose.** Without a shared store the
agent's memory of a thread lives on whichever instance answered. In practice
Vercel keeps routing a visitor to the same warm instance, so a conversation
usually holds together. But it is not guaranteed: after an idle gap, or under
any concurrency, the next message can land elsewhere and the agent will have
forgotten everything said before it. It will not error — it will just answer
as though the visitor had only ever said that one line.

So:

| | Without Redis | With Redis |
|---|---|---|
| Marketing pages | perfect | perfect |
| Agent answers | yes | yes |
| Remembers the previous message | usually | always |
| Rate limit | soft, per instance | exact |

**If the site is there to exist rather than to sell** — a link on a business
plan, something to show it is real — ship without it. The pages are the point
and they are unaffected, and a visitor who sends one message gets a perfectly
good answer.

**Add it the moment someone is actually being demoed to.** An agent that
forgets the prospect's company name halfway through is worse than no agent.

### Adding it later takes about two minutes

1. Vercel project → **Storage** → **Create Database** → **Upstash Redis** →
   free plan.
2. Connect it to the project. Redeploy.

No code change. The integration injects `KV_URL`, which `config.py` already
reads:

```python
REDIS_URL = os.getenv("REDIS_URL") or os.getenv("KV_URL")
```

`/health` tells you which mode you are in — `"redis": "available"` or
`"memory-fallback"`.

## 4. Environment variables

Vercel project → **Settings** → **Environment Variables** → Production.

| Name | Value | Why |
|---|---|---|
| `OPENAI_API_KEY` | the new key from step 0 | the agent |
| `ENV` | `production` | makes `SESSION_SECRET` mandatory |
| `SESSION_SECRET` | see below | signs the session cookie |
| `CONTACT_EMAIL` | your real inbox | otherwise the site shows `hello@salesmateai.com`, which does not exist |
| `CONTACT_LINKEDIN` | the company page URL | footer link |
| `ALLOW_INDEXING` | `false` for now | step 5 |
| `CHAT_MODEL` | `gpt-4.1` | optional, this is the default |
| `ALLOWED_ORIGINS` | leave empty | the browser calls the API same-origin; CORS never applies |

Generate the session secret:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Redeploy after adding variables — Vercel does not apply them to an existing
build.

---

## 5. Domain, then indexing — in that order

1. Vercel → **Settings** → **Domains** → add `salesmateai.com` and `www`.
2. Add the DNS records Vercel shows you at your registrar; wait for the
   certificate.
3. **Only then**, in Environment Variables:
   - `SITE_URL` = `https://salesmateai.com`
   - `ALLOW_INDEXING` = `true`
4. Redeploy.

Until `ALLOW_INDEXING` is true, `robots.txt` blocks everything. That is
deliberate: it stops Google indexing the `*.vercel.app` address and then
competing with your real domain for the same pages. `SITE_URL` makes the
canonical tags, `og:url` and the sitemap point at the domain rather than at
whatever host served the request.

```bash
curl -s https://salesmateai.com/robots.txt
```

Should show `Allow: /` and a `Sitemap:` line — not `Disallow: /`.

---

## 6. Things that behave differently on Vercel

| | Why it is fine |
|---|---|
| Audio uploads write to `/tmp` | `config.py` switches automatically when it sees `VERCEL` in the environment. The file is deleted after transcription either way. |
| The WebSocket route will not work | Nothing in the UI uses it. It exists for hosts that support it. |
| `public/` is not inside the function | `main.py` detects the missing directory and skips mounting `StaticFiles`; the CDN serves `/static/*` instead. |
| Cold starts | First request after idle takes a second or two on the free tier. |
| No `app.log` | The filesystem is read-only. Logging goes to stdout, which Vercel collects. |

---

## 7. Check it before you send anyone the link

```bash
curl -s https://<your-domain>/health
```

- [ ] `status: ok`, `openai_key: set`
- [ ] `redis` says `available`, or `memory-fallback` if you chose to skip it
- [ ] `/demo` gets a real reply
- [ ] Send two messages in a row. If you added Redis the second must remember
      the first; on memory-fallback it usually will, and an occasional lapse
      is the known trade from step 3.
- [ ] Ask `"Do you integrate with HubSpot? Is voice available?"` — it should
      refuse to promise either
- [ ] Ask `"just get me a human"` — it should stop selling and take an email
- [ ] `/pricing` — the Monthly/Annual switch lands on real figures
- [ ] Footer email is yours, not `hello@salesmateai.com`
- [ ] `robots.txt` matches what you intend
- [ ] Open it on a phone
- [ ] Spend limit set on the OpenAI project

---

## Cost

| | Monthly |
|---|---|
| Vercel Hobby | $0 |
| Upstash Redis free tier (optional) | $0 |
| Domain | ~$1 |
| OpenAI | usage-based — **set a cap** |

Vercel's Hobby plan is for non-commercial use. Once the site is selling
something, their terms want you on Pro ($20/month).

OpenAI is the only figure that moves with traffic. Set the cap before you
publicise the link, not after.

---

## If something goes wrong

**The whole site 500s.** `api/index.py` catches import errors and serves the
reason as plain text instead of a bare 500 — open the URL and read it. It
redacts credentials before printing.

**Pages load, the agent 503s.** `OPENAI_API_KEY` is missing or invalid. Check
`/health`.

**The agent replies but forgets the previous message.** Expected on
memory-fallback; see step 3. Add Upstash Redis to make it consistent.

**A CSS or JS change does not show.** Static URLs are cache-busted with the
commit SHA, so a real deploy always breaks the cache. If you are looking at a
preview deployment, check you are on the production URL.

---

## Where things live

| To change | Edit |
|---|---|
| What the agent says or refuses | `utils/conversation_utils.py` → `BASE_PROMPT` |
| Prices, entity details, contact | `config.py` → `COMPANY`, or the Vercel env vars |
| Colours, type, spacing | `public/static/css/site.css` → `:root` |
| The ported animations | `public/static/css/components.css` + `js/components.js` |

If you change a price or ship a feature, change it in **both** `config.py` and
`BASE_PROMPT`, or the page and the agent will contradict each other in front of
a customer.

---

*`render.yaml` is also in the repo. Ignore it unless you ever want a host where
Redis is optional and WebSockets work.*
