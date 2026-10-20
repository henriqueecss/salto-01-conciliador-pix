from conciliador.models import ReconciliationResult
from conciliador.report import to_csv, to_json, to_table


def _sample_results():
    return [
        ReconciliationResult("P001", "E123", "conciliado"),
        ReconciliationResult("P002", "", "pendente"),
        ReconciliationResult("", "E456", "sem_pedido"),
    ]


class TestReport:
    def test_csv_header(self):
        output = to_csv(_sample_results())
        assert output.startswith("pedido;id_transacao;resultado")

    def test_csv_rows(self):
        output = to_csv(_sample_results())
        lines = output.strip().split("\n")
        assert len(lines) == 4  # header + 3 rows

    def test_json_valid(self):
        import json
        output = to_json(_sample_results())
        data = json.loads(output)
        assert len(data) == 3

    def test_table_summary(self):
        output = to_table(_sample_results())
        assert "Conciliado: 1" in output
        assert "Pendente: 1" in output
        assert "Sem pedido: 1" in output
