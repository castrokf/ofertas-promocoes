# AutoTechDealsX

Plataforma SaaS para monitorar promoções de hardware, periféricos, eletrônicos, jogos digitais e produtos tech, com coleta segura, histórico de preços, engine de decisão, anti-duplicidade, geração de mensagens e publicação em canais oficiais ou permitidos.

## Stack escolhida

Usei Python 3.11 + FastAPI no backend porque a maior parte do sistema depende de conectores, filas, regras de preço, integração com APIs e workers assíncronos. Python deixa essa camada mais simples de testar e evoluir. Para o painel, usei React + Vite + TypeScript, que entrega uma interface leve para administrar ofertas, lojas, regras, canais, logs e URLs monitoradas.

Componentes principais:

- Backend: FastAPI, SQLAlchemy, Alembic, Pydantic.
- Banco: PostgreSQL.
- Fila e scheduler: Redis + Celery.
- Frontend: React, Vite, TypeScript.
- Deploy: Docker Compose local e Blueprint do Render.
- Publicação: Discord Webhook, Telegram Bot API, X/Twitter API oficial, canal interno do site.

## Estrutura

```text
backend/
  app/
    api/
    affiliate/
    ai/
    connectors/
    core/
    models/
    price_engine/
    publishers/
    schemas/
    services/
    workers/
  alembic/
  scripts/
  tests/
frontend/
  src/
    components/
    hooks/
    pages/
    services/
docker/
docker-compose.yml
render.yaml
.env.example
```

## O que já está implementado

- API REST protegida por JWT.
- Seed com usuário admin inicial.
- Modelagem PostgreSQL para lojas, categorias, produtos, histórico de preços, ofertas, publicações, regras, canais, logs, URLs monitoradas, configurações e afiliados.
- Migração Alembic inicial.
- Worker Celery e Celery Beat com filas de coleta/publicação.
- Conector funcional da Steam usando endpoint público de loja.
- Conectores preparados e seguros para Amazon, Mercado Livre, AliExpress, Magazine Luiza, Shopee, Kabum, Terabyte, Pichau, Nuuvem, Epic, Green Man Gaming, GOG, Xbox, PlayStation e Nintendo.
- Engine de preço com desconto mínimo, média histórica, menor preço, frete abusivo, estoque, anti-duplicidade e classificação de qualidade.
- Gerador de mensagens para Twitter/X, Telegram, Discord e site.
- Publicadores para Discord, Telegram, X/Twitter oficial e site.
- Painel React com login, cards de ofertas com imagem, aprovação, publicação, lojas, regras, canais, URLs e logs.
- Modo seguro `PUBLISH_DRY_RUN=true`, que gera publicação registrada sem enviar para canais externos.

## Requisitos locais

- Docker Desktop, recomendado.
- Ou Python 3.11, PostgreSQL, Redis e Node.js 20+ se rodar sem Docker.

## Configuração

Crie o arquivo `.env`:

```bash
copy .env.example .env
```

Principais variáveis:

```env
DATABASE_URL=postgresql+psycopg://autotech:autotech@postgres:5432/autotechdealsx
REDIS_URL=redis://redis:6379/0
SECRET_KEY=troque-em-producao
ADMIN_EMAIL=admin@autotech.local
ADMIN_PASSWORD=troque-esta-senha
RESET_ADMIN_PASSWORD_ON_START=false
PUBLISH_MODE=semi_automatic
PUBLISH_DRY_RUN=true
MIN_DISCOUNT_PERCENT=15
AMAZON_ASSOCIATE_TAG=
MERCADO_LIVRE_AFFILIATE_ID=
MERCADO_LIVRE_TOOL_ID=
ALIEXPRESS_AFFILIATE_ID=
DISCORD_WEBHOOK_URL=
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
X_API_KEY=
X_API_SECRET=
X_ACCESS_TOKEN=
X_ACCESS_TOKEN_SECRET=
X_BEARER_TOKEN=
```

Comece com `PUBLISH_DRY_RUN=true`. Só mude para `false` quando os canais estiverem configurados e você já tiver testado as mensagens.

## Rodar com Docker

```bash
docker compose up --build
```

