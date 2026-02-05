import requests
import os
from bs4 import BeautifulSoup
from urllib.parse import urljoin

BASE_URL = "https://dadosabertos.ans.gov.br/FTP/PDA/"
PASTA_DESTINO = "downloads"

def baixar_arquivos():
    os.makedirs(PASTA_DESTINO, exist_ok=True)
    resposta = requests.get(BASE_URL)
    if resposta.status_code != 200:
        print("Erro ao acessar o site de dados abertos da ANS.")
        return 
    soup = BeautifulSoup(resposta.content, 'html.parser')
    for link in soup.find_all('a'):
        href = link.get('href')
        if href and href.endswith('contabeis/'):
            url_contabeis = urljoin(BASE_URL, href)
            resposta_contabeis = requests.get(url_contabeis)
            if resposta_contabeis.status_code != 200:
                print("Erro ao acessar a seção de dados contábeis.")
                return
            abrir_contabeis = BeautifulSoup(resposta_contabeis.content, 'html.parser')
            for sublink in abrir_contabeis.find_all('a'):
                subhref = sublink.get('href')
                if subhref and subhref.endswith('2025/'):
                    url_2025 = urljoin(url_contabeis, subhref)
                    resposta_2025 = requests.get(url_2025)
                    if resposta_2025.status_code != 200:
                        print("Erro ao acessar a seção de dados de 2025.")
                        return
                    abrir_2025 = BeautifulSoup(resposta_2025.content, 'html.parser')
                    for arquivo_link in abrir_2025.find_all('a'):
                        arquivo_href = arquivo_link.get('href')
                        if arquivo_href and arquivo_href.endswith('.zip'):
                            url_arquivo = urljoin(url_2025, arquivo_href)
                            nome_arquivo = os.path.join(PASTA_DESTINO, arquivo_href.split('/')[-1])
                            print(f"Baixando {nome_arquivo}...")
                            resposta_arquivo = requests.get(url_arquivo)
                            if resposta_arquivo.status_code == 200:
                                with open(nome_arquivo, 'wb') as f:
                                    for chunk in resposta_arquivo.iter_content(chunk_size=8192):
                                        if chunk:
                                            f.write(chunk)
                            else:
                                print(f"Erro ao baixar o arquivo {arquivo_href}.")

if __name__ == "__main__":
    baixar_arquivos()

