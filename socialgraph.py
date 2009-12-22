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

'''A library that provides a python interface to the Google Social Graph API'''

__author__ = 'colgur@gmail.com'
__version__ = '0.1-devel'

import urllib2
import urllib
import simplejson as json

import igraph

SGAPI_LOOKUP = "http://socialgraph.apis.google.com/lookup"
NODE_COUNT_LIMIT = 15

class SocialGraphError(Exception):
    '''Base class for Twitter errors'''  
    @property
    def message(self):
        '''Returns the first argument used to construct this error.'''
        return self.args[0]

class VertexSet(set):
    def __contains__(self, val):
        for each_vertex in self:
            if val['uri'] == each_vertex['uri']:
                return True
        return False

class DFSIter(object):
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
    '''A Google Social Sub-Graph'''
    def __init__(self):
        '''An object to hold some portion of the Google Social Graph'''
        # IGraph Instance is Directed
        super(SocialSubGraph, self).__init__(1, [], True)

    def populate_vertices(self, uris):
        '''Cache a copy of Social Graph Node'''
        for start_index in range(0, len(uris), NODE_COUNT_LIMIT):
            end_index = start_index + NODE_COUNT_LIMIT
            if end_index > len(uris): 
                end_index = None
            query_uris = uris[start_index:end_index]
            
            params = [
                ("q", ",".join(query_uris))
                ]
            commerr = 0
            while True:                
                try:
                    node_dict = lookup(params)
                    break
                except SocialGraphError, socerr:
                    # TODO: Log instead
                    print "%s" % socerr.message()
                    commerr = commerr + 1
                    if commerr > 2:
                        raise
                    # TODO: Sleep?
                    print "Retrying..."
                except:
                    #TODO: Anything more?
                    raise

            for each_nodeuri in node_dict.keys():
                try:
                    self._add_vertex(node_dict, each_nodeuri)
                except SocialGraphError:
                    raise

    def populate_neighbors(self, uris, type=igraph.ALL):
        '''Cache a copy of each Neighbor Node in Social Graph'''
        params = [
            ("q", ",".join(uris))
            ]
        if type == igraph.OUT:
            params.extend([("edo", "1"), ("edi", "0")])
        elif type == igraph.IN:
            params.extend([("edo", "0"), ("edi", "1")])
        else:
            params.extend([("edo", "1"), ("edi", "1")])
        node_dict = lookup(params)

        for each_nodeuri in node_dict.keys():
            try:
                self._add_vertex(node_dict, each_nodeuri)

                target_dict = node_dict[each_nodeuri]['nodes_referenced']
                self._populate_es(target_dict, each_nodeuri)
            except SocialGraphError:
                raise
            except KeyError:
                # Empty is OK, non-existent is unexpected
                raise SocialGraphError("Malformed Social Graph for uri='%s'" % each_nodeuri)

    def dfsiter(self, vid, depth=6, advanced=False):
        ret = []
        update_ret = lambda vertex: ret.extend([vertex])

        try:
            self._init_dfsiter(self.vs[vid], depth, None, self.populate_neighbors, update_ret)
        except:
            # TODO: OK? Looking for 'best-effort'
            pass
        return DFSIter(ret)

    def _init_dfsiter(self, vertex,  depth, visited = None,
                      preorder_process = lambda x: None,
                      postorder_process = lambda x: None):
        if visited is None:
            visited = VertexSet()
            visited.add(vertex)

        if depth == 0:
            postorder_process(vertex)
            return
        depth = depth - 1

        try:
            preorder_process([vertex['uri']])
        except:
            print "Gave up on '%s'" % vertex['uri']
            raise

        for neighbor in self.neighbors(vertex.index):
            if self.vs[neighbor] not in visited:
                self._init_dfsiter(self.vs[neighbor], depth, visited, preorder_process, postorder_process)

        postorder_process(vertex)
        
    def _add_vertex(self, node_dict, nodeuri):
        '''Helper updates igraph.VertexSeq (as necessary)'''
        igraph_vertex = self.vs[0]
        try:
            vertex_match = self.vs.select(uri=nodeuri)
            if len(vertex_match) == 0:
                # New Vertex
                self.add_vertices(1)

                reverse_vs = self.vs[::-1]
                igraph_vertex = reverse_vs[0]
            elif len(vertex_match) == 1:
                # Replacement Vertex
                igraph_vertex = vertex_match[0]
            else:
                # Confusion
                raise SocialGraphError("Too many Vertices with uri='%s'" % nodeuri)
        except KeyError:
            # (Should) Only happen on the very first
            pass
        except SocialGraphError:
            # Confusion
            raise

        try:
            attributes = node_dict[nodeuri]['attributes']
        except KeyError:
            # Empty is OK, non-existent is unexpected
            raise SocialGraphError("Malformed Social Graph Node for uri='%s'" % nodeuri)

        attributes['uri'] = nodeuri
        self._populate_v(igraph_vertex, attributes)

    def _populate_es(self, target_dict, vertexuri):
        '''Helper populates igraph.EdgeSeq'''
        target_seq = [eachuri for eachuri in target_dict.keys() if 'me' not in target_dict[eachuri]['types']]
        self.populate_vertices( target_seq )

        vertex_match = self.vs.select(uri=vertexuri)
        assert len(vertex_match) == 1, SocialGraphError("Too many Neighbors with uri='%s'" % vertexuri)
        vertex = vertex_match[0]

        for each_neighboruri in target_seq:
            neighbor_match = self.vs.select(uri=each_neighboruri)
            assert len(neighbor_match) == 1, SocialGraphError("Too many Neighbors with uri='%s'" % vertexuri)
            neighbor = neighbor_match[0]

            self.add_edges( [(vertex.index, neighbor.index)] )

    def _populate_v(self, vertex, attributes):
        '''Helper populates igraph.Vertex.attributes()'''
        attributes.setdefault('uri', None)
        vertex['uri'] = attributes['uri']

        attributes.setdefault('url', None)
        vertex['url'] = attributes['url']

        attributes.setdefault('profile', None)
        vertex['profile'] = attributes['profile']

        attributes.setdefault('rss', None)
        vertex['rss'] = attributes['rss']

        attributes.setdefault('atom', None)
        vertex['atom'] = attributes['atom']

        attributes.setdefault('foaf', None)
        vertex['foaf'] = attributes['foaf']

        attributes.setdefault('photo', None)
        vertex['photo'] = attributes['photo']

        attributes.setdefault('fn', None)
        vertex['fn'] = attributes['fn']
        
def lookup(params):
    '''Low-level access to the underlying Direct Graph'''
    qs = urllib.urlencode(params)
    url = "?".join([SGAPI_LOOKUP, qs])

    try:
        result = urllib2.urlopen(url)
    except HTTPError, hterr:
        raise SocialGraphError("Remote Service error: '%d - %s'" % (hterr.code, hterr.reason))
    except URLError, urlerr:
        raise SocialGraphError("Remote Service error: '%s'" % urlerr.reason)

    struct = json.load(result)

    return struct['nodes']

if __name__ == '__main__':
    print "Loaded socialgraph"

