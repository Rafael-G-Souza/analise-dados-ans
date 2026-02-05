-- Criação do Banco de Dados
CREATE DATABASE IF NOT EXISTS ans_analytics;
USE ans_analytics;

-- Criação da Tabela Operadoras
-- Importante: O charset utf8mb4 garante que acentos funcionem corretamente
CREATE TABLE IF NOT EXISTS operadoras (
    reg_ans INT PRIMARY KEY,
    cnpj VARCHAR(20),
    razao_social VARCHAR(255),
    modalidade VARCHAR(100),
    uf CHAR(2)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;