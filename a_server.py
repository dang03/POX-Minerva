import xmlrpclib
import time
import signal, os
from service_thread import ServiceThread
from SimpleXMLRPCServer import SimpleXMLRPCServer


def ping():
    print "Ping Received in SERVER A"
    return "Pong_A"


def read(db_id):
    print "Server A: Reading file with ID %d" % db_id
    f = open("/home/pox/apps/flowA/" + str(db_id), "r+")
    data = f.read()
    f.close()
    return data


def write(data, db_id):
    print "Server A: writing file with ID %d" % db_id
    f = open("/home/pox/apps/flowA/" + str(db_id), "w+")
    f.write(data)
    f.close()
    return "SERVER A: Data Correctly Saved"


def signal_handler(signum, frame):
    #ServiceThread.start_in_new_thread(timer, None)
    if status.up == True:
        print mcolors.FAIL+"SERVICE DOWN!"+mcolors.ENDC
        status.up = False
        print "OUT_TIMER:", status.up

    else:
        print mcolors.OKGREEN+"SERVICE UP!"+mcolors.ENDC
        status.up = True
        #server.serve_forever()

    return


def keepRunning():
    #print "While keepRunning", status.up
    return status.up



class server_status(object):
    up = True


class mcolors:
    OKGREEN = '\033[92m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

    def disable(self):
        self.OKGREEN = ''
        self.FAIL = ''
        self.ENDC = ''

server = SimpleXMLRPCServer(("127.0.0.1", 9595))
server.register_function(ping, "ping")
server.register_function(read, "read")
server.register_function(write, "write")
print "starting server A..."
status = server_status()
server.allow_reuse_address = True
#server.serve_forever()

signal.signal(signal.SIGALRM, signal_handler)
signal.setitimer(signal.ITIMER_REAL, 20, 20)

while 1:

    """
    if status.up == False:
        signal.alarm(10)
    #print "OUT_TIMER:10", status.up
    #server.serve_forever()
    """

    while keepRunning():

        #signal.setitimer(signal.ITIMER_REAL, 10, 10)
        print "Server A active"
        print "IN_TIMER:", status.up
        server._handle_request_noblock()
        #handle_timer()


