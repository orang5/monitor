# -*- coding: utf-8 -*-
from collections import namedtuple
import agent_utils
import time

# 配置文件中对metric和plugin的描述结构
# 并不是必须的。因为只要发送的metric消息符合消息规则，就视为合法的
MetricDesc = namedtuple("MetricDesc", "name, value_type, interval, cmd")
PluginDesc = namedtuple("PluginDesc", "name, description, type, cmd_list, platform_data, metrics",
#                        verbose=True,
                       )

# metric消息结构
class Metric(MetricDesc):
    def __init__(self, *args, **kwargs):
        super(Metric, self).__init__(*args, **kwargs)
        self.enabled = True
        # timestamps: latest, queue, execute
        self.ts = {'latest' : time.time()}
        self.value = None
        self.last_value = None
        self.tags = {}
        self.args = {}

    @classmethod
    def _make(cls, m):
        return cls(m.name, m.value_type, m.interval, m.cmd)

    def __repr__(self):
        return agent_utils.to_dict(self).__repr__()

    def timestamp(self):
        # to be modified in future
        return int(self.ts['latest'])

    # use tag to substitute self.cmd
    def cmdline(self):
        t = self.cmd
        for k, v in self.args.iteritems():
            t = t.replace("%%%s%%" % k, v)
        return t

    def message(self):
        msg = " ".join([self.name, self.timestamp().__str__(), self.value.__str__(),
                        " ".join(["%s=%s" % (k, v.__str__()) for k, v in self.tags.iteritems()])
                      ])
        return msg

    def message_json(self):
        return agent_utils.to_json({'name' : self.name, 'timestamp' : self.timestamp(),
                             'value' : self.value, 'tags' : self.tags})

    # todo:
    def from_message(self, msg): pass

# plugin运行时结构
class Plugin(PluginDesc):
    def __init__(self, *args, **kwargs):
       # print "init", args
        PluginDesc.__init__(*args, **kwargs)
        self.enabled = True
        self.uptime = int(time.time())
        self.handle = None
        
    @classmethod
    def _make(cls, p):
       # print "make", p
        return cls(p.name, p.description, p.type,
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
    print mm.message()
    print mm.message_json()