Acesse:

```text
http://localhost:3000
```

Login inicial:

```text
admin@autotech.local
admin123
```

Troque esse usuário/senha antes de produção.

## Rodar backend manualmente

Use estes comandos dentro da pasta `backend`, para evitar conflito com o `app.py` legado da raiz:

```bash
cd backend
python -m venv ..\.venv
..\.venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
python scripts/seed.py
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Workers:

```bash
cd backend
celery -A app.core.celery_app.celery_app worker --loglevel=INFO
celery -A app.core.celery_app.celery_app beat --loglevel=INFO
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

## Testes

```bash
cd backend
..\.venv\Scripts\python.exe -m pytest tests
```

## Publicação em canais

Discord:

- Crie um webhook no servidor/canal desejado.
- Preencha `DISCORD_WEBHOOK_URL`.
- Cadastre ou use o canal `discord` no painel.

Telegram:

- Crie um bot com o BotFather.
- Pegue o token do bot.
- Pegue o `chat_id` do canal/grupo.
- Preencha `TELEGRAM_BOT_TOKEN` e `TELEGRAM_CHAT_ID`.

X/Twitter:

- Use apenas a API oficial.
- Crie o app no X Developer Console.
- Ative permissão de escrita.
- Gere `API Key`, `API Secret`, `Access Token`, `Access Token Secret` e `Bearer Token`.
- Preencha as variáveis `X_*`.
- Mude `PUBLISH_DRY_RUN=false` somente depois de testar.

## Afiliados

Amazon:

- Use o ID de associado no formato parecido com `seutag-20`.
- Configure `AMAZON_ASSOCIATE_TAG`.

Mercado Livre:

- Use o `matt_word` como `MERCADO_LIVRE_AFFILIATE_ID`.
- Use o `matt_tool` como `MERCADO_LIVRE_TOOL_ID`.

AliExpress:

- Configure `ALIEXPRESS_AFFILIATE_ID` quando tiver acesso ao portal/ID de afiliado.
- Se ainda não tiver, pode rodar sem ele. Os links recebem UTM normal, mas não ficam monetizados pelo AliExpress.

O sistema nunca deve esconder que o link é afiliado. As mensagens incluem aviso quando aplicável.

## Como adicionar uma nova loja

1. Crie um conector em `backend/app/connectors/`.
2. Herde de `BaseConnector`.
3. Prefira API oficial, feed de afiliado, RSS ou endpoint público documentado.
4. Não burle captcha, login, Cloudflare ou bloqueios.
5. Respeite rate limits e `robots.txt` quando usar HTML público.
6. Retorne uma lista de `ProductSnapshot`.
7. Registre o conector em `backend/app/connectors/registry.py`.
8. Rode testes e uma coleta em `PUBLISH_DRY_RUN=true`.

## Como adicionar um canal

1. Crie um publisher em `backend/app/publishers/`.
2. Implemente `publish(payload)`.
3. Adicione o tipo de canal no enum `ChannelType`.
4. Registre no `PublicationService`.
5. Crie variáveis de ambiente para tokens.
6. Garanta logs sem expor segredos.

## Regras de coleta segura

- Não usar técnicas agressivas de scraping.
- Não contornar captcha, login, Cloudflare, bloqueio ou proteção anti-bot.
- Preferir API oficial, feed de afiliado, RSS e webhooks.
- Usar delays, retry com backoff e pausa quando houver erro excessivo.
- Não prometer menor preço sem histórico suficiente.
- Bloquear marketplace ou vendedor suspeito quando o dado estiver disponível.
- Bloquear frete abusivo quando o dado estiver disponível.
- Evitar repostar a mesma oferta no cooldown configurado.

## Deploy no Render

O projeto inclui `render.yaml` com:

- Web service Docker do backend.
- Worker Celery.
- Scheduler Celery Beat.
- Render Key Value para Redis.
- PostgreSQL gerenciado.
- Static site para o frontend.

Passos:

