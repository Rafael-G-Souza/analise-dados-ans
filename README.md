# 📊 Análise de Dados ANS - ETL e Visualização

Este projeto consiste em uma solução completa de **Engenharia de Dados (ETL)** e **Desenvolvimento Web** para análise das despesas das operadoras de planos de saúde, utilizando dados públicos da **ANS (Agência Nacional de Saúde Suplementar)**.

O sistema automatiza a extração de arquivos zipados complexos, trata inconsistências de codificação (UTF-8/Latin1), consolida as informações em um banco de dados MySQL e apresenta os resultados em uma interface web interativa.

## 🚀 Funcionalidades Principais

### 1. Processamento de Dados (ETL)
- **Extração Automática:** O script `processador.py` varre a pasta de downloads e identifica arquivos `.zip` da ANS.
- **Tratamento de Encoding Inteligente:** Resolve o problema de arquivos mistos (UTF-8 e Latin1/CP1252) que quebram a acentuação (ex: "ASSISTÊNCIA" vs "ASSISTÃNCIA").
- **Cruzamento de Dados:** Enriquece as tabelas financeiras cruzando com o cadastro oficial das operadoras (Razão Social, CNPJ, UF) via API/CSV da ANS.
- **Limpeza de Dados:** Remove linhas órfãs (sem registro ANS válido) e padroniza campos nulos.

### 2. Banco de Dados
- **Inserção Segura:** O script `popular_banco.py` utiliza Python para inserir dados no MySQL, contornando limitações de importação do Workbench e garantindo a integridade dos caracteres especiais.
- **Modelagem Relacional:** Estrutura otimizada para consultas rápidas por operadora.

### 3. Interface Web (Frontend)
- **Dashboard Interativo:** Visualização limpa dos dados em `index.html`.
- **Busca e Filtros:** Pesquisa dinâmica de operadoras.
- **Tecnologias:** Desenvolvido com Vue.js (CDN) para reatividade sem necessidade de build complexo.

---

## 🛠️ Tecnologias Utilizadas

- **Linguagem:** Python 3.12+
- **Bibliotecas Python:**
  - `pandas` (Manipulação de dados massivos)
  - `mysql-connector-python` (Conexão com Banco de Dados)
  - `requests` (Download de dados cadastrais)
  - `python-dotenv` (Gestão segura de credenciais)
- **Banco de Dados:** MySQL
- **Frontend:** HTML5, CSS3, Vue.js

---

## ⚖️ Decisões Técnicas e Trade-offs

Conforme solicitado nas instruções, abaixo estão documentadas as principais decisões de arquitetura e implementação, bem como as justificativas para cada escolha.

### 1. ETL e Processamento de Dados

#### **Estratégia de Processamento: Streaming/Incremental vs. In-Memory**
* **Decisão:** Processamento incremental (arquivo a arquivo) com leitura otimizada via Pandas.
* **Justificativa:** Embora o volume de dados atual (3 trimestres) pudesse caber na memória, optei por uma abordagem que processa cada arquivo ZIP individualmente. Isso garante que a solução seja **escalável** (Resiliente). [cite_start]Se precisássemos processar 10 anos de histórico, a abordagem *In-Memory* travaria por falta de RAM, enquanto a abordagem incremental continuaria funcionando com consumo de memória constante[cite: 38, 39].

#### **Tratamento de Inconsistências de Encoding (O Desafio UTF-8 vs Latin1)**
* **Problema:** Identificou-se que a ANS mistura arquivos em UTF-8 e Latin1 (CP1252), além de conter bytes inválidos (`0x8d`) em alguns arquivos de cadastro.
* **Decisão:** Implementação de um `TextIOWrapper` com estratégia `errors='replace'`.
* **Justificativa:** Forçar Latin1 corrompia caracteres em arquivos UTF-8 (ex: "ASSISTÊNCIA" virava "ASSISTÃNCIA"). Tentar apenas UTF-8 quebrava o script nos arquivos antigos. A solução híbrida adotada força a leitura em UTF-8 para preservar a acentuação correta e substitui bytes corrompidos isolados em vez de abortar o processo. [cite_start]Isso prioriza a **disponibilidade** e **integridade legível** dos dados[cite: 36, 50].

#### **Tratamento de Dados Órfãos (Integridade Referencial)**
* **Decisão:** Remover linhas de despesas onde o `REG_ANS` não pôde ser identificado/convertido para numérico.
* **Justificativa:** O Registro ANS é a chave primária da operadora. Permitir dados sem essa chave violaria a integridade do banco de dados e geraria relatórios inconsistentes. [cite_start]Dados sem identificação de origem não têm valor analítico confiável neste contexto[cite: 50, 64].

---

### 2. Banco de Dados e Modelagem

#### **Normalização: Tabela Única vs. Tabelas Separadas**
* **Decisão:** Opção B - Tabelas Normalizadas (`operadoras` e `despesas` separadas).
* **Justificativa:**
    1.  **Redundância:** Repetir a `RazaoSocial`, `CNPJ` e `UF` para cada lançamento financeiro (milhares de linhas) desperdiçaria armazenamento e I/O.
    2.  **Manutenibilidade:** Se uma operadora mudar de Razão Social, na tabela normalizada atualizamos apenas 1 linha. Na desnormalizada, teríamos que atualizar milhares de registros.
    3.  [cite_start]**Performance:** Queries de agregação (somas, médias) são mais rápidas em tabelas de fatos (`despesas`) mais "magras" (apenas IDs e valores)[cite: 109, 110].

