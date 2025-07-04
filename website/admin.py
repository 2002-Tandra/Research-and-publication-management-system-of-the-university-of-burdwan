from flask import Blueprint, render_template, redirect, url_for, flash, session, request
from bson.objectid import ObjectId
from .database import get_db
from .views import calculate_api_score  # ✅ Import from your existing views.py

admin = Blueprint('admin', __name__)

# === Admin Password ===
ADMIN_PASSWORD = "Souvik@200"

# === Admin Login ===
@admin.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        entered_password = request.form['admin_password']
        if entered_password == ADMIN_PASSWORD:
            session['is_admin'] = True
            return redirect(url_for('admin.admin_dashboard'))
        else:
            flash('Incorrect admin password.', 'error')
            return redirect(url_for('admin.admin_login'))

    return render_template('admin_login.html')


# === Admin Dashboard ===
@admin.route('/admin-dashboard')
def admin_dashboard():
    if not session.get('is_admin'):
        return redirect(url_for('admin.admin_login'))  # Restrict access

    db = get_db()
    users_collection = db['users']
    qualifications_collection = db['qualifications']

    users = list(users_collection.find())

    # Attach API score to each user
    for user in users:
        qualifications = list(qualifications_collection.find({'user_id': user['_id']}))
        latest_q = qualifications[-1] if qualifications else {}
        user['api_score'] = calculate_api_score(latest_q) if latest_q else 0.0

    return render_template('admin_dashboard.html', users=users)


# === View Publications by User ===
@admin.route('/admin/publications/<user_id>')
def view_publications(user_id):
    db = get_db()
    publications_collection = db['Research Publications']  # Adjust if needed

    publications = list(publications_collection.find({"user_id": ObjectId(user_id)}))

    return render_template('view_publications.html', publications=publications)


# === View User Details ===
@admin.route('/admin/user/<user_id>')
def user_details(user_id):
    db = get_db()
    user = db['users'].find_one({"_id": ObjectId(user_id)})

    if not user:
        flash("User not found!", "error")
        return redirect(url_for('admin.admin_dashboard'))

    return render_template('user_details.html', user=user)


# === Admin Logout ===
@admin.route('/admin-logout')
def admin_logout():
    session.pop('is_admin', None)
    flash('Admin logged out.', 'info')
    return redirect(url_for('auth.login'))
