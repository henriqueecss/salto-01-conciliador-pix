import tempfile
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from conciliador.reconciler import load_inputs, reconcile, reconcile_data
from conciliador.view import build_rows, summarize

STATIC_DIR = Path(__file__).resolve().parent / "static"
SAMPLE_DIR = Path(__file__).resolve().parents[2] / "data"

app = FastAPI(
    title="Conciliador de Pix",
    description="API de conciliacao de pagamentos Pix para a Doce Ipe Confeitaria",
)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/conciliar")
async def conciliar(
    pedidos: UploadFile = File(...),
    extrato: UploadFile = File(...),
):
    with tempfile.TemporaryDirectory() as tmpdir:
        pedidos_path = await _save_upload(pedidos, tmpdir)
        extrato_path = await _save_upload(extrato, tmpdir)

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


@app.post("/api/conciliacao")
async def conciliacao(
    pedidos: UploadFile = File(...),
    extrato: UploadFile = File(...),
):
    with tempfile.TemporaryDirectory() as tmpdir:
        pedidos_path = await _save_upload(pedidos, tmpdir)
        extrato_path = await _save_upload(extrato, tmpdir)

        try:
            return _conciliacao(pedidos_path, extrato_path)
        except (KeyError, ValueError) as exc:
            raise HTTPException(
                status_code=422,
                detail="Não foi possível ler os arquivos. Confira se a planilha de pedidos e o "
                "extrato estão no formato esperado.",
            ) from exc


@app.get("/api/exemplo")
def exemplo():
    if not SAMPLE_DIR.exists():
        raise HTTPException(status_code=404, detail="Dados de exemplo não encontrados.")
    return _conciliacao(SAMPLE_DIR / "pedidos.csv", SAMPLE_DIR / "extrato.csv")


async def _save_upload(upload: UploadFile, directory: str) -> Path:
    # Base name only: the client controls the filename and could send "../"
    path = Path(directory) / Path(upload.filename).name
    path.write_bytes(await upload.read())
    return path


def _conciliacao(pedidos_path: Path, extrato_path: Path) -> dict:
    orders, transactions = load_inputs(pedidos_path, extrato_path)
    rows = build_rows(reconcile_data(orders, transactions), orders, transactions)
    summary = summarize(rows)
    return {
        "resumo": {
            "contagem": summary["counts"],
            "valor_conciliado": summary["reconciled_amount"],
            "valor_pendente": summary["pending_amount"],
            "valor_revisar": summary["review_amount"],
        },
        "linhas": [
            {
                "pedido": r["order_id"],
                "cliente": r["client"],
                "valor_pedido": r["order_value"],
                "data_pedido": _iso(r["order_date"]),
                "id_transacao": r["transaction_id"],
                "pagador": r["payer"],
                "valor_pix": r["txn_value"],
                "data_pix": _iso(r["txn_date"]),
                "diferenca": r["difference"],
                "resultado": r["status"],
                "observacao": r["observation"],
                "motivo": r["reason"],
            }
            for r in rows
        ],
    }


def _iso(value):
    return value.isoformat() if value else None
