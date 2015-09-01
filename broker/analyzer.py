# -*- coding: utf-8 -*-
import projectroot
from common import agent_types, agent_utils
log = agent_utils.getLogger()
list = []

# note: Analyzer class can carry a threading.Thread object to make parallel
# however, this feature remains TO BE implemented in future
# now, single thread is enough ( for listener itself is parallel-ed )
class Analyzer(object):
    def __init__(self, criteria={}, action=None):
        self.crit = criteria
        self.action = action
    
    def check(self, met):
        if isinstance(self.crit, dict):
            # fixme: simpler code for all key-values meet. 
            for k in self.crit.keys():
                if self.crit[k] != met.tags.get(k, "None"): return False
            return True
        else: return self.crit(met)
        
def add_analyzer(criteria, action, name="default"):
    global list
    list.append(Analyzer(criteria, action))
    log.info("[analyze] register analyzer: %s", name)
    
add_analyzer(
    criteria = lambda x: x.name == "hb",
    action   = lambda x: log.debug("[analyze] heartbeat -> %s", x.tags.get("host", "NONAME")),
    name     = "heartbeat"
    )