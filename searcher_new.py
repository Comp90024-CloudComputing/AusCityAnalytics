import re
import sys
import json
import tweepy
import codecs
import string
import jsonpickle
import couchdb
from itertools import islice
from tweepy import OAuthHandler
from collections import defaultdict
import traceback


consumer_key = 'zfcB3Zj5WRp9f1pAHwJdtfiHm'
consumer_secret = 'CWn46FyN3o9jfRePrgNrJwX9VzspR1t38c1Wp5bGLSej0IpETh'
access_token = '2886866490-a9gpG72J31Q8WXK2gUa4KGqBWPbUF0QxIOHrUgl'
access_secret = 'ySpil1O2e2c7qL7zVWCfVZojKiWLDNwT271b44WNVePHt'

auth = OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_secret)

api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)


search_loc = str(sys.argv[1])

server = couchdb.Server("http://admin:password@localhost:5984/")
try:
    server.create(search_loc)
except Exception as e:
    print (str(e)+" The database exists")

db = server[search_loc]

def import_words(file_path, start_line):
    word_set = []
    with open(file_path, 'r') as infile:
        for line in islice(infile, start_line, None):
            word_set.append(line.rstrip())
    return word_set

def import_words_iso(file_path, start_line):
    word_set = []
    with codecs.open(file_path, 'r', encoding='ISO-8859-1') as infile:
        for line in islice(infile, start_line, None):
            word_set.append(line.rstrip())
    return word_set

neg_path = 'opinion-lexicon-English/negative-words.txt'
neg_set = import_words_iso(neg_path, 35)
pos_path = 'opinion-lexicon-English/positive-words.txt'
pos_set = import_words_iso(pos_path, 35)

emo_pos_set = ['lol', ':)', ':-)', ';)']
emo_neg_set = [':(', ':-(']

senti_set = pos_set + neg_set + emo_pos_set + emo_neg_set

alcohol_set = import_words_iso('alcohol word.txt', 1)
vulgar_set = import_words_iso('vulgar word.txt', 1)


remove_punctuation_map = dict()
for char in string.punctuation:
    remove_punctuation_map[ord(char)] = None

# max tweets for this search
#max_tweets = 100000
# tweets per query (limited by api)
tweets_per_qry = 100
# file to write in
#f_name = 'tweets.txt'
loc_dct = defaultdict(dict)
loc_dct['melbourne']['latitude'] = -37.814
loc_dct['melbourne']['longitude'] = 144.96332
loc_dct['sydney']['latitude'] = -33.86785
loc_dct['sydney']['longitude'] = 151.20732
latitude = loc_dct[search_loc]['latitude']
longitude = loc_dct[search_loc]['longitude']
radius = 25

sinceId = None
max_id = -1

# get the city id to search (here melbourne)
#places = api.geo_search(query='Melbourne', granularity='city')
#place_id = places[0].id

tweet_count = 0
#senti_count = {}
#print("Downloading max {0} tweets".format(max_tweets))

while True:
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
            tweet_str = jsonpickle.encode(tweet._json, unpicklable=False)
            tweet_dct = json.loads(tweet_str)
            text = tweet_dct['text'].lower().translate(remove_punctuation_map)
            tweet_dct_truncated = {}
            senti = False
            vulgar = False
            alcohol = False
            education = False
            for word in senti_set:
                if ' '+word+' ' in text:
                    senti = True
                    #senti_count[word] = senti_count.get(word, 0) + 1
                    tweet_dct_truncated['sentiment'] = 'available'
                    break
            for word in vulgar_set:
                if ' '+word+' ' in text:
                    vulgar = True
                    tweet_dct_truncated['vulgar'] = 'available'
                    break
            for word in alcohol_set:
                if ' '+word+' ' in text:
                    alcohol = True
                    tweet_dct_truncated['alcohol'] = 'available'
                    break
                elif re.search('wine$', word):
                    word_list = word.split()
                    phrase = word_list[0]
                    for i in range(1, len(word_list)-1):
                        phrase = phrase + ' ' + word_list[i]
                    if ' '+phrase+' ' in text and ' wine ' in text:
                        alcohol = True
                        tweet_dct_truncated['alcohol'] = 'available'
                        break
            if ' education ' in text:
                education = True
                tweet_dct_truncated['education'] = 'available'

            if senti is False and vulgar is False and alcohol is False and education is False:
                continue
            #change int to string
            tweet_dct_truncated['_id'] = str(tweet_dct['id'])
            tweet_dct_truncated['created_at'] = tweet_dct['created_at']
            tweet_dct_truncated['coordinates'] = tweet_dct['coordinates']
            tweet_dct_truncated['text'] = tweet_dct['text']
            tweet_dct_truncated['place'] = tweet_dct['place']
            tweet_dct_truncated['entities'] = tweet_dct['entities']
            #tweet_json = json.dumps(tweet_dct_truncated)
            #print(tweet_json)
            try:
                db.save(tweet_dct_truncated)
            except Exception as e:
                #print (str(e) +" One repetitive tweet has been excluded")
                print("warning! "+ str(e))
            #f.write(json.dumps(tweet_dct_truncated) + '\n')
        tweet_count += len(new_tweets)
        print ("Downloaded {0} tweets".format(tweet_count))
        max_id = new_tweets[-1].id
    except tweepy.TweepError as e:
        # exit if any error
        print("some error : " + str(e))
        break

#print ("Downloaded {0} tweets, Saved to {1}".format(tweet_count, f_name))
