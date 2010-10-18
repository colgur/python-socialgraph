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

import igraph
from socialgraph import SocialSubGraph

def summarize(graph, indegree):
    '''Summarize Vertices with a given indegree'''
    following_vertices = graph.vs.select(_indegree_eq = indegree)
    for each_vertex in following_vertices:
        follower_vids = graph.neighbors(each_vertex.index, igraph.IN)

        print "Followed: %s" % each_vertex['uri']
        print "\tFollowing ([vid]: uri): "
        for each_vid in follower_vids:
            print "\t\t[%d]: %s" % (each_vid, graph.vs[each_vid]['uri'])

if __name__ == '__main__':
    print "Loaded popular"
    socg = SocialSubGraph()
    socg.populate_vertices(['http://twitter.com/colgur'])
    socg.populate_neighbors(['http://twitter.com/colgur'])

    primaries = ['http://twitter.com/colgur', 'http://twitter.com/freedryk',  'http://twitter.com/deadprogrammer', 
                 'http://twitter.com/bootuplabs', 'http://twitter.com/codinghorror', 'http://twitter.com/secretgeek', 
                 'http://twitter.com/perspx', 'http://twitter.com/migueldeicaza', 'http://twitter.com/andyy', 
                 'http://twitter.com/kevinrose', 'http://twitter.com/techvibes', 'http://twitter.com/bootuplabs', 
                 'http://twitter.com/keremk', 'http://twitter.com/NISSSAMSI']
    secondaries = ['http://twitter.com/wilshipley', 'http://twitter.com/hotdogsladies', 'http://twitter.com/google', 
                   'http://twitter.com/shanselman', 'http://twitter.com/jwz', 'http://twitter.com/accordionguy', 
                   'http://twitter.com/spolsky', 'http://twitter.com/scobleizer']

    primaries_vids = [i for i in range(len(socg.vs)) if socg.vs[i]['uri'] in primaries]
    primariesg = socg.subgraph(primaries_vids)

    primaries_listed = primaries[1:]
    primaries_listed_vids = [i for i in range(len(socg.vs)) if socg.vs[i]['uri'] in primaries_listed]
    primaries_dfsiters = [socg.dfsiter(each_vid, 1) for each_vid in primaries_listed_vids]

    topdeg = socg.vs.maxdegree(igraph.IN)
    topv = socg.vs.select(_degree_eq = topdeg)
    print "Top Primary (%d): %s" %  (topdeg, topv['uri'][0]) 

