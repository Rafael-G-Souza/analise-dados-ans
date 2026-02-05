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