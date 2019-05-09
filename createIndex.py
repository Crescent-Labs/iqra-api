# -*- coding: utf-8 -*-
import io
import json
import re
import os.path
from whoosh.index import create_in
from whoosh.fields import *
from whoosh.analysis import RegexTokenizer, CharsetFilter, SpaceSeparatedTokenizer
from accentMap import accent_map


# Reference: https://alraqmiyyat.github.io/2013/01-02.html
def removeHarakat(text):
    harakat = re.compile(
        u""" ّ    | # Tashdid
            َ    | # Fatha
            ً    | # Tanwin Fath
            ُ    | # Damma
            ٌ    | # Tanwin Damm
            ِ    | # Kasra
            ٍ    | # Tanwin Kasr
            ْ    | # Sukun
           ـ     # Tatwil/Kashida
        """,
        re.VERBOSE
    )
    text = re.sub(harakat, '', text)
    text = text.replace(u'ٰ', u'ا')
    return text


def generateCombos(wordList):
    comboSet = set()
    formedSoFar = None
    for word in wordList:
        if formedSoFar:
            formedSoFar = (formedSoFar[0] + word[0], formedSoFar[1] and word[1])
        else:
            formedSoFar = word
        comboSet.add(formedSoFar)
        comboSet.update(generateCombos(wordList[1:]))
    return comboSet

textAnalyzer = RegexTokenizer() | CharsetFilter(accent_map)
keywordAnalyzer = SpaceSeparatedTokenizer() | CharsetFilter(accent_map)

schema = Schema(
    ayah=STORED,
    simple_ayah=TEXT(stored=True, analyzer=textAnalyzer),
    surah_num=NUMERIC(stored=True),
    ayah_num=NUMERIC(stored=True),
    roots=KEYWORD(scorable=True, analyzer=keywordAnalyzer),
    decomposed_ayah=KEYWORD(scorable=True, analyzer=keywordAnalyzer),
    surah_name_ar=STORED,
    surah_name_en=STORED,
)

if not os.path.exists("whooshdir"):
    os.mkdir("whooshdir")
ix = create_in("whooshdir", schema)
writer = ix.writer()

decompositionWords = {}
roots = {}
with io.open('quran/quran-morphology.txt', 'r', encoding='utf8') as morphologyFile:
    for line in morphologyFile:
        splitLine = line.split('\t')
        indices = splitLine[0].split(':')
        surahNum = indices[0]
        ayahNum = indices[1]
        wordNum = int(indices[2])
        decomposedWord = removeHarakat(splitLine[1])
        characteristics = splitLine[3]

        isPrefixOrSuffix = re.search(r'(PREF|SUFF)', characteristics) is not None

        decompositionKey = surahNum + ":" + ayahNum
        if decompositionKey not in decompositionWords:
            decompositionWords[decompositionKey] = []
        if wordNum > len(decompositionWords[decompositionKey]):
            decompositionWords[decompositionKey].append([(decomposedWord, isPrefixOrSuffix)])
        else:
            decompositionWords[decompositionKey][wordNum - 1].append((decomposedWord, isPrefixOrSuffix))

        rootSearchResult = re.search(r'(?<=ROOT:)([^|\n]+)', characteristics)
        if rootSearchResult and not isPrefixOrSuffix:
            if surahNum not in roots:
                roots[surahNum] = {}
            if ayahNum not in roots[surahNum]:
                roots[surahNum][ayahNum] = set()
            roots[surahNum][ayahNum].add(rootSearchResult.group())

decompositionWordCombinations = {}
for key, ayahWords in decompositionWords.items():
    decompositionWordCombinations[key] = set()
    for decomposedWordList in ayahWords:
        unfilteredCombinations = generateCombos(decomposedWordList)
        decompositionWordCombinations[key].update([c[0] for c in unfilteredCombinations if not c[1]])

with io.open("quran/arabic.json", 'r', encoding='utf8') as Quran:
    QuranObj = json.load(Quran)
    with io.open("quran/quran-simple.json", 'r', encoding='utf8') as simpleQuran:
        simpleQuranObj = json.load(simpleQuran)
        with io.open("surahNames.json", 'r', encoding='utf8') as surahNames:
            surahNamesObj = json.load(surahNames)
            for surahIdx, surahVal in enumerate(simpleQuranObj):
                rootsOfSurah = roots.get(str(surahIdx + 1))
                for ayahIdx, ayahVal in enumerate(surahVal):
                    decompositionKey = str(surahIdx + 1) + ":" + str(ayahIdx + 1)
                    currentDecomposedWords = decompositionWordCombinations.get(decompositionKey)
                    if currentDecomposedWords:
                        currentDecomposedWords = ' '.join(currentDecomposedWords)
                    currentRoots = None
                    if rootsOfSurah:
                        currentRoots = rootsOfSurah.get(str(ayahIdx + 1))
                        if currentRoots:
                            currentRoots = ' '.join(currentRoots)

                    writer.add_document(
                        ayah=QuranObj[surahIdx][ayahIdx],
                        simple_ayah=ayahVal,
                        surah_num=(surahIdx + 1),
                        ayah_num=(ayahIdx + 1),
                        roots=currentRoots,
                        decomposed_ayah=currentDecomposedWords,
                        surah_name_ar=surahNamesObj[0]["arabic"][surahIdx],
                        surah_name_en=surahNamesObj[0]["english"][surahIdx],
                    )
writer.commit()