#### **Tipos de Dados Monetários**
* **Decisão:** Uso de `DECIMAL` (ou equivalente no Pandas antes da inserção) em vez de `FLOAT`.
* **Justificativa:** Dados financeiros exigem precisão exata. O tipo `FLOAT` utiliza ponto flutuante binário, o que pode acarretar erros de arredondamento em somas grandes (o clássico problema do `0.1 + 0.2 != 0.3`). [cite_start]Para contabilidade, precisão decimal é obrigatória[cite: 114, 116].

#### **Inserção de Dados: Script Python vs. LOAD DATA INFILE**
* **Decisão:** Inserção via script Python (`mysql-connector`) em lotes.
* **Justificativa:** O comando nativo `LOAD DATA` do SQL é mais rápido, porém extremamente sensível a configurações de servidor e encoding (especialmente em Windows). [cite_start]O script Python atua como uma camada de segurança, sanitizando dados (convertendo "Não Encontrado" para `NULL`) e garantindo que o encoding `utf8mb4` seja respeitado independente do sistema operacional onde o teste for corrigido[cite: 118, 119].

---

### 3. API e Backend (Sugestão - Ajuste conforme o que você fez)

#### **Framework: FastAPI vs. Flask**
* **Decisão:** FastAPI.
* [cite_start]**Justificativa (Se FastAPI):** Alta performance (assíncrono), validação de dados automática com Pydantic e geração automática de documentação (Swagger UI), o que facilita o teste das rotas conforme exigido[cite: 147, 150].


#### **Estratégia de Paginação**
* **Decisão:** Offset-based (`LIMIT` / `OFFSET`).
* **Justificativa:** O volume de operadoras (cerca de 700-1000 ativas) não justifica a complexidade de *Cursor-based pagination*. [cite_start]O *Offset* é simples de implementar, intuitivo para o Frontend e performático o suficiente para este volume de dados[cite: 152, 155].

---

### 4. Frontend (Vue.js)

#### **Busca e Filtros: Server-side vs. Client-side**
* **Decisão:** Busca no Servidor (Server-side).
* **Justificativa:** Embora o dataset atual seja pequeno, em um cenário real de "Big Data" da ANS, carregar todos os registros para o navegador do cliente causaria lentidão e alto consumo de memória. [cite_start]A busca no servidor é a solução correta pensando em escalabilidade e performance do dispositivo do usuário[cite: 175, 178].

#### **Gerenciamento de Estado**
* **Decisão:** Props e Events simples (ou Composition API).
* **Justificativa:** A aplicação possui baixa complexidade de compartilhamento de estado (basicamente listagem -> detalhes). [cite_start]Introduzir uma lib complexa como Pinia ou Vuex adicionaria "overhead" desnecessário e violaria o princípio KISS (Keep It Simple) valorizado no teste[cite: 181, 206].

---

## ⚙️ Pré-requisitos

Antes de começar, você precisa ter instalado:
- [Python 3.x](https://www.python.org/downloads/)
- [MySQL Server](https://dev.mysql.com/downloads/mysql/)
- Git

---

## 📦 Como rodar o projeto

### Passo 1: Clone o repositório
```bash
git clone [https://github.com/Rafael-G-Souza/analise-dados-ans.git](https://github.com/Rafael-G-Souza/analise-dados-ans.git)
cd analise-dados-ans
Passo 2: Configure o Ambiente
Crie um ambiente virtual (recomendado):

Bash
python -m venv .venv
source .venv/bin/activate  # No Windows: .venv\Scripts\activate
Instale as dependências:

Bash
pip install -r requirements.txt
Configure as variáveis de ambiente:

Crie um arquivo chamado .env na raiz do projeto.

Adicione sua senha do MySQL (não use aspas):

Snippet de código
DB_PASSWORD=sua_senha_aqui
Passo 3: Configure o Banco de Dados
Execute o script SQL (disponível na pasta sql/ ou via Workbench) para criar a tabela:

SQL
CREATE DATABASE IF NOT EXISTS ans_analytics;
USE ans_analytics;

CREATE TABLE IF NOT EXISTS operadoras (
    reg_ans INT PRIMARY KEY,
    cnpj VARCHAR(20),
    razao_social VARCHAR(255),
    modalidade VARCHAR(100),
    uf CHAR(2)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
Passo 4: Execute o Pipeline
Processe os arquivos: (Certifique-se de ter os ZIPs na pasta downloads ou configure o script para baixar)

Bash
python processador.py
Isso irá gerar o arquivo data/processed/consolidado_despesas.csv.

Popule o Banco de Dados:

Bash
python popular_banco.py
Isso irá limpar a tabela antiga e inserir os novos dados processados.

Acesse a Interface:

Abra o arquivo index.html diretamente no seu navegador.

📂 Estrutura do Projeto
Plaintext
analise-dados-ans/
│
├── .gitignore          # Arquivos ignorados pelo Git
├── .env                # Credenciais (NÃO COMMITAR)
├── requirements.txt    # Dependências do Python
├── README.md           # Documentação do projeto
│
├── processador.py      # Script principal de ETL
├── popular_banco.py    # Script de carga no MySQL
├── index.html          # Interface Frontend
│
├── data/               # Armazena os CSVs processados
│   └── processed/
│
└── frontend/           # Scripts e estilos adicionais
    ├── script.js
    └── styles.css
👨‍💻 Autor
Rafael G. Souza

Este projeto foi desenvolvido como parte de um teste técnico para avaliação de competências em Engenharia de Dados e Desenvolvimento Full Stack.