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

'''Unit tests for the socialgraph.py library'''

__author__ = 'colgur@gmail.com'

import unittest
import simplejson as json

import socialgraph as socg

class DlsIterTest(unittest.TestCase):
    def testPopulate(self):
        '''Test socialgraph creation'''
        TESTFILE = "./testPopulate.json"
        def lookup(graphurl, svids):
            '''Test Lookup Generator'''
            try:
                sviditer = iter(svids)
            except TypeError:
                sviditer = iter([svids])
                pass 

            with open(TESTFILE) as result:
                for each_svid in sviditer:
                    vertex = socg.SocialVertex(each_svid)
                    vertex.relations = [socg.SocialVertex(each_relation_svid) 
                                        for each_relation_svid in json.load(result)]
                    yield vertex

        sg = socg.SocialSubGraph(lookup)

        sg.populate_friends(12345)
        self.assertEqual(len(sg.vs), 6, 
                    "Check that '%s' contains 5 entries" % TESTFILE)
        
        sg.populate_friends([12345])
        self.assertEqual(len(sg.vs), 6, 
                             "No new Vertex additions")
        
        self.assertEqual(len(sg.es), 5)
        
        sg.populate_followers(12345)
        self.assertEqual(len(sg.vs), 6, 
                             "set(friends).difference(set(followers)) should be None")
        
        sg.populate_followers([12345])
        self.assertEqual(len(sg.vs), 6, 
                             "set(friends).difference(set(followers)) should be None")

        self.assertEqual(len(sg.es), 10)
        
    def testDlsiter(self):
        '''Test Depth-limited Search functionality'''
        me = 12345
        bob = 2911221
        mary = 749863
        friends_of_mine = [bob, mary]
        friends_of_bob  = [20536157,5676102]
        friends_of_mary = [5676102,7190742]

        postorder = []
        postorder.extend(friends_of_bob)
        postorder.extend([bob])
        postorder.extend(friends_of_mary)
        postorder.extend([mary])
        postorder.extend([me])

        def lookup(url, svids):
            try:
                sviditer = iter(svids)
            except TypeError:
                sviditer = iter([svids])
                pass 

            for each_svid in sviditer:
                vertex = socg.SocialVertex(each_svid)

                relationship = friends_of_mine
                if each_svid == bob:
                    relationship = friends_of_bob
                elif each_svid == mary:
                    relationship = friends_of_mary
                vertex.relations = [socg.SocialVertex(each_relation_svid) 
                                for each_relation_svid in relationship]
                yield vertex

        sg = socg.SocialSubGraph(lookup)
        sg.add_vertex(socg.SocialVertex(me))

        my_svid_match = sg.vs.select(svid=me)
        self.assertEqual(len(my_svid_match), 1,
                         "Social Vertex ID '%d' is not unique" % me)
        my_ivertex = my_svid_match[0]

        my_dlsiter = sg.dlsiter(my_ivertex, 2)
        my_dlsiter_svids = [each_ivertex['svid'] for each_ivertex in my_dlsiter]
        self.assertEqual(len(postorder), len(my_dlsiter_svids))

        my_dlsiter_svids_iter = iter(my_dlsiter_svids)
        for each_svid in postorder:
            self.assertEqual(each_svid, my_dlsiter_svids_iter.next())
      
def suite():
    suite = unittest.TestSuite()
    suite.addTests(unittest.makeSuite(DlsIterTest))
    return suite

suite = suite()
unittest.TextTestRunner().run(suite)
