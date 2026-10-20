import tempfile
from pathlib import Path

from fastapi import FastAPI, File, UploadFile

from conciliador.reconciler import reconcile

app = FastAPI(
    title="Conciliador de Pix",
    description="API de conciliacao de pagamentos Pix para a Doce Ipe Confeitaria",
)


@app.post("/conciliar")
async def conciliar(
    pedidos: UploadFile = File(...),
    extrato: UploadFile = File(...),
):
    with tempfile.TemporaryDirectory() as tmpdir:
        pedidos_path = Path(tmpdir) / pedidos.filename
        extrato_path = Path(tmpdir) / extrato.filename

        pedidos_path.write_bytes(await pedidos.read())
        extrato_path.write_bytes(await extrato.read())

        results = reconcile(pedidos_path, extrato_path)

    return [
        {
            "pedido": r.order_id,
            "id_transacao": r.transaction_id,
            "resultado": r.status,
            "observacao": r.observation,
        }
        for r in results
    ]
