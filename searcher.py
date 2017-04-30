import tweepy
import jsonpickle
from tweepy import OAuthHandler

consumer_key = 'zfcB3Zj5WRp9f1pAHwJdtfiHm'
consumer_secret = 'CWn46FyN3o9jfRePrgNrJwX9VzspR1t38c1Wp5bGLSej0IpETh'
access_token = '2886866490-a9gpG72J31Q8WXK2gUa4KGqBWPbUF0QxIOHrUgl'
access_secret = 'ySpil1O2e2c7qL7zVWCfVZojKiWLDNwT271b44WNVePHt'

auth = OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_secret)

api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)

# max tweets for this search
max_tweets = 10000
# tweets per query (limited by api)
tweets_per_qry = 100
# file to write in
f_name = 'tweets.txt'
latitude = -37.814
longitude = 144.96332
radius = 25

sinceId = None
max_id = -1

# get the city id to search (here melbourne)
#places = api.geo_search(query='Melbourne', granularity='city')
#place_id = places[0].id

tweet_count = 0
#print("Downloading max {0} tweets".format(max_tweets))
with open(f_name, 'w') as f:
    while tweet_count < max_tweets:
        try:
            if (max_id <= 0):
                if (not sinceId):
                    new_tweets = api.search(count=tweets_per_qry, geocode='%f,%f,%dmi'%(latitude,longitude,radius))
                else:
                    new_tweets = api.search(count=tweets_per_qry, geocode='%f,%f,%dmi'%(latitude,longitude,radius),
                                            since_id=sinceId)
            else:
                if (not sinceId):
                    new_tweets = api.search(count=tweets_per_qry, geocode='%f,%f,%dmi'%(latitude,longitude,radius),
                                            max_id=str(max_id - 1))
                else:
                    new_tweets = api.search(count=tweets_per_qry, geocode='%f,%f,%dmi'%(latitude,longitude,radius),
                                            max_id=str(max_id - 1),
                                            since_id=sinceId)
            if not new_tweets:
                print("No more tweets found")
                break
            for tweet in new_tweets:
                f.write(jsonpickle.encode(tweet._json, unpicklable=False) + '\n')
            tweet_count += len(new_tweets)
            print("Downloaded {0} tweets".format(tweet_count))
            max_id = new_tweets[-1].id
        except tweepy.TweepError as e:
            # exit if any error
            print("some error : " + str(e))
            break

#print ("Downloaded {0} tweets, Saved to {1}".format(tweet_count, f_name))
