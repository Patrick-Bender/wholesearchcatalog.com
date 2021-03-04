import os
class Config(object):
    MONGO_URI = os.environ.get('MONGO_URI') or 'mongodb://server:3QWSD9MSMqwy6LvqkbTyP56URAMkgb@54.160.69.68:27017/'
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'NBc3zJFuwAbfMcRiXsm3dFZFmsGe8y'
