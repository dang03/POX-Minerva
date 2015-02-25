#!/usr/bin/env python
# encoding: utf-8

__author__ = 'Daniel'

"""
Simple Graphic User Interface (GUI) for Pathfinder SDNapp
"""

from PIL import ImageFile, Image

import SimpleGUICS2Pygame.simpleguics2pygame as simplegui
import sys

import xmlrpclib
import time
from service_thread import ServiceThread
from SimpleXMLRPCServer import SimpleXMLRPCServer

# ## Globals (state)
message = "GUI Test"
store = 0
inData = 0
#im = Image.open("/home/i2cat/Documents/test.png", mode='r')
#im = simplegui.load_image("http://commondatastorage.googleapis.com/codeskulptor-assets/gutenberg.jpg")
im = simplegui.load_image("/home/i2cat/Documents/test.png")
### Helper functions


### Classes


### Define event handlers
# Handler for mouse click
def click(pos=None):
    global message
    global mag_pos
    message = "Click"
    if pos:
        mag_pos = list(pos)

# Handler to draw on canvas
def draw(canvas):
    canvas.draw_image(im, [IMA_WIDTH // 2, IMA_HEIGHT // 2], [IMA_WIDTH, IMA_HEIGHT], [CAN_WIDTH // 2, CAN_HEIGHT // 2], [CAN_WIDTH, CAN_HEIGHT])
    ima_center = [SCALE * mag_pos[0], SCALE * mag_pos[1]]
    ima_rectangle = [MAG_SIZE, MAG_SIZE]
    mag_center = mag_pos
    mag_rectangle = [MAG_SIZE, MAG_SIZE]
    canvas.draw_image(im, ima_center, ima_rectangle, mag_center, mag_rectangle)

    if inData:
        canvas.draw_text(str(inData), [50, 223], 48, "Green")


def tick():
    print "QoS SDNapp"


def output():
    '''print content of store and operand'''
    print "Store = ", store
    print "Input = ", inData
    print " "


def swap():
    '''swap contents of store and operand'''
    global store, inData
    store, inData = inData, store
    output()


def enter(t):
    '''input for a new data'''
    global inData
    inData = int(t)
    output()


def exit():
    '''Closes GUI window'''
    sys.exit()

def a_service():
    string = "Starting A-server"
    ServiceThread.start_in_new_thread(a_server, string)
    return

def a_server(string=None):
    def ping():
        print "Ping Received in SERVER A"
        return "Pong_A"

    def read(db_id):
        print "Server A: Reading file with ID %d" % db_id
        f = open("/home/flowA/" + str(db_id), "r+")
        data = f.read()
        f.close()
        return data

    def write(data, db_id):
        print "Server A: writing file with ID %d" % db_id
        f = open("/home/flowA/" + str(db_id), "w+")
        f.write(data)
        f.close()
        return "SERVER A: Data Correctly Saved"

    def timer(string):
        print string
        time.sleep(30)
        print "AWAKEN"
        status.up = False
        print "keep_running(timer)", status.up
        return

    def handle_timer():
        string = "TIMER START - 30"
        ServiceThread.start_in_new_thread(timer, string)
        return status.up

    def keepRunning(status):
        print "keepRunning", status.up
        handle_timer()
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

    while keepRunning(status):
        print "server A active"
        print "keepRunning(loop)", status.up
        #server.handle_request()


    print mcolors.FAIL+"SERVICE DOWN!"+mcolors.ENDC


# Image, canvas, magnifier sizes
IMA_WIDTH = 800
IMA_HEIGHT = 600

SCALE = 3

CAN_WIDTH = IMA_WIDTH // SCALE
CAN_HEIGHT = IMA_HEIGHT // SCALE

MAG_SIZE = 120
mag_pos = [CAN_WIDTH // 2, CAN_HEIGHT // 2]


# create frame
f = simplegui.create_frame("SDNapp: Pathfinder GUI", CAN_WIDTH, CAN_HEIGHT)

#im.save("/home/i2cat/Documents/test4534.png")


# register event handlers
#f.add_button("Print", output, 100)
#f.add_button("Swap",swap, 100)
f.add_button("Start A", a_service, 100)
f.add_button("Start B", tick, 100)
f.add_button("Start AxB", click, 100)
f.add_button("Exit", exit, 100)
f.add_input("Enter", enter, 100)


# Main
f.set_mouseclick_handler(click)
f.set_draw_handler(draw)
f.start()

"""
# Some practice on python GUIs
def add():
    '''add operand to store'''
    global store
    store = store + operand
    output()


# Main
timer = simplegui.create_timer(1000, tick)
frame = simplegui.create_frame("Frame", 500, 500, 200)
frame.add_button("Send", click)
frame.add_button("View", click)
frame.set_draw_handler(draw)

frame.start()
timer.start()
"""