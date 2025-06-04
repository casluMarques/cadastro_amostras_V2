import mysql.connector
from dotenv import load_dotenv
import os
from pathlib import Path

# Carrega as variáveis do .env
env_path = Path(__file__).parent / "creds.env"
load_dotenv(dotenv_path=env_path)

# Informações de conexão
db_host = os.getenv("DB_HOST")
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
db_name = os.getenv("DB_NAME")

def create_database_and_table():
    # Conecta sem banco selecionado para criar o banco primeiro (caso não exista)
    conn = mysql.connector.connect(
        host=db_host,
        user=db_user,
        password=db_password
    )
    cursor = conn.cursor()

    # Cria o banco de dados se ainda não existir
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
    conn.commit()
    cursor.close()
    conn.close()

    # Agora conecta no banco criado
    conn = mysql.connector.connect(
        host=db_host,
        user=db_user,
        password=db_password,
        database=db_name
    )
    cursor = conn.cursor()

    # Cria a tabela amostras
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS amostras (
        id INT AUTO_INCREMENT PRIMARY KEY,
        nome VARCHAR(255) NOT NULL,
        fabricante VARCHAR(255) NOT NULL,
        processo INT NOT NULL,
        data_entrada DATE,
        tipo VARCHAR(255),
        numero_nf VARCHAR(255),
        data_retirada DATE,
        status VARCHAR(255) DEFAULT 'Em bancada',
        responsavel_cadastro VARCHAR(255) NOT NULL,
        responsavel_alteracao VARCHAR(255)
    )
    """)

    conn.commit()
    cursor.close()
    conn.close()

if __name__ == "__main__":
    create_db = os.getenv("CREATE_DB")
    print(type(create_db))
    if create_db == '1':
        create_database_and_table()