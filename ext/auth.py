from flask import flash, redirect, url_for
from flask_login import LoginManager
from models import User

login_manager = LoginManager()


# Function to load a user from the database using the user ID
@login_manager.user_loader
def get_user(user_id):
    return User.query.get(int(user_id))


# Handler for unauthorized access attempts
@login_manager.unauthorized_handler
def unauthorized_callback():
    flash('Você precisa estar logado para acessar esta página', 'error')
    return redirect(url_for('front_end.login'))


def init_app(app):
    login_manager.init_app(app)
