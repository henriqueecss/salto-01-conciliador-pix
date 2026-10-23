from conciliador.models import Order, ReconciliationResult, Transaction
from conciliador.report import sort_key

ATTENTION_STATUSES = ("suspeito", "duplicado", "sem_pedido")


def build_rows(
    results: list[ReconciliationResult],
    orders: list[Order],
    transactions: list[Transaction],
) -> list[dict]:
    orders_by_id = {o.id: o for o in orders}
    txns_by_id = {t.id: t for t in transactions}

    rows = []
    for r in sorted(results, key=sort_key):
        order = orders_by_id.get(r.order_id)
        txn = txns_by_id.get(r.transaction_id)
        difference = None
        if order and txn:
            difference = round(txn.value - order.value, 2)
        rows.append({
            "order_id": r.order_id,
            "client": order.client if order else "",
            "order_value": order.value if order else None,
            "order_date": order.date if order else None,
            "transaction_id": r.transaction_id,
            "payer": txn.payer_name if txn else "",
            "txn_value": txn.value if txn else None,
            "txn_date": txn.date if txn else None,
            "difference": difference,
            "status": r.status,
            "observation": r.observation,
        })
    return rows


def summarize(rows: list[dict]) -> dict:
    counts: dict[str, int] = {}
    for row in rows:
        counts[row["status"]] = counts.get(row["status"], 0) + 1

    return {
        "counts": counts,
        "reconciled_amount": sum(
            row["txn_value"] for row in rows if row["status"] == "conciliado"
        ),
        "pending_amount": sum(row["order_value"] for row in rows if row["status"] == "pendente"),
        "review_amount": sum(
            row["txn_value"] for row in rows if row["status"] in ("suspeito", "duplicado")
        ),
    }
