from flask import request, jsonify
from flask_login import current_user
from models import *
from datetime import datetime
from zoneinfo import ZoneInfo


data_to_send = []
collected_data = None


def send_data(data_to_send, collected_data, message):
    try:
        if collected_data:
            collected_data = db.session.merge(collected_data)
            data_to_send.append(collected_data)

        if data_to_send:
            for data in data_to_send:
                db.session.merge(data)

        db.session.commit()
        return jsonify({'type': 'success', 'message': message})

    except Exception as e:
        db.session.rollback()
        return jsonify({'type': 'error', 'message': 'db error:' + str(e)})


def edit_form(form_id):
    try:
        message = 'Dados alterados com sucesso!'
        if form_id == "editFormPlacas":
            collected_data = db.session.merge(Placas.query.get(request.form.get('id')))
            duplicado = Placas.query.filter_by(placa=request.form.get('placa')).all()
            if not collected_data:
                if not duplicado:
                    collected_data = Placas(
                        placa=request.form.get('placa'),
                        veiculo=request.form.get('veiculo'),
                        km_necessario=bool(request.form.get('km-needed'))
                    )
                else:
                    return jsonify({'type': 'info', 'message': 'Placa já cadastrada!'})
            else:
                if len(duplicado) == 1 and duplicado[0].id == collected_data.id or len(duplicado) == 0:
                    collected_data.placa = request.form.get('placa')
                    collected_data.veiculo = request.form.get('veiculo')
                    collected_data.km_necessario = bool(request.form.get('km-needed'))
                else:
                    return jsonify({'type': 'info', 'message': 'Placa já cadastrada!'})

        elif form_id == "editFormMotoristas":
            collected_data = db.session.merge(Motoristas.query.get(request.form.get('id')))
            duplicado = Motoristas.query.filter_by(motorista=request.form.get('motorista')).all()
            if not collected_data:
                if not duplicado:
                    collected_data = Motoristas(
                        motorista=request.form.get('motorista'),
                        cidade=request.form.get('cidade')
                    )
                else:
                    return jsonify({'type': 'info', 'message': 'Motorista já cadastrado!'})
            else:
                if len(duplicado) == 1 and duplicado[0].id == collected_data.id or len(duplicado) == 0:
                    collected_data.motorista = request.form.get('motorista')
                    collected_data.cidade = request.form.get('cidade')
                else:
                    return jsonify({'type': 'info', 'message': 'Motorista já cadastrado!'})

        elif form_id == "editFormVisitantes":
            collected_data = db.session.merge(Visitantes.query.get(request.form.get('id')))
            duplicado = Visitantes.query.filter_by(nome=request.form.get('nome')).all()
            if not collected_data:
                if not duplicado:
                    collected_data = Visitantes(
                        nome=request.form.get('nome'),
                        documento=request.form.get('documento'),
                        empresa=request.form.get('empresa')
                    )
                else:
                    return jsonify({'type': 'info', 'message': 'Visitante já cadastrado!'})
            else:
                if len(duplicado) == 1 and duplicado[0].id == collected_data.id or len(duplicado) == 0:
                    collected_data.nome = request.form.get('nome')
                    collected_data.documento = request.form.get('documento')
                    collected_data.empresa = request.form.get('empresa')
                else:
                    return jsonify({'type': 'info', 'message': 'Visitante já cadastrado!'})

        elif form_id.startswith("editFormRegistros"):
            if form_id == "editFormRegistros_empresa":
                collected_data = db.session.merge(RegistrosEmpresa.query.get(request.form.get('id')))
                fields = [
                    ('categoria', 'categoria'),
                    ('data_reg', lambda: request.form.get("data") + " " + request.form.get("hora") + ":00"),
                    ('motorista', 'motorista'),
                    ('placa', 'placa'),
                    ('quilometragem', 'km'),
                    ('destino', 'destino'),
                    ('observacoes', 'obs')
                ]
            if form_id == "editFormRegistros_visitantes":
                collected_data = db.session.merge(RegistrosVisitantes.query.get(request.form.get('id')))
                fields = [
                    ('categoria', 'categoria'),
                    ('data_reg', lambda: request.form.get("data") + ' ' + request.form.get("hora") + ":00"),
                    ('nome', 'nome'),
                    ('documento', 'documento'),
                    ('empresa', 'empresa'),
                    ('placa', 'placa'),
                    ('destino', 'destino'),
                    ('observacoes', 'obs')
                ]

            col_alteradas = f"{form_id.replace('editForm', '').lower()}: "
            val_antigo = ''

            for attr, form_field in fields:
                old_value = getattr(collected_data, attr) if attr != 'data_reg' else getattr(collected_data, attr).strftime('%Y-%m-%d %H:%M:%S')
                new_value = form_field() if callable(form_field) else request.form.get(form_field) or None
                if str(old_value) != str(new_value):
                    col_alteradas += f'{attr}, '
                    val_antigo += f'{old_value}, '
                    setattr(collected_data, attr, new_value)

            if col_alteradas:
                history = PortariaHistory(
                    id_reg=collected_data.id,
                    user=current_user.username,
                    colunas_alteradas=col_alteradas,
                    valores_antigos=val_antigo
                )
                data_to_send.append(history)
            else:
                return jsonify({'type': 'info', 'message': 'Nenhum dado alterado!'})

        return send_data(data_to_send, collected_data, message)

    except Exception as e:
        return jsonify({'type': 'error', 'message': 'function error:' + str(e)})


def delete_form(form_id):
    try:
        message = 'Dados excluídos com sucesso!'
        if form_id.startswith("deleteForm"):
            table_id = form_id.replace("deleteForm", '').lower()
            data_to_delete = db.session.query(table_object(table_name=table_id)).get(request.form.get('id'))

            col_alteradas = f'{table_id}: '
            val_antigo = ''

            for column in data_to_delete.__table__.columns:
                value = getattr(data_to_delete, column.name)
                col_alteradas += f'{column.name}, '
                val_antigo += f'{value}, '

            if col_alteradas:
                history = PortariaHistory(
                    id_reg=data_to_delete.id,
                    user=current_user.username,
                    colunas_alteradas=col_alteradas,
                    valores_antigos=val_antigo
                )
                data_to_send.append(history)

            db.session.delete(data_to_delete)

        return send_data(data_to_send, collected_data, message)

    except Exception as e:
        return jsonify({'type': 'error', 'message': 'function error:' + str(e)})


def send_form(form_id):
    try:
        message = 'Dados enviados com sucesso!'
        if form_id == "registros_empresa":
            collected_data = RegistrosEmpresa(
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

        elif form_id == "registros_visitantes":
            collected_data = RegistrosVisitantes(
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

            nome_visitante = Visitantes.query.filter_by(nome=collected_data.nome).first()

            if nome_visitante is None:
                registrar_visitante = Visitantes(
                    nome=collected_data.nome,
                    documento=collected_data.documento,
                    empresa=collected_data.empresa
                )
                data_to_send.append(registrar_visitante)

        return send_data(data_to_send, collected_data, message)

    except Exception as e:
        return jsonify({'type': 'error', 'message': 'function error:' + str(e)})
