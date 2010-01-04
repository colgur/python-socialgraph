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

'''Social Subgraph Creation and Manipulation derived from IGraph API'''

__author__ = 'colgur@gmail.com'
__version__ = '0.1-devel'

import urllib2
import urllib
import simplejson as json
from types import *
import time

import igraph

SUCCESSORS = 2
PREDECESSORS = 3

class SocialSubGraphError(Exception):
    '''Base class for Network errors'''  
    @property
    def message(self):
        '''Return first argument used to construct this error'''
        return self.args[0]

class SocialVertex(object):
    '''A Social Vertex'''
    def __init__(self, id = None):
        self._id = id
        self._relations = None

    def get_id(self):
        return self._id

    def set_id(self, id):
        self._id = id

    id = property(get_id, set_id,
                    doc="Globally unique Social Vertex ID")

    def get_relations(self):
        return self._relations

    def set_relations(self, relations):
        self._relations = relations

    relations = property(get_relations, set_relations,
                    doc="Socially connected Vertices")

class SocialVertexSet(set):
    def __contains__(self, val):
        for each_vertex in self:
            if val['svid'] == each_vertex['svid']:
                return True
        return False

class DLSIter(object):
    def __init__(self, data):
        self.iter = iter(data)

    def __iter__(self):
        return self

    def next(self, offset=0):
        ret = None
        try:
            ret = self.iter.next()
            for i in range(offset):
                ret = self.iter.next()
        except StopIteration:
            raise
        return ret

class SocialSubGraph(igraph.Graph):
    '''A Social Sub-Graph'''
    def __init__(self,
                 lookup_method = lambda relationship, svids: None):
        '''An object to hold some portion of the Google Social Graph'''
        # IGraph Instance is Directed
        super(SocialSubGraph, self).__init__(1, [], True)
        self._lookup_method = lookup_method

    def populate_followers(self, svids):
        '''Predeccessors in Graph-speak'''
        try:
            edge_seq = [(each_relation[1], each_relation[0])
                        for each_relation in self._populate_vertices(PREDECESSORS, svids)
                        if not self.are_connected(each_relation[1], each_relation[0])]
            self.add_edges(edge_seq)
        except:
            raise

    def populate_friends(self, svids):
        '''Successors in Graph-speak'''
        try:
            edge_seq = [(each_relation[0], each_relation[1])
                        for each_relation in self._populate_vertices(SUCCESSORS, svids)
                        if not self.are_connected(each_relation[0], each_relation[1])]
            self.add_edges(edge_seq)
        except:
            raise

    def _populate_vertices(self, relationship, svids):
        '''Helper initializes underlying IGraph Vertices'''
        try:
            for each_sv in self._lookup_method(relationship, svids):
                focus_vid = self.add_vertex(each_sv)
                for each_relation in each_sv.relations:
                    related_vid = self.add_vertex(each_relation)
                    yield (focus_vid, related_vid)
        except:
            raise

    def _populate_iv(self, vertex, attributes):
        '''Helper populates igraph.Vertex.attributes()'''
        attributes.setdefault('svid', None)
        vertex['svid'] = attributes['svid']

        attributes.setdefault('url', None)
        vertex['url'] = attributes['url']

        attributes.setdefault('fn', None)
        vertex['fn'] = attributes['fn']

    def add_vertex(self, socialvertex):
        '''Helper updates igraph.VertexSeq (as necessary)'''
        igraphvertex = self.vs[0]
        try:
            vertex_match = self.vs.select(svid=socialvertex.id)
            if len(vertex_match) == 0:
                # New Vertex
                self.add_vertices(1)

                reverse_vs = self.vs[::-1]
                igraphvertex = reverse_vs[0]
            elif len(vertex_match) == 1:
                # Replacement Vertex
                igraphvertex = vertex_match[0]
            else:
                # Confusion
                raise SocialSubGraphError("Too many Vertices with uri='%s'" % nodeuri)
        except KeyError:
            # (Should) Only happen on the very first
            pass
        except SocialSubGraphError:
            # Confusion
            raise

        attributes = dict({'svid': socialvertex.id})
        self._populate_iv(igraphvertex, attributes)
        return igraphvertex.index

    def dlsiter(self, igraphvertex, depth=6, advanced=False):
        ret = []
        update_ret = lambda vertex: ret.extend([vertex])

        try:
            self._init_dlsiter(igraphvertex, depth, None, 
                               self.populate_friends, 
                               update_ret)
        except:
            # TODO: OK? Looking for 'best-effort'
            pass
        return DLSIter(ret)

    def _init_dlsiter(self, vertex, depth, visited = None,
                      preorder_process = lambda x: None,
                      postorder_process = lambda x: None):
        if visited is None:
            visited = SocialVertexSet()
            visited.add(vertex)

        if depth == 0:
            postorder_process(vertex)
            return
        depth = depth - 1

        try:
            preorder_process([vertex['svid']])
        except:
            print "Gave up on '%s'" % vertex['svid']
            raise

        for neighbor in self.neighbors(vertex.index):
            if self.vs[neighbor] not in visited:
                self._init_dlsiter(self.vs[neighbor], depth, visited, 
                                   preorder_process, 
                                   postorder_process)
        postorder_process(vertex)
        
