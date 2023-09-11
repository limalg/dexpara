from flask import Flask, render_template, request, redirect, url_for,Response
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc
from sqlalchemy import not_
import sqlite3
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask import jsonify
from datetime import datetime
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from collections import Counter
import os
import openpyxl


app = Flask(__name__)



app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'sua_chave_secreta_aqui'  # Defina uma chave secreta para segurança

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    tribo = db.Column(db.String(100))
    email = db.Column(db.String(100))
    is_admin = db.Column(db.Boolean, default=False)
    ultimo_acesso = db.Column(db.String(100))

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    data_atualizacao = db.Column(db.DateTime)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    marcacao = db.Column(db.String(255))
    categoria_evento = db.Column(db.String(255))
    acao_evento = db.Column(db.String(255))
    rotulo_evento = db.Column(db.String(255))
    caminho_pagina = db.Column(db.String(255))
    funcionalidade = db.Column(db.String(255))
    canal = db.Column(db.String(255))
    subcanal = db.Column(db.String(255))
    produto = db.Column(db.String(255))
    categoria = db.Column(db.String(255))
    impacta_call_center = db.Column(db.String(255))
    tribo = db.Column(db.String(255))
    tag = db.Column(db.String(255))
    email = db.Column(db.String(255))
    led_de_vendas = db.Column(db.String(255))
    aprovado = db.Column(db.Boolean, default=False)

