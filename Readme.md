# Motivation
Started with a desire to know <i>"who is popular among (some of) my friends"</i>. Learned that users <i>follow</i> for all kinds of reasons and that <i>correspondence</i> is actually more important e.g. might reply to someone located during a search but never actually follow them.

## Sample usage
See [popular.py](http://github.com/colgur/python-socialgraph/blob/master/popular.py).

# Influences
  * [WeFollow](http://wefollow.com/)
    ** Interested less in who is popular on Twitter than among my friends
  * [DoesFollow](http://www.doesfollow.com/)
    ** Answers the fundamental question but not in a scalable way
  * [python-twitter](http://static.unto.net/python-twitter)
    ** More for design cues
  * [Giraffe](http://github.com/markpasc/giraffe/socialgraphapi.py)
    ** One of only a couple of implementations that I could find on a code search

# Notes
  * <b>Needs an update to use OAuth</b>
  * Depth-limited Search needs to be adjusted for Rate-limiting and Bots
    ** A DLSIter with depth=2 populates a huge graph (~250k Nodes)
    ** Bots follow 1000s of Users. Real Users don't follow more than about 300
  * See [Notes.txt](http://github.com/colgur/python-socialgraph/blob/master/Notes.txt) for the gory, twisted trail.
