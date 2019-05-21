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


# Takes in a query and adjusts it based on hard-coded special cases
# Returns a new query with the special cases replaced
# The special cases are for the "Miracle Letters"
def adjustForSpecialCases(value):
    for case in SPECIAL_CASES:
        if case[0] in value:
            value = value.replace(case[0], case[1])

    return value


def getResult(rawValue, translation, ix):
    value = adjustForSpecialCases(rawValue)

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
