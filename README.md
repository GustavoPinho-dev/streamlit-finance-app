# 💰 Minhas Finanças App — Telegram Bot + Streamlit

Projeto de gestão financeira pessoal com **ingestão via Telegram**, **armazenamento no Google Sheets** e **visualização em dashboard no Streamlit**.

> ⚙️ **Build to Learn:** este é um projeto construído com foco em aprendizado prático de engenharia de dados, automação, integração de APIs e desenvolvimento de aplicações de dados ponta a ponta.

---

## 📌 Visão geral

O projeto implementa uma arquitetura simples e didática para controlar movimentações financeiras em três camadas principais:

1. **Entrada de dados (Bot no Telegram)**
   - O usuário registra gastos, receitas, investimentos e rendimentos por conversa guiada.
2. **Persistência (Google Sheets + Bronze opcional em Postgres)**
   - Os dados operacionais ficam em planilhas.
   - Opcionalmente, os eventos também são gravados em uma camada bronze no Postgres.
3. **Consumo analítico (Streamlit)**
   - A aplicação transforma e organiza os dados para exibição em tabelas, métricas e gráficos.

---

## 🧠 Objetivos do projeto (Build to Learn)

Este repositório foi criado para praticar:

- Integração com APIs externas (Telegram e Google Sheets).
- Modelagem de fluxos conversacionais com máquina de estados.
- Construção de pipeline ETL em Python.
- Criação de dashboard interativo com Streamlit e Plotly.
- Organização de código por domínios (`bot`, `etl`, `data`, `services`, `config`).
- Execução local com Docker e orquestração com Docker Compose.

---

## 🏗️ Arquitetura

![Fluxo de Arquitetura](images/diagram_app_finance.png)

### Componentes

- **Telegram Bot (`bot/`)**
  - Coleta dados via comandos e perguntas contextuais.
  - Controla estados de conversa com `ConversationHandler`.
- **Serviços de negócio (`bot/services/`)**
  - Regras para validar e salvar lançamentos.
- **Camada de extração e transformação (`data/` + `etl/`)**
  - Leitura de abas no Google Sheets.
  - Padronização e tipagem de datas/valores para análise.
- **Dashboard (`app.py`)**
  - Visualização por páginas: Rendimentos, Investimentos e Gastos.
  - Filtros por período e instituição, além de área de planejamento financeiro.

---

## 🔄 Fluxo funcional da aplicação

### 1) Registro pelo Telegram

O usuário inicia com `/registrar` e escolhe o tipo de lançamento:

- **Gastos:** valor → categoria → instituição → descrição.
- **Investimentos:** valor → produto → tipo (Aplicação/Retirada) → vencimento → indicador/taxa → instituição.
- **Receita:** valor → descrição → instituição.
- **Rendimentos:** valor → data início → data fim → instituição.

Ao final, o bot resume os dados e salva na planilha associada ao usuário.

### 2) Consulta pelo Telegram

Com `/consultar`, o usuário solicita resumos (como gastos, total investido e saldos) com base nos dados registrados.

### 3) Transformação e consumo no Streamlit

Ao acessar o dashboard:

- A aplicação autentica o usuário.
- Resolve o `sheet_id` correspondente.
- Executa o pipeline `FinanceDataPipeline` para:
  - Converter valores monetários para numérico.
  - Padronizar e converter datas.
  - Criar campos derivados (ex.: mês de referência, tipo composto de investimento).
- Exibe visões analíticas para acompanhamento financeiro.

---

## 📊 Funcionalidades do dashboard

### 📈 Rendimentos

- Tabela de rendimentos com período.
- Série temporal por data de fim.

### 🏦 Investimentos

- Lista de investimentos com valor e vencimento.
- Gráfico de distribuição por tipo/produto.

### 💸 Gastos

- Filtro por mês e recorte “mês inteiro” ou “até o dia atual”.
- Cards por instituição com:
  - Receitas
  - Despesas
  - Saldo
  - Total investido
- Gráfico de pizza por categoria de despesa.
- Área de planejamento com objetivos mensais e distribuição da sobra.

---

## 🧰 Stack utilizada

- **Python**
- **Streamlit** (dashboard)
- **python-telegram-bot** (bot)
- **Pandas** (tratamento de dados)
- **Plotly** (visualizações)
- **Google Sheets API / Google Drive API**
- **PostgreSQL** (opcional, camada bronze)
- **Docker / Docker Compose**

---

## 📁 Estrutura de pastas

```bash
.
├── app.py                        # Dashboard Streamlit
├── main.py                       # Ponto de entrada do bot
├── bot/
│   ├── bot.py                    # Configuração do Application e ConversationHandler
│   ├── handlers/
│   │   ├── registration.py       # Fluxos de registro financeiro
│   │   ├── inquiry.py            # Fluxos de consulta
│   │   └── common.py             # Comandos comuns (ex.: cancelar)
│   └── services/
│       ├── finance_service.py    # Regras de persistência de registros
│       ├── constants.py          # Estados e constantes do bot
│       └── utils.py              # Utilitários do bot
├── config/
│   ├── auth.py                   # Autenticação no app Streamlit
│   └── sheets.py                 # Resolução de sheet_id por usuário
├── data/
│   ├── extract.py                # Extração de dados do Google Sheets
│   └── bronze_postgres.py        # Persistência opcional da camada bronze
├── etl/
│   └── transform.py              # Pipeline de transformação (FinanceDataPipeline)
├── services/
│   ├── utils.py                  # Funções utilitárias de cálculo e normalização
│   └── calc_investimentos.py     # Cálculos auxiliares de investimentos
├── images/
│   ├── diagram_app_finance.png   # Diagrama de arquitetura
│   └── *_logo.png                # Logos usados na interface
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

---

## ✅ Pré-requisitos

- Python **3.10+**
- Conta Google Cloud com:
  - **Google Sheets API** habilitada
  - **Google Drive API** habilitada
- Credenciais de conta de serviço
- Token de bot do Telegram

---

## 🔐 Configuração de segredos

Crie `.streamlit/secrets.toml` com os valores reais:

```toml
bot_token = "SEU_TOKEN_DO_BOT"
SHEET_ID = "ID_DA_PLANILHA_PADRAO"

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

[auth.credentials.usernames.seu_usuario]
name = "Seu Nome"
password = "HASH_OU_VALOR_CONFIGURADO"
sheet_id = "ID_DA_PLANILHA_DO_USUARIO"
```

> Observação: o projeto pode trabalhar com `SHEET_ID` padrão e também com `sheet_id` específico por usuário autenticado.

---

## ▶️ Como executar

### Execução local (Python)

1. Instale as dependências:

```bash
pip install -r requirements.txt
```

2. Rode o bot:

```bash
python main.py
```

3. Rode o dashboard:

```bash
streamlit run app.py
```

### Execução com Docker

Subir apenas o bot:

```bash
docker compose up --build bot
```

Subir bot + Postgres (bronze):

```bash
docker compose up --build
```

Rodar em background:

```bash
docker compose up -d --build bot
```

Ver logs:

```bash
docker compose logs -f bot
```

Parar tudo:

```bash
docker compose down
```

---

## 🤖 Comandos do bot

- `/registrar` → inicia novo lançamento financeiro.
- `/consultar` → inicia fluxo de consulta.
- `/cancelar` → interrompe a conversa atual e limpa dados temporários.

---

## 🚧 Limitações atuais e próximos passos