# app/auth/routes.py - login/register/logout
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

from app.auth import auth_bp
from app.extensions import db
from app.models import User, UserRole, Restaurant


def _validate_registration_fields(name: str, email: str, password: str):
    errors = []
    if not name:
        errors.append("Name is required.")
    if not email or "@" not in email:
        errors.append("Valid email is required.")
    if not password or len(password) < 6:
        errors.append("Password must be at least 6 characters.")
    return errors


def _redirect_by_role(user: User):
    if user.role == UserRole.RESTAURANT_OWNER:
        return redirect(url_for("restaurant_dashboard"))
    return redirect(url_for("customer_dashboard"))


@auth_bp.route("/customer/login", methods=["GET", "POST"], endpoint="customer_login")
def customer_login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not email or not password:
            flash("Email and password are required.", "warning")
            return render_template("auth/customer_login.html")
        user = User.query.filter_by(email=email, role=UserRole.CUSTOMER).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user, remember=bool(request.form.get("remember")))
            flash("Giriş başarılı.", "success")
            return redirect(url_for("customer_dashboard"))
        flash("E-posta veya şifre hatalı.", "danger")
    return render_template("auth/customer_login.html")


@auth_bp.route("/customer/register", methods=["GET", "POST"], endpoint="customer_register")
def customer_register():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password")
        phone = request.form.get("phone")
        password_confirm = request.form.get("password_confirm")
        errors = _validate_registration_fields(name, email, password)
        if errors:
            for err in errors:
                flash(err, "danger")
            return render_template("auth/customer_register.html")
        if password_confirm and password != password_confirm:
            flash("Passwords do not match.", "danger")
            return render_template("auth/customer_register.html")
        if User.query.filter_by(email=email).first():
            flash("Bu e-posta ile kayıt mevcut.", "warning")
        else:
            user = User(
                name=name,
                email=email,
                phone=phone,
                password_hash=generate_password_hash(password),
                role=UserRole.CUSTOMER,
            )
            db.session.add(user)
            db.session.commit()
            login_user(user)
            flash("Kayıt başarılı, giriş yapıldı.", "success")
            return redirect(url_for("customer_dashboard"))
    return render_template("auth/customer_register.html")


@auth_bp.route("/restaurant/login", methods=["GET", "POST"], endpoint="restaurant_login")
def restaurant_login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not email or not password:
            flash("Email and password are required.", "warning")
            return render_template("auth/restaurant_login.html")
        user = User.query.filter_by(email=email, role=UserRole.RESTAURANT_OWNER).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user, remember=bool(request.form.get("remember")))
            flash("Giriş başarılı.", "success")
            return redirect(url_for("restaurant_dashboard"))
        flash("E-posta veya şifre hatalı.", "danger")
    return render_template("auth/restaurant_login.html")


@auth_bp.route("/restaurant/register", methods=["GET", "POST"], endpoint="restaurant_register")
def restaurant_register():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password")
        phone = request.form.get("phone")
        password_confirm = request.form.get("password_confirm")
        restaurant_name = (request.form.get("restaurant_name") or "").strip()
        tax_number = (request.form.get("tax_number") or "").strip()
        errors = _validate_registration_fields(name, email, password)
        if errors:
            for err in errors:
                flash(err, "danger")
            return render_template("auth/restaurant_register.html")
        if password_confirm and password != password_confirm:
            flash("Passwords do not match.", "danger")
            return render_template("auth/restaurant_register.html")
        if not restaurant_name:
            flash("Restaurant name is required.", "danger")
            return render_template("auth/restaurant_register.html")
        if User.query.filter_by(email=email).first():
            flash("Bu e-posta ile kayıt mevcut.", "warning")
        else:
            user = User(
                name=name,
                email=email,
                phone=phone,
                password_hash=generate_password_hash(password),
                role=UserRole.RESTAURANT_OWNER,
            )
            db.session.add(user)
            db.session.flush()
            db.session.add(
                Restaurant(
                    owner_id=user.id,
                    name=restaurant_name,
                    phone=phone,
                    tax_number=tax_number or None,
                    is_active=True,
                )
            )
            db.session.commit()
            login_user(user)
            flash("Kayıt başarılı, giriş yapıldı.", "success")
            return redirect(url_for("restaurant_dashboard"))
    return render_template("auth/restaurant_register.html")


@auth_bp.route("/logout", endpoint="logout")
def logout():
    if current_user.is_authenticated:
        logout_user()
    flash("Çıkış yapıldı.", "info")
    return redirect(url_for("home"))
