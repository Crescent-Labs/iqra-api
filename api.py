# -*- coding: utf-8 -*-

from Levenshtein import ratio
import alfanous
import re
import io
import json
import os

from specialCases import SPECIAL_CASES
import models


suggestions = {}
myDir = os.path.dirname(__file__)
quranFilePath = os.path.join(myDir, "quran/")


# Helper method for db query
def dbGet(model, text):
    return model.query.filter_by(text=text).first()


# Takes in a query, its list of matches, and a threshold
# Returns the most common match as long as it is similar enough to the query
# If the higest match is not similar enough to the query, None is returned
def mostCommon(spoken, lst, threshold):
    highestCountItem = max(lst, key=lst.count)
    highestCount = lst.count(highestCountItem)
    contenders = []
    for item in lst:
        if (lst.count(item) == highestCount) and (item not in contenders):
            contenders.append(item)
    if len(contenders) > 1:
        print "\nContending"
        bestMatch = [None, 0]
        for ayah in contenders:
            score = ratio(spoken, ayah)
            print ayah
            print score
            if score > threshold and score > bestMatch[1]:
                bestMatch = [ayah, score]
        return bestMatch[0]
    elif ratio(spoken, highestCountItem) > threshold:
        return highestCountItem
    else:
        return None


# Takes in a query and list of matches
# Returns the match with the highest similarity to the query
def bestLevMatch(spoken, lst):
    print " "
    bestMatch = [None, 0.65]
    for ayah in lst:
        score = ratio(spoken, ayah)
        print ayah
        print score
        if score > bestMatch[1]:
            bestMatch = [ayah, score]
    return bestMatch[0]


# Takes in an ayah object from alfanous
# Returns a cleaned-up ayah object
def getAlfanousArabicAyah(ayah):
    arabicAyah = ayah["aya"]["text"].encode("utf-8")

    # Removing html formatting provided by default by alfanous
    while arabicAyah.find("<span") > -1:
        # Remove html highlighting provided by alfanous from the ayah
        startSpan1 = arabicAyah.find("<span")
        endSpan1 = arabicAyah.find(">") + 1
        arabicAyah = arabicAyah[:startSpan1] + arabicAyah[endSpan1:]

        startSpan2 = arabicAyah.find("</span>")
        endSpan2 = arabicAyah.find("</span>") + 7
        arabicAyah = arabicAyah[:startSpan2] + arabicAyah[endSpan2:]

    return arabicAyah


# Takes in a query, the user's requested translation, and a list of matches
# Optionally takes the zeroIndexed flag as False if match indeces are not
# zero-indexed
# Returns a response object with the query and all the matches
def matchIdxListToResponse(
    value, translation, matchingAyahList, zeroIndexed=True
):
    # Load the json file with the user's requested translation
    with io.open(
        quranFilePath + translation + ".json", 'r', encoding='utf8'
    ) as translatedQuran:
        translatedQuranObj = json.load(translatedQuran)

    adjustment = 0
    if zeroIndexed:
        adjustment = 1

    finalMatches = []
    for item in matchingAyahList:
        currentAyah = models.QuranAyah.query.filter_by(
            surahNum=(item[0] + adjustment),
            ayahNum=(item[1] + adjustment)
        ).first()
        adjustedSurah = item[0] - 1 + adjustment
        adjustedAyah = item[1] - 1 + adjustment
        finalMatches.append({
            "surahNum": currentAyah.surahNum,
            "ayahNum": currentAyah.ayahNum,
            "translationSurahName": currentAyah.englishSurahName,
            "arabicSurahName": currentAyah.arabicSurahName,
            "translationAyah": translatedQuranObj[adjustedSurah][adjustedAyah],
            "arabicAyah": currentAyah.text
        })

    returnObj = {
        "queryText": value.encode('utf-8'),
        "matches": finalMatches,
    }

    return returnObj


