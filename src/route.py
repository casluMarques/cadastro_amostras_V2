
from flask import Flask, render_template, request, send_file, session, url_for, redirect
from authlib.integrations.flask_client import OAuth
import mysql.connector
import qrcode
import io
import base64
import os
from dotenv import load_dotenv
from pathlib import Path
import re
import aux_func
import db_connect



#carregando as credenciais google do arquivo creds.env
env_path = Path(__file__) / "creds.env"
load_dotenv(dotenv_path=env_path)
client_id = os.getenv("GOOGLE_CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")

#rota de upload
UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER")

app = Flask(__name__)

app.secret_key = os.getenv("FLASK_KEY")

print(app.secret_key)

oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=client_id,
    client_secret=client_secret,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)


API_URL = "http://172.16.15.71"



@app.route('/')
def login_page():
    return render_template('login.html')

#processo de login
#Redireciona para a autorização da google
@app.route('/login/google')
def login_google():
    redirect_uri = url_for('authorize_google', _external=True)
    return google.authorize_redirect(redirect_uri)

#retorna os parametros da autenticação e redireciona para o form
@app.route('/auth/google')
def authorize_google():
    token = google.authorize_access_token()
    resp = google.get('https://openidconnect.googleapis.com/v1/userinfo')
    user_info = resp.json()
    session['user'] = user_info
    return redirect('/start')

@app.route('/start')
def start():
    return render_template('redirect.html')

#carrega o form, verificanso se o usuário está autenticado
@app.route('/registro')
def index():
    if 'user' not in session:
        return redirect('/login/google')
    return render_template('start_page.html', user=session['user'])

