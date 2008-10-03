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
from matplotlib.lines import Line2D


path_to_files = '/dls/ops-data/Postmortems/BPM_postmortems/'
#path_to_files = '/tmp/BPM_postmortems'
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

try:
    disabled = m['enabled'] == 0
except KeyError:
    # For backwards compatibility
    disabled = zeros(168, dtype = bool)
else:
    # If an enabled array was given, use it to knock out all the disabled
    # values.
    for a in (x, y, xfa, yfa):
        a[:,disabled] = NaN
    for a in (x_offset, y_offset, adc_offset):
        a[disabled] = NaN

# convert the offsets into trigger relative offsets
for a in (x_offset, y_offset, adc_offset):
    a -= 15384

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
ttonfa_turnbase = ttonfa(linspace(faasturns_start,faasturns_stop,faasturns_stop-
faasturns_start))

# code to flag up if there has been an ADC overflow
# removing zeros as this means that the libera was rebooted (only a problem for
# initial dataset)
flow_remove_0 = adc_offset != 0
overflow = min(adc_offset[flow_remove_0])

# Generating the main title
time = datetime.utcfromtimestamp(utctime)
disptime = 'BPM postmortem for %02d/%02d/%04d at %02d:%02d.%02d' %( time.day,
time.month, time.year, time.hour, time.minute, time.second)
# class PointBrowser:
#     """
#     Click on a point to select and highlight it -- the data that
#     generated the point will be shown in the lower axes.  Use the 'n'
#     and 'p' keys to browse through the next and pervious points
#     """
#     def __init__(self):
#         self.lastind = 0
#
#     def onpress(self, event):
#         if self.lastind is None:
#             return
#         if event.key not in ('n', 'p'):
#             return
#         if event.key=='n':
#             inc = 1
#         else:
#             inc = -1
#
#         self.lastind += inc
#         self.lastind = clip(self.lastind, 0, len(xs)-1)
#         self.update()
#
#     def onpick(self, event):
#
#        if not isinstance(event.artist, Line2D ):
#            print 'not line'
#            return True
#
#        N = len(event.ind)
#        if not N:
#            print 'No N'
#            return True
#
#        # the click locations
#        x = event.mouseevent.xdata
#        y = event.mouseevent.ydata
#
#        xdata=event.artist._x
#        ydata=event.artist._y
#
#        distances = hypot(x-xdata[event.ind], y-ydata[event.ind])
#        indmin = distances.argmin()
#        dataind = event.ind[indmin]
#
#        self.xs = xdata[dataind]
#        self.ys = ydata[dataind]
#        self.ap_num = event.artist._xcid -2
#
#        self.lastind = dataind
#        self.update()
#
#     def update(self):
#         if self.lastind is None:
#             return
#
#         dataind = self.lastind
#         xs = self.xs
#         ys = self.ys
#
# #         ax.plot(X[dataind])
#         ap_num = self.ap_num
#         cia_num = ap_num//7 + 1
#         bpm_num = ap_num%7
#         x_string = str(xs)[0:4]
#         y_string = str(ys)[0:4]
#         out_string = 'BPM %d,%d\nx %04s\ny %04s' %(cia_num, bpm_num, x_string,
# y_string)
#         print out_string
#         ax.annotate(out_string, xy=(xs,ys), xytext=(0.02,
# 0.25), textcoords='axes fraction',arrowprops=dict(facecolor='black',
# shrink=0.05,width=1, frac=0.1, headwidth=5), horizontalalignment='left',
# verticalalignment='top')
# #         self.selected.set_visible(True)
# #         self.selected.set_data(xs[dataind], ys[dataind])
# #         self.text.set_text('selected: %d'%dataind)
#         fig1.canvas.draw()

# this function will be called when one of the picker Artists is
# clicked on
def onclick(event) :
#    if isinstance(event.artist, Line2D ):
       ax.cla() # need to fix axis selection
       fa_plotting(fa_turnbase, xfa,ttonfa_turnbase,s)
# the click locations
       x = event.xdata
       y = event.ydata
       inaxes = event.inaxes
       x_string = str(x)[0:4]
       y_string = str(y)[0:4]
       out_string = 'x %s \ny %s' %(x_string, y_string)
       ax.annotate(out_string, xy=(x,y), xytext=(0.02,
0.25), textcoords='axes fraction',arrowprops=dict(facecolor='black',
shrink=0.05, width=1, frac=0.1, headwidth=5),horizontalalignment='left',
verticalalignment='top')

#        xdata=event.artist._x
#        ydata=event.artist._y
# # Finds which of the returned data points was closest to the mouse click
#        distances = hypot(x-xdata[event.ind], y-ydata[event.ind])
#        indmin = distances.argmin()
#        dataind = event.ind[indmin]
#        ap_num = event.artist._xcid -2
#        cia_num = ap_num//7 + 1
#        bpm_num = ap_num%7
#        x_point = xdata[dataind]
#        y_point = ydata[dataind]
#        x_string = str(x_point)[0:4]
#        y_string = str(y_point)[0:4]
#        out_string = 'BPM %d,%d\nx %04s\ny %04s' %(cia_num, bpm_num, x_string,
# y_string)
#        print out_string
#        ax.annotate(out_string, xy=(x_point,y_point), xytext=(0.02, 0.25),
# textcoords='axes fraction',arrowprops=dict(facecolor='black', shrink=0.05,
# width=1, frac=0.1, headwidth=5), horizontalalignment='left',
# verticalalignment='top')

