#!/usr/bin/python
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

'''Affiliation via correspondence within List Timelines'''

__author__ = 'colgur@gmail.com'
__version__ = '0.1-devel'

import sys
import time
import logging

import urllib
import urllib2
import simplejson as json
from types import *

import twitter

class TwitterListError(twitter.TwitterError):
    '''Derived for this module'''
    pass

class RateLimitError(TwitterListError):
    '''Rate Limit Specific Error'''
    def __init__(self, reset_time, message):
        self.reset_time = reset_time
        self.message = message

    @property
    def reset_time(self):
        '''Return Reset Time provided by Service'''
        return self.reset_time

    @property
    def message(self):
        '''Return Reset Time provided by Service'''
        return self.message

class TwitterList(object):
    def __init__(self, listname):
        self._listname = listname
        
    def authenticate(self, username, password):
        '''Twitter User must be authenticated to view other Timelines'''
        try:
            self._api = twitter.Api(username=username, password=password)
        except twitter.TwitterError, twerr:
            raise TwitterListError(twerr.message)

        try:
            (remaining_hits, reset_time) = rate_limit_status()
            self._remaining_hits = remaining_hits
            self._reset_time = reset_time
        except IOError:
            raise TwitterListError("Looks like connectivity issues")

        logging.info("%d hits remain", self._remaining_hits)
        if (self._remaining_hits == 0):
            raise RateLimitError(self._reset_time, "Reached Service Limit")

    def mentions(self):
        '''Print screen_name of mentioned along with Status.text and Status.user.screen_name'''

    def atreplies(self):
        '''Print screen_names with Status.text and Status.user.screen_names.
        Return List of Status objects to be used to view Conversation'''
        self._members = self._api.GetListMembers(self._listname)
        self.timeline = []
        for each_member in self._members['users']:
            each_timeline = self._api.GetUserTimeline(each_member.id)
            self.timeline.extend(each_timeline)

        def compare(timeline1, timeline2):
            '''Return -1 if timeline1.created_at < timeline2.created_at'''
            date1 = timeline1.created_at
            date2 = timeline2.created_at
            expected_format = "%a %b %d %H:%M:%S +0000 %Y"
            try:
                time1 = time.strptime(date1, expected_format)
                time2 = time.strptime(date2, expected_format)
            except ValueError, verr:
                raise TwitterListError(verr.message)

            return cmp(time1, time2) 

        try:
            self.timeline.sort(cmp=compare)
        except:
            raise

        return [each_status 
                for each_status in self.timeline
                if len(each_status.in_reply_to_screen_name) != 0]

    def show_conversation(self, status):
        '''Use Status information to guess at a Conversation'''

def rate_limit_status():
    rate_limit_status_url = 'http://twitter.com/account/rate_limit_status.json'
    try:
        result = urllib2.urlopen(rate_limit_status_url)
    except IOError as (errno, strerror):
        logging.error("I/O error({0}): {1}".format(errno, strerror))
        raise

    rate_limit_dict = json.load(result)

    reset_time = rate_limit_dict['reset_time_in_seconds']
    remaining_hits = rate_limit_dict['remaining_hits']

    return(remaining_hits, reset_time)

def parse_options():
    from optparse import OptionParser
    
    parser = OptionParser()
    parser.add_option("-u", "--username", dest="username",
                     help="Screen Name of User", metavar="USER")
    parser.add_option("-p", "--password", dest="password",
                      help="Password required for Authentication",
                      metavar="PASS")
    parser.add_option("-l", "--listname", dest="listname",
                      help="List Followed by this User",
                      metavar="PASS")

    (options, args) = parser.parse_args()

    if options.username == None or \
            options.password == None or \
            options.listname == None:
        parser.print_help()
        sys.exit()

    return (options.username, options.password, options.listname)

def init(username, password, listname):
    '''Debugging convenience'''
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s : %(message)s',
                        datefmt='%H:%M:%S')

    current_list = TwitterList(listname)
    try:
        current_list.authenticate(username, password)
    except TwitterListError, tlerror:
        logging.error("Failed to Authenticate with %s", tlerror.message)
        sys.exit()
    except RateLimitError as (reset_time, message):
        logging.error("%s (Reset Time: %s", 
                      message,
                      time.strftime("%a %b %d %H:%M:%S %Z %Y",
                                    time.localtime(reset_time)))
        sys.exit()
    except:
        logging.error("Unexpected error:", sys.exc_info()[0])
        sys.exit()

    return current_list

def main():
    (username, password, listname) = parse_options()
    current_list = init(username, password, listname)