#carrega os dados do form para o bd, gera o qr code
@app.route('/registrar', methods=['POST'])
def registrar_amostra():
    try:
        nome_amostra = request.form.get('nome da amostra')
        fabricante = request.form.get('fabricante')
        processo = int(request.form.get('processo'))
        data_entrada = request.form.get('data_entrada')
        tipo = request.form.get('tipo')
        nf_opcao = request.form.get('nf_opcao')
        numero_nf = None

        # Verificar caracteres especiais
        for campo_nome, campo_valor in [('Nome da amostra', nome_amostra), ('Fabricante', fabricante), ('Tipo', tipo)]:
            if aux_func.contem_caracteres_invalidos(campo_valor):
                raise Exception(f"O campo '{campo_nome}' contém caracteres inválidos: ', \", %, ; ou #.")

        # Conectar ao banco para verificar duplicidade
        conn = db_connect.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM amostras WHERE processo = %s", (processo,))
        existe = cursor.fetchone()[0]

        if existe > 0:
            # Fecha conexão antes de renderizar
            cursor.close()
            conn.close()
            dados_do_formulario = request.form.to_dict()
            return render_template('duplicado.html', processo=processo, dados=dados_do_formulario)

        # Criação do diretório
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)

        if nf_opcao == 'texto':
            numero_nf = request.form.get('numero_nf')
        elif nf_opcao == 'imagem':
            file = request.files.get('imagem_nf')
            if file and file.filename != '':
                extensao = file.filename.rsplit('.', 1)[-1]
                nome_arquivo = f"{processo}.{extensao}"
                file_path = os.path.join(UPLOAD_FOLDER, nome_arquivo)
                file.save(file_path)
                numero_nf = f"Imagem salva como {nome_arquivo}"
            else:
                raise Exception("Arquivo de imagem da Nota Fiscal não enviado!")

        responsavel_cadastro = session['user'].get('name') or session['user'].get('email') or "Desconhecido"

        cursor.execute("""
            INSERT INTO amostras (nome, fabricante, processo, data_entrada, tipo, numero_nf, responsavel_cadastro)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (nome_amostra, fabricante, processo, data_entrada, tipo, numero_nf, responsavel_cadastro))
        conn.commit()
        amostra_id = cursor.lastrowid
        cursor.close()
        conn.close()

        # Gera QR Code
        qr_url = f'{API_URL}/amostras/{amostra_id}'
        qr_img = qrcode.make(qr_url)
        img_io = io.BytesIO()
        qr_img.save(img_io, 'PNG')
        img_io.seek(0)
        img_base64 = base64.b64encode(img_io.getvalue()).decode('utf-8')

        return render_template('sucesso.html', amostra_id=amostra_id, qr_img=img_base64, amostra_url=qr_url)

    except Exception as e:
        return render_template('erro.html', message=str(e))

        # Gera o QR Code
        qr_url = f'{API_URL}/amostras/{amostra_id}'
        qr_img = qrcode.make(qr_url)
        img_io = io.BytesIO()
        qr_img.save(img_io, 'PNG')
        img_io.seek(0)
        img_base64 = base64.b64encode(img_io.getvalue()).decode('utf-8')

        return render_template('sucesso.html',
                               amostra_id=amostra_id,
                               qr_img=img_base64,
                               amostra_url=qr_url)

    except Exception as e:
        return render_template('erro.html', message=str(e))

#download do qr code
@app.route('/download_qr/<int:amostra_id>')
def download_qr(amostra_id):
    qr_url = f'{API_URL}/amostras/{amostra_id}'
    qr_img = qrcode.make(qr_url)

    img_io = io.BytesIO()
    qr_img.save(img_io, 'PNG')
    img_io.seek(0)

    return send_file(img_io, mimetype='image/png', as_attachment=True,
                     download_name=f'amostra_{amostra_id}_qrcode.png')

#visualização dos dados qr code / dados de amostras
@app.route('/amostras/<int:amostra_id>')
def amostrar_amostra(amostra_id):
    conn = db_connect.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, nome, fabricante, processo, data_entrada, tipo, numero_nf,
               data_retirada, status, responsavel_cadastro, responsavel_alteracao
        FROM amostras WHERE id = %s
    """, (amostra_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        amostra = {
            "id": row[0],
            "nome": row[1],
            "fabricante": row[2],
            "processo": row[3],
            "data_entrada": row[4],
            "tipo": row[5],
            "numero_nf": row[6],
            "data_retirada": row[7],
            "status": row[8],
            "responsavel_cadastro": row[9],
            "responsavel_alteracao": row[10]
        }

        # Gera o QR Code
        qr_url = f'{API_URL}/amostras/{amostra_id}'
        qr_img = qrcode.make(qr_url)
        img_io = io.BytesIO()
        qr_img.save(img_io, 'PNG')
        img_io.seek(0)
        img_base64 = base64.b64encode(img_io.getvalue()).decode('utf-8')

        # Caminho da imagem da nota fiscal
        imagem_nf_path = f'/home/notas_fiscais/{amostra["processo"]}'
        extensoes_possiveis = ['png', 'jpg', 'jpeg', 'pdf']  # Adapte se necessário
        imagem_nf_existente = None

        for ext in extensoes_possiveis:
            caminho_completo = f'{imagem_nf_path}.{ext}'
            if os.path.exists(caminho_completo):
                imagem_nf_existente = caminho_completo
                break

        if imagem_nf_existente:
            imagem_nf_relativa = imagem_nf_existente.replace('/home', '')  # para servir via Flask
        else:
            imagem_nf_relativa = None

        return render_template('visu_amostra.html',
                               amostra=amostra,
                               qr_img=img_base64,
                               imagem_nf=imagem_nf_relativa)
    else:
        return render_template('erro.html', message="Amostra não encontrada.")

#rota apenas para enviar as fotos para o flask, permitindo que sejam exibidas
@app.route('/nota_fiscal/<int:processo>')
def servir_nota_fiscal(processo):
    extensoes_possiveis = ['jpg', 'jpeg', 'png', 'pdf']
    for ext in extensoes_possiveis:
        caminho = f'C:/home/notas_fiscais/{processo}.{ext}'
        if os.path.exists(caminho):
            return send_file(caminho)
    return 'Nota Fiscal não encontrada.'


#rota para form de pesquisa
@app.route('/pesquisa')
def pesquisa():

    #verifica se o filtro foi selecionado
    status_filtro = request.args.get('status')

    conn = db_connect.get_db_connection()
    cursor = conn.cursor(dictionary=True)
    #se for selecionado, aplica o filtro
    if status_filtro and status_filtro in ['Em bancada', 'Sala Cofre', 'Devolvido']:
        cursor.execute("SELECT * FROM amostras WHERE status = %s", (status_filtro,))
    #Do contrário, apenas mostra todas as amostras
    else:
        cursor.execute("SELECT * FROM amostras")

    equipamentos = cursor.fetchall()
    conn.close()

    return render_template('pesquisa.html', equipamentos=equipamentos, status_filtro=status_filtro) #passando para o html os dados necessários

#rota que retorna os dados pesquisados
@app.route('/resultado_pesquisa', methods=['GET'])
def resultado_pesquisa():
    #recuperando o termo para pesquisa
    pesquisa = request.args.get("termo")
    #pesquisando no BD
    conn = db_connect.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM amostras
        WHERE
            CAST(id AS CHAR) LIKE %s OR
            nome LIKE %s OR
            fabricante LIKE %s OR
            numero_nf LIKE %s
    """, (f'%{pesquisa}%', f'%{pesquisa}%', f'%{pesquisa}%', f'%{pesquisa}%'))
    resultados = cursor.fetchall()
    conn.close()
    return render_template('resultado_pesquisa.html', resultados = resultados, termo = pesquisa)

#rota para alteração de status
@app.route('/amostras/<int:amostra_id>/alterar_status', methods=['GET', 'POST'])
def alterar_status(amostra_id):
    if 'user' not in session:
        return redirect('/login/google')

    conn = db_connect.get_db_connection()
    cursor = conn.cursor()

    #depois de salvar, altera o banco
    if request.method == 'POST':
        novo_status = request.form.get("status")
        data_retirada = request.form.get("data_retirada") if novo_status == "Devolvido" else None
        responsavel = session['user'].get('name') or session['user'].get('email')

        cursor.execute("""
            UPDATE amostras
            SET status = %s, data_retirada = %s, responsavel_alteracao = %s
            WHERE id = %s
        """, (novo_status, data_retirada, responsavel, amostra_id))
        conn.commit()
        conn.close()
        return redirect(f'/amostras/{amostra_id}')

    #pega as informações do form
    cursor.execute("SELECT id, nome, status FROM amostras WHERE id = %s", (amostra_id,))
    amostra = cursor.fetchone()
    conn.close()

    if not amostra:
        return render_template('erro.html', message="Amostra não encontrada.")

    #template a ser carrgeado para modificação do status
    return render_template('alterar_status.html', amostra={
        "id": amostra[0],
        "nome": amostra[1],
        "status": amostra[2]
    })
