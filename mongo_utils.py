from pymongo import MongoClient


def mongo_connection(database="drill_dev"):
    """connects to Mongo database and returns Mongo database object"""
    client = MongoClient(
        host="192.168.1.203", port=27017, username="root", password="pa55word"
    )
    db = client[database]
    return db