import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st

from conciliador.reconciler import reconcile

STATUS_CONFIG = {
    "conciliado": {"emoji": "✅", "color": "#2ecc71"},
    "suspeito": {"emoji": "⚠️", "color": "#f39c12"},
    "duplicado": {"emoji": "🔁", "color": "#e67e22"},
    "pendente": {"emoji": "❌", "color": "#e74c3c"},
    "sem_pedido": {"emoji": "❓", "color": "#9b59b6"},
    "ignorado": {"emoji": "⏭️", "color": "#95a5a6"},
}

st.set_page_config(
    page_title="Conciliador de Pix",
    page_icon="💰",
    layout="wide",
)

st.title("💰 Conciliador de Pix")
st.markdown("Envie o extrato bancário e a planilha de pedidos para conciliar automaticamente.")

col_left, col_right = st.columns(2)

with col_left:
    pedidos_file = st.file_uploader(
        "📋 Planilha de pedidos (.csv)",
        type=["csv"],
        help="CSV com colunas: pedido, data, cliente, itens, valor, canal",
    )

with col_right:
    extrato_file = st.file_uploader(
        "🏦 Extrato bancário (.csv ou .ofx)",
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

    st.divider()

    # Metrics row
    counts = {}
    for r in results:
        counts[r.status] = counts.get(r.status, 0) + 1

    metric_cols = st.columns(len(STATUS_CONFIG))
    for col, (status, cfg) in zip(metric_cols, STATUS_CONFIG.items()):
        col.metric(
            label=f"{cfg['emoji']} {status.replace('_', ' ').title()}",
            value=counts.get(status, 0),
        )

    st.divider()

    # Results table
    rows = []
    for r in results:
        cfg = STATUS_CONFIG.get(r.status, {"emoji": "", "color": "#ccc"})
        pedido = r.order_id if r.order_id else "-"
        txn = r.transaction_id if r.transaction_id else "-"
        rows.append({
            "Pedido": pedido,
            "Transacao": txn,
            "Resultado": f"{cfg['emoji']} {r.status.replace('_', ' ').title()}",
            "status_raw": r.status,
        })

    # Sort: orders first (by number), then unmatched transactions
    def sort_key(row):
        if row["Pedido"] != "-":
            return (0, int(row["Pedido"][1:]), row["status_raw"])
        return (1, 0, row["Transacao"])

    rows.sort(key=sort_key)

    df = pd.DataFrame(rows).drop(columns=["status_raw"])

    def highlight_status(row):
        for status, cfg in STATUS_CONFIG.items():
            if status.replace("_", " ").title() in row["Resultado"]:
                return [f"background-color: {cfg['color']}20" for _ in row]
        return ["" for _ in row]

    styled = df.style.apply(highlight_status, axis=1).set_properties(**{
        "font-size": "14px",
    })

    st.dataframe(styled, use_container_width=True, hide_index=True, height=700)

    # Download button
    csv_data = df.to_csv(index=False, sep=";")
    st.download_button(
        label="📥 Baixar resultado em CSV",
        data=csv_data,
        file_name="conciliacao.csv",
        mime="text/csv",
    )

else:
    st.info("👆 Envie os dois arquivos acima para iniciar a conciliação.")

    with st.expander("ℹ️ Como funciona?"):
        st.markdown("""
**O sistema classifica cada pedido e transação em:**

| Resultado | Quando |
|-----------|--------|
| ✅ **Conciliado** | Valor exato e nome compatível dentro da janela de tempo |
| ⚠️ **Suspeito** | Precisa de confirmação humana |
| 🔁 **Duplicado** | Mesmo cliente pagou o mesmo pedido duas vezes |
| ❌ **Pendente** | Pedido sem pagamento |
| ❓ **Sem pedido** | Pix recebido sem pedido correspondente |
| ⏭️ **Ignorado** | Transação que não é crédito Pix |
        """)
