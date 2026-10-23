import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st

from conciliador.reconciler import load_inputs, reconcile_data
from conciliador.report import to_csv
from conciliador.view import ATTENTION_STATUSES, build_rows, summarize

SAMPLE_DIR = Path(__file__).resolve().parents[2] / "data"

STATUS_LABELS = {
    "conciliado": "Conciliado",
    "suspeito": "Suspeito",
    "duplicado": "Duplicado",
    "pendente": "Pendente",
    "sem_pedido": "Sem pedido",
    "ignorado": "Ignorado",
}

STATUS_COLORS = {
    "conciliado": "#16a34a",
    "suspeito": "#d97706",
    "duplicado": "#ea580c",
    "pendente": "#dc2626",
    "sem_pedido": "#7c3aed",
    "ignorado": "#6b7280",
}

COLUMNS = {
    "Pedido": "order_id",
    "Cliente": "client",
    "Valor do pedido": "order_value",
    "Data do pedido": "order_date",
    "Pagador (extrato)": "payer",
    "Valor do Pix": "txn_value",
    "Data do Pix": "txn_date",
    "Diferença": "difference",
    "Resultado": "status",
    "Observação": "observation",
}

st.set_page_config(page_title="Conciliador de Pix", layout="wide")


def brl(value: float) -> str:
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def load_uploaded(pedidos_file, extrato_file):
    with tempfile.TemporaryDirectory() as tmpdir:
        pedidos_path = Path(tmpdir) / pedidos_file.name
        extrato_path = Path(tmpdir) / extrato_file.name
        pedidos_path.write_bytes(pedidos_file.getvalue())
        extrato_path.write_bytes(extrato_file.getvalue())
        return load_inputs(pedidos_path, extrato_path)


def to_frame(rows: list[dict]) -> pd.DataFrame:
    frame = pd.DataFrame(rows)
    frame["status"] = frame["status"].map(STATUS_LABELS)
    frame = frame.rename(columns={v: k for k, v in COLUMNS.items()})
    return frame[list(COLUMNS)]


def show_table(rows: list[dict]):
    if not rows:
        st.info("Nenhum lançamento nesta categoria.")
        return

    def color_status(label):
        status = next((k for k, v in STATUS_LABELS.items() if v == label), "")
        return f"color: {STATUS_COLORS.get(status, 'inherit')}; font-weight: 600"

    styled = to_frame(rows).style.map(color_status, subset=["Resultado"])
    st.dataframe(
        styled,
        hide_index=True,
        width="stretch",
        column_config={
            "Valor do pedido": st.column_config.NumberColumn(format="R$ %.2f"),
            "Valor do Pix": st.column_config.NumberColumn(format="R$ %.2f"),
            "Diferença": st.column_config.NumberColumn(format="R$ %+.2f"),
            "Data do pedido": st.column_config.DatetimeColumn(format="DD/MM/YYYY HH:mm"),
            "Data do Pix": st.column_config.DatetimeColumn(format="DD/MM/YYYY HH:mm"),
        },
    )


st.title("Conciliador de Pix")
st.caption("Doce Ipê Confeitaria · conferência automática entre extrato e pedidos")

col_left, col_right = st.columns(2)
with col_left:
    pedidos_file = st.file_uploader(
        "Planilha de pedidos",
        type=["csv"],
        help="CSV com colunas: pedido, data, cliente, itens, valor, canal",
    )
with col_right:
    extrato_file = st.file_uploader(
        "Extrato bancário",
        type=["csv", "ofx"],
        help="Extrato do banco em formato CSV ou OFX",
    )

if SAMPLE_DIR.exists() and not (pedidos_file and extrato_file):
    if st.button("Usar dados de exemplo"):
        st.session_state["sample"] = True
elif pedidos_file and extrato_file:
    st.session_state["sample"] = False

if pedidos_file and extrato_file:
    orders, transactions = load_uploaded(pedidos_file, extrato_file)
elif st.session_state.get("sample"):
    orders, transactions = load_inputs(SAMPLE_DIR / "pedidos.csv", SAMPLE_DIR / "extrato.csv")
    st.caption("Exibindo os dados de exemplo do projeto.")
else:
    orders = None

if orders is None:
    st.write("Envie a planilha de pedidos e o extrato bancário para iniciar a conciliação.")
    with st.expander("Como funciona"):
        st.markdown(
            """
| Resultado | Quando |
|---|---|
| **Conciliado** | Valor exato e nome compatível dentro da janela de tempo |
| **Suspeito** | Precisa de confirmação humana (nome diferente ou valor próximo) |
| **Duplicado** | O mesmo cliente pagou de novo um pedido já conciliado |
| **Pendente** | Pedido sem pagamento |
| **Sem pedido** | Pix recebido sem pedido correspondente |
| **Ignorado** | Lançamento que não é crédito Pix (saída, tarifa, rendimento) |
"""
        )
    st.stop()

results = reconcile_data(orders, transactions)
rows = build_rows(results, orders, transactions)
summary = summarize(rows)
counts = summary["counts"]

m1, m2, m3 = st.columns(3)
m1.metric("Recebido e conciliado", brl(summary["reconciled_amount"]))
m2.metric("Pedidos sem pagamento", brl(summary["pending_amount"]))
m3.metric("Valor a revisar", brl(summary["review_amount"]))

cols = st.columns(len(STATUS_LABELS))
for col, (status, label) in zip(cols, STATUS_LABELS.items()):
    col.metric(label, counts.get(status, 0))

attention = [r for r in rows if r["status"] in ATTENTION_STATUSES]
ignored = [r for r in rows if r["status"] == "ignorado"]

tab_attention, tab_all, tab_ignored = st.tabs(
    [f"Precisa de atenção ({len(attention)})", f"Todos ({len(rows) - len(ignored)})",
     f"Ignorados ({len(ignored)})"]
)

with tab_attention:
    st.caption("Confira o pedido ao lado do Pix antes de aprovar cada caso.")
    show_table(attention)

with tab_all:
    f1, f2 = st.columns([2, 1])
    selected = f1.multiselect(
        "Filtrar por resultado",
        [s for s in STATUS_LABELS if s != "ignorado"],
        format_func=STATUS_LABELS.get,
    )
    query = f2.text_input("Buscar por nome").strip().upper()
    filtered = [r for r in rows if r["status"] != "ignorado"]
    if selected:
        filtered = [r for r in filtered if r["status"] in selected]
    if query:
        filtered = [
            r for r in filtered if query in r["client"].upper() or query in r["payer"].upper()
        ]
    show_table(filtered)

with tab_ignored:
    st.caption("Saídas, tarifas e créditos que não são Pix.")
    st.dataframe(
        pd.DataFrame(
            [{"ID": r["transaction_id"], "Descrição": r["observation"]} for r in ignored]
        ),
        hide_index=True,
        width="stretch",
    )

st.download_button(
    "Baixar resultado em CSV",
    data=to_csv(results),
    file_name="conciliacao.csv",
    mime="text/csv",
)
