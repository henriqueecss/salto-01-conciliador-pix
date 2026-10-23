import csv
import io
import json

from conciliador.models import ReconciliationResult

_STATUS_LABELS = {
    "conciliado": "Conciliado",
    "suspeito": "Suspeito",
    "duplicado": "Duplicado",
    "pendente": "Pendente",
    "sem_pedido": "Sem pedido",
    "ignorado": "Ignorado",
}


def to_csv(results: list[ReconciliationResult]) -> str:
    output = io.StringIO()
    writer = csv.writer(output, delimiter=";")
    writer.writerow(["pedido", "id_transacao", "resultado"])
    for r in sorted(results, key=sort_key):
        writer.writerow([r.order_id, r.transaction_id, r.status])
    return output.getvalue()


def to_json(results: list[ReconciliationResult]) -> str:
    data = [
        {
            "pedido": r.order_id,
            "id_transacao": r.transaction_id,
            "resultado": r.status,
            "observacao": r.observation,
        }
        for r in sorted(results, key=sort_key)
    ]
    return json.dumps(data, ensure_ascii=False, indent=2)


def to_table(results: list[ReconciliationResult]) -> str:
    lines = []
    lines.append(f"{'Pedido':<8} {'Transacao':<45} {'Resultado':<12}")
    lines.append("-" * 65)

    for r in sorted(results, key=sort_key):
        pedido = r.order_id or "-"
        txn = r.transaction_id[:42] + "..." if len(r.transaction_id) > 45 else r.transaction_id
        txn = txn or "-"
        label = _STATUS_LABELS.get(r.status, r.status)
        lines.append(f"{pedido:<8} {txn:<45} {label:<12}")

    # Summary
    counts: dict[str, int] = {}
    for r in results:
        counts[r.status] = counts.get(r.status, 0) + 1

    lines.append("-" * 65)
    lines.append("Resumo:")
    for status, label in _STATUS_LABELS.items():
        if status in counts:
            lines.append(f"  {label}: {counts[status]}")

    return "\n".join(lines)


def sort_key(r: ReconciliationResult) -> tuple:
    order_num = int(r.order_id[1:]) if r.order_id else 9999
    status_order = {
        "conciliado": 0, "suspeito": 1, "duplicado": 2,
        "pendente": 3, "sem_pedido": 4, "ignorado": 5,
    }
    return (order_num, status_order.get(r.status, 9), r.transaction_id)
