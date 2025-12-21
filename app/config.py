# app/config.py - basic configuration
import os

# Default MySQL URI (parola gömülü, sadece lokal geliştirme için)
# Paroladaki '!' karakteri URL içinde %21 olarak encode edildi.
DEFAULT_DB_URI = "mysql+pymysql://root:aliileela123%21@localhost:3306/hemenye?charset=utf8mb4"


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or DEFAULT_DB_URI
    SQLALCHEMY_TRACK_MODIFICATIONS = False
