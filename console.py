"""ANSI console helpers and summary builder."""
from typing import List, Any, Dict
import sys

C = {
    "reset": "\x1b[0m", "bold": "\x1b[1m", "dim": "\x1b[2m", "cyan": "\x1b[36m",
    "green": "\x1b[32m", "yellow": "\x1b[33m", "red": "\x1b[31m",
}


def paint(color: str, s: str) -> str:
    return f"{C.get(color, C['reset'])}{s}{C['reset']}"


def stage_banner(number: int, title: str, subtitle: str = ""):
    line = "─" * 64
    sys.stdout.write(f"\n{paint('cyan', line)}\n")
    sys.stdout.write(f"{paint('cyan', paint('bold', f'  STAGE {number}'))}  {paint('bold', title)}\n")
    if subtitle:
        sys.stdout.write(f"  {paint('dim', subtitle)}\n")
    sys.stdout.write(f"{paint('cyan', line)}\n")


def info(msg: str):
    sys.stdout.write(f"  {paint('dim', '›')} {msg}\n")


def warn(msg: str):
    sys.stdout.write(f"  {paint('yellow', '⚠')}  {msg}\n")


def _render_table(title: str, columns: List[str], rows: List[List[Any]]):
    sys.stdout.write(f"\n  {paint('bold', title)}\n")
    widths = []
    for i, c in enumerate(columns):
        # Compute max between header length and any row cell length; handle empty rows
        max_cell = 0
        for r in rows:
            cell = str(r[i]) if i < len(r) else ''
            if len(cell) > max_cell:
                max_cell = len(cell)
        widths.append(max(len(c), max_cell))

    def fmt(cells):
        return "  ".join(str(cells[i] if i < len(cells) else '').ljust(widths[i]) for i in range(len(widths)))
    sys.stdout.write(f"  {paint('dim', fmt(columns))}\n")
    for r in rows:
        sys.stdout.write(f"  {fmt(r)}\n")
    if not rows:
        sys.stdout.write(f"  {paint('dim', '(none)')}\n")


def companies_table(companies: List[Dict[str, Any]]):
    _render_table("Lookalike companies", ["Domain", "Rel", "Size", "Industry", "Country"],
                  [[c.get('domain'), c.get('relevance'), c.get('size') or '-', (c.get('industries') or ['-'])[0], c.get('country') or '-'] for c in companies])


def contacts_table(contacts: List[Dict[str, Any]], with_email: bool = False):
    cols = ["Name", "Title", "Company", "Email"] if with_email else ["Name", "Title", "Company", "LinkedIn"]
    rows = []
    for c in contacts:
        if with_email:
            rows.append([c.get('fullName'), c.get('jobTitle') or '-', c.get('companyDomain'), c.get('email') or '-'])
        else:
            rows.append([c.get('fullName'), c.get('jobTitle') or '-', c.get('companyDomain'), c.get('linkedinUrl') or '-'])
    _render_table("Contacts", cols, rows)


def send_table(results: List[Dict[str, Any]]):
    rows = []
    for r in results:
        color = {'sent': 'green', 'dry_run': 'cyan', 'skipped': 'yellow', 'error': 'red'}.get(r.get('status'), 'reset')
        rows.append([r.get('contact', {}).get('email') or r.get('contact', {}).get('fullName'), paint(color, r.get('status') or ''), r.get('messageId') or r.get('detail') or '-'])
    _render_table("Send results", ["Recipient", "Status", "Detail"], rows)


def build_summary(seed: str, companies: List[Any], contacts: List[Any], results: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        'seed': seed,
        'companies': len(companies),
        'contacts': len(contacts),
        'sent': sum(1 for r in results if r.get('status') == 'sent'),
        'dryRun': sum(1 for r in results if r.get('status') == 'dry_run'),
        'skipped': sum(1 for r in results if r.get('status') == 'skipped'),
        'errors': sum(1 for r in results if r.get('status') == 'error'),
    }


def print_summary(s: Dict[str, Any]):
    line = "═" * 64
    sys.stdout.write(f"\n{paint('green', line)}\n")
    sys.stdout.write(f"  {paint('bold', 'Run complete for ' + str(s.get('seed')))}\n")
    sys.stdout.write(f"  Companies: {s.get('companies')}   Contacts: {s.get('contacts')}\n")
    sys.stdout.write("  " + paint('green', f"Sent: {s.get('sent')}") + "   " + paint('cyan', f"Dry-run: {s.get('dryRun')}") + "   " +
                     paint('yellow', f"Skipped: {s.get('skipped')}") + "   " + paint('red', f"Errors: {s.get('errors')}") + "\n")
    sys.stdout.write(f"{paint('green', line)}\n")
