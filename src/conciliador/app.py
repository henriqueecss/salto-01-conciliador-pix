import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st

from conciliador.reconciler import reconcile

STATUS_COLORS = {
    "conciliado": "#16a34a",
    "suspeito": "#d97706",
    "duplicado": "#ea580c",
    "pendente": "#dc2626",
    "sem_pedido": "#7c3aed",
    "ignorado": "#6b7280",
}

STATUS_LABELS = {
    "conciliado": "Conciliado",
    "suspeito": "Suspeito",
    "duplicado": "Duplicado",
    "pendente": "Pendente",
    "sem_pedido": "Sem pedido",
    "ignorado": "Ignorado",
}

st.set_page_config(page_title="Conciliador de Pix", layout="wide")

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 1.8rem;
        font-weight: 700;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1rem;
        color: #6b7280;
        margin-bottom: 2rem;
    }
    .stat-card {
        border-radius: 8px;
        padding: 16px 20px;
        text-align: center;
        border: 1px solid #e5e7eb;
    }
    .stat-value {
        font-size: 2rem;
        font-weight: 700;
        line-height: 1.2;
    }
    .stat-label {
        font-size: 0.85rem;
        color: #6b7280;
        margin-top: 4px;
    }
    .status-badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 600;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">Conciliador de Pix</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">Doce Ipe Confeitaria &mdash; '
    "Reconciliacao automatica de pagamentos</div>",
    unsafe_allow_html=True,
)

col_left, col_right = st.columns(2)

with col_left:
    pedidos_file = st.file_uploader(
        "Planilha de pedidos",
        type=["csv"],
        help="CSV com colunas: pedido, data, cliente, itens, valor, canal",
    )

with col_right:
    extrato_file = st.file_uploader(
        "Extrato bancario",
        type=["csv", "ofx"],
        help="Extrato do banco em formato CSV ou OFX",
    )

if pedidos_file and extrato_file:
    with tempfile.TemporaryDirectory() as tmpdir:
        pedidos_path = Path(tmpdir) / pedidos_file.name
        extrato_path = Path(tmpdir) / extrato_file.name
        pedidos_path.write_bytes(pedidos_file.getvalue())
        extrato_path.write_bytes(extrato_file.getvalue())
        results = reconcile(pedidos_path, extrato_path)

    counts = {}
    for r in results:
        counts[r.status] = counts.get(r.status, 0) + 1

    # Stats cards
    st.markdown("---")
    cols = st.columns(len(STATUS_COLORS))
    for col, (status, color) in zip(cols, STATUS_COLORS.items()):
        count = counts.get(status, 0)
        label = STATUS_LABELS[status]
        col.markdown(
            f'<div class="stat-card">'
            f'<div class="stat-value" style="color: {color}">{count}</div>'
            f'<div class="stat-label">{label}</div>'
            f"</div>",
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # Build table with colored status badges
    rows = []
    for r in results:
        pedido = r.order_id if r.order_id else "-"
        txn = r.transaction_id if r.transaction_id else "-"
        color = STATUS_COLORS.get(r.status, "#6b7280")
        label = STATUS_LABELS.get(r.status, r.status)
        badge = f'<span class="status-badge" style="background-color:{color}">{label}</span>'
        rows.append({
            "Pedido": pedido,
            "ID Transacao": txn,
            "Resultado": badge,
            "_sort_order": (0 if pedido != "-" else 1),
            "_sort_num": int(pedido[1:]) if pedido != "-" else 9999,
            "_status": r.status,
        })

    rows.sort(key=lambda x: (x["_sort_order"], x["_sort_num"], x["_status"]))

    df_display = pd.DataFrame(rows)[["Pedido", "ID Transacao", "Resultado"]]

    st.markdown(
        df_display.to_html(escape=False, index=False, classes="dataframe"),
        unsafe_allow_html=True,
    )

    # Download
    df_export = pd.DataFrame([
        {"pedido": r.order_id, "id_transacao": r.transaction_id, "resultado": r.status}
        for r in results
    ])
    st.download_button(
        label="Baixar resultado em CSV",
        data=df_export.to_csv(index=False, sep=";"),
        file_name="conciliacao.csv",
        mime="text/csv",
    )

else:
    st.markdown(
        "Envie a planilha de pedidos e o extrato bancario acima para iniciar a conciliacao."
    )

    with st.expander("Como funciona"):
        st.markdown("""
O sistema classifica cada pedido e transacao em:

| Resultado | Quando |
|-----------|--------|
| **Conciliado** | Valor exato e nome compativel dentro da janela de tempo |
| **Suspeito** | Precisa de confirmacao humana (nome diferente ou valor proximo) |
| **Duplicado** | Mesmo cliente pagou o mesmo pedido duas vezes |
| **Pendente** | Pedido sem pagamento |
| **Sem pedido** | Pix recebido sem pedido correspondente |
| **Ignorado** | Transacao que nao e credito Pix (saida, tarifa, rendimento) |
        """)