# Takes in a query, the user's requested translation, and a list of matches
# Returns a response object with the query and all the matches
def matchDbListToResponse(value, translation, matchingAyahList):
    # Load the json file with the user's requested translation
    with io.open(
        quranFilePath + translation + ".json", 'r', encoding='utf8'
    ) as translatedQuran:
        translatedQuranObj = json.load(translatedQuran)

    finalMatches = []
    for item in matchingAyahList:
        tAyah = translatedQuranObj[item.surahNum - 1][item.ayahNum - 1]
        finalMatches.append({
            "surahNum": item.surahNum,
            "ayahNum": item.ayahNum,
            "translationSurahName": item.englishSurahName,
            "arabicSurahName": item.arabicSurahName,
            "translationAyah": tAyah,
            "arabicAyah": item.text
        })

    returnObj = {
        "queryText": value.encode('utf-8'),
        "matches": finalMatches,
    }

    return returnObj


# Returns a response object with no matches
def returnEmptyResponse(value):
    returnObj = {
        "queryText": value.encode('utf-8'),
        "matches": [],
    }

    return returnObj


# Takes in the query word and checks if it or a suggested replacement is in the
# Quran
# Returns the word in the Quran if one is found, otherwise returns None
def checkForWordInQuran(value):
    wordMatch = dbGet(models.QuranWord, value)
    if wordMatch:
        return wordMatch.text
    else:
        # The original word is not in the Quran so we try alfanous' suggestions
        wordSuggestionList = []
        wordSuggestions = alfanous.do({
            "action": "suggest", "query": value
        })["suggest"]
        for word in wordSuggestions:
            for suggestion in wordSuggestions[word]:
                wordMatch = dbGet(models.QuranWord, value)
                if wordMatch:
                    wordSuggestionList.append(wordMatch.text)
        if len(wordSuggestionList) > 1:
            topRatioValue = 0
            topSuggestion = ""
            while len(wordSuggestionList) > 0:
                suggestion = wordSuggestionList.pop(0)
                suggestionRatio = ratio(value, suggestion)
                if suggestionRatio > topRatioValue:
                    topRatioValue = suggestionRatio
                    topSuggestion = suggestion
            return topSuggestion
        elif len(wordSuggestionList) == 1:
            return wordSuggestionList[0]
        else:
            return None


# Takes in a query and checks if any part of it is in the Quran
# Return the part in the Quran if one is found, otherwise it returns None
def checkForPartialVerseInQuran(value):
    valueComboList = []
    valueList = value.split()
    for i in range(0, len(valueList)):
        for j in range(i + 1, len(valueList) + 1):
            newString = ""
            for k in valueList[i:j]:
                newString += k + " "
            newString = newString[:-1]
            valueComboList.append(newString)

    noDuplicateValueComboList = list(set(valueComboList))
    comboList = sorted(noDuplicateValueComboList, key=len)[::-1]
    for combo in comboList:
        subAyahMatch = dbGet(models.QuranSubAyah, combo)
        if subAyahMatch:
            return subAyahMatch.text
    return None


# Takes in a query word and returns all the ayahs containing the word
def findSingleWordMatches(value, translation):
    matchingAyahList = []
    matches = models.QuranAyah.query.filter(
        models.QuranAyah.simpleText.contains(value)
    ).all()
    for match in matches:
        if value in match.simpleText.split():
            matchingAyahList.append(match)
    return matchDbListToResponse(value, translation, matchingAyahList)


# Takes in a partial ayah and returns all the full ayahs containing it
def findPartialVerseMatches(value, translation):
    matchingAyahList = models.QuranAyah.query.filter(
        models.QuranAyah.simpleText.contains(value)
    ).all()
    return matchDbListToResponse(value, translation, matchingAyahList)


# Takes in a query and compares it to hard-coded special cases
# Returns a list of ayah matches if there is a match, otherwise returns None
# The special cases are for the "Miracle Letters"
def specialCasesSearch(value, translation):
    matchingAyahList = []
    for case in SPECIAL_CASES:
        if case[0] == value.encode("utf-8"):
            value = case[1].decode("utf-8")
            matchingAyahList = case[2]

    if len(matchingAyahList) > 0:
        return matchIdxListToResponse(
            value, translation, matchingAyahList, zeroIndexed=False
        )
    else:
        return None


