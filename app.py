from flask import Flask
from ext import configuration, database, auth
from blueprints import views, admin


app = Flask(__name__)
configuration.init_app(app)
database.init_app(app)
auth.init_app(app)
views.init_app(app)
admin.init_app(app)
