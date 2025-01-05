from flask import request, jsonify, abort
from sqlalchemy import func, or_
from models import *


def api_data(data):
    if data in ['placas', 'motoristas', 'visitantes']:
        return {
            'data': [row.to_dict() for row in db.session.query(table_object(table_name=data))],
        }

    query = db.session.query(table_object(table_name=data))

    if data == 'retrieve_mileage':
        try:
            placa = request.args.get('placa[value]')
            km_needed = Placas.query.filter_by(placa=placa).one_or_none()
            query = RegistrosEmpresa.query.filter_by(placa=placa).order_by(
                RegistrosEmpresa.id.desc()).first()
            if query:
                if query.categoria == "entrada":
                    retrieved_mileage = query.quilometragem
                    if km_needed.km_necessario == 0:
                        message = 'km no needed'
                    else:
                        message = 'success'
                    return jsonify({'message': f'{message}', 'retrieved_mileage': f'{retrieved_mileage}'})
                else:
                    abort(404, description='Nenhum dado encontrado!')
            else:
                abort(404, description='Nenhum dado encontrado!')

        except Exception as e:
            abort(500, description=str(e))

    if data == 'load_visitor_data':
        try:
            placa = request.args.get('placa[value]')
            query = RegistrosVisitantes.query.filter_by(placa=placa).order_by(
                RegistrosVisitantes.id.desc()).first()
            if query:
                if query.categoria == "entrada":
                    visitor_name = query.nome
                    return jsonify({'message': 'success', 'visitor_name': f'{visitor_name}'})
                else:
                    abort(404, description='Nenhum dado encontrado!')
            else:
                abort(404, description='Nenhum dado encontrado!')

        except Exception as e:
            abort(500, description=str(e))

    # search filter
    search = request.args.get('search[value]')

    if search:
        search_str = str(search).strip().replace('-', '')

        if data == "registros_empresa":
            query = query.filter(
                or_(
                    RegistrosEmpresa.data_reg.ilike(f"%{search_str}%"),
                    RegistrosEmpresa.user.ilike(f"%{search_str}%"),
                    RegistrosEmpresa.motorista.ilike(f"%{search_str}%"),
                    func.replace(RegistrosEmpresa.placa, '-', '').ilike(f"%{search_str}%"),
                    RegistrosEmpresa.descricao.ilike(f"%{search_str}%"),
                    RegistrosEmpresa.destino.ilike(f"%{search_str}%"),
                    RegistrosEmpresa.observacoes.ilike(f"%{search_str}%")
                )
            )

        elif data == "registros_visitantes":
            query = query.filter(
                or_(
                    RegistrosVisitantes.nome.ilike(f"%{search_str}%"),
                    RegistrosVisitantes.user.ilike(f"%{search_str}%"),
                    RegistrosVisitantes.documento.ilike(f"%{search_str}%"),
                    func.replace(RegistrosVisitantes.placa, '-', '').ilike(f"%{search_str}%"),
                    RegistrosVisitantes.empresa.ilike(f"%{search_str}%"),
                    RegistrosVisitantes.destino.ilike(f"%{search_str}%"),
                    RegistrosVisitantes.observacoes.ilike(f"%{search_str}%")
                )
            )

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
            if col_name not in ['data_reg', 'user', 'categoria', 'motorista', 'placa', 'destino']:
                col_name = 'name'
            col = getattr(RegistrosEmpresa, col_name)
        elif data == "registros_visitantes":
            if col_name not in ['data_reg', 'user', 'categoria', 'nome', 'documento', 'empresa', 'destino']:
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

    if length == -1:
        final_query = query.offset(start)
    else:
        final_query = query.offset(start).limit(length)

    # response
    return {
        'data': [row.to_dict() for row in final_query],
        'recordsFiltered': total_filtered,
        'recordsTotal': query.count(),
        'draw': request.args.get('draw', type=int),
    }
