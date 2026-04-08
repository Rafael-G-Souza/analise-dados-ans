# 📊 Painel ANS Analytics - Teste Técnico Intuitive Care

Este projeto apresenta uma solução completa de **Engenharia de Dados (ETL)** e **Desenvolvimento Full Stack** para análise de despesas de operadoras de planos de saúde, utilizando dados públicos da ANS.

A aplicação automatiza a extração de dados contábeis, trata inconsistências de codificação, consolida as informações em um banco de dados relacional e disponibiliza um dashboard interativo para consulta e visualização de indicadores.

## 🚀 Funcionalidades

### 1. Pipeline de Dados (ETL)
- **Extração e Identificação:** Script (`processador.py`) que varre arquivos ZIP baixados da ANS.
- **Tratamento de Encoding:** Solução robusta para lidar com a mistura de arquivos `UTF-8` e `Latin1` (CP1252), preservando acentos (ex: "ASSISTÊNCIA").
- **Normalização:** Conversão de diferentes formatos (CSV, TXT) e limpeza de dados inconsistentes.

### 2. Backend & API
- **API RESTful:** Desenvolvida com **FastAPI**, oferecendo alta performance e documentação automática (Swagger UI).
- **Consultas Otimizadas:** Paginação de resultados e endpoints específicos para estatísticas agregadas.
- **Inserção Segura:** Script dedicado (`popular_banco.py`) para carga de dados no MySQL, garantindo integridade referencial.

### 3. Frontend & Visualização
- **Dashboard Interativo:** Interface construída com **Vue.js 3** e **Chart.js**.
- **Busca Server-Side:** Pesquisa eficiente de operadoras por CNPJ ou Razão Social.
- **Detalhamento:** Modal com histórico financeiro completo de cada operadora.

---

## 🛠️ Tecnologias Utilizadas

- **Linguagem:** Python 3.12+
- **Backend Framework:** FastAPI
- **Banco de Dados:** MySQL 8.0
- **Bibliotecas de Dados:** Pandas, MySQL Connector
- **Frontend:** HTML5, CSS3, Vue.js 3 (CDN), Chart.js
- **Ferramentas:** Git, Python-dotenv

---

## ⚖️ Decisões Técnicas e Trade-offs

Conforme solicitado nos critérios de avaliação, abaixo estão documentadas as decisões de arquitetura e implementação adotadas no projeto:

### 1. Processamento de Dados (ETL)
* **Estratégia de Processamento: Incremental vs. In-Memory**
    * **Decisão:** Processamento incremental (arquivo a arquivo).
    * **Justificativa:** O script `processador.py` itera sobre os arquivos ZIP um por um. Embora o volume atual coubesse na memória, a abordagem incremental garante **escalabilidade**. Se o histórico aumentasse para 10 anos de dados, o consumo de RAM permaneceria estável, evitando erros de *Out of Memory*.

* **Tratamento de Encoding**
    * **Decisão:** Leitura híbrida (UTF-8 forçado com fallback/replace).
    * **Justificativa:** Identificou-se que os arquivos da ANS não possuem padronização (mistura de UTF-8 e Latin1). Forçar um único encoding corrompia dados. A solução implementada tenta ler como UTF-8 e, em caso de bytes inválidos, substitui o caractere sem interromper o fluxo, priorizando a **disponibilidade** dos dados.

### 2. Banco de Dados
* **Inserção de Dados: Script Python vs. LOAD DATA**
    * **Decisão:** Script Python com `mysql-connector`.
    * **Justificativa:** O comando SQL nativo `LOAD DATA INFILE` é performático, mas depende de configurações específicas do servidor e do sistema operacional (Windows vs Linux) para lidar com encodings. O uso do script Python atua como uma camada de abstração que sanitiza os dados (ex: tratando valores "Não Encontrado" como `NULL`) antes da inserção, garantindo consistência.

* **Modelagem (Normalização)**
    * **Decisão:** Tabelas separadas (`operadoras` e `despesas`).
    * **Justificativa:** Separar os dados cadastrais dos lançamentos financeiros reduz drasticamente a redundância de armazenamento e facilita a atualização de dados cadastrais (como mudança de Razão Social) sem a necessidade de atualizar milhões de linhas de despesas.

### 3. Backend (API)
* **Framework: FastAPI vs. Flask**
    * **Decisão:** **FastAPI**.
    * **Justificativa:** Escolhido pela performance superior (assíncrono), tipagem forte com Pydantic (reduz erros de dados em tempo de execução) e geração automática de documentação `/docs`, o que facilita a validação e teste das rotas exigidas no desafio.

* **Estratégia de Paginação**
    * **Decisão:** Offset-based (`LIMIT` / `OFFSET`).
    * **Justificativa:** Para o volume de dados de operadoras ativas (~700-1000 registros), a paginação por offset é simples de implementar e intuitiva para o frontend. A complexidade de *Cursor-based pagination* não se justifica para este volume de dados.

* **Estratégia de Estatísticas**
    * **Decisão:** Uso de tabela pré-calculada (`despesas_agregadas`).
    * **Justificativa:** A rota `/api/estatisticas` consulta uma tabela onde os dados já foram sumarizados durante o ETL. Isso evita que a API tenha que somar milhões de linhas de despesas brutas a cada requisição (tempo real), garantindo resposta instantânea ao usuário.

### 4. Frontend
* **Busca e Filtro: Server-side vs. Client-side**
    * **Decisão:** Busca no Servidor (Server-side).
    * **Justificativa:** Carregar todos os registros para o navegador do cliente consumiria memória desnecessária e aumentaria o tempo de carregamento inicial. A busca no servidor é a solução escalável e correta para aplicações de dados.

* **Gerenciamento de Estado**
    * **Decisão:** Reatividade simples (Vue 3 Options API).
    * **Justificativa:** A aplicação possui fluxo de dados unidirecional simples. Adicionar bibliotecas complexas como Vuex ou Pinia adicionaria "boilerplate" desnecessário, violando o princípio **KISS** (*Keep It Simple, Stupid*) valorizado no teste.

---

## ⚙️ Como Executar

### Pré-requisitos
1. Clone o repositório.
2. Crie um ambiente virtual e instale as dependências:
   ```bash
   pip install -r requirements.txt
Configure o arquivo .env na raiz com sua senha do MySQL:

      Snippet de código
DB_PASSWORD=sua_senha_aqui
Passo a Passo
Banco de Dados: Execute o script sql/schema.sql no seu MySQL para criar a estrutura da tabela.

ETL (Processamento): Execute o comando abaixo para tratar os arquivos e gerar os CSVs:

Bash
python processador.py
Carga no Banco: Execute o script para inserir os dados:

Bash
python popular_banco.py
Backend (API): Inicie o servidor da API:

Bash
uvicorn backend.main:app --reload
Frontend: Abra o arquivo index.html diretamente no seu navegador.

Autor: Rafael G. Souza
