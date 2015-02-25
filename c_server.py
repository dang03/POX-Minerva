import xmlrpclib
from SimpleXMLRPCServer import SimpleXMLRPCServer

def ping():
    print "Ping Received in SERVER AxB"
    return "Pong_AxB"

def read(db_id):
    print "Reading file with ID %d" % db_id
    f = open("/home/pox/apps/flowAxB/" + str(db_id), "r+")
    data = f.read()
    f.close()
    return data

def write(data, db_id):
    print "writing file with ID %d" % db_id
    f = open("/home/pox/apps/flowAxB/" + str(db_id), "w+")
    f.write(data)
    f.close()
    return "SERVER AxB: Data Correctly Saved"


server = SimpleXMLRPCServer(("127.0.0.1", 9797))
server.register_function(ping, "ping")
server.register_function(read, "read")
server.register_function(write, "write")
print "starting server AxB..."
server.serve_forever()    
