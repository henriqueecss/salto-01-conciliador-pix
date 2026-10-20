from pathlib import Path

from fastapi.testclient import TestClient

from conciliador.api import app

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
client = TestClient(app)


class TestApi:
    def test_conciliar_returns_200(self):
        with (
            open(DATA_DIR / "pedidos.csv", "rb") as pedidos,
            open(DATA_DIR / "extrato.csv", "rb") as extrato,
        ):
            response = client.post(
                "/conciliar",
                files={
                    "pedidos": ("pedidos.csv", pedidos, "text/csv"),
                    "extrato": ("extrato.csv", extrato, "text/csv"),
                },
            )
        assert response.status_code == 200

    def test_conciliar_has_results(self):
        with (
            open(DATA_DIR / "pedidos.csv", "rb") as pedidos,
            open(DATA_DIR / "extrato.csv", "rb") as extrato,
        ):
            response = client.post(
                "/conciliar",
                files={
                    "pedidos": ("pedidos.csv", pedidos, "text/csv"),
                    "extrato": ("extrato.csv", extrato, "text/csv"),
                },
            )
        data = response.json()
        assert len(data) > 0
        statuses = {r["resultado"] for r in data}
        assert "conciliado" in statuses

    def test_conciliar_with_ofx(self):
        with (
            open(DATA_DIR / "pedidos.csv", "rb") as pedidos,
            open(DATA_DIR / "extrato.ofx", "rb") as extrato,
        ):
            response = client.post(
                "/conciliar",
                files={
                    "pedidos": ("pedidos.csv", pedidos, "text/csv"),
                    "extrato": ("extrato.ofx", extrato, "application/octet-stream"),
                },
            )
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
