from flask import request, jsonify, abort
from models import *


def api_data(data):
    if data in ['placas', 'motoristas', 'visitantes']:
        return {
            'data': [row.to_dict() for row in db.session.query(table_object(table_name=data))],
        }

    query = db.session.query(table_object(table_name=data))

    if data == 'last_km':
        try:
            placa = request.args.get('placa[value]')
            km_needed = Placas.query.filter_by(placa=placa).one_or_none()
            if km_needed.km_necessario == 1:
                query = RegistrosEmpresa.query.filter_by(placa=placa).order_by(
                    RegistrosEmpresa.id.desc()).first()
                if query:
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
