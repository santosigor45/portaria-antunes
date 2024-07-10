from flask import request, jsonify
from flask_login import current_user
from models import *
from datetime import datetime
from zoneinfo import ZoneInfo


def processar_formulario():
    try:
        enviar_dados = []
        dados_coletados = None
        message = 'Dados enviados com sucesso!'
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
            duplicado = Placas.query.filter_by(placa=request.form.get('placa')).all()
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
                if len(duplicado) == 1 and duplicado[0].id == dados_coletados.id or len(duplicado) == 0:
                    dados_coletados.placa = request.form.get('placa')
                    dados_coletados.veiculo = request.form.get('veiculo')
                    dados_coletados.km_necessario = bool(request.form.get('km-needed'))
                else:
                    return jsonify({'type': 'info', 'message': 'Placa já cadastrada!'})

        elif formulario_id == "editFormMotoristas":
            dados_coletados = Motoristas.query.get(request.form.get('id'))
            duplicado = Motoristas.query.filter_by(motorista=request.form.get('motorista')).all()
            if not dados_coletados:
                if not duplicado:
                    dados_coletados = Motoristas(
                        motorista=request.form.get('motorista'),
                        cidade=request.form.get('cidade')
                    )
                else:
                    return jsonify({'type': 'info', 'message': 'Motorista já cadastrado!'})
            else:
                if len(duplicado) == 1 and duplicado[0].id == dados_coletados.id or len(duplicado) == 0:
                    dados_coletados.motorista = request.form.get('motorista')
                    dados_coletados.cidade = request.form.get('cidade')
                else:
                    return jsonify({'type': 'info', 'message': 'Motorista já cadastrado!'})

        elif formulario_id == "editFormVisitantes":
            dados_coletados = Visitantes.query.get(request.form.get('id'))
            duplicado = Visitantes.query.filter_by(nome=request.form.get('nome')).all()
            if not dados_coletados:
                if not duplicado:
                    dados_coletados = Visitantes(
                        nome=request.form.get('nome'),
                        documento=request.form.get('documento'),
                        empresa=request.form.get('empresa')
                    )
                else:
                    return jsonify({'type': 'info', 'message': 'Visitante já cadastrado!'})
            else:
                if len(duplicado) == 1 and duplicado[0].id == dados_coletados.id or len(duplicado) == 0:
                    dados_coletados.nome = request.form.get('nome')
                    dados_coletados.documento = request.form.get('documento')
                    dados_coletados.empresa = request.form.get('empresa')
                else:
                    return jsonify({'type': 'info', 'message': 'Visitante já cadastrado!'})

        elif formulario_id.startswith("editFormRegistros"):
            if formulario_id == "editFormRegistros_empresa":
                dados_coletados = RegistrosEmpresa.query.get(request.form.get('id'))
                fields = [
                    ('categoria', 'categoria'),
                    ('data_reg', lambda: request.form.get("data") + " " + request.form.get("hora") + ":00"),
                    ('motorista', 'motorista'),
                    ('placa', 'placa'),
                    ('quilometragem', 'km'),
                    ('destino', 'destino'),
                    ('observacoes', 'obs')
                ]
            if formulario_id == "editFormRegistros_visitantes":
                dados_coletados = RegistrosVisitantes.query.get(request.form.get('id'))
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

            col_alteradas = f"{formulario_id.replace('editForm', '').lower()}: "
            val_antigo = ''

            for attr, form_field in fields:
                old_value = getattr(dados_coletados, attr) if attr != 'data_reg' else getattr(dados_coletados, attr).strftime('%Y-%m-%d %H:%M:%S')
                new_value = form_field() if callable(form_field) else request.form.get(form_field) or None
                if str(old_value) != str(new_value):
                    col_alteradas += f'{attr}, '
                    val_antigo += f'{old_value}, '
                    setattr(dados_coletados, attr, new_value)

            if col_alteradas:
                history = PortariaHistory(
                    id_reg=dados_coletados.id,
                    user=current_user.username,
                    colunas_alteradas=col_alteradas,
                    valores_antigos=val_antigo
                )
                enviar_dados.append(history)
            else:
                return jsonify({'type': 'info', 'message': 'Nenhum dado alterado!'})

        elif formulario_id.startswith("deleteForm"):
            table_id = formulario_id.replace("deleteForm", '').lower()
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
                enviar_dados.append(history)

            db.session.delete(data_to_delete)
            message = 'Dados excluídos com sucesso!'

        if dados_coletados:
            enviar_dados.append(dados_coletados)

        if enviar_dados:
            for dado in enviar_dados:
                db.session.add(dado)

        db.session.commit()

        return jsonify({'type': 'success', 'message': message})

    except Exception as e:
        db.session.rollback()
        return jsonify({'type': 'error', 'message': str(e)})
