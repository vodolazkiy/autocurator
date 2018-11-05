# Powered by NewsAPI.org

import json, twitter, time
from newspaper import Config, Article, Source
from datetime import datetime as dt, timedelta
from newsapi import NewsApiClient
from operator import itemgetter
from threading import Thread

# Twitter API Tokens
consumerKey = ''
consumerSecret = ''
accessTokenKey = ''
accessTokenSecret = ''

# Google News API Key
newsApi = NewsApiClient(api_key='')

# Initialize API object. Used to call Twitter library functions, i.e. twitterApi.PostRetweet
twitterApi = twitter.Api(consumer_key=consumerKey,
                  consumer_secret=consumerSecret,
                  access_token_key=accessTokenKey,
                  access_token_secret=accessTokenSecret)

# Loop Controls
sentinelValue = 0
queryList = [] # List of search strings for the NewsAPI
pastQueries = []
pastRetweets = []
newsDict = {}
for category in queryList:
    newsDict[category] = ''

# Not a list object, must be a comma-separated string to pass to Google get_everything API call.
newsSources = ''


# tested, works.
def query_news_api(query):
    newsjson = newsApi.get_everything(q=query,
                                    sources=newsSources,
                                    from_param=dt.strftime(dt.now() - timedelta(3), '%Y-%m-%d'),
                                    to=dt.strftime(dt.now(), '%Y-%m-%d'),
                                    language='en',
                                    sort_by='relevancy')
    return newsjson['articles']

# tested works
def populate_dict():
    for category in queryList:
        newsDict[category] = query_news_api(category)
    for key in newsDict.keys():
        newentry = []
        for article in newsDict[key]:
            newentry.append(article['url'])
        newsDict[key] = newentry
    print('Dictionary successfully populated.')


# needs testing
def get_url_from_dict():
    candidates = newsDict[queryList[sentinelValue]]
    for url in candidates:
        if url not in pastQueries:
            pastQueries.append(url)
            return url
        else:
            continue


# tested, works.
def news_post(url):
    content = Article(url=str(url), memoize_articles=False, MAX_SUMMARY_SENT=1, MAX_SUMMARY=215)
    content.download()
    content.parse()
    content.nlp()
    status = content.summary
    try:
        twitterApi.PostUpdate(status + ' ' + url)
        print(dt.strftime(dt.now(), '%H:%M:%S') + ' - Tweeted: ' + status + ' ' + url)
        return True
    except:
        print(dt.strftime(dt.now(), '%H:%M:%S') + ' - Error: post already exists.')
        return False


def send_post():
    while True:
        url = get_url_from_dict()
        success = news_post(url)
        if success is True:
            break
        else:
            continue


def send_post_thread():
    global sentinelValue
    while True:
        if (dt.now().hour >= 8) and (dt.now().hour < 18):
            send_post()
            sentinelValue += 1
            if sentinelValue >= (len(queryList)):
                sentinelValue = 0
        time.sleep(1800)


# tested, works
def retweet():
    candidates = []
    listjson = twitterApi.GetListTimeline(slug='apiList', owner_screen_name='',
                                          count=50, include_rts=False, include_entities=False, return_json=True)
    for i in listjson:
        candidates.append([i["id"], i["text"], i["retweet_count"]])
    candidates = sorted(candidates, key=itemgetter(2), reverse=True)
    for i in candidates:
        if i[0] in pastRetweets:
            continue
        else:
            tweetid = i[0]
            pastRetweets.append(tweetid)
            try:
                twitterApi.PostRetweet(tweetid)
                print(dt.strftime(dt.now(), '%H:%M:%S') + ' - Retweet: ID ' + str(tweetid))
                break
            except:
                print(dt.strftime(dt.now(), '%H:%M:%S') + ' - Error: retweet already exists.')


def retweet_thread():
    while True:
        if (dt.now().hour >= 8) and (dt.now().hour < 18):
            retweet()
        time.sleep(900)


def populate_past_retweets():
    retweets = twitterApi.GetUserRetweets(trim_user=True)
    for i in retweets:
        tempdict = json.loads(str(i))
        pastRetweets.append(tempdict["id"])


def history_cleanup():
    while len(pastQueries) > 100:
        queryList.pop(0)
    while len(pastRetweets) > 100:
        pastRetweets.pop(0)


def housekeeping():
    while True:
        if (dt.now().hour >= 8) and (dt.now().hour < 18):
            populate_dict()
            history_cleanup()
        time.sleep(7200)


# Initial field population.
populate_past_retweets()
populate_dict()

# Timed threads.
if __name__ == '__main__':
    t0 = Thread(target=housekeeping())
    t1 = Thread(target=send_post_thread())
    t2 = Thread(target=retweet_thread())
    t0.setDaemon(True)
    t1.setDaemon(True)
    t2.setDaemon(True)
    t0.start()
    t1.start()
    t2.start()
    while True:
        pass
