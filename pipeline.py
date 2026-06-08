"""Orchestrator (CLI entrypoint) for the Python outreach pipeline."""
from http_client import HttpClient
from config import load_dotenv, build_settings
from models import dedup_key
from email_copy import build_email_copy
from stages import ocean as ocean_mod, prospeo as prospeo_mod, brevo as brevo_mod
import console as ui
import sys


default_deps = {
    'make_client': lambda: HttpClient(min_interval=1.2),
    'build_email_copy': build_email_copy,
    'ui': ui,
    'ocean': ocean_mod,
    'prospeo': prospeo_mod,
    'brevo': brevo_mod,
}


def dedupe(contacts):
    seen = set()
    out = []
    for c in contacts:
        key = dedup_key(c)
        if key in seen:
            continue
        seen.add(key)
        out.append(c)
    return out


def run(settings, deps=None):
    deps = deps or default_deps
    make_client = deps['make_client']
    ocean = deps['ocean']
    prospeo = deps['prospeo']
    brevo = deps['brevo']
    build_email_copy = deps['build_email_copy']
    ui = deps['ui']
    client = make_client()

    ui.info(f"Seed domain: {settings['seedDomain']}")
    bal = ocean.get_credit_balance(client, settings['oceanApiKey'])
    if bal is not None:
        ui.info(f"Ocean credits: {bal}")
    acct = prospeo.get_account_info(client, settings['prospeoApiKey'])
    if acct and acct.get('response'):
        ui.info(f"Prospeo credits: {acct.get('response').get('remaining_credits')}")

    ui.stage_banner(1, "Ocean.io — lookalike companies", f"seed {settings['seedDomain']} → similar domains")
    companies = ocean.find_lookalike_companies(client, settings['seedDomain'], api_key=settings['oceanApiKey'], limit=settings['maxCompanies'], min_relevance=settings['minRelevance'])
    ui.info(f"Found {len(companies)} companies (relevance ≥ {settings['minRelevance']})")
    ui.companies_table(companies)

    ui.stage_banner(2, "Prospeo — decision-makers", "domains → C-suite/VP + LinkedIn URLs")
    contacts = []
    for co in companies:
        try:
            found = prospeo.find_decision_makers(client, co['domain'], api_key=settings['prospeoApiKey'], max_contacts=settings['maxContacts'])
            for c in found:
                if not c.get('companyName'):
                    c['companyName'] = co.get('name')
            ui.info(f"{co['domain']}: {len(found)} contacts")
            contacts.extend(found)
        except Exception as err:
            ui.warn(f"{co.get('domain')}: skipped ({err})")
    contacts = dedupe(contacts)
    ui.info(f"{len(contacts)} unique contacts")
    ui.contacts_table(contacts, with_email=False)

    ui.stage_banner(3, "Prospeo — verified work emails", "person_ids → verified emails")
    verified = []
    if contacts:
        try:
            verified = prospeo.resolve_emails(client, contacts, api_key=settings['prospeoApiKey'])
        except Exception as err:
            ui.warn(f"email resolution failed: {err}")
    ui.info(f"{len(verified)} contacts with VERIFIED emails")
    ui.contacts_table(verified, with_email=True)

    if verified and settings.get('confirm') and not settings.get('dryRun'):
        ui.warn(f"About to send {len(verified)} real emails from {settings.get('senderEmail')}.")
        answer = input("Type 'yes' to send: ").strip().lower()
        if answer != 'yes':
            ui.warn("Aborted before sending.")
            aborted = ui.build_summary(settings['seedDomain'], companies, verified, [])
            ui.print_summary(aborted)
            return aborted

    ui.stage_banner(4, "Brevo — send personalized outreach", "emails → outreach sent")
    if verified and not settings.get('dryRun'):
        try:
            brevo.preflight_account(client, api_key=settings['brevoApiKey'])
        except Exception as err:
            ui.warn(f"Brevo preflight failed: {err}")
    results = []
    for c in verified:
        copy = build_email_copy(c, sender_name=settings.get('senderName'))
        res = brevo.send_outreach(client, c, copy, api_key=settings.get('brevoApiKey'), sender_email=settings.get('senderEmail'), sender_name=settings.get('senderName'), reply_to=settings.get('replyTo'), dry_run=settings.get('dryRun'), test_email=settings.get('testEmail'))
        results.append(res)
    ui.send_table(results)

    summary = ui.build_summary(settings['seedDomain'], companies, verified, results)
    ui.print_summary(summary)
    return summary


def main(argv=None):
    load_dotenv()
    try:
        settings = build_settings(argv)
    except Exception as err:
        ui.warn(str(err))
        return 2
    run(settings)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
