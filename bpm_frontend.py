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

# turn by turn data for x,y and s
x = m['x']
y = m['y']
s = m['s']

# filtered postmortem data for x and y
xfa = m['xfa']
yfa = m['yfa']


x_offset   = m['x_offset']
y_offset   = m['y_offset']
adc_offset = m['adc_offset']

# Revolution frequency
f_t = 533818.
start = -15384000 / f_t
stop = 999000. / f_t


fa_turnbase = linspace(start, stop, len(xfa))
xfa=xfa[-37:-1,:]
yfa= yfa[-37:-1,:]
fa_turnbase= fa_turnbase[-37:-1]

tt_turnbase = linspace(-500, 500, len(x))    
s = (s / max(s))*8 -4


ioff()

figure(1)
a = axes([0,0,1,0.93],axisbg='grey')
setp(a,xticks=[],yticks=[])
time = datetime.fromtimestamp(utctime)   
disptime = ['BPM postmortem for ',str(time.day),'/',str(time.month),'/',str(time.year),' at ',str(time.hour),':',str(time.minute),'.',str(time.second), ' UTC']
disptime = ''.join(disptime)
title(disptime)

#
# Trigger overflow Offsets
#
axes([0.1,0.08+0.45,0.35,0.3])
plot(x_offset,linspace(1,168,168),'.')
plot(y_offset,linspace(1,168,168),'.')
plot(adc_offset,linspace(1,168,168),'.')
for p in arange(24):
    axhline(y=p*7,color='grey', ls='--', alpha=0.5)
axis([15500,16500,0,168])
yticks(arange(24)*7,arange(24)+1)
#xticks(arange(9)*10+15500,arange(9)*10)
xlabel('Turns')
ylabel('CIA number')

# S (intensity)
axes([0.6,0.08+0.45,0.35,0.3])
plot(tt_turnbase,s,'k')
axvline(0)
axis([-500,500,-5, 5])
xlabel('turns relative to post mortem event')
ylabel('Intensity')
title('    RF <--|--> MPS')

#
# X positions as overlaid curves
#
axes([0.1,0.08,0.35,0.3])
plot(fa_turnbase, xfa)
axvline(0)
axhline(y=1, color='r', ls='--')
axhline(y=-1, color='r', ls='--')
axis([-1.85,1.85,-5, 5])
xlabel('ms relative to post mortem event')
ylabel('X [mm]')
title('    RF <--|--> MPS')


#
# Y positions as overlaid curves
#
axes([0.6,0.08,0.35,0.3])
plot(fa_turnbase, yfa)
axvline(0)
axhline(y=1, color='r', ls='--')
axhline(y=-1, color='r', ls='--')
axis([-1.85,1.85,-5, 5])
xlabel('ms relative to post mortem event')
ylabel('Y [mm]')
title('    RF <--|--> MPS')

figure(2)
a = axes([0,0,1,0.93],axisbg='grey')
setp(a,xticks=[],yticks=[])
time = datetime.fromtimestamp(utctime)   
disptime = ['BPM postmortem for ',str(time.day),'/',str(time.month),'/',str(time.year),' at ',str(time.hour),':',str(time.minute),'.',str(time.second), ' UTC']
disptime = ''.join(disptime)
title(disptime)

# #
# # X position as an image
# #
# axes([0.1,0.08+0.45,0.35,0.3])
# imshow(xfa, aspect='auto', interpolation=None)
# axhline(y=18.3, color='r', ls='--')
# for p in arange(24):
#     axvline(x=p*7,color='grey', ls='--', alpha=0.5)
# axis([0,168,len(fa_turnbase),0])
# xticks(arange(24)*7,arange(24)+1)
# yticks(arange(8)*5,floor(fa_turnbase[arange(8)*5]*10)/10)
# xlabel('CIA number')
# ylabel('<-- ms <--')


#
# X position as an image
#
axes([0.1,0.08+0.45,0.35,0.3])
imshow(x, aspect='auto', interpolation=None)
axhline(y=500, color='r', ls='--')
for p in arange(24):
    axvline(x=p*7,color='grey', ls='--', alpha=0.5)
axis([0,168,len(tt_turnbase),0])
xticks(arange(24)*7,arange(24)+1)
yticks(arange(9)*100,arange(9)*100 -500)
xlabel('CIA number')
ylabel('<-- turns <--')


#
# X positions as overlaid curves
#
axes([0.1,0.08,0.35,0.3])
plot(tt_turnbase, x)
plot(tt_turnbase,s,'b--')
axvline(0)
axhline(y=1, color='r', ls='--')
axhline(y=-1, color='r', ls='--')
axis([-500,500,-5, 5])
xlabel('turns relative to post mortem event')
ylabel('X [mm]')
title('    RF <--|--> MPS')

#
# Y position as an image
#
axes([0.6,0.08+0.45,0.35,0.3])
imshow(y, aspect='auto', interpolation=None)
axhline(y=500, color='r', ls='--')
for p in arange(24):
    axvline(x=p*7,color='grey', ls='--', alpha=0.5)
axis([0,168,len(tt_turnbase),0])
xticks(arange(24)*7,arange(24)+1)
yticks(arange(9)*100,arange(9)*100-500)
xlabel('CIA number')
ylabel('<-- turns <--')


#
# Y positions as overlaid curves
#
axes([0.6,0.08,0.35,0.3])
plot(tt_turnbase, y)
plot(tt_turnbase,s,'b--')
axvline(0)
axhline(y=1, color='r', ls='--')
axhline(y=-1, color='r', ls='--')
axis([-500,500,-5, 5])
xlabel('turns relative to post mortem event')
ylabel('Y [mm]')
title('    RF <--|--> MPS')

show()
WaitForQuit()

