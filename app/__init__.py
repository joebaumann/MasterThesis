import os
from flask import Flask


def create_app(test_config=None):
    app = Flask(__name__)

    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY') or 'dev_key')

    # register welcome page blueprint
    from app.welcome_page.welcome_page import welcome_page_bp
    app.register_blueprint(welcome_page_bp)

    # register admin area blueprint
    from app.admin_area.admin_area import admin_area_bp
    app.register_blueprint(admin_area_bp, url_prefix='/admin_area')

    # register annotation tool blueprint
    from app.textannotation.textannotation import textannotation_bp
    app.register_blueprint(textannotation_bp, url_prefix='/textannotation')

    return app
