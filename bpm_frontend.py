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
from scipy.interpolate import *
import sys
from datetime import datetime


path_to_files = '/home/ops/BPMs/BPM_postmortems/'
path_to_files = '/tmp/BPM_postmortems'
capture_length = 16384

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
s = (s / max(s))*8 -4

# filtered postmortem data for x and y
xfa = m['xfa']
yfa = m['yfa']


x_offset   = m['x_offset']
y_offset   = m['y_offset']
adc_offset = m['adc_offset']

# turn by turn x axis
tt_turnbase = linspace(-500, 500, len(x))    
# Revolution frequency (Hz)
f_t = 533818.
# full time x axis
trigger_point = (capture_length -1000) / f_t * 1000
fa_turnbase = linspace(0, capture_length/f_t * 1000, len(xfa))
fa_turnbase= fa_turnbase - trigger_point

# x axis to allow tt data to be overlayed ontop of fa data
faasturns    =    fa_turnbase*f_t/1000
faasturns_start = ceil(faasturns[0])
faasturns_stop  = floor(faasturns[len(faasturns)-1])
ttonfa = interp1d(faasturns,fa_turnbase)
ttonfa_turnbase = ttonfa(linspace(faasturns_start,faasturns_stop,faasturns_stop-faasturns_start))

# code to flag up if there has been an ADC overflow
overflow = min(adc_offset)-1250 # -1250 for testing purposes only



ioff()

figure(1)
a = axes([0,0,1,0.93],axisbg='grey')
setp(a,xticks=[],yticks=[])
time = datetime.fromtimestamp(utctime)   
disptime = ['BPM postmortem for ',str(time.day),'/',str(time.month),'/',str(time.year),' at ',str(time.hour),':',str(time.minute),'.',str(time.second), ' UTC']
disptime = ''.join(disptime)
title(disptime)


#
# X positions as overlaid curves
#
axes([0.1,0.08+0.45,0.35,0.3])
plot(fa_turnbase, xfa)
plot(ttonfa_turnbase,s,'b--')
axvline(0)
axhline(y=1, color='r', ls='--')
axhline(y=-1, color='r', ls='--')
axis([fa_turnbase[0],fa_turnbase[len(fa_turnbase)-1],-5, 5])
xlabel('ms relative to post mortem event')
ylabel('X [mm]')
#title('    RF <--|--> MPS')


#
# Y positions as overlaid curves
#
axes([0.6,0.08+0.45,0.35,0.3])
plot(fa_turnbase, yfa)
plot(ttonfa_turnbase,s,'b--')
axvline(0)
axhline(y=1, color='r', ls='--')
axhline(y=-1, color='r', ls='--')
axis([fa_turnbase[0],fa_turnbase[len(fa_turnbase)-1],-5, 5])
xlabel('ms relative to post mortem event')
ylabel('Y [mm]')
#title('    RF <--|--> MPS')

#
# X positions as overlaid curves
#
axes([0.1,0.08,0.35,0.3])
plot(tt_turnbase, x)
plot(tt_turnbase,s[len(s)-1500:len(s)-500],'b--')
# putting in a line to show where the ADC overflow happened
if overflow != capture_length:
    # TODO need to add annotation to line
    axvline(x=overflow-(capture_length-1000),color='r')
# TODO need to add annotation to line (to enable removal of title)
axvline(0)
axhline(y=1, color='r', ls='--')
axhline(y=-1, color='r', ls='--')
axis([-500,500,-5, 5])
xlabel('turns relative to post mortem event')
ylabel('X [mm]')
title('    RF <--|--> MPS')

#
# Y positions as overlaid curves
#
axes([0.6,0.08,0.35,0.3])
plot(tt_turnbase, y)
plot(tt_turnbase,s[len(s)-1500:len(s)-500],'b--')
# putting in a line to show where the ADC overflow happened
if overflow != capture_length:
    # TODO need to add annotation to line
    axvline(x=overflow-(capture_length-1000),color='r')
# TODO need to add annotation to line (to enable removal of title)
axvline(0)
axhline(y=1, color='r', ls='--')
axhline(y=-1, color='r', ls='--')
axis([-500,500,-5, 5])
xlabel('turns relative to post mortem event')
ylabel('Y [mm]')
title('    RF <--|--> MPS')


figure(2)
a = axes([0,0,1,0.93],axisbg='grey')
setp(a,xticks=[],yticks=[])
time = datetime.fromtimestamp(utctime)   
disptime = ['BPM postmortem for ',str(time.day),'/',str(time.month),'/',str(time.year),' at ',str(time.hour),':',str(time.minute),'.',str(time.second), ' UTC']
disptime = ''.join(disptime)
title(disptime)

#
# Trigger overflow Offsets
#
axes([0.1,0.08,0.35,0.3])
plot(x_offset,linspace(1,168,168),'.')
plot(y_offset,linspace(1,168,168),'.')
plot(adc_offset,linspace(1,168,168),'.')
for p in arange(24):
    axhline(y=p*7,color='grey', ls='--', alpha=0.5)
axis([capture_length-1000,capture_length,0,168])
yticks(arange(24)*7,arange(24)+1)
xticks(arange(11)*100+15384,arange(11)*100-500)
xlabel('Turns')
ylabel('CIA number')
title('Times overflows triggered \n (x=blue y=green ADC=red)')


# S (intensity)
axes([0.6,0.08,0.35,0.3])
plot(linspace(-(capture_length-1000),1000,capture_length),s,'k')
yticks([-4,-2,0,2,4],[0,0.25,0.5,0.75,1])
axhline(y=-2, color='grey', ls='--', alpha=0.5)
axhline(y=0, color='grey', ls='--', alpha=0.5)
axhline(y=2, color='grey', ls='--', alpha=0.5)
axvline(0)
xlabel('turns relative to post mortem event')
ylabel('Intensity')
title('    RF <--|--> MPS')

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

show()
WaitForQuit()

