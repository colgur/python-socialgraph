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

'''WeFollow-type analysis using socialgraph module'''

__author__ = 'colgur@gmail.com'
__version__ = '0.1-devel'

import sys
import time
import urllib
import urllib2
import simplejson as json
from types import *

import twitter
import igraph
import socialgraph as socg

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

api = twitter.Api(username='colgur',password='xxxxxx')
colgur = api.GetUser('colgur')

def lookup(relationship, svids):
    '''Low-level access to Twitter Social Graph'''
    sviditer = iter([svids])
    if type(svids) is ListType:
        sviditer = iter(svids)

    known_bots = ['MrTweet', 'wefollow', 'TweetStats', 'grader']

    filtered_svids = []
    for each_sv in sviditer:
        user = api.GetUser(each_sv)
        if user.friends_count > 300:
            print "'%s' has %d friends..." % (user.screen_name, user.friends_count)
        if user.screen_name not in known_bots:
            filtered_svids.extend([each_sv])
    try:
        for each_socialvertex in socg.twitter_lookup(relationship, filtered_svids):
            yield each_socialvertex
    except:
        raise

def summarize(graph, indegree):
    '''Summarize Vertices with a given indegree'''
    following_vertices = graph.vs.select(_indegree_eq = indegree)
    for each_vertex in following_vertices:
        follower_vids = graph.neighbors(each_vertex.index, igraph.IN)

        user = api.GetUser(each_vertex['svid'])
        print "Followed: %s" % user.screen_name
        print "\tFollowing ([vid]: screen_name): "
        for each_vid in follower_vids:
            user = api.GetUser(graph.vs[each_vid]['svid'])
            print "\t\t[%d]: %s" % (each_vid, user.screen_name)

colgur_sg = socg.SocialSubGraph(lookup)
try:
    colgur_sg.populate_friends(colgur.id)
except socg.SocialSubGraphError, sgerr:
    print sgerr.message()
    sys.exit()
except:
    raise

socialgraph_userids = [11336782, 11388132, 1528701, 7746932, 14971237, 892821, 3829151, 9534522, 639643, 1919231, 30923, 18713, 5702, 641433, 765694, 3839, 989, 14763, 14064122, 752673]
tech_userids = [14076724, 18137723, 11486902, 2892261, 19754893, 749863, 2911221, 20536157, 5676102, 1117901, 15948437, 13348, 1176801, 5637652, 7975062, 657863, 823083, 14736421, 14797016, 43158454]

ids_of_interest = tech_userids
ids_of_interest.extend(socialgraph_userids)

for each_id in ids_of_interest:
   svid_match = colgur_sg.vs.select(svid=each_id)
   ivertex = svid_match[0]
   try:
       colgur_sg.dlsiter(ivertex, 1)
   except socg.SocialSubGraphError, sgerr:
       print sgerr.message()
       sys.exit()
   except:
       raise

topdeg = colgur_sg.vs.maxdegree(igraph.IN)
topv = colgur_sg.vs.select(_indegree_eq=topdeg)
user = api.GetUser(topv[0]['svid'])
print "Top (%d): '%s'" %  (topdeg, user.screen_name)

