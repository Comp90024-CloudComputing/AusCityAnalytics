import re
import sys
import json
import codecs
import string
from tweepy import Stream
from itertools import islice
from tweepy import OAuthHandler
from tweepy.streaming import StreamListener

consumer_key = 'zfcB3Zj5WRp9f1pAHwJdtfiHm'
consumer_secret = 'CWn46FyN3o9jfRePrgNrJwX9VzspR1t38c1Wp5bGLSej0IpETh'
access_token = '2886866490-a9gpG72J31Q8WXK2gUa4KGqBWPbUF0QxIOHrUgl'
access_secret = 'ySpil1O2e2c7qL7zVWCfVZojKiWLDNwT271b44WNVePHt'

auth = OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_secret)


search_loc = str(sys.argv[1])
# approximate bounding boxes for melbourne, sydney, adelaide, brisbane and perth
mel_box = [144.5937, -38.4339, 145.5125, -37.5113]
syd_box = [150.5209, -34.1183, 151.3430, -33.5781]
loc_dct = {}
loc_dct['melbourne'] = mel_box
loc_dct['sydney'] = syd_box
#ade_box = [138.4421, -35.3490, 138.7802, -34.6526]
#bri_box = [152.6685, -27.7674, 153.3179, -26.9968]
#per_box = [115.6840, -32.4556, 116.2390, -31.6245]
loc_box = loc_dct[search_loc]

def import_words(file_path, start_line):
    word_set = []
    with open(file_path, 'r') as infile:
        for line in islice(infile, start_line, None):
            word_set.append(line.rstrip())
    return word_set

def import_words_utf8(file_path, start_line):
    word_set = []
    with codecs.open(file_path, 'r', 'utf-8') as infile:
        for line in islice(infile, start_line, None):
            word_set.append(line.rstrip())
    return word_set

neg_path = 'opinion-lexicon-English/negative-words.txt'
neg_set = import_words(neg_path, 35)
pos_path = 'opinion-lexicon-English/positive-words.txt'
pos_set = import_words(pos_path, 35)

emo_pos_set = ['lol', ':)', ':-)', ';)']
emo_neg_set = [':(', ':-(']

senti_set = pos_set + neg_set + emo_pos_set + emo_neg_set

alcohol_set = import_words_utf8('alcohol word.txt', 1)
vulgar_set = import_words_utf8('vulgar word.txt', 1)


remove_punctuation_map = dict()
for char in string.punctuation:
    remove_punctuation_map[ord(char)] = None

class MyListener(StreamListener):

    # write data into file
    def on_data(self, data):
        try:
            with open('python.json', 'a') as f:
                tweet_dct = json.loads(data)
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
                if senti is True or vulgar is True or alcohol is True or education is True:
                    tweet_dct_truncated['id'] = tweet_dct['id']
                    tweet_dct_truncated['created_at'] = tweet_dct['created_at']
                    tweet_dct_truncated['coordinates'] = tweet_dct['coordinates']
                    tweet_dct_truncated['text'] = tweet_dct['text']
                    tweet_dct_truncated['place'] = tweet_dct['place']
                    tweet_dct_truncated['entities'] = tweet_dct['entities']
                    f.write(json.dumps(tweet_dct_truncated) + '\n')
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
