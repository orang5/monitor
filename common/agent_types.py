# -*- coding: utf-8 -*-
from collections import namedtuple
import agent_utils
import time, json

# 配置文件中对metric和plugin的描述结构
# 并不是必须的。因为只要发送的metric消息符合消息规则，就视为合法的
# fixme: namedtuple is immutable, use class instead
MetricDesc = namedtuple("MetricDesc", "name, type, interval, cmd, enabled")
PluginDesc = namedtuple("PluginDesc", "name, description, type, enabled, cmd_list, platform_data, metrics",
#                        verbose=True,
                       )

# metric消息结构
class Metric(MetricDesc):
    def __init__(self, *args, **kwargs):
        super(Metric, self).__init__(*args, **kwargs)
        # timestamps: latest, queue, execute
        self.ts = {'latest' : time.time()}
        self.value = None
        self.last_value = None
        self.tags = {}
        self.args = {}

    def __repr__(self):
        return agent_utils.to_dict(self).__repr__()
        
    @classmethod
    def _make(cls, m):
        return cls(m.name, m.type, m.interval, m.cmd, getattr(m, "enabled", True))
        
    @classmethod
    def from_message_json(cls, msg):
        d = msg
        if isinstance(msg, basestring): d = json.loads(msg)
        m = cls(d["name"], d["type"], 0, "", True)
        m.ts = {'latest': d["timestamp"]}
        m.value = d["value"]
        m.tags = d["tags"]
        return m
    
    # returns a dict, containing readable info for this object
    @classmethod
    def describe(cls, m):
        # "name, type, interval, cmd, enabled"
        return dict(
            name = m.name,
            type = m.type,
            interval = m.interval,
            cmd = m.cmd, 
            args = getattr(m, "args", {})
        )
        
    @property
    def timestamp(self):
        # to be modified in future
        return int(self.ts['latest'])

    # use tag to substitute self.cmd
    def cmdline(self):
        t = self.cmd
        for k, v in self.args.iteritems():
            t = t.replace("%%%s%%" % k, v)
        return t
        
    def update_tags(self, **kwargs):
        for k in kwargs.keys():
            self.tags[k] = self.tags.get(k, kwargs[k])

    def message_json(self):
        return agent_utils.to_json({'name' : self.name, 'timestamp' : self.timestamp, 'type' : self.type, 
                             'value' : self.value, 'tags' : self.tags})
                             
    def tagdict(self):
        t = dict(name = self.name)
        t.update(self.tags)
        return t

# plugin运行时结构
class Plugin(PluginDesc):
    def __init__(self, *args, **kwargs):
       # print "init", args
        PluginDesc.__init__(*args, **kwargs)
        self.uptime = int(time.time())
        self.handle = None
        
    @classmethod
    def _make(cls, p):
       # print "make", p
        return cls(p.name, p.description, p.type,
            getattr(p, "enabled", True), 
            getattr(p, "cmd_list", {}),
            getattr(p, "platform_data", {}),
            getattr(p, "metrics", [])
        )

    def __repr__(self):
        return agent_utils.to_dict(self).__repr__()
        
    @property
    def pid(self):
        if self.handle:
            return self.handle.pid
        else: return None
    
    # returns a dict, containing readable info for this object
    def describe(self):
        # "name, description, type, enabled, cmd_list, platform_data, metrics"
        return dict(
            name = self.name,
            description = self.description,
            type = self.type,
            enabled = self.enabled,
            cmd_list = self.cmd_list,
            platform_data = self.platform_data, 
            metrics = [Metric.describe(m) for m in self.metrics], 
            uptime = self.uptime,
            pid = self.pid
        )

def _test():
    m1 = MetricDesc("test.dir", "config", 30, "dir")
    m2 = MetricDesc("test.username", "config", 30, r'echo %USERNAME%')
    p1 = PluginDesc("test", "test plugin", "shell", {}, {}, [m1, m2])

    print "m1 = %s" % m1.__repr__()
    print "m2 = %s" % m2.__repr__()
    print "p1 = %s" % p1.__repr__()

    d1 = agent_utils.to_dict(p1)
    j1 = agent_utils.to_json(p1)
    print "d1 = %s" % d1.__repr__()
    print "j1 = %s" % j1.__repr__()

    p2 = agent_utils.from_json(j1)

    print "p2 = %s" % p2.__repr__()

    print "--------------------------------"

    pp = Plugin("test", "test plugin", "shell", {}, {}, [m1, m2])

    print pp

    print "--------------------------------"

    mm = Metric("test.username", "config", 30, r'echo %USERNAME%')
    mm.value = 1
    mm.tags = {"hostname" : "host1", "cluster" : "cl01"}

    print mm
 #   print mm.message()
    print mm.message_json()

if __name__ == "__main__" : _test()