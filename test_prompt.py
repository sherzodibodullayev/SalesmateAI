"""Checks on the agent's system prompt.

Two things here have already gone wrong once and would go wrong silently:

  - BASE_PROMPT is one long string held together by backslash continuations. A
    continuation needs the space BEFORE the backslash, because the backslash
    eats the newline and nothing else. Drop it and two words fuse into one in
    the text the model actually reads, while the source still looks fine.

  - Prices live in config.COMPANY *and* in the prompt. PROJECT_NOTES section 4
    says to change both together; until now only memory enforced that, and the
    failure mode is the page and the agent quoting different numbers to a
    customer.

Run: .venv/Scripts/python.exe test_prompt.py   (or pytest)
"""

import io
import os
import re

from config import COMPANY
from utils.conversation_utils import BASE_PROMPT, LANGUAGES, get_system_prompt

SOURCE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                      "utils", "conversation_utils.py")

PRICE_KEYS = [k for k in COMPANY if k.startswith("price_")]


def test_continuations_keep_their_word_gap():
    """Every line ending in a backslash must end in ' \\', not '\\'."""
    bad = []
    for n, line in enumerate(io.open(SOURCE, encoding="utf-8"), 1):
        line = line.rstrip("\n")
        if line.endswith("\\") and not line.endswith(" \\"):
            bad.append("%d: %s" % (n, line[-60:]))
    assert not bad, "continuation with no space before the backslash:\n" + "\n".join(bad)


def test_prompt_renders_in_every_language():
    for code, name in LANGUAGES.items():
        prompt = get_system_prompt(code)
        assert "[LANGUAGE: %s]" % code in prompt
        assert "Reply in %s." % name in prompt
        assert "{" not in prompt.replace("{code}", ""), "unfilled placeholder in %s" % code


def test_every_published_price_is_in_the_prompt():
    """config.py and the prompt must not be able to quote different numbers."""
    prompt = get_system_prompt("en")
    missing = [k for k in PRICE_KEYS
               if k != "price_smb_avg" and COMPANY[k] not in prompt]
    assert not missing, (
        "price(s) in config.COMPANY that the agent was never told about: %s. "
        "Change config.py and BASE_PROMPT together." % missing)


def test_the_agent_knows_which_product_it_is():
    prompt = get_system_prompt("en")
    assert "HIULIX" in prompt and COMPANY["name"] == "Hiulix"
    # The platform name stays: it is what the business plan calls the product,
    # and the agent has to be able to explain the relationship.
    assert COMPANY["platform"] in prompt


def test_the_refusals_that_matter_are_still_stated():
    """Each of these was verified live against the model; losing one is silent."""
    prompt = get_system_prompt("en")
    for required in ("not shipped", "ConnectWise", "white-label",
                     "no paying customers", "planning assumptions"):
        assert required in prompt, "prompt no longer says %r" % required


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
    print("\nall prompt checks passed")
