import os
class Config(object):
    MONGO_URI = os.environ.get('MONGO_URI') or 'mongodb://localhost:27017/'
    SECRET_KEY = os.environ.get('SECRET_KEY') or #insert secret key here
