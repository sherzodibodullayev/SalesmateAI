import os
import tempfile
import time

import openai
from dotenv import load_dotenv

load_dotenv()

# True on Vercel, where the filesystem is read-only apart from /tmp and each
# request may land on a different, cold instance with no shared memory.
SERVERLESS = bool(os.getenv("VERCEL"))

# Cache-buster appended to static URLs, so a deploy never serves stale CSS/JS.
STATIC_V = (
    os.getenv("VERCEL_GIT_COMMIT_SHA", "")[:8]
    or os.getenv("RENDER_GIT_COMMIT", "")[:8]
    or str(int(time.time()))
)

def env(name: str, default=None):
    """An unset variable and a variable set to "" mean the same thing here.

    They do not to os.getenv: a dashboard field left blank still *exists*, so
    getenv returns "" rather than the default. That crashed a production boot
    (`int("")` on REDIS_PORT) purely because the variable had been added and
    left empty, which is exactly what happens when someone fills in a hosting
    panel. Treat blank as absent everywhere instead.
    """
    value = os.getenv(name)
    return default if value is None or not value.strip() else value.strip()


def env_int(name: str, default: int) -> int:
    """Same, and never let a malformed value take the whole site down — a
    typo'd port is worth a log line and a default, not a 500 on every page."""
    raw = env(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        print(f"config: {name}={raw!r} is not a number; using {default}")
        return default


# OpenAI API configuration.
# Deliberately not fatal: the assistant needs this key, the marketing pages do
# not. Taking the whole site down over a missing chat credential is worse than
# serving the site and failing the one endpoint that needs it — and the failure
# is far easier to diagnose when /health can still answer.
OPENAI_API_KEY = env("OPENAI_API_KEY")
HAS_OPENAI_KEY = bool(OPENAI_API_KEY)
openai.api_key = OPENAI_API_KEY

CHAT_MODEL = env("CHAT_MODEL", "gpt-4.1")

# Redis configuration. REDIS_URL wins when present — it is what hosted
# providers hand you, and rediss:// carries the TLS setting and password
# without four separate variables. KV_URL is what Vercel's Upstash
# integration injects.
REDIS_URL = env("REDIS_URL") or env("KV_URL")
REDIS_HOST = env("REDIS_HOST", "localhost")
REDIS_PORT = env_int("REDIS_PORT", 6379)
REDIS_DB = env_int("REDIS_DB", 0)
REDIS_PASSWORD = env("REDIS_PASSWORD")
REDIS_PREFIX = "hiulix:"
REDIS_EXPIRATION = 60 * 60 * 24 * 7  # 7 days

# Audio uploads are transient: written, transcribed, deleted. On a read-only
# serverless filesystem that has to be the temp dir.
AUDIO_DIR = os.getenv(
    "AUDIO_DIR",
    os.path.join(tempfile.gettempdir(), "audio_uploads") if SERVERLESS else "audio_uploads",
)

# Company details injected into every template.
#
# TWO NAMES, ON PURPOSE. "Hiulix" is the product sold to managed service
# providers — the name on this site. "SalesmateAI" is the platform underneath
# it and the name used throughout the five-year business plan, so it stays:
# renaming the plan's product would put the site and the plan in conflict, and
# the plan is the document that has to hold up. Section 9 of the plan already
# names IT service providers inside the Technology vertical, which is why this
# is a narrowing rather than a pivot.
#
# Everything factual here comes from that plan: the entity details from
# Section 2.1 and Appendix A, the pricing from Section 13.1.
COMPANY = {
    "name": "Hiulix",
    "platform": "SalesmateAI",
    "vertical": "managed service providers",
    "legal_name": "Tora Labs LLC",
    "dba": "Tora Labs LLC, d/b/a SalesmateAI",
    "tagline": "The AI sales agent for managed service providers",
    "city": "Philadelphia, Pennsylvania",
    "entity_number": "0014963635",
    "entity_type": "Pennsylvania Domestic LLC",
    "filing_date": "October 30, 2025",
    "email": env("CONTACT_EMAIL", "Toralabs@outlook.com"),
    "phone": "(804) 719-1159",
    "phone_href": "tel:+18047191159",
    "facebook": "https://www.facebook.com/share/1C7jHY94cx/",
    "instagram": "https://www.instagram.com/zenith.anvarov/",
    "linkedin": env("CONTACT_LINKEDIN", "https://www.linkedin.com/company/tora-labs"),
    "linkedin_label": "Tora Labs on LinkedIn",
    # Section 13.1 — illustrative pricing architecture. The plan is explicit
    # that these are planning assumptions to be validated in Months 1–6, and
    # the pricing page says so on the page rather than only here.
    "price_smb_low": "199",
    "price_smb_high": "499",
    "price_mid_low": "750",
    "price_mid_high": "2,000",
    "price_enterprise_from": "2,500",
    # Section 13.3 — illustrative SMB unit economics.
    "price_smb_avg": "349",
}

# The founder, per Section 2.2 of the business plan. That section is explicit
# that nothing beyond its documented items should be asserted on his behalf,
# so this list stops exactly where the documentation does.
FOUNDER = {
    "name": "Nodirbek Anvarov",
    "role": "Founder & Chief Executive Officer",
    "home": "Philadelphia, Pennsylvania",
    "credentials": [
        "Organizer and sole member of Tora Labs LLC, a Pennsylvania domestic LLC "
        "filed October 30, 2025 — 100% ownership",
        "Capitalized the company with $50,000 of personal funds, with no outside "
        "investors, lenders or grant funding to date",
        "Built the SalesmateAI MVP himself and is running it through pre-launch "
        "conversational-accuracy and integration testing",
        "Conditional, fully-scholarshipped offer of admission to Cyprus International "
        "University, BA Digital Media and Marketing (2021–2022)",
        "Regional and national Taekwon-do (ITF) honors in Uzbekistan; delegate at the "
        "Asian Youth Conference (Tashkent, 2019) and an international Model UN (2020)",
    ],
}
