
# 📦 Sistema de Cadastro de Amostras - LASPI

Este projeto é uma aplicação web para cadastro, consulta e visualização de amostras no laboratório LASPI, com autenticação via Google OAuth 2.0.

---

## ✅ Requisitos

- Python 3.8 ou superior
- `pip` instalado
- Variáveis de ambiente configuradas

---

## ⚙️ Configuração do Ambiente

1. Clone o repositório:
   ```bash
   git clone https://github.com/seu-usuario/seu-repositorio.git
   cd seu-repositorio
   ```

2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

3. Crie um arquivo `.env` ou `creds.env` com o seguinte conteúdo:
   ```env
   GOOGLE_CLIENT_ID=seu-client-id-aqui
   CLIENT_SECRET=seu-client-secret-aqui
   ```

4. Crie o banco de dados:
   ```bash
   python db.py
   ```

---
## ✨ Funcionalidades

- Login com Google
- Cadastro de amostras com QR Code
- Geração de link único para cada amostra
- Visualização de dados via QR Code
- Pesquisa por ID, nome, fabricante ou nota fiscal

---

## 👨‍🔬 Desenvolvido por

Lucas Marques
