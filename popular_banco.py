import os
import pandas as pd
import mysql.connector
from dotenv import load_dotenv # Você precisará instalar: pip install python-dotenv

load_dotenv() # Carrega o arquivo .env

# CONFIGURAÇÕES
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root', 
    'password': os.getenv('DB_PASSWORD'), # <--- Pega do arquivo oculto
    'database': 'ans_analytics',
    'charset': 'utf8mb4',
    'collation': 'utf8mb4_unicode_ci'
}

CAMINHO_CSV = r'C:\Users\Rafael\Teste_Intuitive_Care\data\processed\consolidado_despesas.csv'

def popular_operadoras():
    print("1. Conectando ao banco de dados...")
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
    except mysql.connector.Error as err:
        print(f"❌ Erro ao conectar: {err}")
        return

    # --- LIMPEZA DA TABELA ---
    print("2. Limpando tabela 'operadoras' antiga...")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
    cursor.execute("TRUNCATE TABLE operadoras;")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")

    # --- LEITURA DO ARQUIVO ---
    print(f"3. Lendo arquivo CSV: {CAMINHO_CSV}")
    try:
        df = pd.read_csv(CAMINHO_CSV, sep=';', encoding='utf-8-sig')
        df.columns = df.columns.str.strip() # Limpa nomes das colunas
    except Exception as e:
        print(f"❌ Erro ao ler o CSV: {e}")
        return

    # --- DETECÇÃO DE COLUNA ---
    nome_coluna_ans = 'RegistroANS' if 'RegistroANS' in df.columns else 'REG_ANS'
    if nome_coluna_ans not in df.columns:
        print(f"❌ Erro: Coluna ANS não encontrada. Colunas: {list(df.columns)}")
        return

    # --- CORREÇÃO DO ERRO 'Não encontrado' ---
    print("4. Limpando dados inválidos...")
    
    # 1. Tenta converter a coluna ANS para número. Se for texto ('Não encontrado'), vira NaN (Nulo)
    df[nome_coluna_ans] = pd.to_numeric(df[nome_coluna_ans], errors='coerce')
    
    # 2. Remove linhas que ficaram com NaN (ou seja, as que não tinham número válido)
    linhas_antes = len(df)
    df = df.dropna(subset=[nome_coluna_ans])
    linhas_depois = len(df)
    
    if linhas_antes > linhas_depois:
        print(f"⚠️ Removidas {linhas_antes - linhas_depois} linhas com Registro ANS inválido.")

    # 3. Garante que é Inteiro
    df[nome_coluna_ans] = df[nome_coluna_ans].astype(int)

    # --- FILTRAGEM ---
    print("5. Filtrando operadoras únicas...")
    df_unicas = df.drop_duplicates(subset=[nome_coluna_ans])
    print(f"-> {len(df_unicas)} operadoras válidas para inserir.")

    # --- INSERÇÃO ---
    print("6. Inserindo no banco...")
    query = """
    INSERT INTO operadoras (reg_ans, cnpj, razao_social, modalidade, uf)
    VALUES (%s, %s, %s, %s, %s)
    """

    inseridos = 0
    for index, row in df_unicas.iterrows():
        def limpar(val):
            # Função para garantir que texto 'Não encontrado' vire NULL no banco
            if pd.isna(val) or str(val).strip().upper() == 'NÃO ENCONTRADO':
                return None
            return str(val).strip()

        reg_ans = int(row[nome_coluna_ans]) # Agora garantido que é número
        cnpj = limpar(row.get('CNPJ'))
        razao = limpar(row.get('RazaoSocial'))
        modalidade = limpar(row.get('Modalidade'))
        uf = limpar(row.get('UF'))

        valores = (reg_ans, cnpj, razao, modalidade, uf)
        
        try:
            cursor.execute(query, valores)
            inseridos += 1
        except mysql.connector.Error as err:
            print(f"⚠️ Erro no ANS {reg_ans}: {err}")

    conn.commit()
    cursor.close()
    conn.close()
    print("-" * 30)
    print(f"✅ SUCESSO! {inseridos} operadoras inseridas.")

if __name__ == "__main__":
    popular_operadoras()