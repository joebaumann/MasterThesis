from flask import Blueprint, render_template


welcome_page_bp = Blueprint('welcome_page_bp', __name__)


@welcome_page_bp.route('/')
def test():
    return """<h1>Welcome!</h1><h2>This is <a href="mailto:joachim.baumann@uzh.ch">Joachim Baumann</a>'s Master Thesis.</h2>"""
