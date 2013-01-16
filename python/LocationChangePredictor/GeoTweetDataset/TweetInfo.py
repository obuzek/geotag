from . import User, Place
import Coordinates

from email.utils import parsedate_tz,mktime_tz,formatdate
from time import struct_time
import calendar
import datetime

class TweetInfo:

    # u'coordinates': {u'coordinates': [-99.155480800000007, 19.403500319999999],
    #                 u'type': u'Point'}
    # u'geo': {u'coordinates': [19.403500319999999, -99.155480800000007],
    #                 u'type': u'Point'},
    # u'id': 156246300290060288,
    # u'id_str': u'156246300290060288',
    # u'place': {u'attributes': {},
    #            u'bounding_box': {u'coordinates': [[[-99.191678999999993,
    #                                                 19.357102000000001],
    #                                                [-99.131066000000004,
    #                                                 19.357102000000001],
    #                                                [-99.131066000000004,
    #                                                 19.404087000000001],
    #                                                [-99.191678999999993,
    #                                                 19.404087000000001]]],
    #                              u'type': u'Polygon'},
    #            u'country': u'Mexico',
    #            u'country_code': u'MX',
    #            u'full_name': u'Benito Ju\xe1rez, Distrito Federal',
    #            u'id': u'7d93122509633720',
    #            u'name': u'Benito Ju\xe1rez',
    #            u'place_type': u'city',
    #            u'url': u'http://api.twitter.com/1/geo/id/7d93122509633720.json'},

    days = ['M','Tu','W','Th','F','Sa','Su']
    wkday = dict([[i,days[i]] for i in range(7)])

    def __init__(self,d):
        self._data = d
        self.id = d[u'id']
        self.place = None
        if d[u'place'] is not None:
            self.place = Place(d[u'place'][u'attributes'],
                           d[u'place'][u'bounding_box'],
                           d[u'place'][u'country'],
                           d[u'place'][u'country_code'],
                           d[u'place'][u'full_name'],
                           d[u'place'][u'id'],
                           d[u'place'][u'name'],
                           d[u'place'][u'place_type'],
                           d[u'place'][u'url'])
        self.geo = Coordinates(float(d[u'geo'][u'coordinates'][0]),
                               float(d[u'geo'][u'coordinates'][1]))
        self.tweet = d[u'text']
        self.user = User(d[u'user'][u'id'],
                         d[u'user'][u'name'],
                         d[u'user'][u'screen_name'],
                         d[u'user'])
        self.time = parsedate_tz(d[u'created_at'])
        self._wktime = mktime_tz(self.time)
        self.weekday = calendar.weekday(*(self.time[:3]))

        self.BEFORE = None
        self.STABLE_HOME = None
        self.AWAY = None
        self.AFTER = None

    def compareTimewise(self,ut):
        # did self or ut come first?
        return mktime_tz(self.time) < mktime_tz(ut.time)

    def timeString(self):
        return datetime.date(*(parsedate_tz(formatdate(self._wktime))[:3]))

    def addTokenization(self,tokenization):
        self.tokenization = tokenization

    def addBeforeLabel(self,num_days):
        self.BEFORE = num_days
        self.STABLE_HOME = False
        self.AWAY = False

    def addAfterLabel(self,num_days):
        self.AFTER = num_days
        self.STABLE_HOME = False
        self.AWAY = False
        
    def addStableHomeLabel(self):
        self.BEFORE = None
        self.STABLE_HOME = True
        self.AWAY = False

    def addAwayLabel(self):
        self.BEFORE = None
        self.STABLE_HOME = False
        self.AWAY = True

    def predictTravel(self):
        self.PREDICT_TRAVEL = True
        self.PREDICT_STABLE = False

        if self.BEFORE is not None or self.AWAY is True:
            self.CORRECT = True
        else:
            self.CORRECT = False

    def predictStability(self):
        self.PREDICT_TRAVEL = False
        self.PREDICT_STABLE = True

        if self.BEFORE is None and self.AWAY is False:
            self.CORRECT = True
        else:
            self.CORRECT = False
