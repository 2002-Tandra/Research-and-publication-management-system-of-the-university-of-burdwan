# website/database.py
from pymongo import MongoClient
import certifi

def get_db():
    # MongoDB Atlas connection string
    connection_string = "mongodb+srv://Scholarlyarticles:1919Articles6045@research.c9c4luw.mongodb.net/?retryWrites=true&w=majority&tls=true"

    client = MongoClient(connection_string, tls=True, tlsCAFile=certifi.where())

    # Access the database
    db = client["Resarch_Publications"]
    return db
