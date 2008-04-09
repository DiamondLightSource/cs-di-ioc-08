#!/usr/bin/env python2.4

# This is the frontend for the BPM postmortem.
from pkg_resources import require
require('cothread')
require('matplotlib')

from cothread import *
iqt()

#import pylab
from pylab import *

import matplotlib.backends.backend_qt
import qt, plotter

def paintEvent(self, e):
    print "hello"
    p = qt.QPainter(self)
    p.fillRect(qt.QWidget.rect(self), qt.QBrush(qt.Qt.white))
    pt = plotter.Plotter(p, self.get_width_height()[1])
    self.figure.draw(pt)
    p.end()

matplotlib.backends.backend_qtagg.FigureCanvasQTAgg.paintEvent = paintEvent

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
# filtered postmortem data for x and y
xfa = m['xfa']
yfa = m['yfa']

#What units are the y axis in (original data is in nm? um? mm?)
# assuming nm for the moment
xfa = xfa / 1000000
yfa = yfa / 1000000

turnbase = linspace(-2**14+1000,1000,len(xfa))

# keep = backend_qtagg.test()
fig = figure(1001)
print fig.canvas
print fig.canvas.__class__.paintEvent
print fig.canvas.paintEvent

# fig.canvas.paintEvent(None)

ioff()
a = axes([0,0,1,0.93],axisbg='grey')
setp(a,xticks=[],yticks=[])
time = datetime.fromtimestamp(utctime)   
disptime = ['BPM postmortem for ',str(time.day),'/',str(time.month),'/',str(time.year),' at ',str(time.hour),':',str(time.minute),'.',str(time.second)]
disptime = ''.join(disptime)
title(disptime)

axes([0.1,0.08+0.45,0.35,0.3])
plot(turnbase,xfa)
axvline(0)
axhline(y=1, color='r', ls='--')
axhline(y=-1, color='r', ls='--')
axis([-13000,1000,-2, 2])
xlabel('turns relative to post mortem event')
ylabel('X [mm]')

axes([0.1,0.08,0.35,0.3])
plot(turnbase,xfa)
axvline(0)
axhline(y=1, color='r', ls='--')
axhline(y=-1, color='r', ls='--')
axis([-500,500,-5, 5])
xlabel('turns relative to post mortem event')
ylabel('X [mm]')
title('    RF <--|--> MPS')

axes([0.6,0.08+0.45,0.35,0.3])
plot(turnbase,yfa)
axvline(0)
axhline(y=1, color='r', ls='--')
axhline(y=-1, color='r', ls='--')
axis([-13000,1000,-2, 2])
xlabel('turns relative to post mortem event')
ylabel('Y [mm]')

axes([0.6,0.08,0.35,0.3])
plot(turnbase,yfa)
axvline(0)
axhline(y=1, color='r', ls='--')
axhline(y=-1, color='r', ls='--')
axis([-500,500,-5, 5])
xlabel('turns relative to post mortem event')
ylabel('Y [mm]')
title('    RF <--|--> MPS')

draw()
show()
WaitForQuit()

