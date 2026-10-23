from pathlib import Path

import pytest

from conciliador.reconciler import load_inputs, reconcile_data
from conciliador.view import build_rows, summarize

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


@pytest.fixture(scope="module")
def rows():
    orders, transactions = load_inputs(DATA_DIR / "pedidos.csv", DATA_DIR / "extrato.csv")
    return build_rows(reconcile_data(orders, transactions), orders, transactions)


def _by_order(rows, order_id):
    return [r for r in rows if r["order_id"] == order_id]


class TestBuildRows:
    def test_conciliado_has_order_and_payer_side_by_side(self, rows):
        row = _by_order(rows, "P001")[0]
        assert row["status"] == "conciliado"
        assert row["client"] == "Mariana Alves Costa"
        assert row["payer"] == "MARIANA ALVES COSTA"
        assert row["order_value"] == 65.00
        assert row["txn_value"] == 65.00
        assert row["difference"] == 0.0

    def test_pendente_has_no_transaction_side(self, rows):
        row = _by_order(rows, "P009")[0]
        assert row["status"] == "pendente"
        assert row["payer"] == ""
        assert row["txn_value"] is None
        assert row["difference"] is None

    def test_sem_pedido_has_no_order_side(self, rows):
        sem = [r for r in rows if r["status"] == "sem_pedido"]
        assert sem
        assert all(r["client"] == "" and r["order_value"] is None for r in sem)
        assert all(r["payer"] for r in sem)

    def test_suspeito_with_different_value_shows_difference(self, rows):
        diffs = [r["difference"] for r in rows if r["status"] == "suspeito"]
        assert any(d is not None and abs(d) > 0.001 for d in diffs)

    def test_split_payment_has_one_row_per_transaction(self, rows):
        split = [r for r in rows if r["observation"] == "Pagamento dividido"]
        assert len(split) >= 2
        assert len({r["transaction_id"] for r in split}) == len(split)

    def test_ordered_by_order_number_then_unlinked_last(self, rows):
        with_order = [r["order_id"] for r in rows if r["order_id"]]
        assert with_order == sorted(with_order)
        first_unlinked = next(i for i, r in enumerate(rows) if not r["order_id"])
        assert all(not r["order_id"] for r in rows[first_unlinked:])


class TestSummarize:
    def test_counts_cover_every_row(self, rows):
        summary = summarize(rows)
        assert sum(summary["counts"].values()) == len(rows)

    def test_amounts(self, rows):
        summary = summarize(rows)
        expected_pending = sum(r["order_value"] for r in rows if r["status"] == "pendente")
        assert summary["pending_amount"] == pytest.approx(expected_pending)
        assert summary["reconciled_amount"] > 0
        assert summary["review_amount"] > 0



class TestReason:
    def test_every_row_has_a_reason(self, rows):
        assert all(r["reason"] for r in rows)

    def test_suspeito_with_exact_value_blames_the_name(self, rows):
        exact = [
            r for r in rows if r["status"] == "suspeito" and r["difference"] == 0.0
        ]
        assert exact
        assert all("nome" in r["reason"] for r in exact)

    def test_suspeito_with_different_value_blames_the_value(self, rows):
        off = [
            r for r in rows
            if r["status"] == "suspeito" and r["difference"] not in (None, 0.0)
        ]
        assert off
        assert all("valor" in r["reason"] for r in off)

    def test_split_payment_reason(self, rows):
        split = [r for r in rows if r["observation"] == "Pagamento dividido"]
        assert all("dividido" in r["reason"] for r in split)
