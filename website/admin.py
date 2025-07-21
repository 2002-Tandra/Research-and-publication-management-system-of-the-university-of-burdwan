from flask import Blueprint, render_template, redirect, url_for, flash, session, request
from bson.objectid import ObjectId
from .database import get_db
from .views import calculate_api_score
import datetime

admin = Blueprint('admin', __name__)
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
        return redirect(url_for('admin.admin_login'))

    db = get_db()
    users = list(db['users'].find())

    for user in users:
        user_id = user['_id']

        qualifications = list(db['qualifications'].find({'user_id': user_id}))
        adqualifications = list(db['adqualifications'].find({'user_id': user_id}))
        adexperience = list(db['adexperience'].find({'user_id': user_id}))

        # Fetch publications across all collections
        publications = []
        publication_collections = [
            "journal_publications", "conference_publications", "chapter_publications",
            "book_publications", "thesis_publications", "patent_publications",
            "website_publications", "others_publications"
        ]
        for col in publication_collections:
            try:
                pubs = db[col].find({"Name": {"$regex": user.get("username", ""), "$options": "i"}})
                publications.extend(pubs)
            except Exception as e:
                print(f"Error accessing {col}: {e}")

        # Calculate total experience in years
        total_years = 0
        for exp in adexperience:
            try:
                start = datetime.datetime.strptime(exp['StartDate'], "%Y-%m-%d")
                end = datetime.datetime.strptime(exp['EndDate'], "%Y-%m-%d")
                total_years += (end - start).days // 365
            except Exception:
                continue

        # Compute API Score
        api_score = calculate_api_score(
            qualifications=qualifications,
            adqualifications=adqualifications,
            publications=publications,
            experience_years=total_years
        )
        user['api_score'] = api_score

    return render_template('admin_dashboard.html', users=users)

# === View Publications by User ===
@admin.route('/admin/publications/<user_id>')
def view_publications(user_id):
    db = get_db()
    user = db['users'].find_one({"_id": ObjectId(user_id)})
    if not user:
        flash("User not found.", "error")
        return redirect(url_for('admin.admin_dashboard'))

    publications = []
    publication_collections = [
        "journal_publications", "conference_publications", "chapter_publications",
        "book_publications", "thesis_publications", "patent_publications",
        "website_publications", "others_publications"
    ]
    for col in publication_collections:
        try:
            pubs = db[col].find({"Name": {"$regex": user.get("username", ""), "$options": "i"}})
            publications.extend(pubs)
        except Exception as e:
            print(f"Error accessing {col}: {e}")

    return render_template('view_publications.html', publications=publications, user=user)

# === View User Details ===
@admin.route('/admin/user/<user_id>')
def user_details(user_id):
    db = get_db()
    user = db['users'].find_one({"_id": ObjectId(user_id)})
    if not user:
        flash("User not found!", "error")
        return redirect(url_for('admin.admin_dashboard'))

    qualifications = list(db['qualifications'].find({'user_id': user['_id']}))
    adqualifications = list(db['adqualifications'].find({'user_id': user['_id']}))
    adexperience = list(db['adexperience'].find({'user_id': user['_id']}))

    return render_template(
        'user_details.html',
        user=user,
        qualifications=qualifications,
        adqualifications=adqualifications,
        adexperience=adexperience
    )

# === Admin Logout ===
@admin.route('/admin-logout')
def admin_logout():
    session.pop('is_admin', None)
    flash('Admin logged out.', 'info')
    return redirect(url_for('auth.login'))
