#import argparse
import xmlrpclib
from SimpleXMLRPCServer import SimpleXMLRPCServer

class mcolors:
    OKGREEN = '\033[92m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

    def disable(self):
        self.OKGREEN = ''
        self.FAIL = ''
        self.ENDC = ''

def is_ping(s):
    s1 = "ping"
    s2 = "pong"
    print "Received message: %s" % s
    if s == s1:
        return s2

server = SimpleXMLRPCServer(("127.0.0.1", 8000))
print "Listening on port 8000..."
server.register_function(is_ping, "is_ping")
server.serve_forever()
