# -*- coding: utf-8 -*-
import sys, os, inspect, subprocess, shlex
import re
from monitor_plugin import *
plugin_info("arp.json")

result = {}
type_chn = {"¶¯Ì¬" : "d", "¾²Ì¬" : "s"}
state = "empty"
current = None

for line in agent_utils.run_cmd("arp -a").splitlines():
    # print line
    m1 = re.search(r'(\d+\.\d+\.\d+\.\d+)\s*---', line)
    m2 = re.search(r'(\d+\.\d+\.\d+\.\d+)\s*(..-..-..-..-..-..)\s*(\S*)', line)
    
    if m1:
        # print "m1", m1.groups()
        result[m1.group(1)] = []
        current = result[m1.group(1)]
        
    if m2:
        # print "m2", m2.groups()
        current.append([m2.group(1), m2.group(2).replace("-", ""), type_chn[m2.group(3)]])

print result