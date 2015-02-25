#import argparse
import xmlrpclib
#from SimpleXMLRPCServer import SimpleXMLRPCServer

class mcolors:
    OKGREEN = '\033[92m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

    def disable(self):
        self.OKGREEN = ''
        self.FAIL = ''
        self.ENDC = ''

s = "ping"
proxy = xmlrpclib.ServerProxy("http://192.168.1.1:8000/")
print "Sending %s..." % s

try:
   r = str(proxy.is_ping(s))
   print "Reply received: ", mcolors.OKGREEN+r+mcolors.ENDC
   #print "Reply received: %s" % str(proxy.is_ping(s))

except:
   print mcolors.FAIL+"ERROR: No 'pong' message received"+mcolors.ENDC
