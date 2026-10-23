# Decisões de projeto

## D1 — Compatibilidade de nomes

**Escolha**: Heurística de expansão de iniciais + `rapidfuzz.fuzz.token_set_ratio` com limiar 80.

**Como funciona**: Antes de calcular o score fuzzy, tokens de 1 letra no nome do banco são expandidos se correspondem à inicial de algum token no nome do pedido. Exemplo: `JOAO P SILVA` com pedido `JOAO PEDRO SILVA` → `P` expande para `PEDRO`. Depois, `token_set_ratio` compara os nomes normalizados (sem acento, caixa alta, sem preposições).

**Por quê**: Resolve diretamente o caso P002 (banco abrevia `João Pedro da Silva` para `JOAO P SILVA`). O `token_set_ratio` já lida naturalmente com nomes que têm tokens extras (P006: `FERNANDA LIMA SOUZA` vs `Fernanda Lima`; P016: `EDUARDO DOS SANTOS PEREIRA` vs `Eduardo Santos`). Para P004, o score de `ANA BEATRIZ ROCHA` vs `CARLOS EDUARDO ROCHA` fica ≈46, bem abaixo de 80 — corretamente classificado como `suspeito` (sem match de nome).

**Descartadas**:
- `token_set_ratio` puro com limiar ~75: P002 ficaria com score ≈74, no limite, instável.
- Score composto (token_set_ratio + partial_ratio + pesos): difícil de calibrar e de explicar em entrevista.

---

## D2 — Estratégia de casamento

**Escolha**: Atribuição ótima via algoritmo Húngaro (`scipy.optimize.linear_sum_assignment`).

**Como funciona**: Monta-se uma matriz de custo onde cada par (pedido, transação) recebe custo = `1 − (score_nome / 100)` + penalidade se o valor não for exato. Pares fora da janela de tempo ou com diferença de valor > R$1,00 recebem custo infinito. O algoritmo encontra a atribuição 1:1 que minimiza o custo total.

**Por quê**: É provadamente ótimo — elimina qualquer bug dependente da ordem de processamento. A matriz é 23×29, performance desprezível. O CLAUDE.md já mencionava scipy como possibilidade. Impressiona no portfólio e é fácil de defender: "usei o Húngaro porque o guloso pode dar resultados subótimos se a ordem de processamento mudar".

**Descartadas**:
- Guloso (ordena por score, atribui first-come-first-served): simples, mas pode "roubar" uma transação de um match perfeito que viria depois.
- Guloso com backtracking: ad-hoc, difícil de provar correto.

---

## D3 — Tolerância de valor para `suspeito`

**Escolha**: R$1,00 fixo de tolerância absoluta.

**Como funciona**: Se `|valor_pedido − valor_pix| ≤ 1.00`, o par é candidato. Valor exato → `conciliado` (se nome compatível). Valor dentro da tolerância → `suspeito`. Fora da tolerância → não casa.

**Por quê**: O único caso real é P012 (pedido R$89,90, Pix R$89,00 — diferença de R$0,90). R$1,00 cobre isso com margem. Cenário real: cliente digita `89` no app do banco em vez de `89,90`. Simples de implementar e explicar.

**Descartadas**:
- Tolerância percentual (2%): escala com o valor, mas mais complexo sem necessidade — não há casos ambíguos de pedidos pequenos vs grandes no dataset.
- Combinada (maior entre R$1,00 e 2%): overkill para o escopo.

---

## D4 — Interface

**Escolha**: CLI + API (ambos como wrappers finos sobre a lógica central).

**Como funciona**: O `reconciler.py` expõe uma função pura que recebe caminhos de arquivo e retorna resultados. O `cli.py` (argparse) e o `api.py` (FastAPI) são wrappers de ~30 linhas cada.

**Por quê**: Demonstra boa separação de responsabilidades. CLI é ideal para demo (GIF/vídeo). API cumpre o requisito da stack (FastAPI). Custo marginal mínimo.

**Descartadas**:
- Só CLI: suficiente, mas perde a oportunidade de usar FastAPI.
- Só API: exige subir servidor para uma tarefa batch diária.

**Frontend**: página única em HTML, CSS e JS puros, servida pelo próprio FastAPI (`static/`), que consome `POST /api/conciliacao` e `GET /api/exemplo`. A API devolve as linhas já enriquecidas (cliente, valores, datas, diferença e o motivo da classificação), calculadas em `view.py` e cobertas por testes.

**Por quê**: o usuário final precisa comparar o pedido com o Pix lado a lado para decidir os casos suspeitos, e isso pede controle total do layout. Sem build e sem dependência nova.

**Descartadas**:
- Streamlit: foi a primeira versão. Rápido de montar, mas o visual é padrão e personalizar exige CSS preso à estrutura interna do Streamlit, que muda entre versões.
- Framework JS (React, Vue): exigiria Node e etapa de build para uma tela só.
