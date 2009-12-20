# Motivation
Wanted to know <i>"who is popular among (some of) the people I follow"</i>.

## Sample usage
Find the most popular person among the people I follow
<p><code>
socg = SocialSubGraph()<br>
myuri = ['http://twitter.com/colgur']<br>
socg.populate_vertices(myuri)
socg.populate_neighbors(myuri)

vids = [i for i in range(len(socg.vs)]
socg_dfsiters = [socg.dfsiter(each_vid, 1) for each_vid in vids]

topdeg = socg.vs.maxdegree(igraph.IN)
topv = socg.vs.select(_degree_eq = topdeg)
print "Top Primary (%d): %s" %  (topdeg, topv['uri'][0]) 
</code></p>

# Influences
  * [WeFollow](http://wefollow.com/)
  * [DoesFollow](http://www.doesfollow.com/)
  * [python-twitter](http://static.unto.net/python-twitter)
  * [Giraffe](http://github.com/markpasc/giraffe/socialgraphapi.py)

# Directions
  * Use Twitter API to filter Followed and maybe even build Social Graph itself (although Google is way more reliable
