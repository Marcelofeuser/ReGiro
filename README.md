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
- Publicação de anúncios e catálogo com busca, filtros, ordenação, favoritos e denúncias.
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
- Fotos com armazenamento dedicado, alertas, contrapropostas estruturadas e resolução administrativa de disputas.
- Clube VIP com assinaturas, cupons, uso de benefícios e controle de renovação.
- Termos, privacidade, regras de cancelamento, avaliações e controles contra abuso.
- Provedor de pagamentos de marketplace com divisão de valores, credenciais de teste e segredo de notificações. A integração precisa validar notificações, processar eventos de forma idempotente e reconciliar cobranças e reembolsos. A operação real exige credenciais próprias, recebedores aprovados, produtos e preços de recorrência configurados.
- Infraestrutura de produção com HTTPS, banco gerenciado, backup e configuração de segredos. Defina `REGIRO_SECRET_KEY` e `REGIRO_HOSTS` em ambiente seguro. Use `REGIRO_DEBUG=1` somente em desenvolvimento.

O repositório contém apenas código e ativos do aplicativo. Não há publicação ou ativação de cobranças.
