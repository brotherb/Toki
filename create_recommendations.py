from app.models import Score
from math import sqrt
import cPickle


page_scores = {}
user_scores = {}


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
    num = pSum - (sum1+sum2*1.0/n)
    den = sqrt((sum1Sq - pow(sum1, 2)*1.0/n)*(sum2Sq-pow(sum2, 2)*1.0/n))

    if den == 0:
        return 0
    return num*1.0/den


def sim_distance(prefs, p1, p2):
    # Get the list of shared_items
    si={}
    for item in prefs[p1]:
        if item in prefs[p2]:
            si[item]=1

    # if they have no ratings in common, return 0
    if len(si)==0:
        return 0

    # Add up the squares of all the differences
    sum_of_squares=sum([pow(prefs[p1][item]-prefs[p2][item],2)
                      for item in prefs[p1] if item in prefs[p2]])

    return 1.0/(1+sum_of_squares)


def preprocess():
    for m in Score.query.all():
        if m.page_id not in page_scores:
            page_scores.setdefault(m.page_id, {})
        page_scores[m.page_id][m.user_id] = m.score

    result = {}
    c = 0
    for item in page_scores:
        c += 1
        if c % 100 == 0:
            print "%d / %d" % (c, len(page_scores))
        scores = [(sim_distance(page_scores, item, other), other) for other in page_scores if other != item]
        result[item] = scores

    f = open('mat_sim.pkl', 'wb')
    cPickle.dump(result, f)
    f.close()


def getRecommendedItems(userid):
    pkl_file = open('mat_sim.pkl', 'rb')
    mat_sim = cPickle.load(pkl_file)

    userRatings = {}
    for m in Score.query.filter_by(user_id=userid).all():
        userRatings[m.page_id] = m.score

    scores = {}
    totalSim = {}
    for (item, rating) in userRatings.items():
        for (similarity, item2) in mat_sim[item]:
            if item2 in userRatings:
                continue
            scores.setdefault(item2, 0)
            scores[item2] += similarity*rating
            totalSim.setdefault(item2, 0)
            totalSim[item2] += similarity
    rankings = [(item, score/totalSim[item]) for item, score in scores.items()]
    rankings.sort()
    # rankings.reverse()
    return rankings[:10]

if __name__ == '__main__':
    preprocess()
