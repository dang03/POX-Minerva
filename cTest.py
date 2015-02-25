import binascii
import os
import random
import sys
import xmlrpclib
import socket
import StringIO
import time
import datetime
from service_thread import ServiceThread

def get_time_now(timeout=None):
    if timeout:
        t1 = datetime.datetime.now()
        t3 = t1 - datetime.timedelta(seconds=timeout)
        return str(t3.strftime('%M:%S.%f')[:-3])
    else:
        return str(datetime.datetime.now().strftime('%M:%S.%f')[:-3])

def logger(message):
    ServiceThread.start_in_new_thread(logger_thread, message)

def logger_thread(message, log_file="./timeNormalRead159MB.txt"):
    if os.path.exists(log_file):
        l = open(log_file, 'a')
        l.write(message+"\n")

    else:
        l = open(log_file, 'wb')
        l.write(message+"\n")
    l.close()


class mcolors:
    OKGREEN = '\033[92m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

    def disable(self):
        self.OKGREEN = ''
        self.FAIL = ''
        self.ENDC = ''


class MyDistributedStorageClient:
    def __init__(self):
        self.a_client = "127.0.0.1"
        self.b_client = "127.0.0.1"
        self.c_client = "127.0.0.1"
        self.a_port = 9595
        self.b_port = 9696
        self.c_port = 9797
        self.db_id = 1111
        self.buf = 1016
        self.message = "Hello world!"

    def __str_to_bits(self, string):
        return binascii.b2a_hex(string)

    def __get_flows(self, string):
        global length
        hex_string = self.__str_to_bits(string)
        # print "HEX_STRING", hex_string

        """
        while True:
            length = len(hex_string)
            if not length % 4 == 0:
                hex_string = "0" + hex_string
            else:
                break
        """
        """
        length = len(hex_string)

        a_flow = hex_string[0:length / 2]
        b_flow = hex_string[length / 2:]
        axorb_flow = hex(int(a_flow, 16) ^ int(b_flow, 16))[2:]
        if axorb_flow[-1] in '|L': axorb_flow = axorb_flow[:-1]
        """
        """
        f = open("/home/i2cat/Documents/a_flow", "w+")
        f.write(a_flow)
        f.close()
        """

        #print "AFLOW", a_flow, len(a_flow)
        #print "BFLOW", b_flow, len(b_flow)
        #print "CFLOW", axorb_flow, len(axorb_flow)
        #return a_flow, b_flow, axorb_flow
        return hex_string[2:]

    def __reconstruct(self, a=None, b=None, axorb=None):
        print "-----Reconstructing:"
        myList = [a, b, axorb]
        # print myList
        print "count: ", myList.count(None)
        if myList.count(None) > 1:
            return "Unable To reconstruct the data: Two or more flows were not properly retrieved"

        if a and not b:
            b = hex(int(a, 16) ^ int(axorb, 16))[2:]
            if b[-1] in '|L': b = b[:-1]

        elif not a and b:
            a = hex(int(b, 16) ^ int(axorb, 16))[2:]
            if a[-1] in '|L': a = a[:-1]

        #print "A: ", a, "B: ", b
        result = a + b
        return binascii.a2b_hex(result)

    def __headerize(self, action, length, db_id, seq):
        # Fixed size of each field in bytes
        # f_proto = 1
        # f_action = 1
        # f_length = 2
        # f_db_id = 2
        # f_db_id = 2

        proto = self.__str_to_bits("u")
        # print "proto", proto
        act = self.__str_to_bits(action)
        #print "act", act
        ln = hex(length)[2:]
        #print "ln", ln
        db = hex(db_id)[2:]
        #print "db", db
        sq = hex(seq)[2:]
        #print "sq", sq

        # Padding: fill difference with chars "0", one byte each
        pd_ln = (4 - len(ln)) * "0" + ln
        #print "pd_ln", pd_ln
        pd_db = (4 - len(db)) * "0" + db
        #print "pd_db", pd_db
        pd_sq = (4 - len(sq)) * "0" + sq
        #print "pd_sq", pd_sq

        header = proto + act + pd_ln + pd_db + pd_sq

        #print "HEADER: ", header
        #print "len(header): ", len(header)
        return header

    def unpacker(self, data):
        header = []
        data_to_parse = StringIO.StringIO(data)
        header.append(binascii.a2b_hex(data_to_parse.read(2)))  # Protocol
        header.append(binascii.a2b_hex(data_to_parse.read(2)))  # Action
        header.append(int(data_to_parse.read(4), 16))  # Length
        header.append(int(data_to_parse.read(4), 16))  # DB_ID
        header.append(int(data_to_parse.read(4), 16))  # seq
        # print "HEADER: ", header
        body = data_to_parse.read()
        #print "BODY: ", body

        return header, body

    def ping(self):
        print "Ping round: "

        action = "p"
        data_hex = hex(0)[2:]
        # print "data_hex", data_hex
        ln_data = len(data_hex)
        header = self.__headerize(action, ln_data, 0, 0)
        packet = header + data_hex

        try:
            sock1.connect((self.c_client, self.c_port))
            message = "Ping at: Client Time: %s" % get_time_now()
            logger(message)
            sock1.sendto(packet, (client.c_client, client.c_port))
            received = sock1.recv(4096)
            rcv, rcv_body = self.unpacker(received)
            if rcv[1] == "P":
                message = "Pong at: Client Time: %s" % get_time_now()
                logger(message)
                print "Received: ", mcolors.OKGREEN + rcv[1] + " from SERVER TEST" + mcolors.ENDC
        except:
            print mcolors.FAIL + "Server TEST unknown" + mcolors.ENDC


    def write(self, data, db_id=None):
        #a, b, c = self.__get_flows(data)
        #a = self.__get_flows(data)
        if not db_id:
            db_id = self.db_id
        print "Write round:"
        message = "Write start at: Client Time: %s" % get_time_now()
        logger(message)
        a = data
        action = "w"
        sequences_aw = []

        a_output = StringIO.StringIO(a)
        #a_input = StringIO.StringIO()
        #sock.connect((self.a_client, self.a_port))
        a_packet = a_output.read(1024)
        #print "FIRST PACKET: ", a_packet
        n_seq = 0
        try:
            while a_packet:
                sequences_aw.append(n_seq)
                ln_data = len(a_packet)
                header = self.__headerize(action, ln_data, db_id, n_seq)
                packet = header + a_packet
                print "len BODY: ", len(a_packet), n_seq
                sock1.sendto(packet, (client.c_client, client.c_port))
                #a_input.write(a_packet)
                time.sleep(0.00003)
                a_packet = a_output.read(1024)
                n_seq += 1
                #print "NEXT PACKET: ", a_packet
            print mcolors.OKGREEN + "Data sent" + mcolors.ENDC
            action = "D"
            header = self.__headerize(action, 0, db_id, 0)
            packet = header
            sock1.sendto(packet, (client.c_client, client.c_port))
            #data = a_input.getvalue()
            #data2 = binascii.a2b_hex(data)
            #self.write(data, header[3])
            """
            if os.path.exists("/home/pox/apps/flowAxB/" + str(db_id)):
                f = open("/home/pox/apps/flowAxB/" + str(db_id), "a")
                f.write(data)
                f.close()
            else:
                f = open("/home/pox/apps/flowAxB/" + str(db_id), "w")
                f.write(data)
                f.close()
            """
            message = "Write end at: Client Time: %s" % get_time_now()
            logger(message)
            a_output.close()

        except socket.error as e:
            print e
            pass


        # print "SEQ_AW", sequences_aw
        print "LENGTHS: ", len(sequences_aw)
        return

    def read(self, db_id):
        print "Read round:"
        action = "r"
        sequences_ar = []
        data_hex = hex(0)[2:]
        # print "data_hex", data_hex
        ln_data = len(data_hex)
        header = self.__headerize(action, ln_data, db_id, 0)
        packet = header + data_hex

        message = "Read start at: Client Time: %s" % get_time_now()
        logger(message)
        sock1.sendto(packet, (client.c_client, client.c_port))

        print mcolors.OKGREEN + "Request sent" + mcolors.ENDC
        #r_a = None
        a_input = StringIO.StringIO()

        try:
            r_a = sock1.recv(8192)
            #print "FIRST PACKET: ", r_a

            while r_a:
                header, body = self.unpacker(r_a)
                #print header
                if header[1] == "R" and header[3] == db_id:
                    sequences_ar.append(header[4])
                    a_input.write(body)
                    r_a = sock1.recv(8192)
                    #print "NEXT PACKET: ", r_a
                else:
                    break

        except:
            print mcolors.FAIL + "TIMEOUT!" + mcolors.ENDC

        r_a = a_input.getvalue()
        #print "CONTENT: ", r_a
        if r_a != '':
            message = "Read end at: Client Time: %s" % get_time_now(timeout=2)
            logger(message)
            print "Received: ", mcolors.OKGREEN + "OK" + mcolors.ENDC

        else:
            print mcolors.FAIL + "WRONG response" + mcolors.ENDC
            r_a = None

        a_input.close()
        print "LENGTHS: ", len(sequences_ar)
        #return binascii.a2b_hex(r_a)
        return r_a

    def auto_read(self, db_id):
        print "Server TEST: Reading file with ID %d" % db_id
        if os.path.exists("/home/pox/apps/flowAxB/" + str(db_id)):
            f = open("/home/pox/apps/flowAxB/" + str(db_id), "r+")
            data = f.read()
            action = "R"
            #data2 = self.__str_to_bits(data)
            output = StringIO.StringIO(data)
            a_input = StringIO.StringIO()
            #output = StringIO.StringIO(data2)
            #socket.connect(self.client_address)
            a_packet = output.read(1024)
            #print "FIRST PACKET: ", packet
            n_seq = 0
            #print "READY"
            while a_packet:
                #self.sequences_r.append(n_seq)
                ln_data = len(a_packet)
                header = self.__headerize(action, ln_data, db_id, n_seq)
                packet = header + a_packet
                #print "header", header
                #socket.sendto(packet, self.client_address)
                a_input.write(a_packet)
                time.sleep(0.00003)
                a_packet = output.read(1016)
                n_seq += 1
                #print "NEXT PACKET: ", packet
            message = "Read end at: Server Time: %s" % get_time_now()
            #logger(message)
            #print "TEST data sent"
            r_a = a_input.getvalue()
            a_input.close()
            output.close()
            return r_a

