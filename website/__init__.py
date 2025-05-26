from flask import Flask
from flask_pymongo import PyMongo

# Initialize PyMongo globally
mongo = PyMongo()

def create_app():
    app = Flask(__name__)

    # ✅ Set a secure secret key
    app.secret_key = '9f5c82c13940beec3d5d0b40e53b11aebc6ab3a21b0f1e98c9889b77dba1303f'

    # ✅ MongoDB connection string
    app.config['MONGO_URI'] = 'mongodb+srv://Scholarlyarticles:1919Articles6045@research.c9c4luw.mongodb.net/?retryWrites=true&w=majority&tls=true'

    # ✅ Initialize PyMongo
    mongo.init_app(app)

    # ✅ Import Blueprints
    from .views import views
    from .auth import auth

    # ✅ Register Blueprints
    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    return app