def twitter_lookup(relationship, svids):
    '''Low-level access to Twitter Social Graph'''
    sviditer = iter([svids])
    if type(svids) is ListType:
        sviditer = iter(svids)
  
    graphurl = "http://twitter.com/friends/ids.json"
    if relationship == PREDECESSORS:
        graphurl = "http://twitter.com/followers/ids.json"

    def populate_relations(base_url, svid, relations):
        def rate_limit():
            rate_limit_status_url = 'http://twitter.com/account/rate_limit_status.json'
            result = urllib2.urlopen(rate_limit_status_url)

            rate_limit_dict = json.load(result)
            reset_time = rate_limit_dict['reset_time_in_seconds']
            remaining_hits = rate_limit_dict['remaining_hits']

            if remaining_hits <= 0:
                current_time = time.time()
                sleep_time = reset_time - current_time
                #TODO: Log instead
                print "Local time: '%s'. Sleeping until '%s'" % (
                     time.strftime("%a %b %d %H:%M:%S %Z %Y", time.localtime(current_time)),
                     time.strftime("%a %b %d %H:%M:%S %Z %Y", time.localtime(reset_time))
                     )
                try:
                    time.sleep(sleep_time)
                except KeyboardInterrupt:
                    raise SocialSubGraphError("Quiting lookup")
        
        cursor = -1
        while cursor != 0:
            try:
                rate_limit()
            except:
                raise

            params = [("user_id", svid),
                      ("cursor", cursor)]
            enc_params = urllib.urlencode(params)
            param_url = "?".join([base_url, enc_params])
            try:
                result = urllib2.urlopen(param_url)
            except HTTPError, hterr:
                raise SocialSubGraphError("Remote Service error: '%d - %s'" % 
                                          (hterr.code, hterr.reason))
            except URLError, urlerr:
                raise SocialSubGraphError("Remote Service error: '%s'" % 
                                          urlerr.reason)
            struct = json.load(result)

            relations.extend([SocialVertex(each_rsvid) for each_rsvid in struct['ids']])
            cursor = struct['next_cursor']

    for each_svid in sviditer:
        vertex = SocialVertex(each_svid)
        vertex.relations = []
        try:
            populate_relations(graphurl, each_svid, vertex.relations)
        except:
            raise
        yield vertex

def google_lookup(relationship, svids):
    '''Low-level access to Google Social Graph'''
    sviditer = iter([svids])
    if type(svids) is ListType:
        sviditer = iter(svids)
  
    graphurl = "http://socialgraph.apis.google.com/lookup"
    direction = ("edo", "1")
    if relationship == PREDECESSORS:
        direction = ("edi", "1")

    for each_svid in sviditer:
        params = [
            ("q", each_svid),
            direction
            ]
        qs = urllib.urlencode(params)
        url = "?".join([graphurl, qs])
        try:
            result = urllib2.urlopen(url)
        except HTTPError, hterr:
            raise SocialSubGraphError("Remote Service error: '%d - %s'" % (hterr.code, hterr.reason))
        except URLError, urlerr:
            raise SocialSubGraphError("Remote Service error: '%s'" % urlerr.reason)

        vertex = SocialVertex(each_svid)
        if relationship == PREDECESSORS:
            relationship_dict = json.load(result)['nodes'][each_svid]['nodes_referenced_by']
            vertex.relations = [
                SocialVertex(eachuri) 
                for eachuri in relationship_dict.keys()
                ]
        else:
            relationship_dict = json.load(result)['nodes'][each_svid]['nodes_referenced']
            vertex.relations = [
                SocialVertex(eachuri) 
                for eachuri in relationship_dict.keys()
                if 'me' not in relationship_dict[eachuri]['types']
                ]
        yield vertex

def test():
    import socialgraph_test

if __name__ == '__main__':
    test()

