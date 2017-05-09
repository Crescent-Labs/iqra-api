import io
import json
import os

from app import db
import models


myDir = os.path.dirname(__file__)
surahNamesFilePath = os.path.join(myDir, 'surahNames.json')
quranFilePath = os.path.join(myDir, 'quran/')
count = 1

with io.open(
    quranFilePath + 'quran-simple.json', 'r', encoding='utf8'
) as simpleQuran:
    quranObj = json.load(simpleQuran)

wordList = []
for i in quranObj:
    for j in i:
        ayahList = j.split()
        for word in ayahList:
            if word not in wordList:
                wordList.append(word)
wordSet = set(wordList)
for i in wordSet:
    a = models.QuranWord(text=i)
    db.session.add(a)
    if count % 10000 == 0:
        db.session.commit()
    count += 1
db.session.commit()
print 'Finished adding words of Quran to db'

count = 1

phraseList = []
for i in quranObj:
    for j in i:
        ayahList = j.split()
        for k in range(0, len(ayahList)):
            for l in range(k+1, len(ayahList)+1):
                newString = ''
                for m in ayahList[k:l]:
                    newString += m + ' '
                newString = newString[:-1]
                phraseList.append(newString)
phraseSet = set(phraseList)
for i in phraseSet:
    a = models.QuranSubAyah(text=i)
    db.session.add(a)
    if count % 10000 == 0:
        db.session.commit()
    count += 1
db.session.commit()
print 'Finished adding sub ayahs of Quran to db'

count = 1

with io.open(
    quranFilePath + 'arabic.json', 'r', encoding='utf8'
) as arabicQuran:
    with io.open(
        quranFilePath + 'quran-simple.json', 'r', encoding='utf8'
    ) as simpleQuran:
        with io.open(surahNamesFilePath, 'r', encoding='utf8') as surahNames:
            arabicQuranObj = json.load(arabicQuran)
            simpleQuranObj = json.load(simpleQuran)
            surahNamesObj = json.load(surahNames)
            arabicNameObj = surahNamesObj[0]['arabic']
            englishNameObj = surahNamesObj[0]['english']
            for surahIdx, surahVal in enumerate(arabicQuranObj):
                for ayahIdx, ayahVal in enumerate(surahVal):
                    a = models.QuranAyah(
                        text=ayahVal,
                        simpleText=simpleQuranObj[surahIdx][ayahIdx],
                        surahNum=(surahIdx+1),
                        ayahNum=(ayahIdx+1),
                        englishSurahName=englishNameObj[surahIdx],
                        arabicSurahName=arabicNameObj[surahIdx],
                    )
                    db.session.add(a)
                    if count % 10000 == 0:
                        db.session.commit()
                    count += 1
            db.session.commit()
print 'Finished adding arabic Quran to db'
