# ReGiro

**Slogan:** "Peça parada vira oportunidade."

Marketplace responsivo em português brasileiro para lojas de autopeças venderem e trocarem itens parados em estoque.

## MVP implementado nesta versão

- Cadastro gratuito de lojas com validações básicas (incluindo formato de CNPJ).
- Publicação gratuita de anúncios com campos principais do domínio automotivo.
- Busca pública com filtros e ordenação.
- Negociação com ofertas de venda, propostas de troca e chat interno por anúncio.
- Tarifa de R$ 10 por troca concluída (uma vez), com cobrança da loja iniciadora.
- Clube ReGiro VIP com 1 isenção mensal de troca e desconto nas trocas adicionais.
- Comissão configurável para vendas (inicial: 6%).
- Painel básico da loja e painel administrativo básico.
- Simulação de pagamentos apenas em modo de teste com transparência de custos.
- Histórico de negociações com confirmação de ambas as lojas para conclusão.

## Executar localmente

Abra o arquivo `index.html` no navegador.

## Credenciais para pagamentos reais (documentação obrigatória)

**Não ativar cobranças reais sem integração válida no backend.**

Quando a integração real for implementada, deverão ser configuradas credenciais seguras no servidor (nunca no front-end):

- `PAYMENT_PROVIDER_PUBLIC_KEY`
- `PAYMENT_PROVIDER_SECRET_KEY`
- `PAYMENT_PROVIDER_WEBHOOK_SECRET`
- `PAYMENT_PROVIDER_ACCOUNT_ID` (quando houver split de pagamentos)

Também é obrigatório:

1. Validar notificações por assinatura (webhooks).
2. Registrar logs de transações, comissões, reembolsos e cancelamentos.
3. Manter modo teste em ambiente de homologação.
4. Não armazenar dados completos de cartão.
