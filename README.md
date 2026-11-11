# ReGiro

**Peças automotivas entre lojas**

Peça parada vira oportunidade.

Aplicativo responsivo em português brasileiro com o logotipo ReGiro. O catálogo é público. Lojas aprovadas pelo administrador podem anunciar e negociar. Os dados são persistidos no servidor com Django e PostgreSQL no Neon, ou SQLite no desenvolvimento local.

## Executar localmente

Requer Python 3.11 ou posterior.

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export REGIRO_DEBUG=1
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Abra [o catálogo local](http://localhost:8000). Cadastre duas lojas e aprove ambas em [Administração → Lojas](http://localhost:8000/admin/market/store/). O catálogo começa vazio. Cada anúncio representa um lote completo, com preço total e quantidade informada.

## Conectar ao Neon

Crie um projeto ReGiro no console do Neon. Em **Connect**, selecione a base e a função do aplicativo e copie a URL PostgreSQL. Guarde a URL como o segredo `DATABASE_URL` no ambiente de execução. Preserve os parâmetros de segurança fornecidos pelo Neon. Para a aplicação, pode usar a URL com pool de conexões. Para as migrações, use a URL direta.

Com a URL direta carregada em `DATABASE_URL`, execute:

```sh
python manage.py migrate
python manage.py showmigrations market
```

Fora do modo local, configure também `REGIRO_SECRET_KEY` e `REGIRO_HOSTS`. As migrações criam o esquema em um banco vazio. Dados existentes no SQLite não são transferidos automaticamente. Execute testes apenas com SQLite local ou um servidor PostgreSQL descartável.

[Guia do Neon para Django](https://neon.com/docs/guides/django)

## Fluxo disponível

- Cadastro, login, checagem de dígitos do CNPJ numérico e aprovação manual.
- Publicação de anúncios com uma foto opcional e catálogo com busca, filtros, ordenação, favoritos e denúncias.
- Proposta de venda, oferta ou troca por anúncio próprio, com diferença opcional em dinheiro. A conversa fica restrita às lojas participantes.
- Aceite da vendedora reserva as peças. A conclusão exige confirmação das duas lojas. Antes do aceite é possível cancelar a proposta. Depois, é possível abrir uma disputa, mantendo a reserva para análise.
- Painel da loja com anúncios, favoritos e negociações. Administração com verificação e suspensão de lojas, moderação de anúncios, denúncias, consulta a negociações e configuração da comissão e tarifa.
- Cálculo registrado na proposta. Valores iniciais de 6% para venda e R$ 10 por troca. As telas exibem valores informativos e não processam cobranças.

## Testes

```sh
REGIRO_DEBUG=1 python manage.py test
```

O teste cobre cadastro, aprovação, busca, proposta, restrição de acesso, conversa, reserva e confirmação bilateral.

## Antes da operação comercial

- Verificação de e-mail e telefone, validação cadastral externa e suporte ao CNPJ alfanumérico.
- Armazenamento dedicado para galerias com várias fotos, alertas, contrapropostas estruturadas e resolução administrativa de disputas. Atualmente cada peça aceita uma foto, otimizada para JPEG e guardada no banco.
- Clube VIP com assinaturas, cupons, uso de benefícios e controle de renovação.
- Termos, privacidade, regras de cancelamento, avaliações e controles contra abuso.
- Provedor de pagamentos de marketplace com divisão de valores, credenciais de teste e segredo de notificações. A integração precisa validar notificações, processar eventos de forma idempotente e reconciliar cobranças e reembolsos. A operação real exige credenciais próprias, recebedores aprovados, produtos e preços de recorrência configurados.
- Infraestrutura de produção com HTTPS, banco gerenciado, backup e configuração de segredos. Defina `REGIRO_SECRET_KEY` e `REGIRO_HOSTS` em ambiente seguro. Use `REGIRO_DEBUG=1` somente em desenvolvimento.

O repositório contém apenas código e ativos do aplicativo. Não há publicação ou ativação de cobranças.

## Administração e financeiro

O endereço `/admin/` abre o painel global, exclusivo de superusuários. O painel mostra todas as empresas e seus usuários, permite aprovar ou suspender cada cadastro e aplicar uma identidade visual por loja (nome, logotipo e cor principal nas telas autenticadas). Em `/gestao/empresas/`, escolha a empresa antes de alterar acesso, identidade ou cobranças.

As parcelas têm referência única e vencimento. Registre manualmente recebimento, cancelamento, estorno integral ou baixa como perda para parcelas vencidas. As transições ficam no histórico com autor e data e são protegidas contra repetição. A referência com prefixo `negociacao-` é reservada ao sistema. Novas negociações concluídas geram um lançamento em aberto da comissão ou tarifa atribuída à empresa responsável. Negociações antigas não são faturadas retroativamente pela migração.

Os indicadores e gráficos mostram recebimentos, estornos e baixas como perda, evolução dos cadastros, períodos VIP pagos vigentes e projeção de três meses a partir de parcelas já cadastradas. A comparação percentual usa o mês atual até hoje e o mês anterior completo. Receita líquida registrada significa recebimentos menos estornos. Despesas operacionais, impostos, tarifas de provedor e conciliação bancária ainda não compõem esse indicador. A exportação CSV inclui os lançamentos de todas as empresas.

A política de bloqueio por inadimplência começa desativada. Em Configurações, o administrador pode ativá-la e definir a tolerância. O bloqueio financeiro impede novos anúncios, edição de peças e novas propostas ou aceites. O acesso ao financeiro e às negociações existentes permanece disponível para regularização, mensagens e confirmações. Receber, cancelar ou baixar os lançamentos pendentes pode remover o bloqueio. Suspensão administrativa tem efeito próprio e precisa ser removida manualmente.

O white label atual personaliza as telas autenticadas da loja. Domínio próprio, instância separada e uma vitrine pública exclusiva por empresa exigem implementação adicional. Os registros financeiros ainda são manuais. Cobrança recorrente automática e conciliação por notificações do provedor dependem da integração de pagamentos.
