import os
import datetime
import time
import traceback


class network_measurer(object):
    _switched = False

    def __init__(self):
        """
        Initialize

        See LearningSwitch for meaning of 'transparent'
        'reactive' indicates how
        'ignore' is an optional list/set of DPIDs to ignore
        """

        self.a_flow = {"id": "A",
                       "path": ("00:00:00:00:00:02", "00:00:00:00:00:01", "00:00:00:00:00:04", "00:00:00:00:00:03")}
        self.b_flow = {"id": "B",
                       "path": ("00:00:00:00:00:02", "00:00:00:00:00:05", "00:00:00:00:00:04", "00:00:00:00:00:03")}
        self.topology = list()
        self.priority = 65000  # 16777215 # Highest priority

    def logger(self, message):

        if os.path.exists('./time_log.txt'):
            l = open("time_log.txt", 'a')
            l.write(message+"\n")

        else:
            l = open("time_log.txt", 'wb')
            l.write(message+"\n")

    """
    def logger(self):

        self.message = "Packet_In Time: " + str(datetime.datetime.now())
        if os.path.exists('./time_log.txt'):
            l = open("time_log.txt", 'a')
            l.write(self.message+"\n")

        else:
            l = open("time_log.txt", 'w')
            l.write(self.message+"\n")
    """
    """
        startTime = time.time
        print "Packet_In Time: ", datetime.datetime.now()
    """

    def _handle_PacketIn(self, event=None):

        if network_measurer._switched == True:
            print "!!!"
            self.logger(str(time.time()))
            return
        else:
            return

    def timer(self):
        x = 0

        while x < 5:
            time.sleep(1)
            x += 1
            print "Timer >>> ", x

        s = True
        network_measurer._switched = s
        return network_measurer._switched


"""main"""
print network_measurer()._switched
network_measurer().timer()
print network_measurer()._switched
network_measurer()._handle_PacketIn()
#network_measurer().logger(str(time.time()))

