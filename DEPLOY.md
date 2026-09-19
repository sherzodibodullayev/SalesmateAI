# Deploying SalesmateAI to Vercel

The repo is configured for Vercel: `vercel.json` sends `public/**` to the CDN
and everything else to the Python function in `api/index.py`.

**Read step 3 before you deploy.** On Vercel the agent does not work without
Redis — not "works worse", does not work. Everything else here is routine.

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

## 1. Push to Git

The project is not a repository yet:

```bash
cd "C:/Users/user/American_projects/Tora_Labs" && git init && git add -A && git commit -m "SalesmateAI site"
```

Check the secret did not go with it **before** you push:

```bash
git ls-files | grep -E "^\.env$" && echo "STOP - .env is committed" || echo "clean"
```

Then create an empty repo on GitHub and push:

```bash
git remote add origin https://github.com/<you>/<repo>.git && git branch -M main && git push -u origin main
```

If `.env` did get committed, rotate the key again — rewriting history does not
un-leak it.

---

## 2. Import the project

<https://vercel.com/new> → import the repo → **Deploy**. Leave every build
setting alone: `vercel.json` overrides them.

The first deploy will succeed and the site will render. **The agent will not
answer properly yet** — that is step 3.

### What actually gets uploaded

`vercel.json` uses `includeFiles: "**"` so the function can read `templates/`
at runtime. That is a blunt instrument, so `.vercelignore` does the trimming:
it keeps out the 95 MB virtualenv, the 6 MB chatbot archive, the business-plan
PDF and `chatbot_extracted/`. Roughly 2 MB is uploaded instead of ~102 MB. If
you add large files later, add them to `.vercelignore` too.

---

## 3. Redis — required, not optional

Vercel runs the app as serverless functions. Every request can land on a
different instance with its own memory. Without a shared store:

- every message starts a **brand-new conversation** — the agent forgets the
  previous line, so it cannot qualify anyone;
- the per-IP rate limit never accumulates, so nothing throttles abuse of your
  OpenAI budget.

`utils/redis_utils.py` falls back to a process-local dict when Redis is
missing. That is correct on a normal server and useless here.

**Set it up:**

1. Vercel project → **Storage** → **Create Database** → **Upstash Redis** →
   free plan.
2. Connect it to the project.

That is all. The integration injects `KV_URL` automatically, and `config.py`
already reads it:

```python
REDIS_URL = os.getenv("REDIS_URL") or os.getenv("KV_URL")
```

If you use a Redis provider from outside Vercel instead, set `REDIS_URL`
yourself to the `rediss://` URL it gives you.

**Verify after the next deploy:**

```bash
curl -s https://<your-project>.vercel.app/health
```

`"redis"` must say `"available"`. If it says `"memory-fallback"`, the database
is not connected and the agent will not hold a conversation.

---

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

- [ ] `status: ok`, `openai_key: set`, **`redis: available`**
- [ ] `/demo` gets a real reply
- [ ] Send two messages in a row — the second must show it **remembered the
      first**. This is the real test that step 3 worked.
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
| Upstash Redis free tier | $0 |
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

**The agent replies but forgets everything.** Redis is not connected. `/health`
will say `memory-fallback`. Back to step 3.

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
