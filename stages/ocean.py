"""Stage 1: lookalike companies from a seed domain."""
from typing import List, Dict, Any
from models import make_company

OCEAN_BASE = "https://api.ocean.io"
OCEAN_SEARCH_URL = f"{OCEAN_BASE}/v3/search/companies"
OCEAN_BALANCE_URL = f"{OCEAN_BASE}/v2/credits/balance"

RELEVANCE_RANK = {"A": 3, "B": 2, "C": 1}


def headers(api_key: str) -> Dict[str, str]:
    return {"X-Api-Token": api_key, "Content-Type": "application/json"}


def get_credit_balance(client, api_key: str):
    try:
        return client.request_json("GET", OCEAN_BALANCE_URL, headers=headers(api_key))
    except Exception:
        return None


def find_lookalike_companies(client, seed: str, *, api_key: str, limit: int, min_relevance: str) -> List[Dict[str, Any]]:
    body = {
        "size": limit,
        "companiesFilters": {"lookalikeDomains": [seed], "excludeDomains": [seed]},
    }
    data = client.request_json("POST", OCEAN_SEARCH_URL, headers=headers(api_key), body=body)
    threshold = RELEVANCE_RANK.get(min_relevance, 1)
    out = []
    for item in data.get('companies', []):
        co = item.get('company', {})
        if not co.get('domain'):
            continue
        relevance = item.get('relevance', 'C')
        if RELEVANCE_RANK.get(relevance, 1) < threshold:
            continue
        out.append(make_company(co.get('domain').strip().lower(), name=co.get('name'), size=co.get('companySize'),
                                industries=co.get('industries') or co.get('industryCategories') or [],
                                country=co.get('primaryCountry'), revenue=co.get('revenue'),
                                employee_count=co.get('employeeCountOcean'), relevance=relevance))
    return out[:limit]
