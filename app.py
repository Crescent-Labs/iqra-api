#!/usr/bin/env python
from flask import Flask, jsonify, abort, make_response, request
from flask.ext.sqlalchemy import SQLAlchemy
import os
import traceback


app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)


from api import *


def root_dir():
    return os.path.abspath(os.path.dirname(__file__))


@app.route('/api/search', methods=['POST'])
def getSearchResult():
    if not request.json or 'arabicText' not in request.json:
        abort(400)
    try:
        value = request.json['arabicText']

        if 'translation' in request.json:
            translation = request.json['translation']
        else:
            translation = 'en-hilali'

        result = getResult(value, translation)
    except Exception:
        print traceback.format_exc()
        abort(500)
    return jsonify({'result': result})


@app.route('/api/translations', methods=['POST'])
def getAyahTranslations():
    if not request.json or 'ayahs' not in request.json:
        abort(400)
    try:
        ayahs = request.json['ayahs']

        if 'translation' in request.json:
            translation = request.json['translation']
        else:
            translation = 'en-hilali'

        result = getTranslations(ayahs, translation)
    except Exception:
        print traceback.format_exc()
        abort(500)
    return jsonify({'result': result})


@app.errorhandler(400)
def bad_request(error):
    return make_response(jsonify({'error': 'Bad request'}), 400)


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


@app.errorhandler(500)
def server_error(error):
    return make_response(jsonify({'error': 'Server error'}), 500)


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
