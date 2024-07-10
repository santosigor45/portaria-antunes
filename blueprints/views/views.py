from flask import render_template, redirect, url_for, send_from_directory
from flask_login import current_user
from models import Motoristas, Placas, Visitantes


def home():
    if current_user.is_authenticated:
        return render_template("home.html")
    else:
        return redirect(url_for('views.login'))


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


def serve_file(filename):
    return send_from_directory('', filename)


def health_check():
    return 'OK', 200
