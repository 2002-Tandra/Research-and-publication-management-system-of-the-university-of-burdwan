from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from bson.objectid import ObjectId
from .database import get_db
import datetime

views = Blueprint('views', __name__)

@views.route('/')
def home():
    return render_template('index1.html')

@views.route('/index1.html')
def index1():
    return render_template('index1.html')

@views.route('/about-us')
def about_us():
    return render_template('about_us.html')

@views.route('/contact')
def contact_us():
    return render_template('contact_us.html')

@views.route('/register')
def register():
    return render_template('login.html')

@views.route('/credentials')
def credentials():
    return render_template('user_credentials.html')

@views.route('/scholarly_articles', methods=["GET", "POST"])
def scholarly_articles():
    db = get_db()
    collection_names = db.list_collection_names()
    articles = []
    selected_collection = None

    if request.method == "POST":
        selected_collection = request.form.get("collection_name")
        if selected_collection and selected_collection in collection_names:
            collection = db[selected_collection]
            sample_doc = collection.find_one()
            if sample_doc:
                if 'Sr_No' in sample_doc:
                    articles = list(collection.find({}).sort('Sr_No', 1))
                elif 'sr_no' in sample_doc:
                    articles = list(collection.find({}).sort('sr_no', 1))
                else:
                    articles = list(collection.find({}))
            else:
                articles = []

    return render_template(
        "articles.html",
        articles=articles,
        collection_names=collection_names,
        selected_collection=selected_collection
    )

def calculate_api_score(qualifications, adqualifications, publications, experience_years):
    score = 0
    for q in qualifications:
        qual = q.get("qualification", "").lower()
        try:
            marks = float(q.get("marks", 0))
        except (ValueError, TypeError):
            marks = 0

        # Under Graduation scoring based on marks
        if "under graduation" in qual:
            if marks >= 80:
                score += 15
            elif marks >= 70:
                score += 10
            elif marks >= 60:
                score += 5

        # Post Graduation scoring based on marks
        elif "post graducation" in qual:
            if marks >= 80:
                score += 25
            elif marks >= 70:
                score += 20
            elif marks >= 60:
                score += 10

        # M.Phil has fixed score
        elif "m.phil" in qual:
            score += 10

        # Ph.D. has fixed score
        elif "ph.d" in qual or "phd" in qual:
            score += 30

    # Additional Qualifications scoring
    for aq in adqualifications:
        title = aq.get("adqualification", "").lower()
        if "ugc jrf" in title:
            score += 25
        elif "net" in title or "gate" in title:
            score += 15

    # Publications: 5 points each
    score += len(publications) * 5

    # Teaching Experience: 2 points per year
    score += experience_years * 2

    return score


@views.route('/dashboard')
def dashboard():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('auth.login'))

    db = get_db()
    user = db['users'].find_one({'_id': ObjectId(user_id)})
    if not user:
        return redirect(url_for('auth.login'))

    scholar_name = user.get("username", "").lower()
    publications = []

    publication_collections = [
        "journal_publications",
        "conference_publications",
        "chapter_publications",
        "book_publications",
        "thesis_publications",
        "patent_publications",
        "website_publications",
        "others_publications"
    ]

    for col in publication_collections:
        try:
            for pub in db[col].find({"Name": {"$regex": scholar_name, "$options": "i"}}):
                publications.append({
                    "publication_type": col.replace("_publications", ""),
                    "title": pub.get("title") or pub.get("Title") or "N/A",
                    "authors": pub.get("authors") or pub.get("Authors") or pub.get("Inventors") or "N/A",
                    "publication_date": pub.get("publication_date") or pub.get("Publication_Date") or "N/A",
                    "source": (
                        pub.get("source") or pub.get("Journal") or pub.get("Conference") or
                        pub.get("Book") or pub.get("Institution") or pub.get("Website") or
                        pub.get("court") or "N/A"
                    ),
                    "_id": str(pub.get("_id"))
                })
        except Exception as e:
            print(f"Error reading from {col}:", e)

    qualifications = list(db['qualifications'].find({"user_id": ObjectId(user_id)}))
    adqualifications = list(db['adqualifications'].find({"user_id": ObjectId(user_id)}))
    adawards = list(db['adAwards'].find({"user_id": ObjectId(user_id)}))
    adexperience = list(db['adexperience'].find({"user_id": ObjectId(user_id)}))

    # Calculate total years of experience
    total_years = 0
    for exp in adexperience:
        try:
            start = datetime.datetime.strptime(exp['StartDate'], "%Y-%m-%d")
            end = datetime.datetime.strptime(exp['EndDate'], "%Y-%m-%d")
            total_years += (end - start).days // 365
        except:
            continue

    api_score = calculate_api_score(qualifications, adqualifications, publications, total_years)

    return render_template(
        "dashboard.html",
        scholar=user,
        publications=publications,
        qualifications=qualifications,
        adqualifications=adqualifications,
        adawards=adawards,
        adexperience=adexperience,
        api_score=api_score
    )

