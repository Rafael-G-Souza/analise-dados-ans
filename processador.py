import zipfile
import pandas as pd
import requests
import io
from pathlib import Path

PASTA_ORIGEM = Path('downloads')
ARQUIVO_SAIDA = Path('data/processed/consolidado_despesas.csv')
ARQUIVO_AGREGADO = Path('data/processed/despesas_agregadas.csv')
CADASTRO_OPERADORAS = "https://dadosabertos.ans.gov.br/FTP/PDA/operadoras_de_plano_de_saude_ativas/Relatorio_cadop.csv"


def ler_csv_flexivel(arquivo_ou_buffer):
    """
    Tenta ler CSV primeiro como UTF-8 (Padrão Moderno).
    Se falhar, tenta Latin1 (Padrão Antigo/Windows).
    """
    try:
        # Tenta UTF-8 primeiro. Se o arquivo for Latin1, isso vai dar erro (o que é bom!)
        return pd.read_csv(arquivo_ou_buffer, sep=';', encoding='utf-8')
    except UnicodeDecodeError:
        # Se deu erro, reinicia a leitura e tenta Latin1
        if hasattr(arquivo_ou_buffer, 'seek'):
            arquivo_ou_buffer.seek(0)
        return pd.read_csv(arquivo_ou_buffer, sep=';', encoding='latin1')
    
def coletar_informacoes():
    lista_busca = []
    for arquivo_zip in PASTA_ORIGEM.glob('*.zip'):
        with zipfile.ZipFile(arquivo_zip, 'r') as zip_ref:
            for f_name in zip_ref.namelist():
                if f_name.endswith('.csv') or f_name.endswith('.txt'):
                    print(f"Processando arquivo: {f_name} do zip: {arquivo_zip.name}")
                    with zip_ref.open(f_name) as f:
                        # Usa a função inteligente de leitura
                        df = ler_csv_flexivel(f)
                    busca = df[df['DESCRICAO'].str.contains('even',case=False, na=False) & df['DESCRICAO'].str.contains('sin', case=False, na=False)]
                    if not busca.empty:
                        busca['ORIGEM_ARQUIVO'] = arquivo_zip.name
                        print(busca)
                        lista_busca.append(busca)
                if f_name.endswith('.xlsx'):
                    print(f"Processando arquivo: {f_name} do zip: {arquivo_zip.name}")
                    df = pd.read_excel(zip_ref.open(f_name))
                    busca = df[df['DESCRICAO'].str.contains('even',case=False, na=False) & df['DESCRICAO'].str.contains('sin', case=False, na=False)]
                    if not busca.empty:
                        busca['ORIGEM_ARQUIVO'] = arquivo_zip.name
                        print(busca)
                        lista_busca.append(busca)

    if lista_busca:
        return pd.concat(lista_busca, ignore_index=True)
    return pd.DataFrame()

def ajustar_informacoes(df):
    print("Ajustando informações coletadas...")
    df['Trimestre'] = df['ORIGEM_ARQUIVO'].str.extract(r'(\d)T')[0] + 'º Trimestre'
    df['Ano'] = df['ORIGEM_ARQUIVO'].str.extract(r'T(\d{4})')[0]
    df['CNPJ'] = "" 
    df['VL_SALDO_INICIAL'] = df['VL_SALDO_INICIAL'].astype(str).str.replace(',', '.').astype(float)
    df['VL_SALDO_FINAL'] = df['VL_SALDO_FINAL'].astype(str).str.replace(',', '.').astype(float)
    df['CalculoDespesas'] = df['VL_SALDO_FINAL'] - df['VL_SALDO_INICIAL']
    df['Status_Valor'] = 'Válido'
    df.loc[df['CalculoDespesas'] == 0, 'Status_Valor'] = 'Zerado'
    df.loc[df['CalculoDespesas'] < 0, 'Status_Valor'] = 'Negativo'
    df['ValorDespesas'] = df['CalculoDespesas'].map('{:.2f}'.format)
    colunas_finais = ['REG_ANS', 'CD_CONTA_CONTABIL','CNPJ','DESCRICAO', 'Trimestre', 'Ano', 'VL_SALDO_INICIAL', 'VL_SALDO_FINAL','ValorDespesas', 'Status_Valor', 'CalculoDespesas']
    if 'DESCRICAO' in df.columns:
        df['DESCRICAO'] = df['DESCRICAO'].astype(str).str.strip().str.upper()
    return df[colunas_finais]

