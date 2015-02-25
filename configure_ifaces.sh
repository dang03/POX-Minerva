#!/bin/bash

ifconfig eth1 up
vconfig add eth1 1550
ifconfig eth1.1550 up
ifconfig eth1.1550 192.168.1.254
