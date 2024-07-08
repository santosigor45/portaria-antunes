from ext.database import db
from sqlalchemy.inspection import inspect
from flask_login import UserMixin


class Placas(db.Model):
    __tablename__ = 'placas'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    placa = db.Column(db.String(10), nullable=False)
    veiculo = db.Column(db.String(30))
    km_necessario = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs}

    def __repr__(self):
        return f'<Placa id={self.id} placa={self.placa}>'


class Motoristas(db.Model):
    __tablename__ = 'motoristas'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    motorista = db.Column(db.String(50), nullable=False)
    cidade = db.Column(db.String(30))

    def to_dict(self):
        return {c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs}

    def __repr__(self):
        return f'<Motorista id={self.id} motorista={self.motorista}>'


class Visitantes(db.Model):
    __tablename__ = 'visitantes'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    nome = db.Column(db.String(50), nullable=False)
    documento = db.Column(db.String(50))
    empresa = db.Column(db.String(50))

    def to_dict(self):
        return {c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs}

    def __repr__(self):
        return f'<Visitante id={self.id} nome={self.nome}>'


class RegistrosEmpresa(db.Model):
    __tablename__ = 'registros_empresa'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    user = db.Column(db.String(10), nullable=False)
    data_lanc = db.Column(db.DateTime, nullable=False)
    data_reg = db.Column(db.DateTime, nullable=False)
    categoria = db.Column(db.String(10), nullable=False)
    motorista = db.Column(db.String(50), nullable=False)
    placa = db.Column(db.String(10), nullable=False)
    descricao = db.Column(db.String(100))
    quilometragem = db.Column(db.Integer)
    destino = db.Column(db.String(50), nullable=False)
    observacoes = db.Column(db.String(100))

    def to_dict(self):
        return {c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs}


class RegistrosVisitantes(db.Model):
    __tablename__ = 'registros_visitantes'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    user = db.Column(db.String(10), nullable=False)
    data_lanc = db.Column(db.DateTime, nullable=False)
    data_reg = db.Column(db.DateTime, nullable=False)
    categoria = db.Column(db.String(10), nullable=False)
    nome = db.Column(db.String(50), nullable=False)
    documento = db.Column(db.String(50), nullable=False)
    placa = db.Column(db.String(10))
    empresa = db.Column(db.String(50))
    destino = db.Column(db.String(50), nullable=False)
    observacoes = db.Column(db.String(100))

    def to_dict(self):
        return {c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs}


class PortariaHistory(db.Model):
    __tablename__ = 'portaria_history'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    id_reg = db.Column(db.Integer, nullable=False)
    user = db.Column(db.String(32), nullable=False)
    colunas_alteradas = db.Column(db.String(100))
    valores_antigos = db.Column(db.String(250))

    def to_dict(self):
        return {c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs}


class User(db.Model, UserMixin):
    __tablename__ = "portaria_users"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    username = db.Column(db.String(140))
    password = db.Column(db.String(512))
    is_admin = db.Column(db.Boolean, default=False)
    is_manager = db.Column(db.Boolean, default=False)
    is_editor = db.Column(db.Boolean, default=False)

    def __init__(self, username, password):
        self.username = username
        self.password = password


tables_dict = {table.__tablename__: table for table in db.Model.__subclasses__()}


def table_object(table_name):
    return tables_dict.get(table_name)
