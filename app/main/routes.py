# app/main/routes.py - landing and general pages
from flask import render_template

from app.main import main_bp


@main_bp.route("/", endpoint="home")
def home():
    return render_template("landing.html")
