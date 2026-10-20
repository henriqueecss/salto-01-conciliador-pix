from datetime import datetime
from pathlib import Path

from conciliador.parsers import (
    extract_payer_name,
    is_pix_credit,
    parse_br_date,
    parse_br_value,
    parse_extrato_csv,
    parse_ofx,
    parse_ofx_date,
    parse_pedidos_csv,
)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


# ---------- parse_br_value ----------

class TestParseBrValue:
    def test_simple(self):
        assert parse_br_value("R$ 65,00") == 65.0

    def test_thousands_separator(self):
        assert parse_br_value("R$ 1.234,56") == 1234.56

    def test_negative(self):
        assert parse_br_value("-340,00") == -340.0

    def test_negative_with_prefix(self):
        assert parse_br_value("-29,90") == -29.9

    def test_small_positive(self):
        assert parse_br_value("0,42") == 0.42

    def test_no_prefix(self):
        assert parse_br_value("89,90") == 89.9


# ---------- parse_br_date ----------

class TestParseBrDate:
    def test_with_minutes(self):
        assert parse_br_date("13/10/2026 09:12") == datetime(2026, 10, 13, 9, 12)

    def test_afternoon(self):
        assert parse_br_date("14/10/2026 18:00") == datetime(2026, 10, 14, 18, 0)


# ---------- parse_ofx_date ----------

class TestParseOfxDate:
    def test_with_timezone(self):
        assert parse_ofx_date("20261013092014[-3:BRT]") == datetime(2026, 10, 13, 9, 20, 14)

    def test_with_timezone_2(self):
        assert parse_ofx_date("20261013103107[-3:BRT]") == datetime(2026, 10, 13, 10, 31, 7)

    def test_without_timezone(self):
        assert parse_ofx_date("20261013092014") == datetime(2026, 10, 13, 9, 20, 14)


# ---------- extract_payer_name ----------

class TestExtractPayerName:
    def test_pix_recebido(self):
        assert extract_payer_name("PIX RECEBIDO MARIANA ALVES COSTA") == "MARIANA ALVES COSTA"

    def test_pix_receb(self):
        assert extract_payer_name("PIX RECEB JOAO P SILVA") == "JOAO P SILVA"

    def test_pix_cpf_masked(self):
        assert extract_payer_name("PIX RECEBIDO CPF ***.482.917-**") == "CPF ***.482.917-**"

    def test_pix_enviado(self):
        assert extract_payer_name("PIX ENVIADO DISTRIBUIDORA SUL DE MINAS LTDA") == (
            "DISTRIBUIDORA SUL DE MINAS LTDA"
        )

    def test_tarifa(self):
        assert extract_payer_name("TARIFA PACOTE DE SERVICOS") == ""

    def test_rendimento(self):
        assert extract_payer_name("RENDIMENTO CONTA REMUNERADA") == ""


# ---------- is_pix_credit ----------

class TestIsPixCredit:
    def test_pix_recebido(self):
        assert is_pix_credit("PIX RECEBIDO MARIANA ALVES COSTA", 65.0) is True

    def test_pix_receb(self):
        assert is_pix_credit("PIX RECEB JOAO P SILVA", 120.0) is True

    def test_pix_enviado(self):
        assert is_pix_credit("PIX ENVIADO DISTRIBUIDORA SUL DE MINAS LTDA", -340.0) is False

    def test_tarifa(self):
        assert is_pix_credit("TARIFA PACOTE DE SERVICOS", -29.9) is False

    def test_rendimento(self):
        assert is_pix_credit("RENDIMENTO CONTA REMUNERADA", 0.42) is False


# ---------- parse_pedidos_csv ----------

class TestParsePedidosCsv:
    def test_count(self):
        orders = parse_pedidos_csv(DATA_DIR / "pedidos.csv")
        assert len(orders) == 23

    def test_first_order(self):
        orders = parse_pedidos_csv(DATA_DIR / "pedidos.csv")
        o = orders[0]
        assert o.id == "P001"
        assert o.date == datetime(2026, 10, 13, 9, 12)
        assert o.client == "Mariana Alves Costa"
        assert o.value == 65.0
        assert o.channel == "Instagram"

    def test_last_order(self):
        orders = parse_pedidos_csv(DATA_DIR / "pedidos.csv")
        o = orders[-1]
        assert o.id == "P023"
        assert o.value == 120.0


# ---------- parse_extrato_csv ----------

class TestParseExtratoCsv:
    def test_count(self):
        txns = parse_extrato_csv(DATA_DIR / "extrato.csv")
        assert len(txns) == 29

    def test_first_transaction(self):
        txns = parse_extrato_csv(DATA_DIR / "extrato.csv")
        t = txns[0]
        assert t.id == "E90400888202610130920ObKD3nz50vS"
        assert t.date == datetime(2026, 10, 13, 9, 20, 14)
        assert t.value == 65.0
        assert t.payer_name == "MARIANA ALVES COSTA"
        assert t.is_pix_credit is True

    def test_debit_transaction(self):
        txns = parse_extrato_csv(DATA_DIR / "extrato.csv")
        debit = [t for t in txns if t.value == -340.0][0]
        assert debit.is_pix_credit is False

    def test_tarifa(self):
        txns = parse_extrato_csv(DATA_DIR / "extrato.csv")
        tarifa = [t for t in txns if "TARIFA" in t.description][0]
        assert tarifa.is_pix_credit is False
        assert tarifa.value == -29.9

    def test_rendimento(self):
        txns = parse_extrato_csv(DATA_DIR / "extrato.csv")
        rend = [t for t in txns if "RENDIMENTO" in t.description][0]
        assert rend.is_pix_credit is False
        assert rend.value == 0.42


# ---------- parse_ofx ----------

class TestParseOfx:
    def test_count(self):
        txns = parse_ofx(DATA_DIR / "extrato.ofx")
        assert len(txns) == 29

    def test_first_transaction(self):
        txns = parse_ofx(DATA_DIR / "extrato.ofx")
        t = txns[0]
        assert t.id == "E90400888202610130920ObKD3nz50vS"
        assert t.date == datetime(2026, 10, 13, 9, 20, 14)
        assert t.value == 65.0
        assert t.payer_name == "MARIANA ALVES COSTA"
        assert t.is_pix_credit is True

    def test_ids_match_csv(self):
        csv_txns = parse_extrato_csv(DATA_DIR / "extrato.csv")
        ofx_txns = parse_ofx(DATA_DIR / "extrato.ofx")
        csv_ids = {t.id for t in csv_txns}
        ofx_ids = {t.id for t in ofx_txns}
        assert csv_ids == ofx_ids

    def test_values_match_csv(self):
        csv_txns = parse_extrato_csv(DATA_DIR / "extrato.csv")
        ofx_txns = parse_ofx(DATA_DIR / "extrato.ofx")
        csv_vals = sorted((t.id, t.value) for t in csv_txns)
        ofx_vals = sorted((t.id, t.value) for t in ofx_txns)
        assert csv_vals == ofx_vals
