import os
class Config(object):
    MONGO_URI = os.environ.get('MONGO_URI') or #insert mongo URI here 'mongodb://server:password@ipaddress/'
    SECRET_KEY = os.environ.get('SECRET_KEY') or #insert secret key here
