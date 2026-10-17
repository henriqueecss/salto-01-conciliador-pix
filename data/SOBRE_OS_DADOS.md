# Sobre os dados

Todos os nomes, valores e identificadores são fictícios. Período: 13 a 15 de outubro de 2026.

| arquivo | o que é |
|---|---|
| `pedidos.csv` | 23 pedidos da planilha da dona, exportada do Google Planilhas. Separador `;`, valores com `R$` e vírgula decimal. |
| `extrato.csv` | 29 lançamentos do extrato do banco, no formato de exportação comum de bancos brasileiros. Separador `;`, saídas com sinal negativo. |
| `extrato.ofx` | Os mesmos 29 lançamentos em OFX 1.0.2 (SGML), o formato que a maioria dos bancos oferece para download. |
| `gabarito.csv` | O resultado esperado para cada pedido e cada transação. |

O `id_transacao` dos Pix segue o formato do identificador fim a fim do Banco Central: `E` + ISPB do banco (8 dígitos) + data e hora + 11 caracteres.

## Armadilhas que o gabarito testa

- Nome abreviado pelo banco (`JOAO P SILVA`), acentos removidos e sobrenomes a mais ou a menos
- Dois pedidos de R$ 50,00 no mesmo horário, decididos pelo nome
- Pix sem nome, só com CPF mascarado
- Pagador diferente do cliente, com o mesmo sobrenome
- Cliente que pagou R$ 89,00 de um pedido de R$ 89,90
- Cliente que pagou duas vezes o mesmo pedido
- Pix que chegou antes do pedido ser registrado, e Pix pago no dia seguinte
- Pedidos sem pagamento que têm Pix de mesmo valor de outros clientes dentro da janela
- Pix de outro cliente com o valor certo dentro da janela de um pedido pendente (um casamento só por valor erra aqui)
- Saídas, tarifa e rendimento, que devem ser ignorados
- Bônus: pedido pago em dois Pix (sinal e restante)
