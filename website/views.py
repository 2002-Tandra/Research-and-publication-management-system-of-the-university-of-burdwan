# website/views.py
from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from bson.objectid import ObjectId  # <-- required to work with _id
from .database import get_db
from bson import ObjectId
from pymongo import MongoClient

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
            
            # Try sorting by 'Sr_no' or 'sr_no'
            sample_doc = collection.find_one()
            if sample_doc:
                if 'Sr_No' in sample_doc:
                    articles = list(collection.find({}).sort('Sr_no', 1))  # Ascending
                elif 'sr_no' in sample_doc:
                    articles = list(collection.find({}).sort('sr_no', 1))  # Ascending
                else:
                    articles = list(collection.find({}))  # No sorting field found
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

    return render_template('dashboard.html', scholar=user)