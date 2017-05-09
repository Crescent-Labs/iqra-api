import os
basedir = os.path.abspath(os.path.dirname(__file__))

# Sqlite3
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'dbRepository')
SQLALCHEMY_TRACK_MODIFICATIONS = False
