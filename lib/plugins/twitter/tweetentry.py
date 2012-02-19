import re
import time
from datetime import datetime, timedelta
from xml.sax.saxutils import escape

import dateutil.parser

from ...utils.usercolor import UserColor
from ...utils.htmlentities import decode_html_entities

user_color = UserColor()


class TweetEntry(object):

    def __init__(self, entry):
        self.retweet_icon = ''

        self.entry=entry

    def get_dict(self, api):
        entry = self.entry

        body, body_string = self._get_body(entry.text)
        time = TwitterTime(entry.created_at)
        user = entry.sender if api.name == _('Direct Messages') else entry.user

        text = dict(
            date_time=time.get_local_time(),
            id=entry.id,
            image_uri=user.profile_image_url,
            retweet=self.retweet_icon,
            user_name=user.screen_name,
            user_color=user_color.get(user.screen_name),

            status_body=body,
            popup_body=body_string,
            )

        return text

    def _get_body(self, text):
        body_string = decode_html_entities(text)
        body = add_markup.convert(body_string) # add_markup is global

        return body, body_string

class RestRetweetEntry(TweetEntry):

    def __init__(self, entry):
        self.retweet_icon = "<img src='retweet.png' width='18' height='14'>"

        self.entry=entry.retweeted_status

class FeedRetweetEntry(RestRetweetEntry):

    def __init__(self, entry):
        super(FeedRetweetEntry, self).__init__(entry)

        self.entry=DictObj(entry.raw.get('retweeted_status'))
        self.entry.user=DictObj(self.entry.user)

class SearchTweetEntry(TweetEntry):

    def get_dict(self, api):
        entry = self.entry

        time = TwitterTime(entry.published)
        body, body_string = self._get_body(entry.title)

        name = entry.author.name.split(' ')[0]
        entry_id = entry.id.split(':')[2]

        text = dict(
            date_time=time.get_local_time(),
            id=entry_id,
            image_uri=entry.image,
            retweet='',
            user_name=name,
            user_color=user_color.get(name),
            status_body=body,
            popup_body=body_string)

        return text

class DictObj(object):

    def __init__(self, d):
        self.d = d

    def __getattr__(self, m):
        return self.d.get(m, None)

class TwitterTime(object):

    def __init__(self, utc_str):
        self.utc = dateutil.parser.parse(utc_str).replace(tzinfo=None)
        self.local_time = self.utc.replace(tzinfo=dateutil.tz.tzutc()
                                   ).astimezone(dateutil.tz.tzlocal())

    def get_local_time(self):
        datetime_format = '%y-%m-%d' \
            if datetime.utcnow() - self.utc >= timedelta(days=1) \
            else '%H:%M:%S'

        return self.local_time.strftime(datetime_format)

class AddedHtmlMarkup(object):

    def __init__(self):
        self.link_pattern = re.compile(
            r"(s?https?://[-_.!~*'a-zA-Z0-9;/?:@&=+$,%#]+)", 
            re.IGNORECASE | re.DOTALL)
        self.nick_pattern = re.compile("\B@([A-Za-z0-9_]+|@[A-Za-z0-9_]$)")
        self.hash_pattern = re.compile(
            u'(?:#|\uFF03)([a-zA-Z0-9_\u3041-\u3094\u3099-\u309C\u30A1-\u30FA\u3400-\uD7FF\uFF10-\uFF19\uFF20-\uFF3A\uFF41-\uFF5A\uFF66-\uFF9E]+)')

    def convert(self, text):
        text = escape(text, {"'": '&apos;'}) # Important!

        text = self.link_pattern.sub(r"<a href='\1'>\1</a>", text)
        text = self.nick_pattern.sub(r"<a href='https://twitter.com/\1'>@\1</a>", 
                                     text)
        text = self.hash_pattern.sub(
            r"<a href='https://twitter.com/search?q=%23\1'>#\1</a>", text)

        text = text.replace('"', '&quot;')
        text = text.replace('\n', '<br>')

        return text

add_markup = AddedHtmlMarkup()
