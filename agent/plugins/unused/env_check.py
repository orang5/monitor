# -*- coding: utf-8 -*-
import time, logging, os, platform, subprocess, shlex
from monitor_plugin import *
plugin_info("env_check.json")

indent = -2
prompt = "->"
def check(func):
    def checker(*args):
        global indent
        global prompt
        indent += 2; prompt = "*"
        if indent == 0: prompt = "|"
        ret = func(*args)
        print " "*indent + prompt, func.__name__, args[1:], "->", ret
        indent -= 2; prompt = "->"
        return ret
    return checker
    
class WindowsChecker:
    def cmd(self, line):
        ret = subprocess.check_output(shlex.split("cmd /c \"" + line + "\"")).rstrip("\n\r")
 #       print ret
        return ret

    @check
    def has_process(self, x):
        return ("PID" in self.cmd("tasklist /fi \"imagename eq %s\" /fo csv" % x))
    
    @check
    def has_service(self, x):
        return ("PID" in self.cmd("tasklist /fi \"services eq %s\" /fo csv" % x))
    
    @check    
    def check_mongo(self):
        return self.has_process("mongod.exe")
        
    @check
    def check_rabbit(self):
        return self.has_service("RabbitMQ")
        
    @check
    def check_workstation(self):
        return self.has_service("VMwareHostd")
        
    def run(self):
        self.check_mongo()
        self.check_rabbit()
        self.check_workstation()

class LinuxChecker: pass
    
@check
def check_platform(): return platform.system()

if __name__ == "__main__":
    check_platform()
    if platform.system() == "Windows": WindowsChecker().run()