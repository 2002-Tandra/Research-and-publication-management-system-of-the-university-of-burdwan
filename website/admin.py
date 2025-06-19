from flask import Blueprint, render_template, redirect, url_for, flash, session, request
from bson.objectid import ObjectId
from .database import get_db  # ✅ Adjust this if needed to match your structure

admin = Blueprint('admin', __name__)

# Admin password (hardcoded or from environment)
ADMIN_PASSWORD = "Souvik@200"

@admin.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        entered_password = request.form['admin_password']
        if entered_password == ADMIN_PASSWORD:
            session['is_admin'] = True
            return redirect(url_for('admin.admin_dashboard'))
        else:
            flash('Incorrect admin password.')
            return redirect(url_for('admin.admin_login'))

    return render_template('admin_login.html')

# === Admin Dashboard Route ===
@admin.route('/admin-dashboard')
def admin_dashboard():
    if not session.get('is_admin'):
        return redirect(url_for('admin.admin_login'))  # block access
    
    db = get_db()
    users_collection = db['users']

    # ✅ Fetch all users (you can apply filters if needed)
    users = list(users_collection.find())

    return render_template('admin_dashboard.html', users=users)


# === View Publications Route ===
@admin.route('/admin/publications/<user_id>')
def view_publications(user_id):
    db = get_db()
    publications_collection = db['Research Publications']  # Replace with your actual collection name

    # ✅ Fetch publications for the user
    publications = list(publications_collection.find({"user_id": ObjectId(user_id)}))

    return render_template('view_publications.html', publications=publications)


# === Optional: View User Details (if you want to open a detailed page) ===
@admin.route('/admin/user/<user_id>')
def user_details(user_id):
    db = get_db()
    user = db['users'].find_one({"_id": ObjectId(user_id)})

    if not user:
        flash("User not found!", "error")
        return redirect(url_for('admin.admin_dashboard'))

    return render_template('user_details.html', user=user)


@admin.route('/admin-logout')
def admin_logout():
    session.pop('is_admin', None)
    flash('Admin logged out.')
    return redirect(url_for('auth.login'))


