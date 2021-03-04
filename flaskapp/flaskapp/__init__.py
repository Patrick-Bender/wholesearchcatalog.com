from flask import Flask, render_template, redirect
from flask_pymongo import PyMongo
from .settings import Config
from .search import Searcher
from .forms import SearchForm
import time

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    client = PyMongo(app, connect = True).cx
    searcher = Searcher(client)
    @app.route('/')
    def index():
        form = SearchForm()
        return render_template('index.html', form = form)
    @app.route('/search', methods=('GET', 'POST'))
    def search():
        startTime = time.time()
        form = SearchForm()
        if form.validate_on_submit():
            query = form.query.data
            if query == None:
                return str(form)
            results, searchTime = searcher.search(query)
            print('whole thing took', time.time()-startTime)
            return render_template('search.html', query = query, results = results, searchTime = searchTime)
        return redirect('/')
    return app

