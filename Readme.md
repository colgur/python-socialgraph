# Motivation
Want to know <i>"who is popular among (some of) my friends"</i>.

## Sample usage
See [popular.py](http://gist.github.com/xxxxxx) Gist

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
  * Depth-limited Search needs to be adjusted for Rate-limiting and Bots
    ** A DLSIter with depth=2 populates a huge graph (~250k Nodes)
    ** Bots follow 1000s of Users. Real Users don't follow more than about 300

# Directions
  * Honor Twitter Rate Limit
  * Implement Node Selection Policy that avoids large Outgoing Edge Sets

