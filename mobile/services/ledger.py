"""Pure accounting helpers (no Kivy) so the ledger maths can be unit-tested."""


def _num(v):
    try:
        return float(str(v if v not in (None, "") else 0).replace(",", ""))
    except Exception:
        return 0.0


def ledger_rows(rows):
    """Chronological ledger with running balance (credit - debit).

    A row that only carries `amount` is classified by transaction_type
    (income/credit-like -> credit, expense/debit-like -> debit) so legacy
    rows still enter the books instead of silently counting as zero.
    """
    out = []
    for r in rows or []:
        debit, credit = _num(r.get("debit")), _num(r.get("credit"))
        if debit == 0 and credit == 0:
            amt = _num(r.get("amount"))
            kind = str(r.get("transaction_type") or "").lower()
            if amt and any(x in kind for x in ("income", "receipt", "credit", "درآمد", "دریافت", "بستانکار")):
                credit = amt
            elif amt and any(x in kind for x in ("expense", "payment", "debit", "هزینه", "پرداخت", "بدهکار")):
                debit = amt
        d = dict(r)
        d["_debit"], d["_credit"] = debit, credit
        out.append(d)
    out.sort(key=lambda x: (str(x.get("transaction_date") or x.get("created_at") or ""), int(x.get("id") or 0)))
    bal = 0.0
    for d in out:
        bal += d["_credit"] - d["_debit"]
        d["_balance"] = bal
    return out


def totals(ledger):
    td = sum(r["_debit"] for r in ledger)
    tc = sum(r["_credit"] for r in ledger)
    return {"debit": td, "credit": tc, "balance": tc - td, "count": len(ledger)}
