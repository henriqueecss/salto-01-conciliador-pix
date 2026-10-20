import argparse
from pathlib import Path

from conciliador.reconciler import reconcile
from conciliador.report import to_csv, to_json, to_table


def main():
    parser = argparse.ArgumentParser(
        description="Conciliador de pagamentos Pix — Doce Ipê Confeitaria",
    )
    parser.add_argument(
        "--pedidos", required=True, type=Path,
        help="Caminho para o CSV de pedidos",
    )
    parser.add_argument(
        "--extrato", required=True, type=Path,
        help="Caminho para o extrato (CSV ou OFX)",
    )
    parser.add_argument(
        "--formato", choices=["tabela", "csv", "json"], default="tabela",
        help="Formato de saída (padrão: tabela)",
    )
    parser.add_argument(
        "--saida", type=Path, default=None,
        help="Arquivo de saída (padrão: stdout)",
    )

    args = parser.parse_args()

    results = reconcile(args.pedidos, args.extrato)

    formatters = {"tabela": to_table, "csv": to_csv, "json": to_json}
    output = formatters[args.formato](results)

    if args.saida:
        args.saida.write_text(output, encoding="utf-8")
        print(f"Relatório salvo em {args.saida}")
    else:
        print(output)


if __name__ == "__main__":
    main()
