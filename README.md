# AutoTechDealsX

Projeto em Python 3.11 para monitorar ofertas de hardware, periféricos, tecnologia e jogos digitais, aplicar filtros de qualidade, manter histórico local em SQLite e publicar automaticamente no X/Twitter usando a API oficial.

## O que o projeto entrega

- Coleta modular por loja com delays entre requisições.
- Respeito a `robots.txt` antes de tentar coletar HTML ou JSON público.
- Normalização de produtos em um formato único.
- Filtro de descontos, estoque, histórico de preço e sinais de risco.
- Geração de link afiliado com aviso explícito no post.
- Publicação oficial no X em modo real ou `TEST_MODE`.
- Scheduler simples com painel no terminal.
- Banco SQLite para produtos, histórico e itens já publicados.

## Estrutura

```text
AutoTechDealsX/
├── main.py
├── config.py
├── requirements.txt
├── .env.example
├── README.md
├── scrapers/
├── filters/
├── affiliate/
├── publisher/
├── database/
├── scheduler/
├── logs/
└── tests/
```

## Requisitos

- Python 3.11
- `pip`
- Conta de desenvolvedor no X com app configurado

## Instalação

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

## Como criar app no X Developer

Em maio de 2026, a documentação do X indica que você deve criar um app dentro do console oficial e usar a API v2 para publicação de posts.