"""
#SOCKET TEST
client = MyDistributedStorageClient()

sock.sendto(client.message, (client.a_client, client.a_port))
sock.sendto(client.message, (client.b_client, client.b_port))
sock.sendto(client.message, (client.c_client, client.c_port))

received = sock.recv(1024)
print "Received: ", received
"""

client = MyDistributedStorageClient()
socket.setdefaulttimeout(2)
sock1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

random_db_id = random.randrange(0, 1000)
# random_db_id = 222

if len(sys.argv) >= 2:
    try:
        file_contents = open(sys.argv[1], "r")
    except Exception as e:
        raise Exception("Could not open file. Details: %s" % str(e))

    file_read = file_contents.read()

    #file_encoded = binascii.b2a_hex(file_read)
    file_encoded = file_read.encode("utf16")

    # Encode and decode as necessary
    # Client only retrieves in the same format as stored
    client.write(file_encoded, random_db_id)

else:
    """
    while True:
        client.ping()
        time.sleep(1)
    """

    f = open("/home/i2cat/Downloads/trailer_sd.mp4", "r+")
    #f = open("/home/i2cat/Downloads/skyfall.avi", "r+")
    #f = open("/home/i2cat/Downloads/pirates.avi", "r+")
    #f = open("/home/i2cat/Downloads/sample.jpg", "r+")
    data = f.read()
    client.write(data, random_db_id)
    f.close()
    print "DB_ID: ", random_db_id
    time.sleep(4)


    """
    while True:

        #f = open("/home/i2cat/Downloads/sample.jpg", "r+")
        #f = open("/home/i2cat/Downloads/music_clip.avi", "r+")
        f = open("/home/i2cat/Downloads/movie_clip.avi", "r+")
        data = f.read()
        client.write(data, (random.randrange(0, 1000)))
        f.close()

        time.sleep(3)
    """
    """
    client.message = "Goodbye, you damned world! After so many times trying to send these packets in the correct order..."
    client.write(client.message, random_db_id)


    time.sleep(4)
    """
    """
    while True:
        read_result = client.read(536)
        f = open("/home/i2cat/Downloads/backup.avi", "w+")
        f.write(read_result)
        f.close()
        time.sleep(2)
    """

    read_result = client.read(random_db_id)
    #read_result = client.auto_read(random_db_id)
    #result = binascii.a2b_hex(read_result)
    f = open("/home/i2cat/Downloads/backup_sd2.mp4", "w+") #destiny
    #f = open("/home/i2cat/Downloads/backup2.avi", "w+") #skyfall
    #f = open("/home/i2cat/Downloads/backup3.avi", "w+") #pirates
    #f = open("/home/i2cat/Downloads/backup.jpg", "w+") #image
    f.write(read_result)
    f.close()

    """
    print "read_result: ", read_result
    """
    sock1.close()
