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

## Limitações desta versão

Este branch contém um protótipo de interface executado no navegador. Os dados ficam apenas na memória da página e são apagados ao recarregar. Ainda não há autenticação, banco de dados, envio real de e-mail ou SMS, moderação protegida, cobrança de taxa/comissão nem assinatura recorrente. O painel administrativo e os valores de pagamento são demonstrativos. Não use informações reais de lojas nesta versão.

## Arquitetura escolhida para a próxima etapa

- **GitHub:** repositório do código, histórico, revisão e integração com a Railway.
- **Railway:** hospedagem da aplicação e da API, banco PostgreSQL e Bucket S3-compatível para fotos dos anúncios.
- **Autenticação:** será implementada na aplicação/API, com senhas protegidas, sessões seguras e autorização por loja.
- **Pagamentos:** integração posterior com um provedor de pagamentos; não será simulada como cobrança real.

A Railway permite conectar um repositório GitHub e fazer novos deploys quando houver commits na branch configurada. O PostgreSQL e os Buckets serão serviços separados dentro do mesmo projeto Railway. Backups do banco precisam ser ativados e acompanhados na configuração da Railway.

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
