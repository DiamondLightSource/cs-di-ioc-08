#!/usr/bin/env python2.4

# This is the frontend for the BPM postmortem.
from pkg_resources import require
require('cothread==1.5')
require('matplotlib==0.91.1')

from cothread import *
iqt()

from pylab import *
from numpy import *
from qt import *
from scipy.io import loadmat
import sys
from datetime import datetime
from bpm_pm_file_select import *

path_to_files = '/home/ops/BPMs/BPM_postmortems/'

# if given an argument (whatever) will use file_list to find out the required filenames otherwise it will ask for a file through the browser.
print len(sys.argv)
if len(sys.argv) == 7:
    filenames = file_list(sys.argv[1],path_to_files,sys.argv[2],sys.argv[3],sys.argv[4],sys.argv[5])
    print filenames
elif len(sys.argv) == 2:
    # takes the n newest files
    filenames = file_list(sys.argv[1],path_to_files,'*','*','*','*')
    print filenames
else:
    filenames = []
    # No filename specified, so prompt for filename!
    import tkFileDialog
    filename = tkFileDialog.askopenfilename(
        initialdir = path_to_files,
        filetypes = ['mat *.mat'])
    if not filename:
        sys.exit(1)
    else:
        filenames.append(filename)
    print filenames    
        
print 'Loading postmortem'


utctime = []
xfa = []
yfa = []
x = []
y = []

for filename in filenames:
    m = loadmat(filename)
    # splitting out the data and the timestamp
    utctime.append(m['time'])
    # filtered postmortem data for x and y
#    xfa.append(m['xfa'])
#    yfa.append(m['yfa'])
    x.append(m['x'])
    y.append(m['y'])

#f_t = 533818.
#start = -15384000 / f_t
#stop = 999000. / f_t
#fa_turnbase = linspace(start, stop, len(xfa[0]))
tt_turnbase = linspace(-500, 500, len(x[0]))

ioff()
a = axes([0,0,1,0.93],axisbg='grey')
setp(a,xticks=[],yticks=[])
time = datetime.fromtimestamp(utctime[0])   
disptime = ['BPM postmortem for ',str(time.day),'/',str(time.month),'/',str(time.year),' at ',str(time.hour),':',str(time.minute),'.',str(time.second)]
disptime = ''.join(disptime)
title(disptime)

axes([0.1,0.08+0.45,0.35,0.3])
imshow(x[0], aspect='auto', interpolation=None)
axhline(y=500, color='r', ls='--')
for p in arange(24):
    axvline(x=p*7,color='grey', ls='--', alpha=0.5)
axis([0,168,1000,0])
yticks(arange(11)*100,(arange(11)*100)-500)
xlabel('BPM number')
ylabel('<-- Turns <--')


axes([0.1,0.08,0.35,0.3])
plot(tt_turnbase, x[0])
axvline(0)
axhline(y=1, color='r', ls='--')
axhline(y=-1, color='r', ls='--')
axis([-500,500,-5, 5])
xlabel('turns relative to post mortem event')
ylabel('X [mm]')
title('    RF <--|--> MPS')

axes([0.6,0.08+0.45,0.35,0.3])
imshow(y[0], aspect='auto', interpolation=None)
axhline(y=500, color='r', ls='--')
for p in arange(24):
    axvline(x=p*7,color='grey', ls='--', alpha=0.5)
axis([0,168,1000,0])
yticks(arange(11)*100,(arange(11)*100)-500)
xlabel('BPM number')
ylabel('<-- Turns <--')

axes([0.6,0.08,0.35,0.3])
plot(tt_turnbase, y[0])
axvline(0)
axhline(y=1, color='r', ls='--')
axhline(y=-1, color='r', ls='--')
axis([-500,500,-5, 5])
xlabel('turns relative to post mortem event')
ylabel('Y [mm]')
title('    RF <--|--> MPS')

show()
WaitForQuit()

