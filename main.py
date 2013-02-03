
import webapp2
import json
#import re
#import random
from uuid import uuid4
import os
import jinja2
import logging
from datetime import datetime
#import cgi
#import urllib
#from urlparse import parse_qs

from google.appengine.ext import ndb
from google.appengine.api import urlfetch

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape=False)

getnewsurl = "http://api.ihackernews.com/page"

def parse_query_string(q):
    p = parse_qs(q)
    for s in p:
        p[s] = p[s][0]
    return p

class Post(ndb.Model):
    title = ndb.StringProperty(required = True)
    url = ndb.StringProperty(required = True) 
    eid = ndb.IntegerProperty(required = True)
    comments = ndb.IntegerProperty(required = True)
    points = ndb.IntegerProperty(required = True)
    ago = ndb.StringProperty(required = False)
    by = ndb.StringProperty(required = True)

    day = ndb.IntegerProperty(required = True)
    month = ndb.IntegerProperty(required = True)
    year = ndb.IntegerProperty(required = True)
    hour = ndb.IntegerProperty(required = True)
    minute = ndb.IntegerProperty(required = True)

    created = ndb.DateTimeProperty(auto_now_add = True, required = True)
    lastmodified = ndb.DateTimeProperty(auto_now = True)


class Handler(webapp2.RequestHandler):

    def write(self, *a, **kw):

        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):

        t = jinja_env.get_template(template)
        return t.render(params)
    
    def render(self, template, **kw):

        self.write(self.render_str(template, **kw))

    def writejson(self, success, data):

        self.response.headers['Content-Type'] = 'application/json'  
        jdata = {'success':success, 'data':data}       
        self.write(json.dumps(jdata))


class MainPage(Handler):
    
    def render_front(self):
        # messages = Message.query().order(-Message.lastmodified)
        self.render("front.html")
        one = Post.query().order(Post.created).get()
        self.write(one.title)

    def get(self, json=""):
        self.render_front()

class GetNewsHandler(Handler):

    def get(self):

        result = urlfetch.fetch(url=getnewsurl,
                                headers={'User-Agent': 'Mozilla/5.0'})

        logging.error(result.status_code)

        if result.status_code == 200:
            data = json.loads(result.content)
            posts = data.get('items')

            if posts:
                now = datetime.now()

                new_posts = []
                for post in posts:
                    p = Post(title=post.get('title'), url=post.get('url'), eid=post.get('id'), 
                            comments=post.get('commentCount'), points=post.get('points'), ago=post.get('postedAgo'), 
                            by=post.get('postedBy'), day=now.day, month=now.month, year=now.year, 
                            hour=now.hour, minute=now.minute)
                    new_posts.append(p)

                logging.error("NEW POSTS: %s" %len(new_posts))

                new_posts_ids = [new_post.eid for new_post in new_posts]

                same_posts = list(Post.query(Post.eid.IN(new_posts_ids)))
                same_posts_ids = [same_post.eid for same_post in same_posts]

                logging.error("SAME POSTS: %s" %len(same_posts))

                new_posts = filter(lambda x: x.eid not in same_posts_ids, new_posts)
                ndb.put_multi(new_posts)


class SampleNewsHandler(Handler):

    def get(self):
        self.render("sample.json")

class WelcomeHandler(Handler):

    def get(self): 

        self.response.out.write("Welcome!")
                    

app = webapp2.WSGIApplication([ ('/(/?\.json)?', MainPage),
                                ('/getnews', GetNewsHandler),
                                ('/samplenews', SampleNewsHandler),
                                ], debug=True)






