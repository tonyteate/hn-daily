import webapp2
import json
import os
import logging
from datetime import datetime, timedelta
from urlparse import urlparse

from google.appengine.ext import ndb
from google.appengine.api import urlfetch

getnewsurl = "http://api.ihackernews.com/page"
#http://hn-daily.appspot.com/samplenews

flushnewsurl = "http://hn-daily.appspot.com/flush"

#redundant in both apps
class Post(ndb.Model):
    title = ndb.StringProperty(required = True)
    url = ndb.StringProperty(required = True) 
    eid = ndb.IntegerProperty(required = True)
    comments = ndb.IntegerProperty(required = True)
    points = ndb.IntegerProperty(required = True)
    ago = ndb.StringProperty(required = False)
    by = ndb.StringProperty(required = False)

    created = ndb.DateTimeProperty(auto_now_add = True, required = True)
    lastmodified = ndb.DateTimeProperty(auto_now = True)

class Set(ndb.Model):

    eids = ndb.IntegerProperty(repeated = True)

    day = ndb.IntegerProperty(required = True)
    month = ndb.IntegerProperty(required = True)
    year = ndb.IntegerProperty(required = True)
    hour = ndb.IntegerProperty(required = True)
    minute = ndb.IntegerProperty(required = True)    

    date = ndb.DateTimeProperty(required = True) #no minute, no second, no microsecond
    created = ndb.DateTimeProperty(auto_now_add = True, required = True)    

class GetNewsHandler(webapp2.RequestHandler):

    def get(self):

        result = urlfetch.fetch(url=getnewsurl, headers={'User-Agent': 'Mozilla/5.0'})

        logging.error("GETNEWSHANDLER STATUS: %s" %result.status_code)

        if result.status_code == 200:
            data = json.loads(result.content)
            posts = data.get('items')

            if posts:
                now = datetime.utcnow()

                new_posts = []
                for post in posts:
                    p = Post(title=post.get('title'), url=post.get('url'), eid=post.get('id'), 
                            comments=post.get('commentCount'), points=post.get('points'), ago=post.get('postedAgo'), 
                            by=post.get('postedBy'))
                    new_posts.append(p)

                logging.error("NEW POSTS: %s" %len(new_posts))

                new_posts_ids = [new_post.eid for new_post in new_posts]

                set_dt = datetime(now.year, now.month, now.day, now.hour, 0, 0, 0)

                s = Set(eids=new_posts_ids, day=now.day, month=now.month, year=now.year, 
                        hour=now.hour, minute=now.minute, date=set_dt).put()

                same_posts = list(Post.query(Post.eid.IN(new_posts_ids)))
                same_posts_ids = [same_post.eid for same_post in same_posts]

                logging.error("SAME POSTS: %s" %len(same_posts))

                #update all Posts properties except key & created
                new_posts_dict = dict(zip(new_posts_ids, new_posts))
                for same_post in same_posts:
                    sp = new_posts_dict[same_post.eid]
                    sp.key = same_post.key
                    sp.created = same_post.created

                #new_posts = filter(lambda x: x.eid not in same_posts_ids, new_posts)

                if len(new_posts) - len(same_posts) > 0:
                    # should probably be a POST w/ Authentication
                    urlfetch.fetch(url=flushnewsurl, headers={'User-Agent': 'Mozilla/5.0'})                   

                logging.error("NEW POSTS - SAME POSTS: %s" %(len(new_posts)-len(same_posts))) #%len(new_posts))

                ndb.put_multi(new_posts)

class PageHandler(webapp2.RequestHandler):

    def get(self):

        now = datetime.utcnow()
        logging.error("NOW: %s" %now)

        ref_hour = 15 #10AM ET
        ref = datetime(year=now.year, month=now.month, day=now.day, 
                        hour=ref_hour, minute=now.minute, second=now.second, microsecond=now.microsecond)

        delta = now - ref
        if delta.days < 0:
            ref = ref - timedelta(days=1)          
            delta = now - ref            

        delta_hours = int(delta.total_seconds() / 3600) #float?
        delta_range = [(now-timedelta(hours=h)).replace(minute=0, second=0, microsecond=0) for h in range(delta_hours+1)]

        logging.error(delta_range)

        sets = []
        if delta_range:
            sets = Set.query(Set.date.IN(delta_range))
            sets = list(sets)

        logging.error(len(sets))

        posts_eids = []
        [posts_eids.extend(s.eids) for s in sets]
        posts_eids = list(set(posts_eids))

        jposts = []
        if posts_eids:
            posts = list(Post.query(Post.eid.IN(posts_eids)).order(-Post.points))

            for post in posts:
                jpost = {'title':post.title, 'url':post.url, 'eid':post.eid, 'comments':post.comments,
                            'points':post.points, 'ago':post.ago, 'by':post.by,
                            'domain':urlparse(post.url).netloc.replace('www.','')}
                jposts.append(jpost)

        jdata = {'success':'is what you make it', 'items':jposts}

        self.response.headers['Content-Type'] = 'application/json'  
        self.response.out.write(json.dumps(jdata))            



class ClearAllHandler(webapp2.RequestHandler):

    def get(self):
        while Post.query().count() > 0:
            keys = Post.query().fetch(1000, keys_only=True)
            num = len(keys)
            ndb.delete_multi(keys)
            logging.error("%s Post objects deleted" %num)
        logging.error("I just deleted some Post stuff....")

        while Set.query().count() > 0:
            keys = Set.query().fetch(1000, keys_only=True)
            num = len(keys)
            ndb.delete_multi(keys)
            logging.error("%s Set objects deleted" %num)      
        logging.error("I just deleted some Set stuff....")


class SampleNewsHandler(webapp2.RequestHandler):

    def get(self):
        content = open("sample.json").read()
        self.response.headers['Content-Type'] = 'application/json'          
        self.response.out.write(content)

class KeepAliveHandler(webapp2.RequestHandler):

    def get(self):

        self.response.out.write("I'm Alive!")        

class WelcomeHandler(webapp2.RequestHandler):

    def get(self): 

        self.response.out.write("Why are <b><em>you</em></b> here? "*10000+"<h6>Still here? You must be a pretty cool person :)</h6>")
                    


app = webapp2.WSGIApplication([ ('/', WelcomeHandler),
                                ('/keepalive', KeepAliveHandler),
                                ('/getnews', GetNewsHandler),
                                ('/samplenews', SampleNewsHandler),
                                ('/clearall', ClearAllHandler),
                                ('/page', PageHandler),                                
                                ], debug=True)