1. Acesse o console oficial: [console.x.com](https://console.x.com/)
2. Crie ou selecione um `Project`.
3. Crie um `App` dentro do projeto.
4. Habilite permissões de escrita para o app.
5. Gere as credenciais do app:
   - `API Key`
   - `API Key Secret`
   - `Access Token`
   - `Access Token Secret`
   - `Bearer Token`
6. Preencha essas chaves no arquivo `.env`.

Referências oficiais usadas para esta parte:

- [X API overview](https://docs.x.com/x-api)
- [Manage Posts](https://docs.x.com/x-api/posts/manage-tweets/introduction)
- [Create or Edit Post](https://docs.x.com/x-api/posts/create-post)
- [Developer account support](https://developer.x.com/en/support/twitter-api/developer-account1)

## Configuração do `.env`

```env
X_API_KEY=
X_API_SECRET=
X_ACCESS_TOKEN=
X_ACCESS_TOKEN_SECRET=
X_BEARER_TOKEN=
AMAZON_ASSOCIATE_TAG=
ALIEXPRESS_AFFILIATE_ID=
MERCADO_LIVRE_AFFILIATE_ID=
MERCADO_LIVRE_TOOL_ID=
POST_INTERVAL_MINUTES=15
MAX_POSTS_PER_HOUR=4
MIN_DISCOUNT_PERCENT=15
TEST_MODE=true
DISABLED_STORES=
```

### Variáveis principais

- `POST_INTERVAL_MINUTES`: intervalo do ciclo automático.
- `MAX_POSTS_PER_HOUR`: trava de volume de publicação.
- `MIN_DISCOUNT_PERCENT`: corte mínimo do filtro.
- `TEST_MODE`: se `true`, gera o texto do post sem publicar.
- `DISABLED_STORES`: lista separada por vírgulas para pular lojas instáveis ou sem permissão, por exemplo `Nuuvem,Amazon Brasil`.

## Como rodar

### Painel web local

```bash
python app.py
```

Abra:

```text
http://127.0.0.1:5000
```

O painel mostra ofertas aprovadas com capa/imagem, preco, desconto, link da oferta e texto pronto para copiar e publicar manualmente.

### Modo teste

Gera tweets de preview e logs, mas não publica no X. O modo teste usa `autotechdealsx_test.sqlite3`, separado do banco de produção, para não travar a primeira publicação real com histórico de simulação.

```bash
python main.py --test
```

### Modo publicação

Executa uma rodada usando o valor atual de `TEST_MODE`. Se quiser publicar de verdade, deixe `TEST_MODE=false` no `.env`.

```bash
python main.py --once
```

### Modo exportação manual

Filtra e gera posts prontos em `exports/`, sem chamar a API do X.

```bash
python main.py --export --games
```

Para escolher quantos posts salvar:

```bash
python main.py --export --games --export-limit 10
```

### Loop contínuo

```bash
python main.py --run
```

### Somente hardware

```bash
python main.py --hardware
```

### Somente jogos

```bash
python main.py --games
```

Você também pode combinar:

```bash
python main.py --run --hardware
python main.py --test --games
```

## Banco SQLite

O arquivo padrão do banco é `autotechdealsx.sqlite3`.

Quando `TEST_MODE=true` ou `--test` é usado, o banco passa a ser `autotechdealsx_test.sqlite3`.

Tabelas criadas automaticamente:

### `products`

- `id`
- `title`
- `category`
- `store`
- `current_price`
- `old_price`
- `discount_percent`
- `url`
- `affiliate_url`
- `image_url`
- `stock_status`
- `created_at`
- `updated_at`

### `posted_deals`

- `id`
- `product_hash`
- `title`
- `store`
- `posted_url`
- `posted_at`
- `tweet_id`

### `price_history`

- `id`
- `product_hash`
- `price`
- `checked_at`

## Regras implementadas

- Coleta em intervalos automáticos.
- Evita repost com base em `product_hash`.
- Bloqueia itens sem estoque.
- Exige desconto mínimo configurável.
- Exige preço atual menor que o último salvo quando houver histórico.
- Tenta bloquear títulos genéricos, suspeitos ou vendedores pouco confiáveis.
- Tenta bloquear frete abusivo quando a informação está disponível.
- Prioriza maior desconto, marcas fortes, novos mínimos históricos e sinais de popularidade.
- Limita postagens por hora.
- Sinaliza claramente quando o link é afiliado.

## Painel no terminal

O scheduler mostra:

- ofertas coletadas
- ofertas aprovadas
- ofertas postadas
- erros
- próximo horário de execução

## Como adicionar novos sites

1. Crie um novo módulo dentro de `scrapers/`.
2. Reutilize `BaseScraper` ou `HtmlListingScraper`.
3. Prefira endpoints JSON públicos ou APIs oficiais.
4. Valide `robots.txt` e os termos do site.
5. Registre a nova função em `scrapers/__init__.py`.
6. Inclua a loja no plano de coleta em `main.py`.

## Como configurar afiliados

Hoje o projeto já possui suporte inicial para:

- Amazon Brasil via `tag=`
- AliExpress via parâmetros básicos de rastreio
- Mercado Livre via `matt_word`, com `matt_tool` opcional para separar canais

Observação importante:

Cada programa de afiliados pode exigir um formato exato de deeplink, subid, campanha ou assinatura. Se a sua conta exigir parâmetros diferentes, ajuste os módulos em `affiliate/`.

## Como evitar spam e bloqueio

- Use `TEST_MODE=true` antes de ativar a publicação real.
- Mantenha `POST_INTERVAL_MINUTES` e `MAX_POSTS_PER_HOUR` conservadores.
- Não publique o mesmo link repetidamente.
- Não poste ofertas fracas só para encher o feed.
- Não remova a sinalização de link afiliado.
- Revise periodicamente os templates de texto para manter variedade.

## Scraping responsável

O projeto foi estruturado para evitar scraping agressivo:

- usa delay entre requisições
- tenta respeitar `robots.txt`
- não tenta burlar login, captcha, Cloudflare ou proteções
- prefere APIs públicas quando disponíveis

Se uma loja bloquear ou limitar acesso, o comportamento esperado é falhar com log e não contornar a proteção.

Quando uma loja retorna `403`, `429` ou `503`, o sistema pausa essa loja no ciclo atual em vez de insistir em todas as categorias. Quando `robots.txt` bloqueia a rota, a loja é apenas pulada no ciclo e isso não conta como erro operacional.

Para reduzir ruído enquanto testa, você pode pular lojas específicas:

```env
DISABLED_STORES=Nuuvem,Amazon Brasil
```

## Hospedagem em VPS

Fluxo recomendado:

1. Crie a VPS com Python 3.11.
2. Faça clone do projeto.
3. Configure `.env`.
4. Instale dependências.
5. Teste com `python main.py --test`.
6. Rode em produção com `python main.py --run`.
7. Use `systemd`, `supervisor` ou `pm2` para manter o processo vivo.
8. Faça rotação do arquivo `logs/autotechdealsx.log`.

Exemplo simples com `systemd`:

```ini
[Unit]
Description=AutoTechDealsX
After=network.target

[Service]
WorkingDirectory=/srv/autotechdealsx
ExecStart=/srv/autotechdealsx/.venv/bin/python main.py --run
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

## Hospedagem no Render

O projeto inclui `render.yaml`, `runtime.txt` e `app.py` para subir como Web Service Flask.

### Pelo Blueprint

1. Suba o projeto para um repositorio no GitHub.
2. No Render, escolha `New` > `Blueprint`.
3. Conecte o repositorio.
4. O Render vai ler `render.yaml`.
5. Depois do deploy, acesse a URL `onrender.com`.

### Pelo Web Service manual

No Render, escolha `New` > `Web Service` e use:

```text
Language: Python 3
Build Command: pip install -r requirements.txt
Start Command: gunicorn app:app
```

Variaveis recomendadas no Render:

```env
TEST_MODE=true
DISABLED_STORES=Nuuvem,Amazon Brasil
POST_INTERVAL_MINUTES=15
MAX_POSTS_PER_HOUR=4
MIN_DISCOUNT_PERCENT=15
WEB_CACHE_TTL_SECONDS=600
AMAZON_ASSOCIATE_TAG=seu-tag
MERCADO_LIVRE_AFFILIATE_ID=seu-matt-word
MERCADO_LIVRE_TOOL_ID=seu-matt-tool
ALIEXPRESS_AFFILIATE_ID=
```

Para este painel manual, as chaves do X nao sao obrigatorias. Ele filtra e mostra o conteudo pronto para copiar, sem publicar automaticamente.

Observacao: no plano gratuito, o Render pode desligar a instancia quando ela fica ociosa. O primeiro acesso pode demorar e a coleta inicial tambem pode levar alguns segundos. O SQLite local do servico nao deve ser tratado como armazenamento permanente; para historico duravel em producao, use disco persistente ou banco externo.

## Limitações conhecidas

- Alguns scrapers HTML dependem da estrutura atual das páginas e podem exigir manutenção.
- Nem todas as lojas listadas no objetivo possuem API pública estável para promoções.
- As integrações de afiliado podem precisar de adaptação conforme a sua rede de parceria.
- O projeto não promete identificar "menor preço histórico" quando ainda não houver histórico local suficiente.

## Testes

```bash
pytest
```

## Próximos passos recomendados

- adicionar métricas por loja e taxa de conversão
- enriquecer histórico de preços por mais tempo
- incluir ranking de avaliações para jogos por endpoint adicional
- separar fila de coleta e fila de publicação
