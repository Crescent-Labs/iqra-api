# -*- coding: utf-8 -*-
import io
import os
import json
from operator import itemgetter
from whoosh.qparser import (
    QueryParser, MultifieldParser, OrGroup, FieldsPlugin, WildcardPlugin,
    PhrasePlugin, SequencePlugin
)
from specialCases import SPECIAL_CASES

myDir = os.path.dirname(__file__)
quranFilePath = os.path.join(myDir, "quran/")


def getResponseObjectFromParams(queryText, matches, matchedTerms, suggestions):
    return {
        "queryText": queryText,
        "matches": matches,
        "matchedTerms": matchedTerms,
        "suggestions": suggestions,
    }


def getEmptyResponse(value):
    return getResponseObjectFromParams(value, [], [], [])


def getMatchesFromResults(results, translation):
    with io.open(
        quranFilePath + translation + ".json", 'r', encoding='utf8'
    ) as translatedQuran:
        translatedQuranObj = json.load(translatedQuran)

    finalMatches = []
    for result in results:
        finalMatches.append({
            "surahNum": result['surah_num'],
            "ayahNum": result['ayah_num'],
            "translationSurahName": result['surah_name_en'],
            "arabicSurahName": result['surah_name_ar'],
            "translationAyah": translatedQuranObj[result['surah_num'] - 1][result['ayah_num'] - 1],
            "arabicAyah": result['ayah']
        })
    return sorted(finalMatches, key=itemgetter('surahNum', 'ayahNum'))


# Takes in a query and compares it to hard-coded special cases
# Returns a list of ayah matches if there is a match, otherwise returns None
# The special cases are for the "Miracle Letters"
def getSpecialCasesResults(value, translation, ix):
    matchingAyahList = []
    for case in SPECIAL_CASES:
        if case[0] == value:
            value = case[1]
            matchingAyahList = case[2]

    if len(matchingAyahList) > 0:
        allowedResults = []
        for matchingAyah in matchingAyahList:
            allowedResults.append("surah_num:" + str(matchingAyah[0]) + " AND ayah_num:" + str(matchingAyah[1]))
        parser = MultifieldParser(["surah_num", "ayah_num"], ix.schema)
        parser.remove_plugin_class(PhrasePlugin)
        parser.add_plugin(SequencePlugin())
        query = parser.parse(" OR ".join(allowedResults))
        with ix.searcher() as searcher:
            results = searcher.search(query, limit=7)
            return getResponseObjectFromParams(
                value,
                getMatchesFromResults(results, translation),
                [],
                []
            )
    else:
        return None


def getResult(value, translation, ix):
    specialCasesResults = getSpecialCasesResults(value, translation, ix)
    if specialCasesResults:
        return specialCasesResults

    with ix.searcher() as searcher:
        isSingleWordQuery = False
        if len(value.split()) == 1:
            parser = MultifieldParser(["simple_ayah", "roots", "decomposed_ayah"], ix.schema)
            isSingleWordQuery = True
        else:
            parser = QueryParser("simple_ayah", ix.schema)
        parser.remove_plugin_class(FieldsPlugin)
        parser.remove_plugin_class(WildcardPlugin)
        query = parser.parse(value)
        results = searcher.search(query, limit=None)
        if results:
            finalMatches = getMatchesFromResults(results, translation)
            return getResponseObjectFromParams(
                value,
                finalMatches,
                value.split(' '),
                []
            )

        if not isSingleWordQuery:
            parser = QueryParser("simple_ayah", ix.schema, group=OrGroup)
            parser.remove_plugin_class(FieldsPlugin)
            parser.remove_plugin_class(WildcardPlugin)
            query = parser.parse(value)
            results = searcher.search(query, terms=True, limit=None)
            if not results:
                parser = QueryParser("roots", ix.schema, group=OrGroup)
                parser.remove_plugin_class(FieldsPlugin)
                parser.remove_plugin_class(WildcardPlugin)
                query = parser.parse(value)
                results = searcher.search(query, terms=True, limit=None)
                if not results:
                    parser = QueryParser("decomposed_ayah", ix.schema, group=OrGroup)
                    parser.remove_plugin_class(FieldsPlugin)
                    parser.remove_plugin_class(WildcardPlugin)
                    query = parser.parse(value)
                    results = searcher.search(query, terms=True, limit=None)
            if results:
                matchedTerms = results.matched_terms()

                firstResults = None
                if len(matchedTerms) > 1 and results.scored_length() > 1:
                    if results[1].score > 10:
                        firstResults = results

                    parser = QueryParser("simple_ayah", ix.schema)
                    parser.remove_plugin_class(FieldsPlugin)
                    parser.remove_plugin_class(WildcardPlugin)
                    query = parser.parse(results[0]["simple_ayah"])
                    results = searcher.search(query, limit=None)

                finalMatches = getMatchesFromResults(results, translation)

                suggestions = []
                if firstResults:
                    for result in [fR for fR in firstResults if fR.score > 10]:
                        suggestions.append(result['simple_ayah'])

                return getResponseObjectFromParams(
                    value,
                    finalMatches,
                    # term is a tuple where the second index contains the matching
                    # term
                    [term[1] for term in matchedTerms],
                    suggestions
                )

    return getEmptyResponse(value)


def getTranslations(ayahs, translation):
    # Load the json file with the user's requested translation
    with io.open(
        quranFilePath + translation + ".json", 'r', encoding='utf8'
    ) as translatedQuran:
        translatedQuranObj = json.load(translatedQuran)
    for idx, ayahObj in enumerate(ayahs):
        surahIdx = ayahObj["surahNum"] - 1
        ayahIdx = ayahObj["ayahNum"] - 1
        ayahs[idx]["translationAyah"] = translatedQuranObj[surahIdx][ayahIdx]
    return ayahs
