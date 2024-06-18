from flask import url_for, request, redirect, flash
from flask_admin.contrib.sqla import ModelView
from flask_admin import AdminIndexView
from flask_login import current_user


class MyModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin

    def inaccessible_callback(self, name, **kwargs):
        flash('Você não tem permissão para acessar esta página.', 'error')
        return redirect(url_for('front_end.home', next=request.url))

    def scaffold_list_columns(self):
        columns = super(MyModelView, self).scaffold_list_columns()
        if 'id' not in columns:
            columns.insert(0, 'id')
        return columns


class RegistrosEmpresaView(MyModelView):
    column_filters = ['user', 'data_lanc', 'data_reg', 'motorista', 'placa', 'destino', 'observacoes']
    column_searchable_list = ['id', 'user', 'data_lanc', 'data_reg', 'motorista', 'placa', 'destino', 'observacoes']


class RegistrosVisitantesView(MyModelView):
    column_filters = ['user', 'data_lanc', 'data_reg', 'nome', 'documento', 'empresa', 'destino', 'observacoes']
    column_searchable_list = ['id', 'user', 'data_lanc', 'data_reg', 'nome', 'documento', 'empresa', 'destino', 'observacoes']


class PlacasView(MyModelView):
    column_filters = ['veiculo']
    column_searchable_list = ['placa']


class MotoristasView(MyModelView):
    column_filters = ['cidade']
    column_searchable_list = ['motorista']


class VisitantesView(MyModelView):
    column_filters = ['empresa']
    column_searchable_list = ['nome']


class MyAdminIndexView(AdminIndexView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin

    def inaccessible_callback(self, name, **kwargs):
        flash('Você não tem permissão para acessar esta página.', 'error')
        return redirect(url_for('front_end.home', next=request.url))
