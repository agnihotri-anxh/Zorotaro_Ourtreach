"""Model factories and dedup helper."""
from typing import Dict, Any


def make_company(domain: str, name: str = None, size: Any = None, industries=None,
                 country: str = None, revenue: Any = None, employee_count: Any = None,
                 relevance: str = "C") -> Dict[str, Any]:
    return {
        "domain": domain,
        "name": name,
        "size": size,
        "industries": industries or [],
        "country": country,
        "revenue": revenue,
        "employeeCount": employee_count,
        "relevance": relevance,
    }


def make_contact(full_name: str, company_domain: str, person_id: str = None, first_name: str = None,
                 job_title: str = None, seniority: str = None, department: str = None,
                 linkedin_url: str = None, company_name: str = None, email: str = None,
                 email_status: str = None) -> Dict[str, Any]:
    return {
        "fullName": full_name,
        "companyDomain": company_domain,
        "personId": person_id,
        "firstName": first_name,
        "jobTitle": job_title,
        "seniority": seniority,
        "department": department,
        "linkedinUrl": linkedin_url,
        "companyName": company_name,
        "email": email,
        "emailStatus": email_status,
    }


def dedup_key(c: Dict[str, Any]) -> str:
    if c.get("email"):
        return c.get("email", "").strip().lower()
    return c.get("personId") or c.get("linkedinUrl") or f"{(c.get('fullName') or '').lower()}@{c.get('companyDomain') or ''}"
