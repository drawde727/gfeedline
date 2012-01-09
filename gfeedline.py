#!/usr/bin/env python

from lib import gtk3reactor
gtk3reactor.install()
from twisted.internet import reactor

import os
import sys
from BeautifulSoup import BeautifulStoneSoup

from gi.repository import Gtk, WebKit, GLib, GObject

import dateutil.parser
from twittytwister import twitter
from oauth import oauth

consumer = oauth.OAuthConsumer(sys.argv[1], sys.argv[2])
token = oauth.OAuthToken(sys.argv[3], sys.argv[4])

class MainWindow(object):

    def __init__(self):

        gui = Gtk.Builder()
        gui.add_from_file(os.path.abspath('gfeedline.glade'))

        self.window = window = gui.get_object('window1')
        notebook = gui.get_object('notebook1')
        menubar = gui.get_object('menubar1')
        self.sw = gui.get_object('scrolledwindow1')

        window.resize(480, 600)
        window.connect("delete-event", self.stop)
        window.show_all()
        menubar.hide()

    def stop(self, *args):
        reactor.stop()

class FeedWebKit(object):

    def __init__(self, parent):

        self.w = w = WebKit.WebView()
        w.load_uri("file://%s" % os.path.abspath('base.html')) 

        parent.sw.add(self.w)
        self.w.show_all()

    def update(self, text=None):
        text = text.replace('\n', '<br>')
        js = 'append("%s")' % text
        print js
        self.w.execute_script(js)

class TwitterTime(object):

    def __init__(self, utc_str):
        dt = dateutil.parser.parse(utc_str)
        self.datetime = dt.replace(tzinfo=dateutil.tz.tzutc()
                                   ).astimezone(dateutil.tz.tzlocal())

    def get_local_time(self):
        return self.datetime.strftime('%H:%M:%S')

class HomeTimeline(object):

    def __init__(self, win=None):
        self.all_entries = []
        self.last_id = 0
        self.win = win

    def got_entry(self, msg, *args):
        self.all_entries.append(msg)

    def conv(self, text):
        #return text
        return BeautifulStoneSoup(
            text, convertEntities=BeautifulStoneSoup.HTML_ENTITIES)

    def print_entry(self):
        for entry in reversed(self.all_entries):
            time = TwitterTime(entry.created_at)

            text = "%s %s %s " % (time.get_local_time(), 
                                  entry.user.screen_name, self.conv(entry.text))
            #print text
            self.last_id = entry.id
            self.win.update(text)

        self.all_entries = []

    def error(self, e):
        print e

    def start(self):
        params = {'since_id': str(self.last_id)} if self.last_id else {}
        twitter.Twitter(consumer=consumer, token=token).\
            home_timeline(self.got_entry, params).\
            addErrback(self.error).\
            addBoth(lambda x: self.print_entry())

        GLib.timeout_add_seconds(30, self.start)

main = MainWindow()
w = FeedWebKit(main)
home = HomeTimeline(w)
home.start()

reactor.run()
