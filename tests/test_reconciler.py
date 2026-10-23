from pathlib import Path

from conciliador.reconciler import load_inputs, reconcile

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def _get_results():
    return reconcile(DATA_DIR / "pedidos.csv", DATA_DIR / "extrato.csv")


def _find(results, order_id="", txn_id=""):
    if order_id:
        return [r for r in results if r.order_id == order_id]
    return [r for r in results if r.transaction_id == txn_id]


class TestReconciler:
    def test_p001_conciliado(self):
        results = _get_results()
        matches = _find(results, order_id="P001")
        assert any(r.status == "conciliado" for r in matches)

    def test_p008_conciliado_and_duplicado(self):
        results = _get_results()
        matches = _find(results, order_id="P008")
        statuses = {r.status for r in matches}
        assert "conciliado" in statuses
        assert "duplicado" in statuses

    def test_p009_pendente(self):
        results = _get_results()
        matches = _find(results, order_id="P009")
        assert any(r.status == "pendente" for r in matches)

    def test_p010_suspeito(self):
        results = _get_results()
        matches = _find(results, order_id="P010")
        assert any(r.status == "suspeito" for r in matches)

    def test_p012_suspeito(self):
        results = _get_results()
        matches = _find(results, order_id="P012")
        assert any(r.status == "suspeito" for r in matches)

    def test_p022_pendente(self):
        results = _get_results()
        matches = _find(results, order_id="P022")
        assert any(r.status == "pendente" for r in matches)

    def test_debits_ignored(self):
        results = _get_results()
        ignored = [r for r in results if r.status == "ignorado"]
        assert len(ignored) >= 3  # 2 PIX ENVIADO + TARIFA

    def test_sem_pedido_exists(self):
        results = _get_results()
        sem = [r for r in results if r.status == "sem_pedido"]
        assert len(sem) >= 2  # Roberto Almeida + André Luiz Batista

    def test_p002_conciliado(self):
        """Bank abbreviates: JOAO P SILVA → João Pedro da Silva"""
        results = _get_results()
        matches = _find(results, order_id="P002")
        assert any(r.status == "conciliado" for r in matches)

    def test_p013_conciliado(self):
        """Pix arrived 9 min before order registered"""
        results = _get_results()
        matches = _find(results, order_id="P013")
        assert any(r.status == "conciliado" for r in matches)


class TestLoadInputs:
    def test_csv_statement(self):
        orders, transactions = load_inputs(DATA_DIR / "pedidos.csv", DATA_DIR / "extrato.csv")
        assert orders[0].id == "P001"
        assert any(t.is_pix_credit for t in transactions)

    def test_ofx_statement(self):
        orders, transactions = load_inputs(DATA_DIR / "pedidos.csv", DATA_DIR / "extrato.ofx")
        assert len(orders) > 0
        assert len(transactions) > 0
