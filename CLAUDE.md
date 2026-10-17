# Case 01 · Conciliador de Pix

Projeto 1 de 15 do meu Salto (Carreira de Excelência Na Prática): 15 problemas reais resolvidos com código, publicados no GitHub e no LinkedIn. Eu sou o Henrique, estudante de Ciência da Computação na UFLA. Quero entender e conseguir defender cada decisão deste projeto numa entrevista, então explique o porquê das escolhas e não esconda complexidade de mim.

## O problema

A Doce Ipê Confeitaria (fictícia, em Lavras) vende pelo Instagram e pelo WhatsApp e recebe quase tudo por Pix. No fim do dia, a dona confere o extrato do banco contra a planilha de pedidos na mão. Pix sem nome, nomes abreviados pelo banco e valores repetidos geram erro, cliente cobrado duas vezes e pedido entregue sem pagamento.

## O que o sistema faz

Recebe o extrato do banco (CSV ou OFX) e a planilha de pedidos (CSV) e devolve um relatório que classifica cada pedido e cada transação.

## Regras de negócio (versão inicial)

- Só créditos Pix entram na conciliação. Saídas, tarifas e créditos que não são Pix são classificados como `ignorado`.
- Janela de tempo: um Pix pode pagar um pedido se chegou entre 2 horas antes e 48 horas depois do registro do pedido.
- Uma transação paga no máximo um pedido.
- Nomes são comparados depois de normalizar: sem acento, em caixa alta, sem preposições (da, de, do, das, dos). O banco abrevia nomes (JOAO P SILVA) e às vezes mostra mais sobrenomes que o pedido.

Resultados possíveis:

| resultado | quando |
|---|---|
| `conciliado` | valor exato e nome compatível dentro da janela |
| `suspeito` | precisa de confirmação humana: valor exato com nome ausente ou diferente, ou nome compatível com valor diferente |
| `duplicado` | o mesmo pagador pagou de novo um pedido que já está conciliado |
| `pendente` | pedido sem pagamento |
| `sem_pedido` | Pix recebido que não corresponde a nenhum pedido |
| `ignorado` | lançamento que não é crédito Pix |

Bônus (fora do MVP): pagamento dividido, quando dois ou mais Pix do mesmo pagador somam o valor do pedido.

## Dados e testes

- `data/` tem os arquivos de entrada e o gabarito oficial. **Nunca altere nada em `data/`.**
- `data/gabarito.csv` traz o resultado esperado de cada pedido e transação, com a coluna `dificuldade` (`basico`, `intermediario`, `bonus`).
- Os testes de aceitação comparam a saída do sistema com o gabarito. O MVP está pronto quando todas as linhas `basico` e `intermediario` passam. As linhas `bonus` ficam marcadas como `xfail` até o bônus ser implementado.
- Escreva testes unitários para o parsing (valores como `R$ 1.234,56` e `-86,40`, datas `dd/mm/aaaa hh:mm`, OFX com datas `20261013103107[-3:BRT]`) e para a normalização de nomes.

## Decisões em aberto

Decida comigo e registre em `DECISOES.md`, com as alternativas descartadas:

1. Como medir a compatibilidade de nomes e qual limiar usar (rapidfuzz: `token_set_ratio`, `partial_ratio`, regra de iniciais?).
2. Casamento guloso ou atribuição ótima (por exemplo `scipy.optimize.linear_sum_assignment`). A ordem importa: veja P004 × P017 e P012 × P021 no gabarito.
3. Tolerância de valor para classificar como `suspeito`.
4. Como expor o resultado: CLI, API, ou as duas.

## Stack

- Python 3.12, pandas, rapidfuzz, FastAPI, pytest, ruff
- GitHub Actions rodando ruff e pytest a cada push
- Pergunte antes de adicionar qualquer dependência fora desta lista
- Nomes no código em inglês; README e mensagens para o usuário em português

## Como trabalhar comigo

1. Antes de escrever código, proponha arquitetura, estrutura de pastas e plano de testes, e espere minha aprovação.
2. Escreva os testes antes da implementação.
3. Trabalhe em passos pequenos, com um commit por passo e mensagens descritivas.
4. Ao terminar cada passo, explique em poucas linhas o que mudou e por quê.
5. Se uma regra de negócio acima parecer errada para algum caso do gabarito, me avise em vez de mudar o gabarito.

## Definição de pronto

- [ ] Testes `basico` e `intermediario` passando no GitHub Actions
- [ ] README em português: problema, solução, arquitetura, decisões, resultados (quantos casos acertou) e como rodar
- [ ] `DECISOES.md` com as decisões acima
- [ ] Demo: GIF ou vídeo curto rodando a conciliação
- [ ] Post no LinkedIn
