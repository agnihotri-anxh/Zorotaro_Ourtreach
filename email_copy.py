"""Build personalized email copy."""
from typing import Dict, Any


def _first_name_of(contact: Dict[str, Any]) -> str:
    if contact.get('firstName'):
        return contact.get('firstName')
    return (contact.get('fullName') or 'there').split()[:1][0]


def build_email_copy(contact: Dict[str, Any], *, sender_name: str) -> Dict[str, Any]:
    company = contact.get('companyName') or contact.get('companyDomain')
    params = {
        'firstName': _first_name_of(contact),
        'company': company,
        'role': contact.get('jobTitle') or 'your team',
        'senderName': sender_name,
    }
    subject = "Quick idea for {{params.company}}, {{params.firstName}}"
    html = (
        "<html><body style='font-family:Arial,sans-serif;font-size:15px;color:#222'>"
        "<p>Hi {{params.firstName}},</p>"
        "<p>I came across {{params.company}} and was impressed by what your team is building. "
        "I build automation that turns a single target account into a fully-researched, "
        "ready-to-send outreach list — no manual prospecting.</p>"
        "<p>Worth a quick 10-minute call to show how it'd work for {{params.company}}?</p>"
        "<p>Best,<br>{{params.senderName}}</p>"
        "</body></html>"
    )
    text = (
        "Hi {{params.firstName}},\n\n"
        "I came across {{params.company}} and was impressed by what your team is building. "
        "I build automation that turns a single target account into a fully-researched, "
        "ready-to-send outreach list — no manual prospecting.\n\n"
        "Worth a quick 10-minute call to show how it'd work for {{params.company}}?\n\n"
        "Best,\n{{params.senderName}}"
    )
    return {'subject': subject, 'html': html, 'text': text, 'params': params}
