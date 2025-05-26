from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from .database import get_db

auth = Blueprint('auth', __name__)

# === LOGIN ===
@auth.route('/login', methods=['GET', 'POST'])
def login():
    db = get_db()  # ✅ Get the MongoDB connection
    users_collection = db['users']  # ✅ Access the 'users' collection

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # ✅ Retrieve user by email
        user = users_collection.find_one({'email': email})

        # ✅ If user exists and password is correct
        if user and check_password_hash(user['password'], password):
            session['user_id'] = str(user['_id'])  # ✅ Store user ID in session
            return redirect(url_for('views.dashboard'))  # ✅ Redirect to dashboard

        else:
            flash('Bokachoda Password thik kore de')  # ❌ or user doesn't exist

    return render_template('login.html')  # ✅ Show login form (GET)



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

        # Insert new user
        user_data = {
            'username': username,
            'email': email,
            'password': hashed_password
        }
        users_collection.insert_one(user_data)

        flash("Signup successful! Please login.")
        return redirect(url_for('auth.login'))

    return render_template('signup.html')
