from flask import Blueprint
from flask_login import login_required
from .views import (home, registros_empresa, registros_visitantes, pesquisar, pesquisar_tables,
                    api_data, processar_formulario, login, logout, serve_file, health_check)

bp = Blueprint("front_end", __name__)


bp.add_url_rule("/", view_func=login_required(home), endpoint="default")
bp.add_url_rule("/home", view_func=login_required(home))
bp.add_url_rule("/registros_empresa", view_func=login_required(registros_empresa))
bp.add_url_rule("/registros_visitantes", view_func=login_required(registros_visitantes))
bp.add_url_rule("/pesquisar", view_func=login_required(pesquisar))
bp.add_url_rule("/pesquisar/<path:table>", view_func=login_required(pesquisar_tables))
bp.add_url_rule("/api/<path:data>", view_func=login_required(api_data))
bp.add_url_rule("/processar_formulario", view_func=login_required(processar_formulario), methods=["POST"])
bp.add_url_rule("/login", view_func=login, methods=["POST", "GET"])
bp.add_url_rule("/logout/", view_func=login_required(logout), methods=["POST", "GET"])
bp.add_url_rule("/<path:filename>", view_func=login_required(serve_file))
bp.add_url_rule("/ping", view_func=health_check)


def init_app(app):
    app.register_blueprint(bp)