# browser = PointBrowser()
ioff()

def fa_plotting(x1, y1, x2, y2):
    plot(x1,y1,picker=5)
    plot(x2,y2,'b--')
    axvline(0, color='g')
    axhline(y=1, color='r', ls='--')
    axhline(y=-1, color='r', ls='--')
    axis([x1[0],x1[len(x1)-1],-5, 5])
    annotate('Current',xy=(x1[50],4),xytext=(x1[2],4.4),arrowprops =dict(facecolor='black', shrink=0.05, width=1, frac=0.1, headwidth=5))
    annotate('MPS\nlimit',xy=(x1[50],1),xytext=(x1[4],1.4), arrowprops=dict(facecolor='black', shrink=0.05, width=1, frac=0.1, headwidth=5))
    annotate('MPS\nlimit',xy=(x1[50],-1),xytext=(x1[4],-2), arrowprops=dict(facecolor='black', shrink=0.05, width=1, frac=0.1, headwidth=5))
    xlabel('ms relative to post mortem event')
    ylabel('X [mm]')

def tt_plotting(x1, y1, x2, y2, overflow):
    plot(x1,y1)
    plot(x2,y2[len(s)-1500:len(s)-500],'b--')
    # putting in a line to show where the ADC overflow happened
    if overflow != capture_length:
        overflow_pos = overflow-(capture_length-1000)
        axvline(x=overflow_pos,color='r')
        annotate('ADC\noverflow',xy=(overflow_pos,1.5),xytext=(-490,2.5),arrowprops=dict(facecolor='black', shrink=0.05, width=1, frac=0.1, headwidth=5))
    annotate('Current',xy=(-300,4),xytext=(-490,4.4),arrowprops=dict(facecolor='black', shrink=0.05, width=1, frac=0.1, headwidth=5))
    axvline(0, color='g')
    axhline(y=1, color='r', ls='--')
    axhline(y=-1, color='r', ls='--')
    axis([-500,500,-5, 5])
    xlabel('turns relative to post mortem event')
    ylabel('X [mm]')



fig1 = figure(1)
a = axes([0,0,1,0.93],axisbg='grey')
setp(a,xticks=[],yticks=[])
title(disptime)

# X positions as overlaid curves
ax = axes([0.07,0.08+0.45,0.40,0.35])
fa_plotting(fa_turnbase, xfa,ttonfa_turnbase,s)
# register for callback
fig1.canvas.mpl_connect('button_press_event', onclick)

# Y positions as overlaid curves
axes([0.55,0.08+0.45,0.40,0.35])
fa_plotting(fa_turnbase, yfa,ttonfa_turnbase,s)

# X positions as overlaid curves
axes([0.07,0.08,0.40,0.35])
tt_plotting(tt_turnbase, x,tt_turnbase,s,overflow)

# Y positions as overlaid curves
axes([0.55,0.08,0.40,0.35])
tt_plotting(tt_turnbase, y,tt_turnbase,s,overflow)


figure(2)
a = axes([0,0,1,0.93],axisbg='grey')
setp(a,xticks=[],yticks=[])
title(disptime)

#
# Trigger overflow Offsets
#
axes([0.07,0.08,0.40,0.32])
plot(x_offset,linspace(1,168,168),'.')
plot(y_offset,linspace(1,168,168),'.')
plot(adc_offset,linspace(1,168,168),'.')
for p in arange(24):
    axhline(y=p*7,color='grey', ls='--', alpha=0.5)
axvline(x=0, color='grey')
axis([-100, 500, 0, 168])
yticks(arange(24)*7,arange(24)+1)
xlabel('Turns')
ylabel('CIA number')
title('Times overflows triggered \n (x=blue y=green ADC=red)')


# S (intensity)
axes([0.55,0.08,0.40,0.32])
plot(linspace(-(capture_length-1000),1000,capture_length),s,'k')
yticks([-4,-2,0,2,4],[0,0.25,0.5,0.75,1])
axhline(y=-2, color='grey', ls='--', alpha=0.5)
axhline(y=0, color='grey', ls='--', alpha=0.5)
axhline(y=2, color='grey', ls='--', alpha=0.5)
axvline(0)
axis([-(capture_length-1000),1000,-4.4,4.4])
xlabel('turns relative to post mortem event')
ylabel('Intensity')
#title('    RF <--|--> MPS')

#
# X position as an image
#
axes([0.07,0.08+0.45,0.40,0.35])
imshow(abs(x), aspect='auto', interpolation=None)
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
axes([0.55,0.08+0.45,0.40,0.35])
imshow(abs(y), aspect='auto', interpolation=None)
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

