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

'''Social Graph building via Timeline filters'''

__author__ = 'colgur@gmail.com'
__version__ = '0.1-devel'


import time
import logging

import urllib
import urllib2
import simplejson as json
from types import *

import twitter
import igraph as ig
import socialgraph as sg

class RespondenceError(Exception):
    @property
    def message(self):
        '''Return first argument used to construct this error'''
        return self.args[0]
    
class TwitterUser(object):
    def __init__(self):
        self._sg = sg.SocialSubGraph(self.lookup)

    @property
    def socialgraph(self):
        '''Get Social Subgraph for current User'''
        return self._sg

    def authenticate(self, username, password):
        '''Twitter User must be authenticated to view other Timelines'''
        try:
            self._api = twitter.Api(username=username, password=password)
            self._user = self._api.GetUser(username)
        except twitter.TwitterError, twerr:
            raise RespondenceError(twerr.message)

    def populate_from_list(self, slug):
        '''Helper populates ssg from Twitter List'''
        try:
            list_members = self._api.GetListMembers(slug)
        except twitter.TwitterError, twerr:
            raise RespondenceError("List Members Retrieval error with '%s'" % twerr.message)
        except AttributeError, attrerr:
            raise RepsondenceError("Check python-twitter version: %s" % attrerr.args[0])

        list_users = list_members['users']
        [self._sg.add_vertex(sg.SocialVertex(each_user.id))
         for each_user in list_users if not each_user.protected]

    def lookup(self, relationship, svids):
        '''Low-level access to Twitter Social Graph'''
        sviditer = iter([svids])
        if type(svids) is ListType:
            sviditer = iter(svids)

        known_bots = ['MrTweet', 'wefollow', 'TweetStats', 'grader']

        filtered_svids = []
        for each_sv in sviditer:
            user = self._api.GetUser(each_sv)
            if user.friends_count > 300:
                logging.info("'%s' has %d friends...",
                             user.screen_name, user.friends_count)
            if user.screen_name not in known_bots:
                filtered_svids.extend([each_sv])
        try:
            for each_socialvertex in socg.twitter_lookup(relationship, filtered_svids):
                yield each_socialvertex
        except:
            raise

def rate_limit_status():
    rate_limit_status_url = 'http://twitter.com/account/rate_limit_status.json'
    result = urllib2.urlopen(rate_limit_status_url)
    rate_limit_dict = json.load(result)

    current_time = time.time()
    reset_time = rate_limit_dict['reset_time_in_seconds']
    remaining_hits = rate_limit_dict['remaining_hits']
    print "Remaining Hits: %d" % remaining_hits
    print "\tLocal time: %s" % time.strftime("%a %b %d %H:%M:%S %Z %Y", 
                                             time.localtime(current_time))
    print "\tReset time: %s" % time.strftime("%a %b %d %H:%M:%S %Z %Y", 
                                             time.localtime(reset_time))

def test():
    import respondence_test

def parse_options():
    from optparse import OptionParser
    
    parser = OptionParser()
    parser.add_option("-u", "--username", dest="username",
                     help="Screen Name of User", metavar="USER")
    parser.add_option("-p", "--password", dest="password",
                      help="Password required for Authentication",
                      metavar="PASS")

    (options, args) = parser.parse_args()

    if options.username == None or options.password == None:
        parser.print_help()
        sys.exit()

    return (options.username, options.password)

def main():
    '''Entry point of typical use scenario'''
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s : %(message)s',
                        datefmt='%H:%M:%S')

    (username, password) = parse_options()
    current_user = TwitterUser()
    try:
        current_user.authenticate(username, password)
    except RespondenceError, resperr:
        logging.error("Authentication failed with '%s'", resperr.message())
        sys.exit()
    
    try:
        current_user.populate_from_list("community1")
    except RespondenceError, resperr:
        logging.error("Populate failed with '%s'", resperr.message())
        sys.exit()

    # Free to operate on SocialGraph now
    # e.g. current_sg.dlsiter(<some igraph.Vertex>, <some depth>)
    current_sg = current_user.socialgraph

if __name__ == '__main__':
    # test()
    main() 

