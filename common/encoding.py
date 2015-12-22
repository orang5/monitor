# -*- coding: utf-8 -*-
#　http://blog.csdn.net/heyuxuanzee/article/details/8442718
import sys

class UTF8StreamFilter:
    def __init__(self, stream):
        self.stream = stream
        self.encoding = 'utf-8'
        self.errors = 'replace'
        self.encode_to = self.stream.encoding
        
    def write(self, s):
        if type(s) == str:
            s = s.decode(self.encoding)
        s = s.encode(self.encode_to, self.errors).decode(self.encode_to)
        self.stream.write(s)
    
if sys.stdout.encoding == 'cp936':
    sys.stdout = UTF8StreamFilter(sys.stdout)
    
if __name__ == "__main__":
    print "测试"
    print u"测试"