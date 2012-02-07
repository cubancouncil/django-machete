from datetime import datetime
from urllib import urlencode
from urllib2 import urlopen
import simplejson

def get_tweets(screen_name, *args, **kwargs):
    
    """
    Get tweets from a specified user's timeline. GET parameters can be passed
    as keyword arguments, see available options here:
    
    https://dev.twitter.com/docs/api/1/get/statuses/user_timeline
    
    """
    
    try:
        qs = kwargs.copy()
        qs['screen_name'] = screen_name
        url = 'http://api.twitter.com/1/statuses/user_timeline.json?%s' % urlencode(qs)
        request = urlopen(url, None, 5)
        tweets = simplejson.loads(request.read())
        if tweets:
            for tweet in tweets:
                idx = tweets.index(tweet)
                # Convert 'Thu Dec 22 19:30:11 +0000 2011'-style date to Python-friendly date
                tweets[idx]['created_at'] = datetime.strptime(tweets[idx]['created_at'], '%a %b %d %H:%M:%S +0000 %Y')
        return tweets
    except:
        return None