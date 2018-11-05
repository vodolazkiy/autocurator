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
queryList = ['artificial intelligence',
             'machine learning',
             'big data',
             'internet of things',
             'data science',
             'robots']
pastQueries = []
pastRetweets = []
retweets = twitterApi.GetUserRetweets(trim_user=True)
for i in retweets:
    tempdict = json.loads(str(i))
    pastRetweets.append(tempdict["id"])
print(print(dt.strftime(dt.now(), '%H:%M:%S') + ' - Retweets populated.'))
newsDict = {}
for category in queryList:
    newsDict[category] = ''

# Not a list object, must be a comma-separated string to pass to Google get_everything API call.
newsSources = 'the-verge,ars-technica,hacker-news,techcrunch,techradar,the-next-web,wired,vice-news,the-new-york-times'


def query_news_api(query):
    newsjson = newsApi.get_everything(q=query,
                                    sources=newsSources,
                                    from_param=dt.strftime(dt.now() - timedelta(3), '%Y-%m-%d'),
                                    to=dt.strftime(dt.now(), '%Y-%m-%d'),
                                    language='en',
                                    sort_by='relevancy')
    return newsjson['articles']


class Update(Thread):
    def run(self):
        while True:
            if dt.now().hour in range(8, 18):
                for category in queryList:
                    newsDict[category] = query_news_api(category)
                for key in newsDict.keys():
                    newentry = []
                    for article in newsDict[key]:
                        newentry.append(article['url'])
                    newsDict[key] = newentry
                print(dt.strftime(dt.now(), '%H:%M:%S') + ' - Dictionary successfully populated.')
                while len(pastQueries) > 100:
                    queryList.pop(0)
                while len(pastRetweets) > 100:
                    pastRetweets.pop(0)
                print(dt.strftime(dt.now(), '%H:%M:%S') + ' - History cleaned.')
                print(dt.strftime(dt.now(), '%H:%M:%S') + ' - Housekeeping executed.')
                time.sleep(7200)


class MakePost(Thread):
    def run(self):
        sentinelValue = 0
        while True:
            if dt.now().hour in range(8, 18):
                if bool(newsDict[queryList[sentinelValue]]) is False:
                    time.sleep(60)
                failsafevalue = 0
                print(dt.strftime(dt.now(), '%H:%M:%S') + ' - Fetching news article URL.')
                candidates = newsDict[queryList[sentinelValue]]
                targeturl = ''
                for url in candidates:
                    if url not in pastQueries:
                        pastQueries.append(url)
                        print(dt.strftime(dt.now(), '%H:%M:%S') + ' - URL successfully fetched from dictionary.')
                        targeturl = url
                        break
                    else:
                        print(print(dt.strftime(dt.now(), '%H:%M:%S') + ' - Error: Unable to fetch url. Trying again.'))
                        continue
                content = Article(url=targeturl, memoize_articles=False, MAX_SUMMARY_SENT=1, MAX_SUMMARY=215)
                content.download()
                content.parse()
                content.nlp()
                status = content.summary
                try:
                    twitterApi.PostUpdate(status + ' ' + targeturl)
                    sentinelValue += 1
                    if sentinelValue >= (len(queryList)):
                        sentinelValue = 0
                    print(dt.strftime(dt.now(), '%H:%M:%S') + ' - Tweeted: ' + status + ' ' + targeturl)
                except:
                    print(dt.strftime(dt.now(), '%H:%M:%S') + ' - Error: post already exists.')
                    failsafevalue += 1
                    if failsafevalue >= 20:
                        print(dt.strftime(dt.now(), '%H:%M:%S') + 'Unable to make post. Trying again in 30 minutes.')
                        break
                    else:
                        continue
            time.sleep(1800)


class Retweet(Thread):
    def run(self):
        while True:
            if dt.now().hour in range(8, 18):
                candidates = []
                listjson = twitterApi.GetListTimeline(slug='', owner_screen_name='',
                                                      count=50, include_rts=False, include_entities=False,
                                                      return_json=True)
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
                time.sleep(900)


# Timed threads.
if __name__ == '__main__':
    print(dt.strftime(dt.now(), '%H:%M:%S') + ' - Starting Update() Thread.')
    Update().setDaemon(True)
    Update().start()
    print(dt.strftime(dt.now(), '%H:%M:%S') + ' - Starting MakePost() Thread.')
    MakePost().setDaemon(True)
    MakePost().start()
    print(dt.strftime(dt.now(), '%H:%M:%S') + ' - Starting Retweet() Thread.')
    Retweet().setDaemon(True)
    Retweet().start()
    while True:
        pass
