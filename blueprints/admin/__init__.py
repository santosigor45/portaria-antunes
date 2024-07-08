from flask_admin import Admin
from .admin_views import *
from ext.database import db
from models import RegistrosEmpresa, RegistrosVisitantes, PortariaHistory, Placas, Motoristas, Visitantes, User


def init_app(app):
    admin = Admin(app, template_mode='bootstrap3', base_template='admin_template.html', url='/admin', index_view=MyAdminIndexView())

    admin.add_view(RegistrosEmpresaView(RegistrosEmpresa, db.session, category='Lançamentos'))
    admin.add_view(RegistrosVisitantesView(RegistrosVisitantes, db.session, category='Lançamentos'))
    admin.add_view(PortariaHistoryView(PortariaHistory, db.session, category='Lançamentos'))
    admin.add_view(PlacasView(Placas, db.session, category='Dados'))
    admin.add_view(MotoristasView(Motoristas, db.session, category='Dados'))
    admin.add_view(VisitantesView(Visitantes, db.session, category='Dados'))
    admin.add_view(MyModelView(User, db.session, category='Dados'))
