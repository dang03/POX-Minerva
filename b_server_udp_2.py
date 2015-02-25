import binascii
import os
import select
import socket
import StringIO
import time
import threading

class mcolors:
    OKGREEN = '\033[92m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

    def disable(self):
        self.OKGREEN = ''
        self.FAIL = ''
        self.ENDC = ''

class service_handler(object):

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
        act = self.__str_to_bits(action)
        ln = hex(length)[2:]
        db = hex(db_id)[2:]
        sq = hex(seq)[2:]

        # Padding: fill difference with chars "0", one byte each
        pd_ln = (4 - len(ln)) * "0" + ln
        pd_db = (4 - len(db)) * "0" + db
        pd_sq = (4 - len(sq)) * "0" + sq

        header = proto + act + pd_ln + pd_db + pd_sq
        return header

    def unpacker(self, data):
        header = []
        data_to_parse = StringIO.StringIO(data)
        header.append(binascii.a2b_hex(data_to_parse.read(2)))    # Protocol
        header.append(binascii.a2b_hex(data_to_parse.read(2)))    # Action
        header.append(int(data_to_parse.read(4), 16))    # Length
        header.append(int(data_to_parse.read(4), 16))  # DB_ID
        header.append(int(data_to_parse.read(4), 16))  # seq
        body = data_to_parse.read()
        return header, body

    def ping(self):
        print "Ping Received in SERVER B"
        self.sequences_w[:] = []
        self.sequences_r[:] = []
        action = "P"
        data_hex = hex(0)[2:]
        ln_data = len(data_hex)
        header = self.__headerize(action, ln_data, 0, 0)
        packet = header + data_hex
        return packet

    def read(self, db_id, socket, client):
        print "Server B: Reading file with ID %d" % db_id
        if os.path.exists("/home/pox/apps/flowB/" + str(db_id)):
            f = open("/home/pox/apps/flowB/" + str(db_id), "r+")
            data = f.read()
            action = "R"
            output = StringIO.StringIO(data)
            packet = output.read(1024)
            n_seq = 0
            while packet:
                self.sequences_r.append(n_seq)
                ln_data = len(packet)
                header = self.__headerize(action, ln_data, db_id, n_seq)
                packet = header + packet
                socket.sendto(packet, client)
                time.sleep(0.00003)
                packet = output.read(1024)
                n_seq += 1
            print "B data sent"
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
        print "Server B: writing file with ID %d" % db_id
        if os.path.exists("/home/pox/apps/flowB/" + str(db_id)):
            f = open("/home/pox/apps/flowB/" + str(db_id), "a")
            f.write(data)
            f.close()
        else:
            f = open("/home/pox/apps/flowB/" + str(db_id), "w")
            f.write(data)
            f.close()

        return "SERVER B: Data saved"

    def handle(self, socket, data, buff, client):
        global header, body

        header, body = self.unpacker(data)

        if header[1] == "p":
            packet = self.ping()
            socket.sendto(packet, client)
            buff.truncate(0)
            return

        elif header[1] == "w":
            self.sequences_w.append(header[4])
            buff.write(body)
            print "Packet saved: ", header[3], "SEQ: ", header[4]
            return

        elif header[1] == "r":
            self.read(header[3], socket, client)
            print mcolors.OKGREEN+"Recovery sent for: "+mcolors.ENDC, header[3]
            return

        elif header[1] == "D":
            data = buff.getvalue()
            self.write(data, header[3])
            buff.truncate(0)
            print mcolors.OKGREEN+"Data file written for : "+mcolors.ENDC, header[3]
            print "LENGTH: ", len(self.sequences_w)
            self.sequences_w[:] = []
            return

        else:
            action = "E"
            data_hex = hex(0)[2:]
            ln_data = len(data_hex)
            header = self.__headerize(action, ln_data, 0, 0)
            packet = header + data_hex
            socket.sendto(packet, client)
            return

def listen(handler, buf, sck):
    while True:
        try:
            ready = select.select([sck, ], [sck], [], 2)
            while ready[0]:

                try:
                    data, addr = sck.recvfrom(8192)
                    handler.handle(sck, data, buf, addr)
                except:     # sck.recv timeouts, buffer is then erased to serve next request
                    buf.truncate(0)
                    break

        except KeyboardInterrupt:
            print "Stop."
            break
    return

def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    SERVER_IP = "127.0.0.1"
    SERVER_PORT = 9696
    s.settimeout(2)
    s.bind((SERVER_IP, SERVER_PORT))
    buf = StringIO.StringIO()
    handler = service_handler()
    print "Starting server B... "

    try:
        server_thread = threading.Thread(target=listen, name=None, args=(handler, buf, s))
        #print "Starting server AxB in Thread: ", server_thread.name
        server_thread.start()
    except KeyboardInterrupt:
        print "Stop."

##########################
if __name__ == "__main__":
    main()
