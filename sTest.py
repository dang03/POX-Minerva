import binascii
import os
import select
import socket
import SocketServer
import StringIO
import time
import threading
import datetime
from service_thread import ServiceThread

"""
def get_time_now():
    return str(datetime.datetime.now().strftime('%M:%S.%f')[:-3])

message = "EVENT at: %s" % get_time_now()
ServiceThread.start_in_new_thread(network_measurer.logger_thread, message)

def logger(self, message):
    ServiceThread.start_in_new_thread(network_measurer.logger_thread, message)


@staticmethod
def logger_thread(message, log_file="./time_log_3v2.txt"):
    if os.path.exists(log_file):
        l = open(log_file, 'a')
        l.write(message+"\n")

    else:
        l = open(log_file, 'wb')
        l.write(message+"\n")
    l.close()

self.logger(message)
"""


class mcolors:
    OKGREEN = '\033[92m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

    def disable(self):
        self.OKGREEN = ''
        self.FAIL = ''
        self.ENDC = ''

class service_handler():

    sequences_w = []
    sequences_r = []

    def __str_to_bits(self, string):
        return binascii.b2a_hex(string)

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
        header.append(binascii.a2b_hex(data_to_parse.read(2)))    # Protocol
        header.append(binascii.a2b_hex(data_to_parse.read(2)))    # Action
        header.append(int(data_to_parse.read(4), 16))    # Length
        header.append(int(data_to_parse.read(4), 16))  # DB_ID
        header.append(int(data_to_parse.read(4), 16))  # seq
        #print "HEADER: ", header
        body = data_to_parse.read()
        #print "BODY: ", body

        return header, body

    def ping(self):
        print "Ping Received in SERVER TEST"
        buf.truncate(0)
        self.sequences_w[:] = []
        self.sequences_r[:] = []
        action = "P"
        data_hex = hex(0)[2:]
        #print "data_hex", data_hex
        ln_data = len(data_hex)
        header = self.__headerize(action, ln_data, 0, 0)
        packet = header + data_hex
        return packet

    def read(self, db_id, socket, client):
        print "Server TEST: Reading file with ID %d" % db_id
        if os.path.exists("/home/pox/apps/flowAxB/" + str(db_id)):
            f = open("/home/pox/apps/flowAxB/" + str(db_id), "r+")
            data = f.read()
            action = "R"
            output = StringIO.StringIO(data)
            #socket.connect(self.client_address)
            a_packet = output.read(1024)
            #print "FIRST PACKET: ", packet
            n_seq = 0
            print "READY"
            while a_packet:
                self.sequences_r.append(n_seq)
                ln_data = len(a_packet)
                header = self.__headerize(action, ln_data, db_id, n_seq)
                packet = header + a_packet
                print "header, client", header, client
                socket.sendto(packet, client)
                time.sleep(0.00003)
                a_packet = output.read(1024)
                n_seq += 1
                #print "NEXT PACKET: ", packet
            print "TEST data sent"
            output.close()

            #print "Sent SEQ_R: ", self.sequences_r
            print "LENGTH: ", len(self.sequences_r)
            self.sequences_r[:] = []
            f.close()
            return
        else:
            print "File with ID %d not found" % db_id
            return

    def write(self, data, db_id):
        print "Server TEST: writing file with ID %d" % db_id
        if os.path.exists("/home/pox/apps/flowAxB/" + str(db_id)):
            f = open("/home/pox/apps/flowAxB/" + str(db_id), "a")
            f.write(data)
            f.close()
        else:
            f = open("/home/pox/apps/flowAxB/" + str(db_id), "w")
            f.write(data)
            f.close()

        return "SERVER TEST: Data saved"

    def handle(self, sock1, w_a, buff, client):
        #print "PACKET: ", w_a
        global header, body

        while w_a:
                header, body = self.unpacker(w_a)
                #print "BODY: ", body

                if header[1] == 'w':
                    self.sequences_r.append(header[4])
                    buff.write(body)
                    #print "HEADER: ", header
                    w_a = sock1.recv(8192)
                    #print "NEXT PACKET: ", r_a
                    continue

                elif header[1] == "r":
                    self.read(header[3], sock1, client)
                    print "RECOVERY SENT: ", header[3]
                    return

                else:
                    break
                #sock1.settimeout(1)

        #except:
            #print mcolors.FAIL + "TIMEOUT!" + mcolors.ENDC

        w_a = buff.getvalue()
        #print "CONTENT: ", w_a

        if w_a != '':
            print "Received: ", mcolors.OKGREEN + "OK" + mcolors.ENDC

        else:
            print mcolors.FAIL + "WRONG response" + mcolors.ENDC
            w_a = None
        buff.truncate(0)
        #print "CONTENT: ", w_a
        self.write(w_a, header[3])
        print "ATTENDED PACKETS: ", len(self.sequences_r)
        self.sequences_r[:] = []
        """
        if header[1] == "p":
            packet = self.ping()
            socket.sendto(packet, self.client_address)

        elif header[1] == "w":
            #action = "W"
            self.sequences_w.append(header[4])
            buf.write(body)
            print "Packet saved: ", header[3], "SEQ: ", header[4]

        elif header[1] == "r":
            #action = "R"
            self.read(header[3], socket)
            print "RECOVERY SENT: ", header[3]
            #ln_data = 0
            #header = self.__headerize(action, ln_data, header[3])
            #packet = header
            #socket.sendto(packet, self.client_address)

        elif header[1] == "D":
            #action = "W"
            data = buf.getvalue()
            self.write(data, header[3])
            buf.truncate(0)
            print "Data file written for : ", header[3]
            #print "SEQ_W: ", self.sequences_w
            print "LENGTH: ", len(self.sequences_w)
            self.sequences_w[:] = []

        else:
            action = "E"
            data_hex = hex(0)[2:]
            #print "data_hex", data_hex
            ln_data = len(data_hex)
            header = self.__headerize(action, ln_data, 0, 0)
            packet = header + data_hex
            socket.sendto(packet, self.client_address)
        """

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
SERVER_IP = "127.0.0.1"
SERVER_PORT = 9797
s.bind((SERVER_IP, SERVER_PORT))
buf = StringIO.StringIO()
handler = service_handler()
print "Starting SERVER TEST: "


while True:
    try:
        data, addr = s.recvfrom(8192)
        if data:
            handler.handle(s, data, buf, addr)
        #s.settimeout(0)
    except KeyboardInterrupt:
        print "Stop."
        break