def cruzar_dados_cadastrais(df_main):
    print("Cruzando dados cadastrais...") 
    try:
        r = requests.get(CADASTRO_OPERADORAS)
        r.raise_for_status()

       # --- CORREÇÃO: WRAPPER PARA TRATAR O UTF-8 NA FORÇA ---
        arquivo_buffer = io.BytesIO(r.content)
        
        # Aqui convertemos os bytes para texto FORÇANDO a ignorar erros
        # errors='replace' troca o byte ruim por um quadradinho ou ?, mas não quebra o script
        arquivo_texto = io.TextIOWrapper(arquivo_buffer, encoding='utf-8', errors='replace')
        
        df_referencia = pd.read_csv(
            arquivo_texto, 
            sep=';', 
            dtype=str  # Lê tudo como texto
        )
        # -
        colunas_referencia = {
            'REGISTRO_OPERADORA' : 'REG_ANS',
            'CNPJ': 'CNPJ_REF',
            'Razao_Social': 'RazaoSocial',
            'Modalidade': 'Modalidade',
            'UF': 'UF'
            }
        df_referencia.rename(columns=colunas_referencia, inplace=True)
        cols_texto = ['RazaoSocial', 'Modalidade', 'UF']
        for col in cols_texto:
            if col in df_referencia.columns:
                df_referencia[col] = df_referencia[col].astype(str).str.strip().str.upper()

        for col in ['REG_ANS', 'CNPJ_REF']:
            if col in df_referencia.columns:
                df_referencia[col] = df_referencia[col].astype(str).str.replace(r'\.0$', '',regex=True)

        print("Recuperando CNPJs...")
        mapa_cnpj = df_referencia[['REG_ANS', 'CNPJ_REF']].dropna().drop_duplicates(subset=['REG_ANS'])
        dict_cnpj = pd.Series(mapa_cnpj.CNPJ_REF.values, index=mapa_cnpj.REG_ANS).to_dict()
        df_main['REG_ANS'] = df_main['REG_ANS'].astype(str)
        if 'CNPJ' not in df_main.columns:
            df_main['CNPJ'] = df_main['REG_ANS'].map(dict_cnpj)
        else:
            mask = (df_main['CNPJ'].isna()) | (df_main['CNPJ'] == '')
            df_main.loc[mask,'CNPJ'] = df_main.loc[mask,'REG_ANS'].map(dict_cnpj)

        print("Cruzando tabelas por CNPJ")
        df_main['CNPJ_LIMPO'] = df_main['CNPJ'].astype(str).str.replace(r'\D', '', regex=True)
        df_referencia['CNPJ_LIMPO'] = df_referencia['CNPJ_REF'].astype(str).str.replace(r'\D', '', regex=True)
        df_referencia['RegistroANS'] = df_referencia['REG_ANS']
        cols_join = ['CNPJ_LIMPO', 'RegistroANS', 'Modalidade', 'UF','RazaoSocial']
        cadop_unico = df_referencia[cols_join].drop_duplicates(subset=['CNPJ_LIMPO'])
        df_final = pd.merge(df_main, cadop_unico, on='CNPJ_LIMPO', how='left')
        for col in ['RegistroANS', 'Modalidade', 'UF', 'RazaoSocial']:
            if col in df_final.columns:
                df_final[col] = df_final[col].fillna('Não encontrado')
        
        colunas_finais = ['RegistroANS', 'CNPJ', 'RazaoSocial', 'Modalidade', 'UF','Trimestre', 'Ano', 'ValorDespesas','Status_Valor', 'DESCRICAO','CalculoDespesas']
        cols_existentes = [c for c in colunas_finais if c in df_final.columns]
        print(f"Processo concluído!{len(df_final)} registros processados.")
        return df_final[cols_existentes]
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        print("\n ALERTA: Falha na conexão com a ANS.")
        print("-> Gerando arquivo parcial (sem modalidade/UF)")
        return df_main
    except Exception as e:
        print(f" Erro crítico: {e}")
        return df_main
    
def gerar_relatorio_agregado(df):
    print("\n Gerando relatório de agregação...")
    cols_necessarias = ['RazaoSocial', 'UF', 'CalculoDespesas']
    if not all(col in df.columns for col in cols_necessarias):
        print(" Colunas necessárias para agregação não encontradas.")
        return pd.DataFrame()
    agregado =df.groupby(['RazaoSocial', 'UF'])['CalculoDespesas'].agg(['sum', 'count','mean']).reset_index()
    agregado.columns = ['RazaoSocial','UF', 'Total_Despesas', 'Qtd_Lancamentos', 'Media_Lancamento']
    agregado['Total_Despesas'] = agregado['Total_Despesas'].map('{:.2f}'.format)
    agregado['Media_Lancamento'] = agregado['Media_Lancamento'].map('{:.2f}'.format)
    agregado = agregado.sort_values(by='Qtd_Lancamentos', ascending=False)
    print(f" Agregação concluída! {len(agregado)} linhas geradas.")
    return agregado

def salvar_arquivo(df,caminho):
    try:
        caminho.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(caminho, index=False, sep=';', encoding='utf-8-sig')
        print(f"Arquivo salvo: {caminho}")

    except PermissionError:
        print(f"🛑 ERRO: Feche o arquivo '{caminho.name}' e tente de novo!")

    except Exception as e:
        print(f"❌ Erro ao salvar {caminho.name}: {e}")

if __name__ == "__main__":
    dados_consolidados = coletar_informacoes()
    if not dados_consolidados.empty:
        dados_ajustados = ajustar_informacoes(dados_consolidados)
        dados_completos = cruzar_dados_cadastrais(dados_ajustados)
        dados_agregados= gerar_relatorio_agregado(dados_completos)

        if'CalculoDespesas' in dados_completos.columns:
            dados_completos = dados_completos.drop(columns=['CalculoDespesas'])
        salvar_arquivo(dados_completos, ARQUIVO_SAIDA)
        salvar_arquivo(dados_agregados, ARQUIVO_AGREGADO)
    else:
        print("\n⚠️ Nenhum dado correspondente aos filtros foi encontrado.")