# Takes in a query and tries to find a full ayah that matches it
# Returns a full response object if there is a match, otherwise None
# Tries to find a match in stages and recurses using a skip flag to call the
# next level when a stage fails to get a match
def fullVerseSearch(
    value, translation, skip1=False, skip2=False, skip3=False, skip4=False
):
    global suggestions

    if not skip1 and not skip2 and not skip3 and not skip4:
        ayahs = alfanous.do({
            "action": "search",
            "query": value,
            "vocalized": False,
            "word_info": False,
            "word_derivations": False,
            "word_vocalizations": False,
            "aya_theme_info": False,
            "aya_stat_info": False,
            "aya_sajda_info": False,
            "range": 3,
            "perpage": 3
        })["search"]["ayas"]
        if len(ayahs) > 0:
            levList = []
            for item in ayahs:
                matched = getAlfanousArabicAyah(ayahs[item])
                levList.append(matched)
            bestMatch = bestLevMatch(value.encode("utf-8"), levList)
            if bestMatch is not None:
                matchingAyahList = models.QuranAyah.query.filter(
                    models.QuranAyah.simpleText.contains(
                        bestMatch.decode("utf-8")
                    )
                ).all()
                return matchDbListToResponse(
                    bestMatch.decode("utf-8"), translation, matchingAyahList
                )
            else:
                # Restart call ignoring initial results
                return fullVerseSearch(value, translation, skip1=True)
        else:
            return fullVerseSearch(value, translation, skip1=True)
    elif not skip2 and not skip3 and not skip4:
        print "\nNo matches. Trying spaces."
        spaceAyahs = []
        spaces = [space.start() for space in re.finditer(' ', value)]
        for space in spaces:
            spacedValue = value[:space] + value[(space+1):]
            spacedAyahs = alfanous.do({
                "action": "search",
                "query": spacedValue,
                "vocalized": False,
                "word_info": False,
                "word_derivations": False,
                "word_vocalizations": False,
                "aya_theme_info": False,
                "aya_stat_info": False,
                "aya_sajda_info": False,
                "range": 1,
                "perpage": 1
            })["search"]["ayas"]
            if len(spacedAyahs) > 0:
                spacedMatched = getAlfanousArabicAyah(spacedAyahs[1])
                spaceAyahs.append(spacedMatched)
        if len(spaceAyahs) > 0:
            mostCommonMatch = mostCommon(
                value.encode("utf-8"), spaceAyahs, 0.65
            )
            if mostCommonMatch:
                matchingAyahList = models.QuranAyah.query.filter(
                    models.QuranAyah.simpleText.contains(
                        mostCommonMatch.decode("utf-8")
                    )
                ).all()
                return matchDbListToResponse(
                    mostCommonMatch.decode("utf-8"),
                    translation,
                    matchingAyahList
                )
            else:
                return fullVerseSearch(value, translation, skip2=True)
        else:
            return fullVerseSearch(value, translation, skip2=True)
    elif not skip3 and not skip4:
        print "\nNo matches. Trying suggestions."
        suggestionAyahs = []
        suggestions = alfanous.do({
            "action": "suggest",
            "query": value,
            "vocalized": False
        })["suggest"]

        for i in suggestions:
            for j in suggestions[i]:
                newValue = value.replace(i, j)
                newAyahs = alfanous.do({
                    "action": "search",
                    "query": newValue,
                    "vocalized": False,
                    "word_info": False,
                    "word_derivations": False,
                    "word_vocalizations": False,
                    "aya_theme_info": False,
                    "aya_stat_info": False,
                    "aya_sajda_info": False,
                    "range": 1,
                    "perpage": 1
                })["search"]["ayas"]
                if len(newAyahs) > 0:
                    newMatched = getAlfanousArabicAyah(newAyahs[1])
                    suggestionAyahs.append(newMatched)
        if len(suggestionAyahs) > 0:
            mostCommonMatch = mostCommon(
                value.encode("utf-8"), suggestionAyahs, 0.65
            )
            if mostCommonMatch:
                matchingAyahList = models.QuranAyah.query.filter(
                    models.QuranAyah.simpleText.contains(
                        mostCommonMatch.decode("utf-8")
                    )
                ).all()
                return matchDbListToResponse(
                    mostCommonMatch.decode("utf-8"),
                    translation,
                    matchingAyahList
                )
            else:
                return fullVerseSearch(value, translation, skip3=True)
        else:
            return fullVerseSearch(value, translation, skip3=True)
    elif not skip4:
        if len(value) < 30:
            print "\nNo matches. Trying spaces and suggestions."
            ssAyahs = []
            for i in suggestions:
                for j in suggestions[i]:
                    newValue = value.replace(i, j)
                    spaces = [
                        space.start() for space in re.finditer(' ', newValue)
                    ]
                    for space in spaces:
                        ssValue = newValue[:space] + newValue[(space+1):]
                        newAyahs = alfanous.do({
                            "action": "search",
                            "query": ssValue,
                            "vocalized": False,
                            "word_info": False,
                            "word_derivations": False,
                            "word_vocalizations": False,
                            "aya_theme_info": False,
                            "aya_stat_info": False,
                            "aya_sajda_info": False,
                            "range": 1,
                            "perpage": 1
                        })["search"]["ayas"]
                        if len(newAyahs) > 0:
                            ssMatched = getAlfanousArabicAyah(newAyahs[1])
                            ssAyahs.append(ssMatched)
            if len(ssAyahs) > 0:
                mostCommonMatch = mostCommon(
                    value.encode("utf-8"), ssAyahs, 0.65
                )
                if mostCommonMatch is not None:
                    matchingAyahList = models.QuranAyah.query.filter(
                        models.QuranAyah.simpleText.contains(
                            mostCommonMatch.decode("utf-8")
                        )
                    ).all()
                    return matchDbListToResponse(
                        mostCommonMatch.decode("utf-8"),
                        translation,
                        matchingAyahList
                    )
                else:
                    return fullVerseSearch(value, translation, skip4=True)
            else:
                return fullVerseSearch(value, translation, skip4=True)
        else:
            return fullVerseSearch(value, translation, skip4=True)
    else:
        print "\nNo matches at all."
        return None


