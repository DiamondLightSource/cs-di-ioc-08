#!/usr/bin/env python2.4

# This is the frontend for the BPM postmortem.
from pkg_resources import require
require('cothread')
require('matplotlib')

from cothread import *
iqt()

#import pylab
from pylab import linspace,axes,setp,title,plot,axvline,xlabel,ylabel
#import numpy
from numpy import transpose
import qt
from scipy.io import loadmat
import sys
from datetime import datetime

#print 'args:', sys.argv

if len(sys.argv) > 1:
    filename = sys.argv[1]
else:
    # No filename specified, so prompt for filename!
    import tkFileDialog
    filename = tkFileDialog.askopenfilename(
        initialdir = '/tmp',
        filetypes = ['mat *.mat'])
    if not filename:
        sys.exit(1)

m = loadmat(filename)

# splitting out the data and the timestamp
utctime = m['time']
pm = m['pm']
x = transpose(pm[range(0,336,2)])
y = transpose(pm[range(1,336,2)])

x=x[range(-2000,0)]
y=y[range(-2000,0)]

turnbase = linspace(-1000,1000,2000)
# Need to pull in the RF frequency when the dat is captured
#timebase = turnbase*(1/499.654E6*936)*1000
#What units are the y axis in (original data is in um? mm?)
a = axes([0,0,1,0.93],axisbg='grey')
setp(a,xticks=[],yticks=[])
time = datetime.fromtimestamp(utctime)   
disptime = ['BPM postmortem for ',str(time.day),'/',str(time.month),'/',str(time.year),' at ',str(time.hour),':',str(time.minute),'.',str(time.second)]
disptime = ''.join(disptime)
title(disptime)

axes([0.1,0.08,0.35,0.3])
plot(turnbase,x)
axvline(0)
xlabel('turns relative to post mortem event')
ylabel('X [mm]')
title('    RF <--|--> MPS')

axes([0.6,0.08,0.35,0.3])
#plot(timebase,x)
plot(turnbase[975:1025],x[975:1025])
axvline(0)
xlabel('turns relative to post mortem event')
#xlabel('time [ms] relative to post mortem event')
ylabel('X [mm]')

axes([0.1,0.08+0.45,0.35,0.3])
plot(turnbase,y)
axvline(0)
xlabel('turns relative to post mortem event')
ylabel('Y [mm]')
title('    RF <--|--> MPS')

axes([0.6,0.08+0.45,0.35,0.3])
#plot(timebase,y)
plot(turnbase[975:1025],y[975:1025])
axvline(0)
xlabel('turns relative to post mortem event')
#xlabel('time [ms] relative to post mortem event')
ylabel('Y [mm]')

WaitForQuit()

