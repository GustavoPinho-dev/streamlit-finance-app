# 💰 Minhas Finanças - Telegram Bot

Este projeto é um assistente financeiro automatizado que utiliza o **Telegram** como interface de entrada de dados (Ingestion) para alimentar uma planilha no **Google Sheets**. O sistema foi desenhado como um pipeline de dados ETL que adapta suas perguntas com base no comando escolhido e no tipo de operação escolhida.

## 🏗️ Arquitetura do Sistema

O fluxo de dados segue uma estrutura de Pipeline de dados com integração ao Google Cloud:

![Fluxo de Arquitetura](images/diagram_app_finance.png)

1.  **Interface (Telegram Bot):** Captura os dados brutos via `python-telegram-bot` e salva eles no Google Sheets.
2.  **Armazenamento (Google Sheets):** Armazena os dados normalizados para posterior análise e criação de dashboards.
3.  **Processamento (Backend Python):** Gerencia a máquina de estados (ConversationHandler), valida os inputs e realiza o ETL dos dados salvos para posterior visualização.
4.  **Dashboard (Streamlit):** Os dados são carregados e organizados em tabelas e gráficos para análise.

---

## 🚀 Funcionalidades e Fluxos do Bot

O bot utiliza lógica condicional para garantir que apenas os dados necessários sejam coletados, otimizando a experiência do usuário:

### 1. Gastos
Fluxo padrão para controle de fluxo de caixa mensal.
* **Perguntas:** Valor ➡️ Categoria ➡️ Instituição ➡️ Descrição.

### 2. Investimentos
Fluxo detalhado para acompanhamento de patrimônio.
* **Perguntas:** Valor ➡️ Produto (ex: CDB) ➡️ Tipo (Aplicação/Retirada) ➡️ Vencimento ➡️ Indicador (ex: CDI) ➡️ Instituição.

### 3. Receita
Fluxo expresso para ganhos rápidos.
* **Perguntas:** Valor ➡️ Instituição ➡️ Descrição.

### 4. Rendimentos
Fluxo para registro de rendimentos de investimentos realizados.
* **Perguntas:** Valor ➡️ Data Início ➡️ Data Fim

---

## 🛠️ Configuração

### Pré-requisitos
* Python 3.10 ou superior.
* Uma conta no Google Cloud com a **Google Sheets API** e **Google Drive API** ativas.
* Arquivo de credenciais (`credentials.json`) da conta de serviço.

### Variáveis de Ambiente (Streamlit Secrets)
Para rodar no Streamlit Cloud ou localmente, configure o arquivo `.streamlit/secrets.toml`:

```toml
bot_token = "SEU_TOKEN_DO_BOT_AQUI"
SHEET_ID = "ID_DA_SUA_PLANILHA_GOOGLE"

[gcp_service_account]
type = "service_account"
project_id = "seu-projeto"
private_key_id = "..."
private_key = "..."
client_email = "..."
client_id = ""
auth_uri = ""
token_uri = ""
auth_provider_x509_cert_url = ""
client_x509_cert_url = ""
universe_domain = "googleapis.com"
```
--


## 🐳 Rodando o bot com Docker (local)

### 1) Crie o arquivo de segredo
Crie o arquivo `.streamlit/secrets.toml` com o token do bot, o `SHEET_ID` e as credenciais da conta de serviço (mesmo formato da seção de configuração acima).

### 2) Suba o container do bot
Com Docker e Docker Compose instalados, execute:

```bash
docker compose up --build bot
```

### 2.1) Subir bot + Postgres (camada Bronze)
Para iniciar o banco Postgres junto do bot e habilitar a camada bronze:

```bash
docker compose up --build
```

O serviço `bot` recebe automaticamente a variável `DATABASE_URL` apontando para o serviço `postgres`.
Quando configurada, cada novo evento salvo no Google Sheets também é persistido na tabela `bronze.sheet_events`.

O container inicia com o comando `python main.py`, que executa o Telegram bot em modo polling.

### 3) Rodar em background
Se quiser deixar em segundo plano:

```bash
docker compose up -d --build bot
```

Para acompanhar logs:

```bash
docker compose logs -f bot
```

Para parar:

```bash
docker compose down
```

> Observação: o arquivo de segredos é montado em modo somente leitura (`/app/.streamlit/secrets.toml`) e **não** é incluído na imagem.

### Banco Postgres (Bronze)

No `docker-compose.yml` o Postgres é iniciado com os parâmetros:

- `POSTGRES_DB=finance`
- `POSTGRES_USER=finance_user`
- `POSTGRES_PASSWORD=finance_pass`

String de conexão usada no bot:

```bash
DATABASE_URL=postgresql://finance_user:finance_pass@postgres:5432/finance
```

A tabela de ingestão bronze é criada automaticamente na primeira escrita do bot.

---

## 📂 Estrutura de Pastas


```
├── bot/
│   └── handlers/
│       └── common.py               # Máquina de estados para a função 'cancelar'
│       └── inquiry.py              # Máquina de estados para a função 'consultar'
│       └── registration.py         # Máquina de estados para a função 'registrar'
│   └── services/
│       └── constants.py            # Constantes utilizadas na lógica dos comandos do bot
│       └── finance_service.py      # Service para utilziar classes
│       └── utils.py                # Funções de uso comum
│   └── bot.py                      # Lógica da interface e máquina de estados
├── config/
│   └── auth.py                     # Autorização para acessar o Google Sheets
├── etl/
│   └── transform.py                # Lógica para transformação dos dados
├── data/
│   └── extract.py                  # Funções de integração (ETL/Load)
├── images/
|   └── Imagens Bancos
│   └── Minhas_Finanças_App.drawio  # Diagrama da arquitetura
├── .streamlit/
│   └── secrets.toml                # Configurações sensíveis (não versionar!)
└── requirements.txt                # Dependências do projeto
```

## 📝 Comandos Bot
* /registrar: Inicia um novo lançamento financeiro.

* /cancelar: Interrompe o fluxo atual e limpa os dados temporários.

* /consultar: Inicia um fluxo para consultar um resumo dos dados salvos.
