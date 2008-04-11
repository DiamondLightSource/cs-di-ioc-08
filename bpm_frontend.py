#!/usr/bin/env python2.4

# This is the frontend for the BPM postmortem.
from pkg_resources import require
require('cothread')
require('matplotlib')

from cothread import *
iqt()

from pylab import *
#import numpy
from numpy import *
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

print 'Loading postmortem'
ioff()

m = loadmat(filename)

# splitting out the data and the timestamp
utctime = m['time']
# filtered postmortem data for x and y
xfa = m['xfa']
yfa = m['yfa']
x   = m['x']
y   = m['y']


f_t = 533818.
start = -15384000 / f_t
stop = 999000. / f_t
fa_turnbase = linspace(start, stop, len(xfa))
tt_turnbase = linspace(-500, 500, len(x))

a = axes([0,0,1,0.93],axisbg='grey')
setp(a,xticks=[],yticks=[])
time = datetime.fromtimestamp(utctime)   
disptime = ['BPM postmortem for ',str(time.day),'/',str(time.month),'/',str(time.year),' at ',str(time.hour),':',str(time.minute),'.',str(time.second)]
disptime = ''.join(disptime)
title(disptime)

axes([0.1,0.08+0.45,0.35,0.3])
plot(fa_turnbase,xfa)
axvline(0)
axhline(y=1, color='r', ls='--')
axhline(y=-1, color='r', ls='--')
axis([-25, stop, -2, 2])
xlabel('microseconds relative to post mortem event')
ylabel('X [mm]')

axes([0.1,0.08,0.35,0.3])
plot(tt_turnbase, x)
axvline(0)
axhline(y=1, color='r', ls='--')
axhline(y=-1, color='r', ls='--')
axis([-500,500,-5, 5])
xlabel('turns relative to post mortem event')
ylabel('X [mm]')
title('    RF <--|--> MPS')

axes([0.6,0.08+0.45,0.35,0.3])
plot(fa_turnbase,yfa)
axvline(0)
axhline(y=1, color='r', ls='--')
axhline(y=-1, color='r', ls='--')
axis([-25, stop,-2, 2])
xlabel('microseconds relative to post mortem event')
ylabel('Y [mm]')

axes([0.6,0.08,0.35,0.3])
plot(tt_turnbase, y)
axvline(0)
axhline(y=1, color='r', ls='--')
axhline(y=-1, color='r', ls='--')
axis([-500,500,-5, 5])
xlabel('turns relative to post mortem event')
ylabel('Y [mm]')
title('    RF <--|--> MPS')

show()
WaitForQuit()

