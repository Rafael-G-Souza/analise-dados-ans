from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import mysql.connector
from typing import Optional, List
from pydantic import BaseModel

app = FastAPI(title="API ANS Analytics")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"], 
)

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root', 
    'password': 'Kdallete250995$', 
    'database': 'ans_analytics',
    'charset': 'utf8mb4',
    'collation': 'utf8mb4_unicode_ci'
}

def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

# --- A CORREÇÃO FINAL ESTÁ AQUI ---
class Operadora(BaseModel):
    reg_ans: int
    cnpj: str
    # Mudamos de 'str' para 'Optional[str] = None' para aceitar NULL do banco
    razao_social: Optional[str] = None 
    uf: Optional[str] = None

class MetaData(BaseModel):
    page: int
    limit: int
    total: int

class PaginatedResponse(BaseModel):
    data: List[Operadora]
    meta: MetaData

@app.get("/api/operadoras", response_model=PaginatedResponse)
def listar_operadoras(
    page: int = Query(1, ge=1), 
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = None
):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    offset = (page - 1) * limit

    query = "SELECT reg_ans, cnpj, razao_social, uf FROM operadoras"
    count_query = "SELECT COUNT(*) as total FROM operadoras"
    params = []

    if search:
        search_term = f"%{search}%"
        where_clause = " WHERE razao_social LIKE %s OR cnpj LIKE %s"
        
        query += where_clause
        count_query += where_clause 
        
        params.extend([search_term, search_term])

    cursor.execute(count_query, params)
    total_result = cursor.fetchone()
    total = total_result['total']

    query += " LIMIT %s OFFSET %s"
    params.extend([limit, offset])

    cursor.execute(query, params)
    result = cursor.fetchall()
    
    conn.close()
    
    return {
        "data": result,
        "meta": {"page": page, "limit": limit, "total": total}
    }

@app.get("/api/operadoras/{cnpj}")
def detalhes_operadora(cnpj: str):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM operadoras WHERE cnpj = %s", (cnpj,))
    op = cursor.fetchone()
    
    if not op:
        conn.close()
        raise HTTPException(status_code=404, detail="Operadora não encontrada")
    
    conn.close()
    return op

@app.get("/api/operadoras/{cnpj}/despesas")
def historico_despesas(cnpj: str):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    query = """
        SELECT d.ano, d.trimestre, d.descricao_conta, d.valor_despesa, d.data_referencia
        FROM despesas_detalhadas d
        JOIN operadoras o ON d.reg_ans = o.reg_ans
        WHERE o.cnpj = %s
        ORDER BY d.data_referencia DESC
    """
    cursor.execute(query, (cnpj,))
    result = cursor.fetchall()
    conn.close()
    return result

@app.get("/api/estatisticas")
def estatisticas_agregadas():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # 1. Total Geral e Média
    cursor.execute("SELECT SUM(total_despesas) as total, AVG(media_lancamento) as media FROM despesas_agregadas")
    geral = cursor.fetchone()
    
    # 2. Top 5 Operadoras
    cursor.execute("SELECT razao_social, total_despesas FROM despesas_agregadas ORDER BY total_despesas DESC LIMIT 5")
    top_5 = cursor.fetchall()

    # 3. Distribuição por UF
    cursor.execute("SELECT uf, SUM(total_despesas) as total FROM despesas_agregadas WHERE uf IS NOT NULL GROUP BY uf ORDER BY total DESC")
    por_uf = cursor.fetchall()
    
    conn.close()
    return {
        "total_geral": geral['total'],
        "media_lancamento": geral['media'],
        "top_5": top_5,
        "distribuicao_uf": por_uf
    }