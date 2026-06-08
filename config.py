"""Config helpers: dotenv loader and CLI settings builder."""
from typing import Dict, Any
import os
import argparse

REQUIRED_KEYS = ["OCEAN_API_KEY", "PROSPEO_API_KEY", "BREVO_API_KEY",
                 "BREVO_SENDER_EMAIL", "BREVO_SENDER_NAME"]

DECISION_MAKER_SENIORITIES = [
    "C-Suite", "Vice President", "Director", "Head", "Founder/Owner", "Partner",
]


def load_dotenv(path: str = ".env", env: Dict[str, str] = None):
    env = env or os.environ
    try:
        with open(path, "r", encoding="utf8") as f:
            text = f.read()
    except Exception:
        return
    for line in text.splitlines():
        trimmed = line.strip()
        if not trimmed or trimmed.startswith("#"):
            continue
        if "=" not in trimmed:
            continue
        key, val = trimmed.split("=", 1)
        key = key.strip()
        val = val.strip()
        if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
            val = val[1:-1]
        if env.get(key) is None:
            env[key] = val


def build_settings(argv=None, env=None) -> Dict[str, Any]:
    env = env or os.environ
    missing = [k for k in REQUIRED_KEYS if not env.get(k)]
    if missing:
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")

    parser = argparse.ArgumentParser(prog="pipeline.py")
    parser.add_argument("seed_domain")
    parser.add_argument("--max-companies", type=int, default=10)
    parser.add_argument("--max-contacts", type=int, default=3)
    parser.add_argument("--min-relevance", type=str, default="B")
    parser.add_argument("--confirm", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--test-email", type=str, default=None)

    args = parser.parse_args(argv)
    min_relevance = (args.min_relevance or "B").upper()
    if min_relevance not in ("A", "B", "C"):
        raise RuntimeError(f"--min-relevance must be A, B, or C (got {min_relevance})")
    if args.max_companies < 1 or args.max_contacts < 1:
        raise RuntimeError("--max-companies and --max-contacts must be positive integers")

    return {
        "seedDomain": args.seed_domain.strip().lower(),
        "oceanApiKey": env.get("OCEAN_API_KEY"),
        "prospeoApiKey": env.get("PROSPEO_API_KEY"),
        "brevoApiKey": env.get("BREVO_API_KEY"),
        "senderEmail": env.get("BREVO_SENDER_EMAIL"),
        "senderName": env.get("BREVO_SENDER_NAME"),
        "replyTo": env.get("BREVO_REPLY_TO") or env.get("BREVO_SENDER_EMAIL"),
        "maxCompanies": args.max_companies,
        "maxContacts": args.max_contacts,
        "minRelevance": min_relevance,
        "confirm": bool(args.confirm),
        "auto": not bool(args.confirm),
        "dryRun": bool(args.dry_run),
        "testEmail": args.test_email,
    }