1. Suba o projeto para GitHub.
2. No Render, escolha `New` > `Blueprint`.
3. Conecte o repositório.
4. Confirme os serviços do `render.yaml`.
5. Depois do primeiro deploy, ajuste `VITE_API_BASE_URL` no serviço web se a URL pública do backend for diferente.
6. Preencha variáveis secretas no painel do Render.
7. Mantenha `PUBLISH_DRY_RUN=true` até validar tudo.

Observação: no Render atual, Redis aparece como Render Key Value em Blueprints, e o tipo antigo `redis` é tratado como alias legado. O arquivo usa `type: keyvalue`.

## Deploy no Render sem Blueprint

Se o Render pedir cartão ao abrir Blueprints, crie os serviços manualmente. Esse modo evita worker pago e usa um endpoint de cron seguro para coleta/publicação.

### 1. PostgreSQL

Crie:

```text
New > PostgreSQL
```

Escolha o plano Free se estiver disponível. Copie a `Internal Database URL`.

### 2. Backend API

Crie:

```text
New > Web Service
Repository: castrokf/ofertas-promocoes
Branch: main
Runtime: Docker
Dockerfile Path: backend/Dockerfile
```

Variáveis:

```env
DATABASE_URL=cole-a-internal-database-url-do-postgres
SECRET_KEY=gere-um-texto-longo-aleatorio
ADMIN_EMAIL=admin@autotech.local
ADMIN_PASSWORD=troque-esta-senha
RESET_ADMIN_PASSWORD_ON_START=false
ENVIRONMENT=production
PUBLISH_MODE=semi_automatic
PUBLISH_DRY_RUN=true
CRON_SECRET=gere-um-texto-longo-aleatorio
MIN_DISCOUNT_PERCENT=15
CORS_ORIGINS=https://sua-url-do-frontend.onrender.com
PUBLIC_BASE_URL=https://sua-url-do-frontend.onrender.com
AMAZON_ASSOCIATE_TAG=
MERCADO_LIVRE_AFFILIATE_ID=castrok77
MERCADO_LIVRE_TOOL_ID=23800724
ALIEXPRESS_AFFILIATE_ID=
DISCORD_WEBHOOK_URL=
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
X_API_KEY=
X_API_SECRET=
X_ACCESS_TOKEN=
X_ACCESS_TOKEN_SECRET=
X_BEARER_TOKEN=
```

Teste:

```text
https://sua-api.onrender.com/api/v1/healthz
```

### 3. Frontend

Crie:

```text
New > Static Site
Repository: castrokf/ofertas-promocoes
Branch: main
Root Directory: frontend
Build Command: npm install && npm run build
Publish Directory: dist
```

Variável:

```env
VITE_API_BASE_URL=https://sua-api.onrender.com/api/v1
```

Depois que o frontend tiver URL, volte no backend e ajuste:

```env
CORS_ORIGINS=https://sua-url-do-frontend.onrender.com
PUBLIC_BASE_URL=https://sua-url-do-frontend.onrender.com
```

### 4. Automação sem worker pago

Use um cron externo, por exemplo cron-job.org, para chamar:

```text
https://sua-api.onrender.com/api/v1/cron/run?token=SEU_CRON_SECRET&segment=games&publish=true
```

Sugestão inicial:

```text
Intervalo: 15 minutos
Método: GET
```

Enquanto `PUBLISH_DRY_RUN=true`, o sistema coleta, filtra e registra tentativa, mas não envia para canais externos.

## Limitações importantes

- A Steam já coleta dados reais via endpoint público.
- As outras lojas estão como conectores preparados porque cada uma exige contrato, feed, API oficial ou parser permitido específico.
- O sistema está pronto para integrar esses feeds sem técnicas agressivas.
- O painel administra e publica ofertas, mas métricas avançadas de clique dependem de integrar um redirecionador ou serviço de tracking.

## Exemplos de mensagem

```text
🔥 OFERTA IMPERDÍVEL

SSD NVMe Kingston 1TB
De R$ 399,00 por R$ 299,00
🏬 Kabum
📉 25% OFF

🔗 https://link-da-oferta

link afiliado / posso receber comissão
```

```text
🎮 JOGO EM PROMOÇÃO

Nome do jogo
💰 R$ 19,90
🏬 Steam
📉 80% OFF

🔗 https://link-da-oferta
```
