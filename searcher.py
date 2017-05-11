import re
import sys
import json
import nltk
import tweepy
import codecs
import string
import couchdb
import jsonpickle
from itertools import islice
from tweepy import OAuthHandler
from nltk.corpus import stopwords
from shapely.geometry import shape
from collections import defaultdict
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


consumer_key = 'zfcB3Zj5WRp9f1pAHwJdtfiHm'
consumer_secret = 'CWn46FyN3o9jfRePrgNrJwX9VzspR1t38c1Wp5bGLSej0IpETh'
access_token = '2886866490-a9gpG72J31Q8WXK2gUa4KGqBWPbUF0QxIOHrUgl'
access_secret = 'ySpil1O2e2c7qL7zVWCfVZojKiWLDNwT271b44WNVePHt'

auth = OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_secret)

api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)


# get the search location
search_loc = str(sys.argv[1])

server = couchdb.Server("http://admin:password@localhost:5984/")
try:
    server.create(sys.argv[1])
except Exception as e:
    print (str(e)+" The database exists")

# specify the server (every city has its dbserver)
db = server[sys.argv[1]]

# VADER initialization
analyzer = SentimentIntensityAnalyzer()

# fetch AURIN data
def extract_multipolygon(source):
    dct = {}
    for feature in source['features']:
        id  = feature['properties']['feature_code']
        mp = shape(feature['geometry'])
        dct[id] = mp
    return dct

nsw_income = json.load(open('nsw_SA2_income.json', 'r'))
nsw_income_dct = extract_multipolygon(nsw_income)
vic_income = json.load(open('vic_SA2_income.json', 'r'))
vic_income_dct = extract_multipolygon(vic_income)
nsw_alcohol = json.load(open('alcohol_nsw.json', 'r'))
nsw_alcohol_dct = extract_multipolygon(nsw_alcohol)
vic_alcohol = json.load(open('alcohol_vic.json', 'r'))
vic_alcohol_dct = extract_multipolygon(vic_alcohol)
if search_loc == 'melbourne':
    income_dct = vic_income_dct
    alcohol_dct = vic_alcohol_dct
elif search_loc == 'sydney':
    income_dct = nsw_income_dct
    alcohol_dct = nsw_alcohol_dct


# import lexicons
def import_words(file_path, start_line):
    word_set = []
    with open(file_path, 'r') as infile:
        for line in islice(infile, start_line, None):
            word_set.append(line.rstrip())
    return word_set

def import_words_iso(file_path, start_line):
    word_set = []
    with codecs.open(file_path, 'r', 'ISO-8859-1') as infile:
        for line in islice(infile, start_line, None):
            word_set.append(line.rstrip())
    return word_set

neg_path = 'opinion-lexicon-English/negative-words.txt'
neg_set = import_words_iso(neg_path, 35)
pos_path = 'opinion-lexicon-English/positive-words.txt'
pos_set = import_words_iso(pos_path, 35)

pos_emoticons = ['lol', ':)', ':-)', ';)', ';-)', ':D', ':-D']
neg_emoticons = [':(', ':-(']

alcohol_set = import_words_iso('alcohol word.txt', 1)
vulgar_set = import_words_iso('vulgar word.txt', 1)


# prepare for punctuation removal
remove_punctuation_map = dict()
for char in string.punctuation:
    remove_punctuation_map[ord(char)] = None


# Naive Bayes training
tweets = []
for line in open('training_set.txt', 'r'):
    tweet_data = json.loads(line)
    text = tweet_data['text']
    polarity = tweet_data['polarity']
    words = [e for e in text.split() if not any(c.isdigit() for c in e) and e not in stopwords.words('english')]
    if words == []:
        continue
    tweets.append((words, polarity))
    if len(tweets) >= 10000:
        break

def get_words_in_tweets(tweets):
    all_words = []
    for (words, sentiment) in tweets:
        all_words.extend(words)
    return all_words

def get_word_features(wordlist):
    wordlist = nltk.FreqDist(wordlist)
    word_features = wordlist.keys()
    return word_features

def extract_features(document):
    document_words = set(document)
    features = {}
    for word in word_features:
        features['contains(%s)' % word] = (word in document_words)
    return features

