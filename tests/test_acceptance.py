import csv
from pathlib import Path

import pytest

from conciliador.reconciler import reconcile

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def _load_gabarito():
    rows = []
    with open(DATA_DIR / "gabarito.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            rows.append({
                "pedido": row["pedido"].strip(),
                "id_transacao": row["id_transacao"].strip(),
                "resultado": row["resultado"].strip(),
                "dificuldade": row["dificuldade"].strip(),
                "observacao": row.get("observacao", "").strip(),
            })
    return rows


def _run_reconciliation():
    return reconcile(DATA_DIR / "pedidos.csv", DATA_DIR / "extrato.csv")


def _find_result(results, pedido, id_transacao):
    """Find a matching result by order_id and/or transaction_id."""
    for r in results:
        if pedido and id_transacao:
            if r.order_id == pedido and r.transaction_id == id_transacao:
                return r
        elif pedido and not id_transacao:
            # pendente: match by order_id with empty transaction
            if r.order_id == pedido and r.status == "pendente":
                return r
        elif id_transacao and not pedido:
            # sem_pedido or ignorado: match by transaction_id with empty order
            if r.transaction_id == id_transacao and not r.order_id:
                return r
    return None


_gabarito = _load_gabarito()
_results = _run_reconciliation()


def _make_test_id(row):
    parts = []
    if row["pedido"]:
        parts.append(row["pedido"])
    if row["id_transacao"]:
        parts.append(row["id_transacao"][:20])
    parts.append(row["resultado"])
    return "-".join(parts)


@pytest.mark.parametrize(
    "expected",
    [r for r in _gabarito if r["dificuldade"] in ("basico", "intermediario")],
    ids=[_make_test_id(r) for r in _gabarito if r["dificuldade"] in ("basico", "intermediario")],
)
def test_gabarito_basico_intermediario(expected):
    result = _find_result(_results, expected["pedido"], expected["id_transacao"])
    assert result is not None, (
        f"Resultado não encontrado: pedido={expected['pedido']}, "
        f"txn={expected['id_transacao']}, esperado={expected['resultado']}"
    )
    assert result.status == expected["resultado"], (
        f"pedido={expected['pedido']}: esperado={expected['resultado']}, "
        f"obtido={result.status} (obs: {expected['observacao']})"
    )


@pytest.mark.xfail(reason="bonus: pagamento dividido ainda não implementado")
@pytest.mark.parametrize(
    "expected",
    [r for r in _gabarito if r["dificuldade"] == "bonus"],
    ids=[_make_test_id(r) for r in _gabarito if r["dificuldade"] == "bonus"],
)
def test_gabarito_bonus(expected):
    result = _find_result(_results, expected["pedido"], expected["id_transacao"])
    assert result is not None, (
        f"Resultado não encontrado: pedido={expected['pedido']}, "
        f"txn={expected['id_transacao']}, esperado={expected['resultado']}"
    )
    assert result.status == expected["resultado"]
