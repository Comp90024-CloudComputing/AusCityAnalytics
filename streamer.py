import tweepy
from tweepy import OAuthHandler
from tweepy import Stream
from tweepy.streaming import StreamListener

consumer_key = 'zfcB3Zj5WRp9f1pAHwJdtfiHm'
consumer_secret = 'CWn46FyN3o9jfRePrgNrJwX9VzspR1t38c1Wp5bGLSej0IpETh'
access_token = '2886866490-a9gpG72J31Q8WXK2gUa4KGqBWPbUF0QxIOHrUgl'
access_secret = 'ySpil1O2e2c7qL7zVWCfVZojKiWLDNwT271b44WNVePHt'

auth = OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_secret)

# approximate bounding boxes for melbourne, sydney, adelaide, brisbane and perth
mel_box = [144.5937, -38.4339, 145.5125, -37.5113]
syd_box = [150.5209, -34.1183, 151.3430, -33.5781]
ade_box = [138.4421, -35.3490, 138.7802, -34.6526]
bri_box = [152.6685, -27.7674, 153.3179, -26.9968]
per_box = [115.6840, -32.4556, 116.2390, -31.6245]

class MyListener(StreamListener):

    # write data into file
    def on_data(self, data):
        try:
            with open('python.json', 'a') as f:
                f.write(data)
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
# specify the city to stream
box = mel_box
twitter_stream.filter(locations=[box[0], box[1], box[2], box[3]])