word_features = get_word_features(get_words_in_tweets(tweets))
training_set = nltk.classify.apply_features(extract_features, tweets)
classifier = nltk.NaiveBayesClassifier.train(training_set)


# tweets per query (limited by api)
tweets_per_qry = 100
# file to write in
#f_name = 'tweets.txt'

# city coordinates data
loc_dct = defaultdict(dict)
loc_dct['melbourne']['latitude'] = -37.814
loc_dct['melbourne']['longitude'] = 144.96332
loc_dct['sydney']['latitude'] = -33.86785
loc_dct['sydney']['longitude'] = 151.20732
loc_dct['adelaide']['latitude'] = -34.92866
loc_dct['adelaide']['longitude'] = 138.59863
loc_dct['brisbane']['latitude'] = -27.46794
loc_dct['brisbane']['longitude'] = 153.02809
loc_dct['perth']['latitude'] = -31.95224
loc_dct['perth']['longitude'] = 115.8614
latitude = loc_dct[search_loc]['latitude']
longitude = loc_dct[search_loc]['longitude']
radius = 25

sinceId = None
max_id = -1
tweet_count = 0
database_count = 0
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
            text = tweet_dct['text']

            # VADER test
            vs = analyzer.polarity_scores(text)
            compound = vs['compound']
            if compound >= 0.5:
                senti_vd = 'positive'
            elif compound <= -0.5:
                senti_vd = 'negative'
            else:
                senti_vd = 'neutral'

            # preprocess
            text = re.sub(r'http\S+', '', text.encode('ascii','ignore').decode('ascii'))
            text = re.sub('\n', '', text)
            text = re.sub(r'@\S+', '', text)
            text = re.sub(r'#\S+', '', text)
            for emoticon in pos_emoticons:
                if emoticon in text:
                    text = text.replace(emoticon, 'posemo')
            for emoticon in neg_emoticons:
                if emoticon in text:
                    text = text.replace(emoticon, 'negemo')
            text = text.lower().translate(remove_punctuation_map)

            # Naive Bayes classification
            senti_nb = classifier.classify(extract_features(text.split()))

            # Naive method approach
            score = 0
            for word in pos_set:
                if ' '+word+' ' in text:
                    score += 1
            for word in neg_set:
                if ' '+word+' ' in text:
                    score -= 1
            if score > 0:
                senti_sp = 'positive'
            elif score < 0:
                senti_sp = 'negative'
            else:
                senti_sp = 'neutral'

            #scenario tagging
            tweet_dct_truncated = {}
            for word in vulgar_set:
                if ' '+word+' ' in text:
                    tweet_dct_truncated['vulgar'] = 'available'
                    break
            alcohol = False
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
                tweet_dct_truncated['education'] = 'available'

            if tweet_dct['coordinates'] is not None:
                p = shape(tweet_dct['coordinates'])
                for id in income_dct:
                    if p.within(income_dct[id]):
                        tweet_dct_truncated['income_area'] = id
                if alcohol is True:
                    for id in alcohol_dct:
                        if p.within(alcohol_dct[id]):
                            tweet_dct_truncated['alcohol_area'] = id

            # set couchdb id equivalent to tweet id, solve duplication
            tweet_dct_truncated['_id'] = str(tweet_dct['id'])
            tweet_dct_truncated['created_at'] = tweet_dct['created_at']
            tweet_dct_truncated['coordinates'] = tweet_dct['coordinates']
            tweet_dct_truncated['text'] = tweet_dct['text']
            tweet_dct_truncated['place'] = tweet_dct['place']
            tweet_dct_truncated['sentiment_nb'] = senti_nb
            tweet_dct_truncated['sentiment_vader'] = senti_vd
            tweet_dct_truncated['sentiment_simple'] = senti_sp
            #f.write(json.dumps(tweet_dct_truncated) + '\n')
            try:
                db.save(tweet_dct_truncated)
                database_count += 1
                print(str(database_count)+ "tweets inserted into database " + search_loc)
            except Exception as e:
                #print (str(e) +" One repetitive tweet has been excluded")
                print("warning! "+ str(e))
        tweet_count += len(new_tweets)
        print("Downloaded {0} tweets".format(tweet_count))
        max_id = new_tweets[-1].id
    except tweepy.TweepError as e:
        # exit if any error
        print("some error : " + str(e))
        break
