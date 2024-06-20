from flask import render_template, request, flash, redirect, url_for, send_from_directory, jsonify, abort
from werkzeug.security import check_password_hash
from flask_login import login_user, logout_user, current_user
from models import *
from sqlalchemy import not_
from datetime import datetime
from zoneinfo import ZoneInfo


def home():
    if current_user.is_authenticated:
        return render_template("home.html")
    else:
        return redirect(url_for('front_end.login'))


def registros_empresa():
    motoristas = [row.to_dict() for row in Motoristas.query]
    placas = [row.to_dict() for row in Placas.query]
    return render_template("registros_empresa.html", placas=placas, motoristas=motoristas)


def registros_visitantes():
    visitantes = [row.to_dict() for row in Visitantes.query.all()]
    return render_template("registros_visitantes.html", visitantes=visitantes)


def pesquisar():
    return render_template('pesquisar/pesquisar.html')


def pesquisar_tables(table):
    return render_template(f'pesquisar/pesquisar_{table}.html')


def editar():
    return render_template('editar/editar.html')


def editar_tables(table):
    return render_template(f'editar/editar_{table}.html')


def api_data(data):
    if data in ['placas', 'motoristas', 'visitantes']:
        return {
            'data': [row.to_dict() for row in db.session.query(table_object(table_name=data))],
        }

    query = db.session.query(table_object(table_name=data))

    if data == 'last_km':
        try:
            placa = request.args.get('placa[value]')
            exit_checked = request.args.get('exit[value]') == 'true'
            km_needed = Placas.query.filter_by(placa=placa).one_or_none()
            if km_needed.km_necessario == 1:
                query = RegistrosEmpresa.query.filter_by(placa=placa).order_by(
                    RegistrosEmpresa.id.desc()).first()
                if query and exit_checked:
                    if query.categoria == "entrada":
                        last_km = query.quilometragem
                        return jsonify({'message': 'success', 'last_km': f'{last_km}'})
                    else:
                        abort(404, description='Nenhum dado encontrado!')
                else:
                    abort(404, description='Nenhum dado encontrado!')
            else:
                return jsonify({'message': 'km no needed'})
        except Exception as e:
            abort(500, description=str(e))

    # search filter
    search = request.args.get('search[value]')

    if search:
        if data == "registros_empresa":
            query = query.filter(db.or_(
                RegistrosEmpresa.data_reg.like(f'%{search}%'),
                RegistrosEmpresa.motorista.like(f'%{search}%'),
                RegistrosEmpresa.placa.like(f'%{search}%'),
                RegistrosEmpresa.destino.like(f'%{search}%'),
                RegistrosEmpresa.observacoes.like(f'%{search}%')
            ))

        elif data == "registros_visitantes":
            query = query.filter(db.or_(
                RegistrosVisitantes.nome.like(f'%{search}%'),
                RegistrosVisitantes.documento.like(f'%{search}%'),
                RegistrosVisitantes.placa.like(f'%{search}%'),
                RegistrosVisitantes.empresa.like(f'%{search}%'),
                RegistrosVisitantes.destino.like(f'%{search}%'),
                RegistrosVisitantes.observacoes.like(f'%{search}%')
            ))

    # date range filter
    min_date = request.args.get('minDate')
    max_date = request.args.get('maxDate')
    if min_date and max_date:
        query = query.filter(db.and_(
            db.func.date(table_object(table_name=data).data_reg) >= min_date,
            db.func.date(table_object(table_name=data).data_reg) <= max_date
        ))

    total_filtered = query.count()

    # sorting
    order = []
    i = 0
    while True:
        col_index = request.args.get(f'order[{i}][column]')
        if col_index is None:
            break
        col_name = request.args.get(f'columns[{col_index}][data]')
        if data == "registros_empresa":
            if col_name not in ['data_reg', 'categoria', 'motorista', 'placa', 'destino']:
                col_name = 'name'
            col = getattr(RegistrosEmpresa, col_name)
        elif data == "registros_visitantes":
            if col_name not in ['data_reg', 'categoria', 'nome', 'documento', 'empresa', 'destino']:
                col_name = 'name'
            col = getattr(RegistrosVisitantes, col_name)
        descending = request.args.get(f'order[{i}][dir]') == 'desc'
        if descending:
            col = col.desc()
        order.append(col)
        i += 1
    if order:
        query = query.order_by(*order)

    # pagination
    start = request.args.get('start', type=int)
    length = request.args.get('length', type=int)
    final_query = query.offset(start).limit(length)

    # response
    return {
        'data': [row.to_dict() for row in final_query],
        'recordsFiltered': total_filtered,
        'recordsTotal': query.count(),
        'draw': request.args.get('draw', type=int),
    }


