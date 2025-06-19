from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from .database import get_db

auth = Blueprint('auth', __name__)

# === LOGIN ===
@auth.route('/login', methods=['GET', 'POST'])
def login():
    db = get_db()
    users_collection = db['users']

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = users_collection.find_one({'email': email})

        if user and check_password_hash(user['password'], password):
            session['user_id'] = str(user['_id'])
            return redirect(url_for('views.dashboard'))
        else:
            flash('Wrong email or password!')

    return render_template('login.html')


# === LOGOUT ===
@auth.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.')
    return redirect(url_for('auth.login'))


# === SIGNUP ===
@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    db = get_db()
    users_collection = db['users']

    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password1']
        confirm_password = request.form['password2']

        if users_collection.find_one({'email': email}):
            flash("Email already registered!")
            return redirect(url_for('auth.signup'))

        if password != confirm_password:
            flash("Passwords do not match!")
            return redirect(url_for('auth.signup'))

        hashed_password = generate_password_hash(password)
        user_data = {
            'username': username,
            'email': email,
            'password': hashed_password
        }
        users_collection.insert_one(user_data)

        flash("Signup successful! Please login.")
        return redirect(url_for('auth.login'))

    return render_template('signup.html')


# === FORGOT PASSWORD ===
@auth.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    db = get_db()
    users_collection = db['users']

    if request.method == 'POST':
        email = request.form['email']
        user = users_collection.find_one({'email': email})

        if user:
            # ⚠️ Note: In production, send an email with secure token
            return redirect(url_for('auth.reset_password', email=email))
        else:
            flash("Email not found!")

    return render_template('forgot_password.html')


# === RESET PASSWORD ===
@auth.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    db = get_db()
    users_collection = db['users']
    email = request.args.get('email')

    if request.method == 'POST':
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        if password1 != password2:
            flash("Passwords do not match!")
        else:
            hashed = generate_password_hash(password1)
            users_collection.update_one({'email': email}, {'$set': {'password': hashed}})
            flash("Password reset successfully!")
            return redirect(url_for('auth.login'))

    return render_template('reset_password.html', email=email)
