"""Stage 4: send personalized outreach via Brevo."""
from typing import Dict, Any
from http_client import ApiError

BREVO_BASE = "https://api.brevo.com/v3"
SEND_URL = f"{BREVO_BASE}/smtp/email"
ACCOUNT_URL = f"{BREVO_BASE}/account"


def _headers(api_key: str) -> Dict[str, str]:
    return {"api-key": api_key, "Content-Type": "application/json", "Accept": "application/json"}


def preflight_account(client, *, api_key: str):
    return client.request_json("GET", ACCOUNT_URL, headers=_headers(api_key))


def send_outreach(client, contact: Dict[str, Any], copy: Dict[str, Any], *, api_key: str,
                  sender_email: str, sender_name: str, reply_to: str, dry_run: bool = False, test_email: str = None) -> Dict[str, Any]:
    recipient = test_email or contact.get('email')
    if not recipient:
        return {'contact': contact, 'status': 'skipped', 'messageId': None, 'detail': 'no email'}
    if dry_run:
        return {'contact': contact, 'status': 'dry_run', 'messageId': None, 'detail': f'would send to {recipient}'}

    body = {
        'sender': {'name': sender_name, 'email': sender_email},
        'to': [{'email': recipient, 'name': contact.get('fullName')}],
        'replyTo': {'email': reply_to, 'name': sender_name},
        'subject': copy.get('subject'),
        'htmlContent': copy.get('html'),
        'textContent': copy.get('text'),
        'params': copy.get('params'),
        'tags': ['cold-outreach'],
    }
    try:
        data = client.request_json("POST", SEND_URL, headers=_headers(api_key), body=body)
        return {'contact': contact, 'status': 'sent', 'messageId': data.get('messageId'), 'detail': None}
    except Exception as err:
        if isinstance(err, ApiError):
            return {'contact': contact, 'status': 'error', 'messageId': None, 'detail': getattr(err, 'detail', str(err))}
        return {'contact': contact, 'status': 'error', 'messageId': None, 'detail': str(err)}
