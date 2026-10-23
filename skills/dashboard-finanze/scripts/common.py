"""Shared helpers for the importers: rules, amounts, dates, refs, privacy, entry text."""
import csv
import hashlib
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation

# ── privacy ────────────────────────────────────────────────────────────────
IBAN = re.compile(r"\b[A-Z]{2}\d{2}(?:[A-Z0-9]{11,30}|(?: [A-Z0-9]{4}){3,7}(?: [A-Z0-9]{1,4})?)\b")
CARD = re.compile(r"\b\d(?:[ -]?\d){11,18}\b")
LONG_NUM = re.compile(r"\b\d{8,}\b")


def scrub(text):
    """Remove IBANs, card numbers and long reference numbers from a description."""
    t = IBAN.sub("[IBAN]", text or "")
    t = CARD.sub("[n.]", t)
    t = LONG_NUM.sub("[n.]", t)
    return re.sub(r"\s+", " ", t).strip()


# ── parsing ────────────────────────────────────────────────────────────────
DATE_FORMATS = ("%Y-%m-%d", "%d/%m/%Y", "%d.%m.%Y", "%d-%m-%Y", "%Y/%m/%d", "%d/%m/%y",
                "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%d/%m/%Y %H:%M")


def parse_date(s):
    s = (s or "").strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).date()
    except ValueError:
        raise ValueError(f"unrecognised date {s!r}: normalise the file to YYYY-MM-DD")


def parse_amount(s, decimal=None):
    """'1.234,56' / '1,234.56' / '-12,5' / '€ 12,50' / '(12.50)' -> Decimal.
    decimal=',' forces the Italian style (so '1.234' is a thousand), '.' the English one."""
    s = (s or "").strip().replace("−", "-").replace("\xa0", "").replace(" ", "")
    neg = s.startswith("(") and s.endswith(")")
    s = re.sub(r"[^\d,.\-+]", "", s.strip("()"))
    if not s:
        return None
    if decimal == ",":
        s = s.replace(".", "").replace(",", ".")
    elif decimal == ".":
        s = s.replace(",", "")
    elif "," in s and "." in s:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "," in s:
        head, _, tail = s.rpartition(",")
        s = (head.replace(",", "") + "." + tail) if len(tail) != 3 or head in ("", "-") else s.replace(",", "")
    try:
        v = Decimal(s)
    except InvalidOperation:
        raise ValueError(f"unrecognised amount {s!r}")
    return -v if neg else v


def norm_header(h):
    """'Importo (EUR)', 'Importo EUR', 'importo_eur' -> 'importo eur'."""
    return " ".join(re.sub(r"[^\w]+", " ", (h or "").lower()).split())


def find_column(headers, names):
    """The header matching one of `names` (exactly, after normalising), else None."""
    hs = {norm_header(h): h for h in headers if h}
    for n in names:
        if norm_header(n) in hs:
            return hs[norm_header(n)]
    return None


def pick(row, names):
    col = find_column(row.keys(), names)
    v = row.get(col) if col else None
    return v if v not in (None, "") else ""


# ── rules ──────────────────────────────────────────────────────────────────
def load_rules(path):
    """rules.csv columns: pattern, account, name, tags, direction
    pattern    regular expression, case-insensitive, searched in the description
    account    where the other leg goes; {owner} is replaced by the account's owner
    name       clean payee name (optional), e.g. "Netflix"
    tags       space-separated: shared (split between people), oneoff (left out of
               the savings rate), check (book it there but flag it ! to confirm)
    direction  in / out / blank = both
    The first matching row wins, so put specific rules above generic ones."""
    rules = []
    if not path:
        return rules
    with open(path, encoding="utf-8-sig") as fh:
        for r in csv.DictReader(fh):
            if not (r.get("pattern") or "").strip():
                continue
            rules.append({
                "rx": re.compile(r["pattern"], re.I),
                "account": r["account"].strip(),
                "name": (r.get("name") or "").strip(),
                "tags": (r.get("tags") or "").split(),
                "direction": (r.get("direction") or "").strip().lower(),
            })
    return rules


def categorise(rules, text, owner, amount, unknown_out, unknown_in):
    """-> (account, name, tags, confident)."""
    for r in rules:
        if r["direction"] == "in" and amount < 0 or r["direction"] == "out" and amount > 0:
            continue
        if r["rx"].search(text):
            sure = "check" not in r["tags"]
            tags = [t for t in r["tags"] if t != "check"]
            return r["account"].replace("{owner}", owner), r["name"], tags, sure
    acct = unknown_in.replace("{owner}", owner) if amount > 0 else unknown_out.replace("{owner}", owner)
    return acct, "", [], False


# ── output ─────────────────────────────────────────────────────────────────
def make_ref(*parts):
    return hashlib.sha1("|".join(str(p) for p in parts).encode()).hexdigest()[:12]


def esc(s):
    return (s or "").replace('"', "'").replace("\\", "/").strip()


def owner_of(account):
    parts = account.split(":")
    return parts[1] if len(parts) > 2 and parts[0] in ("Assets", "Liabilities") else "Household"


def entry(d, payee, narration, legs, meta, flag="*", tags=()):
    """legs: list of (account, amount_or_None, currency_or_None, extra) ."""
    tag = "".join(f" #{t}" for t in tags)
    lines = [f'{d} {flag} "{esc(payee)}" "{esc(narration)}"{tag}']
    for k, v in meta.items():
        if v not in (None, ""):
            lines.append(f'  {k}: "{esc(str(v))}"')
    for acct, amt, ccy, extra in legs:
        if amt is None:
            lines.append(f"  {acct}")
        else:
            lines.append(f"  {acct:<40}{amt:>14} {ccy}{(' ' + extra) if extra else ''}")
    return "\n".join(lines) + "\n"


def ledger_texts(ledger_paths):
    """Text of each ledger file and of every file it includes (so main.beancount works)."""
    import glob
    import os
    seen, out = set(), []

    def visit(path):
        path = os.path.abspath(path)
        if path in seen or not os.path.exists(path):
            return
        seen.add(path)
        text = open(path, encoding="utf-8").read()
        out.append(text)
        for inc in re.findall(r'^include\s+"([^"]+)"', text, re.M):
            for q in glob.glob(os.path.join(os.path.dirname(path), inc)):
                visit(q)

    for p in ledger_paths or []:
        visit(p)
    return out


def known_refs(ledger_paths):
    refs = set()
    for text in ledger_texts(ledger_paths):
        refs.update(re.findall(r'^\s+(?:ref|ref_in): "([^"]+)"', text, re.M))
    return refs


def known_balances(ledger_paths):
    """(date, account, currency) of balance assertions already in the ledger."""
    out = set()
    for text in ledger_texts(ledger_paths):
        for d, acct, ccy in re.findall(r"^(\d{4}-\d{2}-\d{2}) balance (\S+)\s+-?[\d.]+ (\S+)", text, re.M):
            out.add((d, acct, ccy))
    return out
