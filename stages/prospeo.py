"""Stage 2/3: find decision-makers and resolve verified emails via Prospeo API."""
from typing import List, Dict, Any
from models import make_contact
from config import DECISION_MAKER_SENIORITIES
from http_client import ApiError

PROSPEO_BASE = "https://api.prospeo.io"
SEARCH_PERSON_URL = f"{PROSPEO_BASE}/search-person"
ENRICH_URL = f"{PROSPEO_BASE}/enrich-person"
ACCOUNT_URL = f"{PROSPEO_BASE}/account-information"


def _headers(api_key: str) -> Dict[str, str]:
    return {"X-KEY": api_key, "Content-Type": "application/json"}


def get_account_info(client, api_key: str):
    try:
        return client.request_json("GET", ACCOUNT_URL, headers=_headers(api_key))
    except Exception:
        return None


def find_decision_makers(client, domain: str, *, api_key: str, max_contacts: int, seniorities: List[str] = None) -> List[Dict[str, Any]]:
    contacts: List[Dict[str, Any]] = []
    page = 1
    seniorities = seniorities or DECISION_MAKER_SENIORITIES
    while len(contacts) < max_contacts:
        body = {
            "page": page,
            "filters": {
                "company": {"websites": {"include": [domain]}},
                "person_seniority": {"include": seniorities},
            },
        }
        try:
            data = client.request_json("POST", SEARCH_PERSON_URL, headers=_headers(api_key), body=body)
        except Exception as err:
            if isinstance(err, ApiError) and getattr(err, 'status', None) == 429:
                reset = err.rate_headers.get('dailyResetSeconds') if err.rate_headers else None
                hrs = f" Resets in ~{max(1, round(float(reset)/3600))}h." if reset else ""
                raise RuntimeError(f"Prospeo search daily quota exhausted (FREE plan).{hrs}")
            if isinstance(err, ApiError) and err.detail and 'NO_RESULTS' in str(err.detail).upper():
                break
            raise
        results = data.get('results', [])
        for r in results:
            p = r.get('person') or {}
            co = r.get('company') or {}
            if not p.get('full_name'):
                continue
            contacts.append(make_contact(
                full_name=p.get('full_name'),
                company_domain=domain,
                person_id=p.get('person_id'),
                first_name=p.get('first_name'),
                job_title=p.get('job_title'),
                seniority=p.get('seniority'),
                department=p.get('department'),
                linkedin_url=p.get('linkedin_url'),
                company_name=co.get('company_name'),
            ))
            if len(contacts) >= max_contacts:
                break
        total_page = (data.get('pagination') or {}).get('total_page') or page
        if page >= total_page or not results:
            break
        page += 1
    return contacts[:max_contacts]


def resolve_emails(client, contacts: List[Dict[str, Any]], *, api_key: str, only_verified: bool = True) -> List[Dict[str, Any]]:
    enriched: List[Dict[str, Any]] = []
    for contact in contacts:
        if not contact.get('personId'):
            continue
        try:
            data = client.request_json("POST", ENRICH_URL, headers=_headers(api_key), body={
                'only_verified_email': only_verified,
                'enrich_mobile': False,
                'data': {'person_id': contact.get('personId')},
            })
        except Exception as err:
            if isinstance(err, ApiError) and getattr(err, 'status', None) == 429:
                continue
            raise
        p = data.get('person') or {}
        email_obj = p.get('email') or {}
        if str(email_obj.get('status', '')).upper() == 'VERIFIED' and email_obj.get('email'):
            contact['email'] = email_obj.get('email')
            contact['emailStatus'] = email_obj.get('status')
            if p.get('linkedin_url'):
                contact['linkedinUrl'] = p.get('linkedin_url')
            if not contact.get('jobTitle') and p.get('current_job_title'):
                contact['jobTitle'] = p.get('current_job_title')
            enriched.append(contact)
    return enriched
