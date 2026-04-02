from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required, login_user, logout_user

from app.models import User, db


auth_bp = Blueprint('auth', __name__, template_folder='templates')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)

            return redirect(url_for('main.home'))
        else:
            flash('Ungültiger Nutzername oder Passwort.')
    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.home'))


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        confirm = request.form.get('confirm', '').strip()

        if not username or not email or not password:
            flash('Alle Felder werden benötigt.')
        elif password != confirm:
            flash('Passwörter stimmen nicht überein.')
        elif User.query.filter(
            (User.username == username) | (User.email == email)
        ).first():
            flash('Nutzername oder E-Mail existieren bereits.')
        else:
            user = User(username=username, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash('Registrierung erfolgreich. Bitte logge dich ein.')
            return redirect(url_for('auth.login'))

    return render_template('auth/register.html')