@views.route('/update-dashboard', methods=['POST'])
def update_dashboard():
    user_id = session.get('user_id')
    if not user_id:
        flash("You must be logged in to update your dashboard.", "error")
        return redirect(url_for('auth.login'))

    db = get_db()
    users_collection = db['users']

    update_data = {
        "username": request.form.get("username", "").strip(),
        "email": request.form.get("email", "").strip(),
        "google_scholar_id": request.form.get("google_scholar_id", "").strip(),
        "institution": request.form.get("institution", "").strip()
    }

    update_data = {k: v for k, v in update_data.items() if v}

    users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": update_data}
    )

    flash("Dashboard updated successfully!", "success")
    return redirect(url_for("views.dashboard"))

@views.route('/upload-journal', methods=['POST'])
def upload_journal():
    user_id = session.get('user_id')
    if not user_id:
        flash("Please login to upload publications.", "error")
        return redirect(url_for('auth.login'))

    publication_type = request.form.get('publication_type')
    if not publication_type:
        flash("Please select a publication type.", "error")
        return redirect(url_for('views.dashboard'))

    data = {key: value for key, value in request.form.items() if key != 'publication_type'}

    db = get_db()
    user = db['users'].find_one({'_id': ObjectId(user_id)})
    if user and user.get("username"):
        data['Name'] = user["username"]

    collection_name = f"{publication_type.lower()}_publications"
    db[collection_name].insert_one(data)

    flash(f"{publication_type.capitalize()} record added successfully!", "success")
    return redirect(url_for("views.dashboard"))

@views.route('/delete-publication/<id>', methods=['DELETE'])
def delete_publication(id):
    db = get_db()
    deleted = False

    publication_collections = [
        "journal_publications", "conference_publications", "chapter_publications",
        "book_publications", "thesis_publications", "patent_publications",
        "website_publications", "others_publications"
    ]

    for col in publication_collections:
        try:
            result = db[col].delete_one({'_id': ObjectId(id)})
            if result.deleted_count > 0:
                deleted = True
                break
        except Exception as e:
            print(f"Error deleting from {col}:", e)

    return ('', 204) if deleted else ('Not Found', 404)

@views.route('/upload-qualification', methods=['POST'])
def upload_qualification():
    user_id = session.get('user_id')
    if not user_id:
        flash("You must be logged in to upload qualification.", "error")
        return redirect(url_for('auth.login'))

    db = get_db()

    qualifications_data = {
        "qualification": request.form.get("qualification", "").strip(),
        "decipline": request.form.get("decipline", "").strip(),
        "institution": request.form.get("institution", "").strip(),
        "marks": request.form.get("marks", "").strip(),
        "user_id": ObjectId(user_id)
    }

    db.qualifications.insert_one(qualifications_data)
    return redirect(url_for('views.dashboard'))

@views.route('/upload-adqualification', methods=['POST'])
def upload_adqualification():
    user_id = session.get('user_id')
    if not user_id:
        flash("You must be logged in to upload qualification.", "error")
        return redirect(url_for('auth.login'))

    db = get_db()

    adqualifications_data = {
        "adqualification": request.form.get("adqualification", "").strip(),
        "Year": request.form.get("Year", "").strip(),
        "user_id": ObjectId(user_id)
    }

    db.adqualifications.insert_one(adqualifications_data)
    return redirect(url_for('views.dashboard'))

@views.route('/upload-adexperience', methods=['POST'])
def upload_adexperience():
    user_id = session.get('user_id')
    if not user_id:
        flash("You must be logged in to upload experience.", "error")
        return redirect(url_for('auth.login'))

    db = get_db()

    adexperience_data = {
        "Title": request.form.get("Title", "").strip(),
        "Companyororganization": request.form.get("Companyororganization", "").strip(),
        "StartDate": request.form.get("StartDate", "").strip(),
        "EndDate": request.form.get("EndDate", "").strip(),
        "user_id": ObjectId(user_id)
    }

    db.adexperience.insert_one(adexperience_data)
    return redirect(url_for('views.dashboard'))

@views.route('/upload-adAwards', methods=['POST'])
def upload_adAwards():
    user_id = session.get('user_id')
    if not user_id:
        flash("You must be logged in to upload awards.", "error")
        return redirect(url_for('auth.login'))

    db = get_db()

    adAwards_data = {
        "Award_Name": request.form.get("Award_Name", "").strip(),
        "Awards_name": request.form.get("Awards_name", "").strip(),
        "Date": request.form.get("Date", "").strip(),
        "user_id": ObjectId(user_id)
    }

    db.adAwards.insert_one(adAwards_data)
    return redirect(url_for('views.dashboard'))
