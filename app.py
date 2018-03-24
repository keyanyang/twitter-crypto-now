import time
from tweepy import Stream
from tweepy import OAuthHandler
from tweepy.streaming import StreamListener
import json
from multiprocessing import Process
import re
import threading

import nltk
from nltk.tokenize import TweetTokenizer
from collections import Counter

from threading import Thread, Event
from flask import Flask, render_template, url_for, copy_current_request_context, request
from flask_socketio import SocketIO, emit

nltk.data.path.append('./nltk_data')
#######################################
app = Flask(__name__)

#turn the flask app into a socketio app
socketio = SocketIO(app)


#random number Generator Thread
thread = Thread()
thread_stop_event = Event()


@app.route('/')
def index():
    #only by sending this page first will the client be connected to the socketio instance
    return render_template('index.html')

@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected')

###################################
secrets = json.load(open('secrets.json'))

consumer_key = secrets['consumer_key']
consumer_secret = secrets['consumer_secret']
access_token = secrets['access_token']
access_token_secret = secrets['access_token_secret']

stopwords = set(nltk.corpus.stopwords.words('english'))

more_stopwords = ['#', '.', ':', '/', 'https', '://', 'co', 'followers_count', '--------------------',
'$', 'ð', '@', '|', ',', "'", 'â', '!', 'ï', '?', 'ã', 'get', '\\', 'rt',
'-', 'tweets', 'đ', 'ď', 'ă', '%', ')', '(', '[', ']', '&', '"', '’', '️', '...', 'de', '🚀', '🔥', '=',
'1', '2', '3', '、', '？',
'cryptocurrency', 'crypto',
'bitcoin', 'btc'
]
stopwords.update(more_stopwords)


class MyStreamListener(StreamListener):

    def on_data(self, data):
        global count, tweets, counter
        try:
            if 'text' in data:
                tweet_data = json.loads(data)

                if "extended_tweet" in tweet_data:
                    text = tweet_data['extended_tweet']['full_text']
                elif 'retweeted_status' in tweet_data:
                    try:
                        text = tweet_data['retweeted_status']['extended_tweet']['full_text']
                    except KeyError:
                        text = tweet_data['text']
                elif 'quoted_status' in tweet_data:
                    try:
                        text = tweet_data['quoted_status']['extended_tweet']['full_text']
                    except KeyError:
                        text = tweet_data['text']
                else:
                    text = tweet_data['text']

                count += 1
                content_text(text)
        except KeyboardInterrupt:
            return False

    def on_error(self, status_code):
        try:
            print(status_code)
        except KeyboardInterrupt:
            return False



@socketio.on('connect', namespace='/test')
def handle_emit():
    global count, counter

    # print(f"The number of tweets mentioned during the last minute:", count)
    # print("Most common:", counter.most_common(10))
    # print(time.ctime(), '\n')

    ln = time.ctime() + '\n' + 'Amount: ' + str(count) + '\n' + 'Top words: ' + str([item for item in counter.most_common(5)])
    # print(ln)
    socketio.emit('newnumber', {'number': ln}, namespace='/test')

    count = 0
    counter = Counter()
    t = threading.Timer(5, handle_emit)
    t.start()


# def print_cnt(kw):
#     global count, tweets, counter
#     try:
#         print(f"The number of tweets mentioned \'{kw}\' during the last minute:", count)
#         print("Most common:", counter.most_common(10))
#         print(time.ctime(), '\n')
#         emit('newnumber', {'number': count}, namespace='/test')
#         count = 0
#         tweets = ''
#         counter = Counter()
#         threading.Timer(10, print_cnt, [kw]).start()
#     except KeyboardInterrupt:
#         return False

def content_text(text):
    global counter
    text = set(tknzr.tokenize(text))
    text = set(w for w in text if not re.compile("^#.*$").match(w))
    for word in text:
        word = word.lower()
        if word not in stopwords:
            counter[word] += 1

def startWebserver():
    socketio.run(app)

if __name__ == '__main__':

    Thread(target=startWebserver).start()

    auth = OAuthHandler(consumer_key, consumer_secret)  # OAuth object
    auth.set_access_token(access_token, access_token_secret)

    myStreamListener = MyStreamListener()
    stream = Stream(auth=auth, listener=myStreamListener, tweet_mode='extended')

    count = 0
    counter = Counter()
    tweets = ""
    tknzr = TweetTokenizer(preserve_case=False, strip_handles=True, reduce_len=True)

    p1_2 = Thread(target=stream.filter(track=['Bitcoin']))
    p1_2.start()

    Thread(target=handle_emit).start()
