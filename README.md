# ReGiro

**Peças automotivas entre lojas**
Peça parada vira oportunidade.

Protótipo responsivo em português brasileiro com o logotipo oficial. O catálogo usa dados fictícios e permite buscar por peça, fabricante, código, veículo e cidade, filtrar por negociação, ordenar por preço, salvar peças e cadastrar anúncios locais. Os anúncios e favoritos ficam no navegador.

## Executar

Na raiz do repositório, rode `python3 -m http.server 8000` e abra `http://localhost:8000`.

## Escopo do MVP a implementar

- Banco de dados, cadastro e verificação de lojas, autenticação, permissões e painéis.
- Anúncios compartilhados com fotos, moderação, denúncias e alertas.
- Chat, propostas, trocas, aceite bilateral, confirmação de recebimento, disputas e histórico.
- Pagamentos em ambiente de teste, comissão ajustável (inicial de 6%), tarifa única de R$ 10 por troca concluída e controle dos benefícios VIP.
- Política de privacidade, termos e regras de cancelamento.

## Pagamentos

A integração futura requer uma conta de marketplace com divisão de valores, credenciais de teste, segredo de verificação de notificações e contas de vendedores habilitadas. Para operação real, serão necessárias credenciais de produção distintas, configuração dos recebedores e notificações de produção, além da configuração de produtos e preços para recorrência. Os segredos devem ficar no servidor. Este protótipo não recebe dados de cartão, não processa transações e não ativa assinaturas.
