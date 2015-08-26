# -*- coding: utf-8 -*-
import json
import collections
import inspect, logging, logging.config
import subprocess, shlex
import projectroot
named_classes = {}

# http://stackoverflow.com/questions/2166818/python-how-to-check-if-an-object-is-an-instance-of-a-namedtuple
def seems_namedtuple(typo):
    b = typo.__bases__
    ret = len(b) >= 1 and (b[0] == tuple or seems_namedtuple(b[0]))
    # print typo, "seems namedtuple? ", ret
    return ret

# http://stackoverflow.com/questions/1036409/recursively-convert-python-object-graph-to-dictionary
def to_dict(obj, classkey='__class__'):
    if isinstance(obj, dict):
        data = {}
        for (k, v) in obj.items():
            data[k] = to_dict(v, classkey)
        return data
    elif hasattr(obj, "_ast"):
        return to_dict(obj._ast())
    elif hasattr(obj, "__iter__") and not seems_namedtuple(type(obj)):
        # change: exclude namedtuple
        return [to_dict(v, classkey) for v in obj]
    elif hasattr(obj, "__dict__"):
        # change: use inspect instead of iter dict. compatible with namedtuples
        data = dict([(x[0], to_dict(x[1], classkey))
            for x in inspect.getmembers(obj)
            if not callable(x[1]) and not x[0].startswith('_')])

        if classkey is not None and hasattr(obj, "__class__"):
            data[classkey] = obj.__class__.__name__
        return data
    else:
        return obj

def from_dict(d):
    global named_classes
    # extract values (w/o '_')
    dd = {k : d[k] for k in d.keys() if not k.startswith('_')}
    # extract class name
    if d.has_key('__class__'):
        class_name = d['__class__']
        # save data structure in named_classes
#        if not named_classes.has_key(class_name):
#            named_classes[class_name] = collections.namedtuple(class_name, dd.keys())
        # use buffered namedtuples, caution: !assuming same data structure!
        named_classes[class_name] = collections.namedtuple(class_name, dd.keys())
        return named_classes[class_name](*dd.values())
    else:
        return d

def to_json(obj):
    x=obj
    if seems_namedtuple(type(x)):
        x=to_dict(obj)
    return json.dumps(x, default=to_dict, sort_keys=True)

def from_json(str):
    return json.loads(str, object_hook=from_dict)
    
#def register_type(klass):
#    global named_classes
#    named_classes[klass.__name__] = klass

def run_cmd(line):
    line = "cmd /c \"" + line + "\""
    return subprocess.check_output(shlex.split(line)).rstrip("\n\r")

def getLogger():
    logging.basicConfig(level=logging.DEBUG)
    logging.config.fileConfig(r"%s\log.conf" % projectroot.agent_root)
    return logging.getLogger("file")    

def _test():
    log = getLogger()
    a = from_dict({'__class__':'MyTest', 'a':1, 'b':2, 'c':3})
    log.debug(a)
    log.debug(to_dict(a))
    log.debug(to_json(a))
    log.debug(from_json(to_json(a)))

if __name__ == "__main__" : _test()