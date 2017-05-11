"""
Team 23
Yidan Gao       617313
Shikai Huang    747544
Jie Xu          685820
Yijie Zhang     744684
Yuxin Zhang     666473
"""

import re
import sys
import json
import nltk
import codecs
import string
import couchdb
from tweepy import Stream
from itertools import islice
from tweepy import OAuthHandler
from nltk.corpus import stopwords
from shapely.geometry import shape
from tweepy.streaming import StreamListener
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


consumer_key = 'zfcB3Zj5WRp9f1pAHwJdtfiHm'
consumer_secret = 'CWn46FyN3o9jfRePrgNrJwX9VzspR1t38c1Wp5bGLSej0IpETh'
access_token = '2886866490-a9gpG72J31Q8WXK2gUa4KGqBWPbUF0QxIOHrUgl'
access_secret = 'ySpil1O2e2c7qL7zVWCfVZojKiWLDNwT271b44WNVePHt'

auth = OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_secret)


# get search location
search_loc = str(sys.argv[1])

# create a new database if it not exists
server = couchdb.Server("http://admin:password@localhost:5984/")
try:
    server.create(search_loc)
except Exception as e:
    print (str(e)+" The database exists")

# specify server (every city has its dbserver)
db = server[search_loc]

# approximate bounding boxes for melbourne, sydney, adelaide, brisbane and perth
mel_box = [144.5937, -38.4339, 145.5125, -37.5113]
syd_box = [150.5209, -34.1183, 151.3430, -33.5781]
ade_box = [138.4421, -35.3490, 138.7802, -34.6526]
bri_box = [152.6685, -27.7674, 153.3179, -26.9968]
per_box = [115.6840, -32.4556, 116.2390, -31.6245]
loc_dct = {}
loc_dct['melbourne'] = mel_box
loc_dct['sydney'] = syd_box
loc_dct['adelaide'] = ade_box
loc_dct['brisbane'] = bri_box
loc_dct['perth'] = per_box
loc_box = loc_dct[search_loc]

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
    with codecs.open(file_path, 'r', encoding='ISO-8859-1') as infile:
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


class MyListener(StreamListener):

    # write data into file
    def on_data(self, data):
        try:
            with open('python2.json', 'a') as f:
                tweet_dct = json.loads(data)
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

                tweet_dct_truncated['_id'] = str(tweet_dct['id'])
                tweet_dct_truncated['created_at'] = tweet_dct['created_at']
                tweet_dct_truncated['coordinates'] = tweet_dct['coordinates']
                tweet_dct_truncated['text'] = tweet_dct['text']
                tweet_dct_truncated['place'] = tweet_dct['place']
                tweet_dct_truncated['sentiment_nb'] = senti_nb
                tweet_dct_truncated['sentiment_vader'] = senti_vd
                tweet_dct_truncated['sentiment_simple'] = senti_sp
                try:
                    db.save(tweet_dct_truncated)
                except Exception as e:
                    print("warning! "+ str(e))
                return True
        except BaseException as e:
            print('Error on_data: %s' % str(e))
        return True

    # handle error
    def on_error(self, status):
        print(status)
        return True

    # handle timeout
    def on_timeout(self):
        print('Timeout. Stream restarted.')
        return True

    # handle disconnection
    def on_disconnect(self, notice):
        print(notice)
        return True

twitter_stream = Stream(auth, MyListener())
twitter_stream.filter(locations=[loc_box[0], loc_box[1], loc_box[2], loc_box[3]])
