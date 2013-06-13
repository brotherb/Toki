from app.models import Score
from math import sqrt


page_scores = {}
user_scores = {}


def preprocess():
    for m in Score.query.alL():
        if m.page_id not in page_scores:
            page_scores.setdefault(m.page_id, {})
        if m.user_id not in user_scores:
            user_scores.setdefault(m.user_id, {})
        page_scores[m.page_id][m.user_id] = m.score
        user_scores[m.user_id][m.page_id] = m.score


def sim_pearson(prefs, p1, p2):
    si = {}
    for item in prefs[p1]:
        if item in prefs[p2]:
            si[item] = 1

    n = len(si)
    if n == 0:
        return 0

    sum1 = sum([prefs[p1][it] for it in si])
    sum2 = sum([prefs[p2][it] for it in si])

    sum1Sq = sum([pow(prefs[p1][it], 2) for it in si])
    sum2Sq = sum([pow(prefs[p2][it], 2) for it in si])

    pSum = sum([prefs[p1][it]*prefs[p2][it] for it in si])
    num = pSum - (sum1+sum2/n)
    den = sqrt((sum1Sq - pow(sum1, 2)/n)*(sum2Sq-pow(sum2, 2)/n))

    if den == 0:
        return 0
    return num/den


def topMatches(prefs, theone, n=5, similarity=sim_pearson):
    scores = [(similarity(prefs, theone, other), other)
                for other in prefs if other != theone]
    scores.sort()
    scores.reverse()
    return scores[0:n]


def getRecommendedItems(prefs, itemMatch, user):
    userRatings = prefs[user]
    scores = {}
    totalSim = {}
    for (item, rating) in userRatings.items():
        for (similarity, item2) in itemMatch[item]:
            if item2 in userRatings:
                continue
            scores.setdefault(item2, 0)
            scores[item2] += similarity*rating
            totalSim.setdefault(item2, 0)
            totalSim[item2] += similarity
    rankings = [(score/totalSim[item], item) for item, score in scores.items()]
    rankings.sort()
    rankings.reverse()
    return rankings


def calculateSimilarItems(prefs, n=10):
    result = {}
    c = 0
    for item in prefs:
        c += 1
        if c % 100 == 0:
            print "%d / %d" % (c, len(prefs))
        scores = topMatches(page_scores, item, n=n, similarity=sim_pearson)
        result[item] = scores
    return result
