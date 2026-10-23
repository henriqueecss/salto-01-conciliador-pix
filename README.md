# Conciliador de Pix

Conciliador automático de pagamentos Pix para a Doce Ipê Confeitaria (fictícia).

## Demo

![Demo](docs/demo-interface.gif)

## O problema

A dona da confeitaria vende pelo Instagram e WhatsApp e recebe quase tudo por Pix. No fim do dia, confere o extrato bancário contra a planilha de pedidos na mão. Pix sem nome, nomes abreviados pelo banco e valores repetidos geram erro: cliente cobrado duas vezes, pedido entregue sem pagamento.

## A solução

O sistema recebe o extrato do banco (CSV ou OFX) e a planilha de pedidos (CSV) e devolve um relatório que classifica cada pedido e cada transação:

| Resultado | Quando |
|-----------|--------|
| **Conciliado** | Valor exato e nome compatível dentro da janela de tempo |
| **Suspeito** | Precisa de confirmação humana (nome ausente/diferente, ou valor próximo) |
| **Duplicado** | Mesmo pagador pagou o mesmo pedido duas vezes |
| **Pendente** | Pedido sem pagamento |
| **Sem pedido** | Pix recebido sem pedido correspondente |
| **Ignorado** | Transação que não é crédito Pix (saída, tarifa, rendimento) |

## Arquitetura

```
src/conciliador/
  models.py         → Dataclasses: pedido, transação e resultado
  parsers.py        → Lê CSV e OFX, parseia valores BR e datas
  normalization.py  → Remove acentos, caixa alta, preposições
  matching.py       → Score de nomes (iniciais + token_set_ratio) e janela de tempo
  reconciler.py     → Pipeline: parsing → atribuição ótima (Húngaro) → classificação
  report.py         → Formata saída (CSV, JSON, tabela)
  view.py           → Enriquece o resultado para a tela: valores, datas, diferença, motivo e totais
  cli.py            → Interface de linha de comando
  api.py            → API FastAPI: interface web, /api/conciliacao, /api/exemplo e /conciliar
  static/           → Frontend em HTML, CSS e JS puros
```

### Decisões técnicas

As decisões e alternativas descartadas estão documentadas em [DECISOES.md](DECISOES.md).

1. **Nomes**: Heurística de expansão de iniciais + `rapidfuzz.fuzz.token_set_ratio` (limiar 80)
2. **Casamento**: Algoritmo Húngaro (`scipy.optimize.linear_sum_assignment`) — atribuição globalmente ótima
3. **Tolerância de valor**: R$1,00 fixo para classificar como suspeito
4. **Interface**: CLI, API FastAPI e frontend próprio (HTML, CSS e JS) servido pela API

## Resultados

- **31/31** casos do gabarito acertados (100%) — básico, intermediário e bônus
- **132** testes automatizados passando

## Como rodar

### Pré-requisitos

- Python 3.11+

### Instalação

```bash
pip install -e ".[dev]"
```

### CLI

```bash
# Tabela legível
python -m conciliador --pedidos data/pedidos.csv --extrato data/extrato.csv

# CSV
python -m conciliador --pedidos data/pedidos.csv --extrato data/extrato.csv --formato csv

# JSON
python -m conciliador --pedidos data/pedidos.csv --extrato data/extrato.csv --formato json

# Com arquivo OFX
python -m conciliador --pedidos data/pedidos.csv --extrato data/extrato.ofx

# Salvar em arquivo
python -m conciliador --pedidos data/pedidos.csv --extrato data/extrato.csv --saida resultado.csv --formato csv
```

### Interface web

```bash
uvicorn conciliador.api:app --reload
```

Abra http://localhost:8000. A página aceita upload por arrastar (ou o botão "Ver com dados de exemplo"), mostra os totais em R$ e separa o que precisa de atenção. Cada caso aparece com o pedido ao lado do Pix e o motivo da classificação, e o tema claro ou escuro segue o do sistema.

### API

O servidor da interface web também expõe a API:

```bash
curl -X POST http://localhost:8000/conciliar \
  -F "pedidos=@data/pedidos.csv" \
  -F "extrato=@data/extrato.csv"
```

### Testes

```bash
pytest -v
ruff check src/ tests/
```

## Stack

- Python 3.11+ (CI em 3.12), pandas, rapidfuzz, scipy, FastAPI, HTML/CSS/JS puros no frontend, pytest, ruff