class Canais(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tribo = db.Column(db.String(255))
    canal = db.Column(db.String(255))
    subcanal = db.Column(db.String(255))
    produto = db.Column(db.String(255))
    categoria = db.Column(db.String(255))
    
#Pagina Login -----------------------------------------------------------

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            # Atualize a data de último acesso
            user.ultimo_acesso = datetime.utcnow()
            db.session.commit()
            login_user(user)
            return redirect(url_for("home"))
        else:
            error = "Usuário ou senha incorretos. Tente novamente."

    return render_template("login.html", error=error)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

#Pagina Home -----------------------------------------------------------



@app.route("/")
@login_required
def home():
    if current_user.is_authenticated and current_user.is_admin:
        todo_list = Todo.query.order_by(desc(Todo.data_criacao)).limit(10).all()
        info_canais = Canais.query.all()
    else:
        todo_list = Todo.query.order_by(desc(Todo.data_criacao)).limit(10).all() 
        info_canais = Canais.query.filter_by(tribo=current_user.tribo).all()
    return render_template("base.html", todo_list=todo_list, info_canais=info_canais)


@app.route("/add", methods=[ "POST"])
@login_required
def add():
    categoria_evento = request.form.get("categoria_evento")
    acao_evento = request.form.get("acao_evento")
    rotulo_evento = request.form.get("rotulo_evento")
    caminho_pagina = request.form.get("caminho_pagina")
    funcionalidade = request.form.get("funcionalidade")
    canal = request.form.get("canal")
    subcanal = request.form.get("subcanal")
    produto = request.form.get("produto")
    categoria = request.form.get("categoria")
    impacta_call_center = request.form.get("impacta_call_center")
    tag = request.form.get("tag")
    led_de_vendas = request.form.get("led_de_vendas")

    # Concatene e converta para maiúsculas
    marcacao = f"{categoria_evento}{acao_evento}{rotulo_evento}{caminho_pagina}".upper()
    # Formate a funcionalidade
    funcionalidade = funcionalidade.title().replace("-", "").replace("_", "").replace("'", "").replace(".", "")

    # Crie um novo objeto Todo com os dados do formulário
    new_todo = Todo(user_id=current_user.id, data_criacao=datetime.utcnow(), marcacao=marcacao,
                    categoria_evento=categoria_evento, acao_evento=acao_evento, rotulo_evento=rotulo_evento,
                    caminho_pagina=caminho_pagina, funcionalidade=funcionalidade, canal=canal, subcanal=subcanal,
                    produto=produto, categoria=categoria, impacta_call_center=impacta_call_center,
                    tribo=current_user.tribo, tag=tag, led_de_vendas=led_de_vendas,email=current_user.email)

    db.session.add(new_todo)
    db.session.commit()
    enviar_email('criada', subcanal,funcionalidade,marcacao)
    return redirect(url_for("home"))

@app.route("/edit_base/<int:todo_id>", methods=["GET", "POST"])
def edit_base(todo_id):
    # Recupere o usuário a ser editado com base no ID fornecido
    if current_user.is_authenticated and current_user.is_admin:
        info_canais = Canais.query.all()
    else:
        info_canais = Canais.query.filter_by(tribo=current_user.tribo).all()
    base_to_edit = Todo.query.get(todo_id)

    if request.method == "POST":
        categoria_evento = request.form.get("categoria_evento")
        acao_evento = request.form.get("acao_evento")
        rotulo_evento = request.form.get("rotulo_evento")
        caminho_pagina = request.form.get("caminho_pagina")
        # Atualize os campos do usuário com base nos dados do formulário enviado
        base_to_edit.categoria_evento = request.form.get("categoria_evento")
        base_to_edit.acao_evento = request.form.get("acao_evento")
        base_to_edit.rotulo_evento = request.form.get("rotulo_evento")
        base_to_edit.caminho_pagina = request.form.get("caminho_pagina")
        base_to_edit.funcionalidade = request.form.get("funcionalidade")
        base_to_edit.canal = request.form.get("canal")
        base_to_edit.subcanal = request.form.get("subcanal")
        base_to_edit.produto = request.form.get("produto")
        base_to_edit.categoria = request.form.get("categoria")
        base_to_edit.impacta_call_center = request.form.get("impacta_call_center")
        base_to_edit.tag = request.form.get("tag")
        base_to_edit.led_de_vendas = request.form.get("led_de_vendas")
        base_to_edit.funcionalidade = request.form.get("funcionalidade")
        base_to_edit.data_atualizacao = datetime.utcnow()

        marcacao = f"{categoria_evento}{acao_evento}{rotulo_evento}{caminho_pagina}".upper()
        base_to_edit.marcacao = marcacao

        # Commit as alterações no banco de dados
        db.session.commit()
        enviar_email('editada', base_to_edit.subcanal,base_to_edit.funcionalidade,marcacao)
        # Redirecione de volta para a página de configurações após a edição do usuário
        return redirect(url_for("funcionalidades"))

    # Renderize o formulário de edição do usuário
    return render_template("edit_base.html", base_to_edit=base_to_edit,info_canais=info_canais)

@app.route("/delete/<int:todo_id>")
def delete(todo_id):
    todo = Todo.query.get(todo_id)
    db.session.delete(todo)
    db.session.commit()
    return redirect(url_for("home"))

@app.route('/alterar_aprovacao/<int:todo_id>')
@login_required
def alterar_aprovacao(todo_id):
    # Recupere o registro da tabela Todo pelo ID
    todo = Todo.query.get(todo_id)
    todo.aprovado = not todo.aprovado
    db.session.commit()
    return redirect(url_for('funcionalidades')) 

#Pagina Configuracao -----------------------------------------------------------

@app.route("/configuracao")
@login_required
def configuracao():
    if current_user.is_admin:
        # Consulte os usuários no banco de dados e passe para o template
        users = User.query.all()
        return render_template("configuracao.html", users=users)
    else:
        # Redirecione para a página inicial se o usuário não for um administrador
        return redirect(url_for("home"))

# Defina as rotas para adicionar, editar e excluir usuários
@app.route("/add_user", methods=["POST"])
def add_user():
    # Recupere os dados do formulário enviado
    username = request.form.get("username")
    password = request.form.get("password")
    tribo = request.form.get("tribo")
    email = request.form.get("email")
    is_admin = "is_admin" in request.form

    # Verifique se o nome de usuário já existe no banco de dados
    existing_user = User.query.filter_by(username=username).first()

    if existing_user:
        # Se o nome de usuário já existe, exiba uma mensagem de erro ou tome outra ação apropriada
        error = "Nome de usuário já existe. Escolha outro nome de usuário."
        return render_template("configuracao.html", error=error)


    # Crie um novo usuário com base nos dados do formulário
    new_user = User(username=username, password=password, tribo=tribo,email=email, is_admin=is_admin)

    # Adicione o novo usuário ao banco de dados
    db.session.add(new_user)
    db.session.commit()

    # Redirecione de volta para a página de configurações após a adição do usuário
    return redirect(url_for("configuracao"))

@app.route("/edit_user/<int:user_id>", methods=["GET", "POST"])
def edit_user(user_id):
    # Recupere o usuário a ser editado com base no ID fornecido
    user_to_edit = User.query.get(user_id)

    if request.method == "POST":
        # Atualize os campos do usuário com base nos dados do formulário enviado
        user_to_edit.username = request.form.get("username")
        user_to_edit.password = request.form.get("password")
        user_to_edit.tribo = request.form.get("tribo")
        user_to_edit.email = request.form.get("email")
        user_to_edit.is_admin = "is_admin" in request.form

        # Commit as alterações no banco de dados
        db.session.commit()

        # Redirecione de volta para a página de configurações após a edição do usuário
        return redirect(url_for("configuracao"))

    # Renderize o formulário de edição do usuário
    return render_template("edit_user.html", user=user_to_edit)

@app.route("/delete_user/<int:user_id>")
def delete_user(user_id):
    # Recupere o usuário a ser excluído com base no ID fornecido
    user_to_delete = User.query.get(user_id)

    # Remova o usuário do banco de dados
    db.session.delete(user_to_delete)
    db.session.commit()

    # Redirecione de volta para a página de configurações após a exclusão do usuário
    return redirect(url_for("configuracao"))

#Pagina cadastro_canais -----------------------------------------------------------

@app.route("/cadastro_canais")
@login_required
def cadastro_canais():
    if current_user.is_admin:
        # Consulte os usuários no banco de dados e passe para o template
        canais = Canais.query.all()
        return render_template("cadastro_canais.html", canais=canais)
    else:
        # Redirecione para a página inicial se o usuário não for um administrador
        return redirect(url_for("home"))

# Adicionar canal
@app.route("/add_canal", methods=["POST"])
@login_required
def add_canal():
    if current_user.is_admin:
        tribo = request.form.get("tribo")
        canal = request.form.get("canal")
        subcanal = request.form.get("subcanal")
        produto = request.form.get("produto")
        categoria = request.form.get("categoria")

        # Crie um novo canal com base nos dados do formulário
        novo_canal = Canais(tribo=tribo, canal=canal, subcanal=subcanal, produto=produto, categoria=categoria)
        print(novo_canal)
        # Adicione o novo canal ao banco de dados
        db.session.add(novo_canal)
        db.session.commit()

    # Redirecione de volta para a página de cadastro de canais
    return redirect(url_for("cadastro_canais"))

# Editar canal
@app.route("/edit_canal/<int:canal_id>", methods=["GET", "POST"])
@login_required
def edit_canal(canal_id):
    if current_user.is_admin:
        canal_a_editar = Canais.query.get(canal_id)

        if request.method == "POST":
            canal_a_editar.tribo = request.form.get("tribo")
            canal_a_editar.canal = request.form.get("canal")
            canal_a_editar.subcanal = request.form.get("subcanal")
            canal_a_editar.produto = request.form.get("produto")
            canal_a_editar.categoria = request.form.get("categoria")

            db.session.commit()

            # Redirecione de volta para a página de cadastro de canais após a edição
            return redirect(url_for("cadastro_canais"))

        return render_template("edit_canal.html", canal=canal_a_editar)

# Excluir canal
@app.route("/delete_canal/<int:canal_id>")
@login_required
def delete_canal(canal_id):
    if current_user.is_admin:
        canal_a_excluir = Canais.query.get(canal_id)

        db.session.delete(canal_a_excluir)
        db.session.commit()

    # Redirecione de volta para a página de cadastro de canais após a exclusão
    return redirect(url_for("cadastro_canais"))

#Pagina Analise Funcionalidades Aprovação --------------------------------------------------

@app.route("/funcionalidades")
@login_required
def funcionalidades():
    if current_user.is_authenticated and current_user.is_admin:
        todo_list = Todo.query.filter(not_(Todo.aprovado == True)).all()
    else:
        todo_list = Todo.query.filter_by(tribo=current_user.tribo).filter(not_(Todo.aprovado == True)).all()
    return render_template("funcionalidades.html", todo_list=todo_list)

#Pagina Graficos Funcionalidades -----------------------------------------------------------

@app.route("/graficos_funcionalidades")
@login_required
def graficos_funcionalidades():
    todo_list = Todo.query.all()
    funcionalidades_tribo = Counter([todo.tribo for todo in todo_list])
    funcionalidades_canal = Counter([todo.canal for todo in todo_list])
    return render_template("graficos_funcionalidades.html", todo_list=todo_list,funcionalidades_tribo=funcionalidades_tribo,
                           funcionalidades_canal=funcionalidades_canal)

# Funções complementares -----------------------------------------------------------
# Função de filtro para formatar data como "AAAA-MM-DD"
def formatar_data(data):
    if data is not None:
        return data.strftime("%Y-%m-%d")
    return ""

app.jinja_env.filters['formatar_data'] = formatar_data


@app.route('/exportar_csv')
def exportar_csv():
    # Recupere todos os registros da tabela Todo
    todos = Todo.query.all()  # Substitua pela forma como você acessa os dados reais

    # Crie um DataFrame pandas com os dados
    df = pd.DataFrame([t.__dict__ for t in todos])

    # Remova a coluna 'id', se você não quiser incluí-la no CSV
    df = df.drop(columns=['id','_sa_instance_state','user_id'])


    # Crie uma resposta CSV para o navegador
    resposta_csv = df.to_csv(index=False, encoding='utf-8')
    
    return Response(
        resposta_csv,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=exportar_funcionalidades.csv"}
    )

@app.route("/importar_excel", methods=["GET", "POST"])
@login_required
def importar_excel():
    error = None
    if request.method == "POST":
            # Verifique se o formulário contém um arquivo
            if "file" not in request.files:
                return render_template("funcionalidades.html", error= "Nenhum arquivo enviado")
            file = request.files["file"]
            # Verifique se o arquivo tem um nome e é um arquivo Excel
            if file.filename == "" or not file.filename.endswith(".xlsx"):
                return render_template("funcionalidades.html", error= "Arquivo inválido. Envie um arquivo Excel (.xlsx).") 
            
            try:
                db_filename = 'instance/db.sqlite' 
                conn = sqlite3.connect(db_filename)
                cursor = conn.cursor()
                
                # Criar um DataFrame a partir das linhas do arquivo xlsx
                workbook = openpyxl.load_workbook(file)
                sheet = workbook.active
                data = []
                for row in sheet.iter_rows(values_only=True):
                    data.append(row)
                df = pd.DataFrame(data[1:], columns=[col[0] for col in data[0]])

                for _, row in df.iterrows():
                    data_atualizacao = datetime.utcnow()
                    data_criacao = datetime.utcnow()
                    marcacao = f"{str(row['Categoria Evento'])}{str(row['Ação Evento'])}{str(row['Rotulo Evento'])}{str(row['Caminho Pagina'])}".upper()
                    categoria_evento = str(row['Categoria Evento'])
                    acao_evento = str(row['Ação Evento'])
                    rotulo_evento = str(row['Rotulo Evento'])
                    caminho_pagina = str(row['Caminho Pagina'])
                    funcionalidade = str(row['Funcionalidade'])
                    canal = str(row['Canal'])
                    subcanal = str(row['Subcanal'])
                    produto = str(row['Produto'])
                    categoria = str(row['Categoria'])
                    impacta_call_center = str(row['Impacta Call Center'])
                    tribo = str(row['Tribo'])
                    tag = str(row['Tag'])
                    email = str(row['e-mail'])
                    led_de_vendas = str(row['Led de Vendas'])
                    aprovado = True  # Você pode ajustar esse valor conforme necessário
                    sql = '''
                    INSERT INTO todo (data_atualizacao, data_criacao, marcacao, categoria_evento, acao_evento, rotulo_evento, caminho_pagina, funcionalidade, canal, subcanal, produto, categoria, impacta_call_center, tribo, tag, email, led_de_vendas, aprovado)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    '''
                    # Execute o comando SQL com os dados fornecidos
                    cursor.execute(sql, (
                        data_atualizacao, data_criacao, marcacao, categoria_evento, acao_evento, rotulo_evento, caminho_pagina,
                        funcionalidade, canal, subcanal, produto, categoria, impacta_call_center, tribo, tag, email, led_de_vendas,
                        aprovado     
                    ))
                conn.commit()  
                return render_template("funcionalidades.html", error= "Importação concluída com sucesso!")
   
            except sqlite3.Error as e:
                # Em caso de erro, faça rollback das alterações
                conn.rollback()
                return render_template("funcionalidades.html", error= ("Ocorreu um erro:", e))

            finally:
                conn.close()    

# Rota para rodar comandos SQL
@app.route("/rodar_sql", methods=['GET', 'POST'])
@login_required
def rodar_sql():
    error = None
    if request.method == 'POST':
        sql_command = request.form.get('sql_command')  # Obtenha o comando SQL do formulário

        try:
            db_filename = 'instance/db.sqlite' 
            conn = sqlite3.connect(db_filename)
            cursor = conn.cursor()
            cursor.execute(sql_command)
            conn.commit() 
            return render_template("funcionalidades.html", error= "SQL Executado com sucesso!")

        except Exception as e:
            # Em caso de erro, você pode lidar com ele como desejar
            return render_template("funcionalidades.html", error= ("Ocorreu um erro:", e))

        finally:
            conn.close()


def enviar_email(acao, subcanal,funcionalidade,regra):
    username = 'leandro.lima.terceiros@gmail.com'
    password = 'pwaqitmyowezpbux'
    mail_from = f"no-roply <{username}>"
    mail_to = "leandro.lima.terceiros@claro.com.br"
    mail_subject = f'App:DeXpara - Funcionalidade {acao}'
    mail_body = f'Funcionalidade: {funcionalidade}\nSubcanal: {subcanal}\nRegra: {regra}'

    mimemsg = MIMEMultipart()
    mimemsg['From']=mail_from
    mimemsg['To']=mail_to
    mimemsg['Subject']=mail_subject
    mimemsg.attach(MIMEText(mail_body, 'plain'))
    try:  
        connection = smtplib.SMTP(host='smtp.gmail.com', port=587)
        connection.starttls()
        connection.login(username,password)
        connection.send_message(mimemsg)
    except smtplib.SMTPException as e:
        print("Erro ao enviar e-mail:", str(e)) 
    finally: 
        connection.quit()

if __name__ == "__main__":
    with app.app_context():
        # Cria o primeiro usuário admin
        db.create_all()
        #admin_user = User(username='lima', password='123',tribo='', is_admin=True)
        #db.session.add(admin_user)
        #db.session.commit()
        
    app.run(host="0.0.0.0")
