#!/usr/bin/env python2.4

# This is the frontend for the BPM postmortem.
from pkg_resources import require
require('numpy==1.1.0')
require('cothread==1.9')
require('matplotlib==0.91.1')

from cothread import *
iqt()

from pylab import *
from numpy import *
from qt import *
from scipy.io import loadmat
import sys
from datetime import datetime


path_to_files = '/home/ops/BPMs/BPM_postmortems/'
path_to_files = '/tmp/BPM_postmortems'

# if given an argument (whatever) will use file_list to find out the required
# filenames otherwise it will ask for a file through the browser.

if len(sys.argv) == 1:
    # No filename specified, so prompt for filename!
    import tkFileDialog
    filename = tkFileDialog.askopenfilename(
        initialdir = path_to_files,
        filetypes = ['mat *.mat'])
    if not filename:
        sys.exit(1)
elif len(sys.argv) == 2:
    filename = sys.argv[1]
else:
    print 'Unexpected extra arguments'
    sys.exit(1)
        
print 'Loading postmortem', filename



m = loadmat(filename)
# splitting out the data and the timestamp
utctime = m['time']
# filtered postmortem data for x and y
xfa=m['xfa']
yfa=m['yfa']
sfa=m['sfa']


f_t = 533818.
start = -15384000 / f_t
stop = 999000. / f_t
fa_turnbase = linspace(start, stop, len(xfa))
# tt_turnbase = linspace(-500, 500, len(x))    
xfa=xfa[-37:-1,:]
yfa= yfa[-37:-1,:]
sfa= sfa[-37:-1]
fa_turnbase= fa_turnbase[-37:-1]
#s = (s / max(s))*8 -4
sfa = (sfa / max(sfa))*8 -4

ioff()
a = axes([0,0,1,0.93],axisbg='grey')
setp(a,xticks=[],yticks=[])
time = datetime.fromtimestamp(utctime)   
disptime = ['BPM postmortem for ',str(time.day),'/',str(time.month),'/',str(time.year),' at ',str(time.hour),':',str(time.minute),'.',str(time.second), ' UTC']
disptime = ''.join(disptime)
title(disptime)

axes([0.1,0.08+0.45,0.35,0.3])
imshow(xfa, aspect='auto', interpolation=None)
axhline(y=18.3, color='r', ls='--')
for p in arange(24):
    axvline(x=p*7,color='grey', ls='--', alpha=0.5)
axis([0,168,len(fa_turnbase),0])
xticks(arange(24)*7,arange(24)+1)
yticks(arange(8)*5,floor(fa_turnbase[arange(8)*5]*10)/10)
xlabel('CIA number')
ylabel('<-- ms <--')


axes([0.1,0.08,0.35,0.3])
plot(fa_turnbase, xfa)
hold
plot(fa_turnbase,sfa,'b--')
axvline(0)
axhline(y=1, color='r', ls='--')
axhline(y=-1, color='r', ls='--')
#axis([-500,500,-5, 5])
axis([-1.85,1.85,-5, 5])
xlabel('ms relative to post mortem event')
#xlabel('turns relative to post mortem event')
ylabel('X [mm]')
title('    RF <--|--> MPS')

axes([0.6,0.08+0.45,0.35,0.3])
imshow(yfa, aspect='auto', interpolation=None)
axhline(y=18.3, color='r', ls='--')
for p in arange(24):
    axvline(x=p*7,color='grey', ls='--', alpha=0.5)
axis([0,168,len(fa_turnbase),0])
xticks(arange(24)*7,arange(24)+1)
yticks(arange(8)*5,floor(fa_turnbase[arange(8)*5]*10)/10)
xlabel('CIA number')
ylabel('<-- ms <--')

axes([0.6,0.08,0.35,0.3])
plot(fa_turnbase, yfa)
hold
plot(fa_turnbase,sfa,'b--')
axvline(0)
axhline(y=1, color='r', ls='--')
axhline(y=-1, color='r', ls='--')
#axis([-500,500,-5, 5])
axis([-1.85,1.85,-5, 5])
xlabel('ms relative to post mortem event')
#xlabel('turns relative to post mortem event')
ylabel('Y [mm]')
title('    RF <--|--> MPS')

show()
WaitForQuit()

