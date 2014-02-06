import webapp2
import json
from uuid import uuid4
import os
import jinja2
import logging
from datetime import datetime, timedelta
from n2sh import n2sh

from google.appengine.api import memcache
from google.appengine.ext import ndb
from google.appengine.api import urlfetch

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape=False)

getnewsurl = "http://hn-daily-remote.appspot.com/page"

mem_key = 'hackernews'
mem_count = 'requestcount'

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

        # req_count = int(2.7e6) #memcache.get(mem_count)
        req_count = memcache.get(mem_count)
        if not req_count:
            req_count = 1
        else:
            req_count = req_count + 1
        memcache.set(mem_count, req_count)

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

        memcache.delete(mem_key)


app = webapp2.WSGIApplication([ ('/', MainPage),
                                ('/flush', FlushHandler),
                                ], debug=True)