def processar_formulario():
    try:
        enviar_dados = []
        dados_coletados = None
        formulario_id = request.form.get('formulario_id')

        # Collect data based on form ID
        if formulario_id == "registros_empresa":
            dados_coletados = RegistrosEmpresa(
                user=current_user.username,
                data_lanc=datetime.now(ZoneInfo("America/Sao_Paulo")).replace(microsecond=0),
                data_reg=request.form.get("data") + " " + request.form.get("hora"),
                categoria=request.form.get("categoria"),
                motorista=request.form.get("motorista"),
                placa=request.form.get("placa"),
                descricao=request.form.get("descricao") or None,
                quilometragem=request.form.get("quilometragem") or None,
                destino=request.form.get("destino"),
                observacoes=request.form.get("observacoes") or None
            )

        elif formulario_id == "registros_visitantes":
            dados_coletados = RegistrosVisitantes(
                user=current_user.username,
                data_lanc=datetime.now(ZoneInfo("America/Sao_Paulo")).replace(microsecond=0),
                data_reg=request.form.get("data") + " " + request.form.get("hora"),
                categoria=request.form.get("categoria"),
                nome=request.form.get("nome"),
                documento=request.form.get("documento"),
                empresa=request.form.get("empresa") or None,
                placa=request.form.get("placa") or None,
                destino=request.form.get("destino"),
                observacoes=request.form.get("observacoes") or None
            )

            nome_visitante = Visitantes.query.filter_by(nome=dados_coletados.nome).first()

            if nome_visitante is None:
                registrar_visitante = Visitantes(
                    nome=dados_coletados.nome,
                    documento=dados_coletados.documento,
                    empresa=dados_coletados.empresa
                )
                enviar_dados.append(registrar_visitante)

        elif formulario_id == "editFormPlacas":
            dados_coletados = Placas.query.get(request.form.get('id'))
            duplicado = Placas.query.filter_by(placa=request.form.get('placa')).one_or_none()
            if not dados_coletados:
                if not duplicado:
                    dados_coletados = Placas(
                        placa=request.form.get('placa'),
                        veiculo=request.form.get('veiculo'),
                        km_necessario=bool(request.form.get('km-needed'))
                    )
                else:
                    return jsonify({'type': 'info', 'message': 'Placa já cadastrada!'})
            else:
                dados_coletados.placa = request.form.get('placa')
                dados_coletados.veiculo = request.form.get('veiculo')
                dados_coletados.km_necessario = bool(request.form.get('km-needed'))

        elif formulario_id == "editFormMotoristas":
            dados_coletados = Motoristas.query.get(request.form.get('id'))
            duplicado = Motoristas.query.filter_by(motorista=request.form.get('motorista')).one_or_none()
            if not dados_coletados:
                if not duplicado:
                    dados_coletados = Motoristas(
                        motorista=request.form.get('motorista'),
                        cidade=request.form.get('cidade')
                    )
                else:
                    return jsonify({'type': 'info', 'message': 'Motorista já cadastrado!'})
            else:
                dados_coletados.motorista = request.form.get('motorista')
                dados_coletados.cidade = request.form.get('cidade')

        enviar_dados.append(dados_coletados)

        for dado in enviar_dados:
            db.session.add(dado)

        db.session.commit()

        return jsonify({'type': 'success', 'message': 'Dados enviados com sucesso!'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'type': 'error', 'message': str(e)})


def login():
    # Check if the request method is POST for form submission
    if request.method == "POST":
        username = request.form["username"].lower()
        password = request.form["password"]

        # Ensure username and password fields are filled
        if not username or not password:
            flash('Preencha os dados corretamente!', 'info')
            return redirect(url_for('front_end.login'))

        # Check if user exists in the database
        existing_user = User.query.filter_by(username=username).first()
        if not existing_user:
            flash('Usuário não encontrado!', 'info')
            return redirect(url_for('front_end.login'))

        # Validate the provided password
        if not check_password_hash(existing_user.password, password):
            flash('Senha incorreta!', 'info')
            return redirect(url_for('front_end.login'))

        # Log in the user and redirect to the home page
        login_user(existing_user, remember=True)
        return redirect(url_for("front_end.home"))

    # Redirect authenticated users directly to home
    if current_user.is_authenticated:
        return redirect(url_for("front_end.home"))
    else:
        # Show the login form to unauthenticated users
        return render_template("login.html")


def logout():
    logout_user()
    return redirect(url_for('front_end.login'))


def serve_file(filename):
    return send_from_directory('', filename)


def health_check():
    return 'OK', 200
