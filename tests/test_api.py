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


class TestWebInterface:
    def test_index_serves_html(self):
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Conciliador de Pix" in response.text

    def test_static_assets_are_served(self):
        assert client.get("/static/app.js").status_code == 200
        assert client.get("/static/style.css").status_code == 200

    def test_sample_returns_summary_and_rows(self):
        response = client.get("/api/exemplo")
        assert response.status_code == 200
        body = response.json()
        assert sum(body["resumo"]["contagem"].values()) == len(body["linhas"])
        assert body["resumo"]["valor_conciliado"] > 0

    def test_conciliacao_row_shape(self):
        body = client.get("/api/exemplo").json()
        row = next(r for r in body["linhas"] if r["pedido"] == "P001")
        assert row["resultado"] == "conciliado"
        assert row["cliente"] == "Mariana Alves Costa"
        assert row["valor_pedido"] == 65.0
        assert row["data_pedido"].startswith("2026-10-13T09:12")
        assert row["motivo"]

    def test_conciliacao_upload(self):
        with (
            open(DATA_DIR / "pedidos.csv", "rb") as pedidos,
            open(DATA_DIR / "extrato.ofx", "rb") as extrato,
        ):
            response = client.post(
                "/api/conciliacao",
                files={
                    "pedidos": ("pedidos.csv", pedidos, "text/csv"),
                    "extrato": ("extrato.ofx", extrato, "application/octet-stream"),
                },
            )
        assert response.status_code == 200
        assert response.json()["linhas"]

    def test_conciliacao_invalid_file_returns_422(self):
        response = client.post(
            "/api/conciliacao",
            files={
                "pedidos": ("pedidos.csv", b"isso;nao;e;um;pedido\n1;2;3;4;5", "text/csv"),
                "extrato": ("extrato.csv", b"x", "text/csv"),
            },
        )
        assert response.status_code == 422
        assert "detail" in response.json()
