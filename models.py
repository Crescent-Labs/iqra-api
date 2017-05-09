from app import db


class QuranWord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(36), unique=True)

    def __repr__(self):
        return '<QuranWord %r>' % (self.text)


class QuranSubAyah(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(1024), unique=True)

    def __repr__(self):
        return '<QuranSubAyah %r>' % (self.text)


class QuranAyah(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(2048))
    simpleText = db.Column(db.String(2048))
    ayahNum = db.Column(db.Integer)
    surahNum = db.Column(db.Integer)
    englishSurahName = db.Column(db.String(64))
    arabicSurahName = db.Column(db.String(64))

    def __repr__(self):
        return '<QuranAyah %r>' % (self.text)
