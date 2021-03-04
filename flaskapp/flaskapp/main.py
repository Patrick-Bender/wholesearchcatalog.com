from flask import Blueprint

from .extensions import mongo

main = Blueprint('main', __name__)
'''
databases = {
        'pageIndex': mongo.cx['pageIndex'],
        'webIndex': mongo.cx['webIndex']
        }
'''
@main.route('/')
def index():#database):
    return str(mongo)
    db = databases[database]
    data = db.brick.find()
    return data
    mongo.db = 'webIndex'
    return mongo.db.brick.find()
