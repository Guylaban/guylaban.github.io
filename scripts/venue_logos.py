"""Map a publication venue string to a journal/conference/publisher logo.

This module is the single source of truth for how a venue name is turned into
a logo badge (the SVG files in ``assets/logos``) and a publication ``type``.
It is used by ``fetch_publications.py`` when new publications are pulled from
Google Scholar, so every newly discovered paper automatically gets the right
logo next to it.

Add new rules to ``LOGO_RULES`` (checked top-to-bottom, first match wins).
Each rule is ``(list_of_keywords, logo_name, type)`` where ``logo_name`` maps
to ``assets/logos/<logo_name>.svg``.
"""

from __future__ import annotations

# Ordered, most-specific-first. The first rule whose *any* keyword appears
# (case-insensitively) in the venue string wins.
LOGO_RULES: list[tuple[list[str], str, str]] = [
    # --- Preprint servers (check before publishers so e.g. "arXiv" wins) ---
    (["arxiv"], "arxiv", "preprint"),
    (["psyarxiv"], "osf", "preprint"),
    (["biorxiv", "medrxiv"], "preprint", "preprint"),
    (["osf", "open science framework"], "osf", "preprint"),

    # --- Nature portfolio ---
    (["nature"], "nature", "journal"),

    # --- ACL / computational linguistics ---
    (["acl", "association for computational linguistics", "emnlp",
      "naacl", "findings of"], "acl", "conference"),

    # --- ACM-published journals (Transactions) come before ACM conferences ---
    (["acm transactions"], "acm", "journal"),

    # --- ACM conference venues ---
    (["chi conference", "human factors in computing",
      "human-agent interaction", "intelligent virtual agents",
      "conversational user interfaces", "intelligent user interfaces",
      "designing interactive systems", "ubicomp", "cscw",
      "acm/ieee international conference on human-robot",
      "acm international conference"], "acm", "conference"),

    # --- IEEE venues & transactions ---
    (["ieee transactions"], "ieee", "journal"),
    (["ieee", "robot and human interactive communication", "ro-man",
      "intelligent robots and systems", "iros",
      "affective computing and intelligent interaction"], "ieee", "conference"),

    # --- Elsevier ---
    (["computers in human behavior", "elsevier", "sciencedirect",
      "computers & education"], "elsevier", "journal"),

    # --- De Gruyter ---
    (["paladyn", "journal of behavioral robotics", "de gruyter"],
     "degruyter", "journal"),

    # --- Frontiers ---
    (["frontiers"], "frontiers", "journal"),

    # --- Springer journals & conference proceedings ---
    (["international journal of social robotics", "current robotics reports",
      "intelligent service robotics", "chatbot research and design",
      "affective science", "springer", "lecture notes in computer science",
      "computing"], "springer", "journal"),

    # --- Theses / institutional ---
    (["university of glasgow", "glasgow"], "glasgow", "thesis"),

    # --- Reports / misc scholarly ---
    (["dagstuhl"], "default", "report"),
]


def resolve_logo(venue: str) -> tuple[str, str]:
    """Return ``(logo_name, publication_type)`` for a venue string.

    Falls back to the generic ``default`` document logo when nothing matches.
    """
    text = (venue or "").lower()
    for keywords, logo, ptype in LOGO_RULES:
        if any(k in text for k in keywords):
            return logo, ptype
    # Generic fallback: still infer a reasonable type from common wording.
    if any(k in text for k in ["conference", "proceedings", "symposium",
                               "workshop", "congress"]):
        return "default", "conference"
    if "journal" in text or "transactions" in text:
        return "default", "journal"
    if "dissertation" in text or "thesis" in text:
        return "default", "thesis"
    return "default", "article"


if __name__ == "__main__":  # tiny self-test / debugging helper
    samples = [
        "IEEE Transactions on Affective Computing",
        "Proceedings of the 12th International Conference on Human-Agent Interaction",
        "International Journal of Social Robotics",
        "Frontiers in Psychiatry",
        "arXiv preprint",
        "Nature Machine Intelligence",
        "Paladyn, Journal of Behavioral Robotics",
        "Some Unknown Workshop",
    ]
    for s in samples:
        print(f"{resolve_logo(s)!s:<24} <- {s}")
