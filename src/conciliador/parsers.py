import csv
import re
from datetime import datetime
from pathlib import Path

from conciliador.models import Order, Transaction


def parse_br_value(text: str) -> float:
    cleaned = text.strip().replace("R$", "").replace(" ", "").replace(".", "").replace(",", ".")
    return float(cleaned)


def parse_br_date(text: str) -> datetime:
    text = text.strip()
    if len(text) == 16:  # dd/mm/aaaa hh:mm
        return datetime.strptime(text, "%d/%m/%Y %H:%M")
    return datetime.strptime(text, "%d/%m/%Y %H:%M:%S")


def parse_ofx_date(text: str) -> datetime:
    text = text.strip()
    # Strip timezone bracket like [-3:BRT]
    bracket = text.find("[")
    if bracket != -1:
        text = text[:bracket]
    return datetime.strptime(text, "%Y%m%d%H%M%S")


def extract_payer_name(description: str) -> str:
    desc = description.strip()
    for prefix in ("PIX RECEBIDO ", "PIX RECEB "):
        if desc.startswith(prefix):
            return desc[len(prefix):]
    if desc.startswith("PIX ENVIADO "):
        return desc[len("PIX ENVIADO "):]
    return ""


def is_pix_credit(description: str, value: float) -> bool:
    desc = description.strip()
    if value <= 0:
        return False
    return desc.startswith("PIX RECEBIDO ") or desc.startswith("PIX RECEB ")


def parse_pedidos_csv(path: Path) -> list[Order]:
    orders = []
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            orders.append(Order(
                id=row["pedido"].strip(),
                date=parse_br_date(row["data"]),
                client=row["cliente"].strip(),
                items=row["itens"].strip(),
                value=parse_br_value(row["valor"]),
                channel=row["canal"].strip(),
            ))
    return orders


def parse_extrato_csv(path: Path) -> list[Transaction]:
    transactions = []
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            desc = row["historico"].strip()
            value = parse_br_value(row["valor"])
            payer = extract_payer_name(desc)
            transactions.append(Transaction(
                id=row["id_transacao"].strip(),
                date=parse_br_date(row["data"]),
                description=desc,
                value=value,
                payer_name=payer,
                is_pix_credit=is_pix_credit(desc, value),
            ))
    return transactions


_OFX_TRN_RE = re.compile(
    r"<STMTTRN>\s*"
    r"<TRNTYPE>(\w+)\s*"
    r"<DTPOSTED>([^\s<]+)\s*"
    r"<TRNAMT>([^\s<]+)\s*"
    r"<FITID>([^\s<]+)\s*"
    r"<MEMO>([^\n<]+)",
    re.DOTALL,
)


def parse_ofx(path: Path) -> list[Transaction]:
    text = path.read_text(encoding="utf-8")
    transactions = []
    for match in _OFX_TRN_RE.finditer(text):
        trn_type, dt_posted, amount_str, fitid, memo = match.groups()
        value = float(amount_str.strip())
        desc = memo.strip()
        payer = extract_payer_name(desc)
        transactions.append(Transaction(
            id=fitid.strip(),
            date=parse_ofx_date(dt_posted),
            description=desc,
            value=value,
            payer_name=payer,
            is_pix_credit=is_pix_credit(desc, value),
        ))
    return transactions
