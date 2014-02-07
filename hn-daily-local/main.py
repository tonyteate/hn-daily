import webapp2
import json
from uuid import uuid4
import os
import jinja2
import logging
from datetime import datetime, timedelta
from n2sh import n2sh
import random

from google.appengine.api import memcache
from google.appengine.ext import ndb
from google.appengine.api import urlfetch

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape=False)

getnewsurl = "http://hn-daily-remote.appspot.com/page"

mem_key = 'hackernews'
mem_count = 'requestcount'




#https://developers.google.com/appengine/articles/sharding_counters
NUM_SHARDS = 20

class SimpleCounterShard(ndb.Model):
    """Shards for the counter"""
    count = ndb.IntegerProperty(default=0)

def get_count():
    """Retrieve the value for a given sharded counter.

    Returns:
        Integer; the cumulative count of all sharded counters.
    """
    total = memcache.get(mem_count)
    if total is None:
        total = 0
        for counter in SimpleCounterShard.query():
            total += counter.count
        memcache.set(mem_count, total)
    return total

def increment_counter():

    """Increment the value for a given sharded counter."""

    @ndb.transactional
    def increment():
        shard_string_index = str(random.randint(0, NUM_SHARDS - 1))
        counter = SimpleCounterShard.get_by_id(shard_string_index)
        if counter is None:
            counter = SimpleCounterShard(id=shard_string_index)
        counter.count += 1
        counter.put()

    increment()

    if memcache.get(mem_count) is None:
        get_count()
    memcache.incr(mem_count)




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
    
    def render_front(self, posts=[], req_count=2.7e6):

        self.render("front.html", posts=posts, req_count=req_count)

    def get(self):

        increment_counter()
        req_count = memcache.get(mem_count)
        if req_count is None: #shouldn't really happen
            req_count = 1

        post_objs = []

        content = memcache.get(mem_key)

        if not content:

            logging.error("FETCHING!")

            result = urlfetch.fetch(url=getnewsurl, headers={'User-Agent': 'Mozilla/5.0'})

            logging.error("GETNEWSHANDLER STATUS: %s" %result.status_code)

            if result.status_code == 200:
                content = result.content
                memcache.set(mem_key, content)

        jdata = json.loads(content)
        posts = jdata.get('items')

        self.render_front(posts=posts, req_count=req_count)

class FlushHandler(Handler):

    # should probably be a POST w/ Authentication
    def get(self):

        token = self.request.get("token")

        if not token:
            return
        elif token != "Pn67W1NpbCH38UlMBznYmeuPico3cdQ8":
            return

        memcache.delete(mem_key)


app = webapp2.WSGIApplication([ ('/', MainPage),
                                ('/flush', FlushHandler),
                                ], debug=True)