# Takes in a partial ayah query and handles passing it off to functions to
# find a match in the Quran
# Returns the response object if there is a match, otherwise returns None
def exactPartialVerseSearch(value, translation):
    matchingPartialVerse = checkForPartialVerseInQuran(value)
    if matchingPartialVerse:
        return findPartialVerseMatches(matchingPartialVerse, translation)
    else:
        return None


# The main entry point for version 3 of the api
# Takes in a query and filters it through different searches until a match is
# found
# Returns a response object containing the query, all matches, and their
# details
def getResult(value, requestedTranslation):
    global translation
    translation = requestedTranslation
    # * and ? have special meaning in alfanous, and so need to be removed
    value = value.replace("*", "")
    value = value.replace("?", "")

    specialCasesSearchResult = specialCasesSearch(value, translation)
    if not specialCasesSearchResult:
        if len(value.split()) == 1:
            matchedWord = checkForWordInQuran(value)
            if matchedWord is None:
                return returnEmptyResponse(value)
            else:
                return findSingleWordMatches(matchedWord, translation)
        else:
            fullVerseSearchResult = fullVerseSearch(value, translation)
            if not fullVerseSearchResult:
                exactPartialVerseSearchResult = exactPartialVerseSearch(
                    value, translation
                )
                if not exactPartialVerseSearchResult:
                    print "\nNo results at all"
                    return returnEmptyResponse(value)
                else:
                    print "\nFound a partial verse"
                    return exactPartialVerseSearchResult
            else:
                print "\nFound a full verse"
                return fullVerseSearchResult
    else:
        print "\nFound a special case"
        return specialCasesSearchResult


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
