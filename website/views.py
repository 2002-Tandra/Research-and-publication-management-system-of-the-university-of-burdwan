from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from bson.objectid import ObjectId
from .database import get_db

views = Blueprint('views', __name__)

@views.route('/')
def home():
    return render_template('index1.html')

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

    try:
        # Book Publications (example)
        book_collection = db['Details_of_Publication_of_Books_Last_Five_Years']
        book_query = {"Name_of_the_Teacher": {"$regex": scholar_name, "$options": "i"}}
        book_results = book_collection.find(book_query)
        book_titles = [
            doc.get("Title_of_the_book/chapters_published")
            for doc in book_results
            if doc.get("Title_of_the_book/chapters_published")
        ]
        user["books_publications"] = book_titles if book_titles else "N/A"
    except Exception as e:
        print("Error fetching books:", e)
        user["books_publications"] = "N/A"

    try:
        # Research Publications
        research_collection = db['Research_Publications']
        publication_query = {"Name": {"$regex": scholar_name, "$options": "i"}}
        publication_results = research_collection.find(publication_query)
        publications_list = [
            {
                "title": pub.get("Title_of_the_Paper"),
                "journal": pub.get("Journal_Name"),
                "year": pub.get("Year"),
                "doi": pub.get("DOI"),
            }
            for pub in publication_results
            if pub.get("Title_of_the_Paper")
        ]
        user["research_publications"] = publications_list if publications_list else []
    except Exception as e:
        print("Error fetching research publications:", e)
        user["research_publications"] = []

    user["patents_last_five_years"] = "N/A"
    user["publication_chapters"] = "N/A"
    user["research_projects_last_year"] = "N/A"
    user["conference_publications"] = "N/A"

    return render_template('dashboard.html', scholar=user)

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
        "institution": request.form.get("institution", "").strip(),
        "publications": request.form.get("publications", "").strip()
    }

    update_data = {k: v for k, v in update_data.items() if v}

    if "publications" in update_data:
        try:
            update_data["publications"] = int(update_data["publications"])
        except ValueError:
            del update_data["publications"]

    users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": update_data}
    )

    flash("Dashboard updated successfully!", "success")
    return redirect(url_for("views.dashboard"))

# ✅ New Route for Handling Publication Uploads
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

    # Convert the form data into a dictionary (excluding the publication_type)
    data = {key: value for key, value in request.form.items() if key != 'publication_type'}

    # Add user context if needed
    db = get_db()
    user = db['users'].find_one({'_id': ObjectId(user_id)})
    if user and user.get("username"):
        data['Name'] = user["username"]

    # Use a consistent naming convention for collections
    collection_name = f"{publication_type.lower()}_publications"
    db[collection_name].insert_one(data)

    flash(f"{publication_type.capitalize()} record added successfully!", "success")
    return redirect(url_for("views.dashboard"))
