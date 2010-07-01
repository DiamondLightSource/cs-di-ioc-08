#!/dls_sw/prod/tools/RHEL5/bin/python2.6

# This is the frontend for the BPM postmortem.

from pkg_resources import require
require('matplotlib==0.99.1.1-r0')
require('scipy==0.8.0b1')

import numpy
import pylab
import scipy.io
import scipy.interpolate
import sys
from datetime import datetime
from PyQt4 import QtGui

qt_app = QtGui.QApplication(sys.argv)

path_to_files = '/dls/ops-data/Postmortems/BPM_postmortems/'
capture_length = 16384

# if given an argument (whatever) will use file_list to find out the required
# filenames otherwise it will ask for a file through the browser.
if len(sys.argv) == 1:
    # No filename specified, so prompt for filename!
    filename = QtGui.QFileDialog.getOpenFileName(None,
        'Select Postmortem File', path_to_files, '*.mat')
    if not filename:
        sys.exit(1)
    filename = str(filename)
elif len(sys.argv) == 2:
    filename = sys.argv[1]
else:
    print 'Unexpected extra arguments'
    sys.exit(1)

print 'Loading postmortem', filename


m = scipy.io.loadmat(filename, squeeze_me=True)
# splitting out the data and the timestamp
utctime = m['time']

# turn by turn data for x, y and s
x = m['x']
y = m['y']
s = m['s']
s = (s / max(s))*8 -4

# filtered postmortem data for x and y
xfa = m['xfa']
yfa = m['yfa']

# We convert the offsets to floats so we can use a knockout plotting trick to
# selectively disable certain entries.  We might be better off using a different
# method...
x_offset   = numpy.float_(m['x_offset'])
y_offset   = numpy.float_(m['y_offset'])
adc_offset = numpy.float_(m['adc_offset'])

try:
    disabled = m['enabled'] == 0
except KeyError:
    # For backwards compatibility
    disabled = zeros(168, dtype = bool)
else:
    # If an enabled array was given, use it to knock out all the disabled
    # values.
    for a in (x, y, xfa, yfa):
        a[:, disabled] = numpy.NaN
    for a in (x_offset, y_offset, adc_offset):
        a[disabled] = numpy.NaN

# code to flag up if there has been an ADC overflow
# removing zeros as this means that the libera was rebooted
#(only a problem for initial dataset)
flow_remove_0 = adc_offset != 0
overflow = min(adc_offset[flow_remove_0])

# convert the offsets into trigger relative offsets
for a in (x_offset, y_offset, adc_offset):
    a -= 15384

# turn by turn x axis
tt_turnbase = numpy.linspace(-500, 500, len(x))
# Revolution frequency (Hz)
f_t = 533818.
# full time x axis
trigger_point = (capture_length -1000) / f_t * 1000
fa_turnbase = numpy.linspace(0, capture_length/f_t * 1000, len(xfa))
fa_turnbase= fa_turnbase - trigger_point

# x axis to allow tt data to be overlayed ontop of fa data
faasturns    =    fa_turnbase*f_t/1000
faasturns_start = numpy.ceil(faasturns[0])
faasturns_stop  = numpy.floor(faasturns[len(faasturns)-1])
ttonfa = scipy.interpolate.interp1d(faasturns, fa_turnbase)
ttonfa_turnbase = ttonfa(
    numpy.linspace(faasturns_start, faasturns_stop,
    faasturns_stop - faasturns_start))

# Generating the main title
time = datetime.utcfromtimestamp(utctime)
disptime = 'BPM postmortem for %02d/%02d/%04d at %02d:%02d.%02d' % (
    time.day, time.month, time.year, time.hour, time.minute, time.second)


# browser = PointBrowser()
pylab.ioff()

def fa_plotting(x1, y1, x2, y2):
    pylab.plot(x1, y1, picker=5)
    pylab.plot(x2, y2, 'b--')
    pylab.axvline(0, color='g')
    pylab.axhline(y=1, color='r', ls='--')
    pylab.axhline(y=-1, color='r', ls='--')
    pylab.axis([x1[0], x1[len(x1)-1], -5, 5])
    pylab.annotate(
        'Current', xy=(x1[50], 4), xytext=(x1[2], 4.4),
        arrowprops =dict(facecolor='black', shrink=0.05, width=1,
        frac=0.1, headwidth=5))
    pylab.annotate(
        'MPS\nlimit', xy=(x1[50], 1), xytext=(x1[4], 1.4),
        arrowprops=dict(facecolor='black', shrink=0.05, width=1,
        frac=0.1, headwidth=5))
    pylab.annotate(
        'MPS\nlimit', xy=(x1[50], -1), xytext=(x1[4], -2),
        arrowprops=dict(facecolor='black', shrink=0.05, width=1,
        frac=0.1, headwidth=5))
    pylab.xlabel('ms relative to post mortem event')
    pylab.ylabel('X [mm]')

def tt_plotting(x1, y1, x2, y2, overflow):
    pylab.plot(x1, y1)
    pylab.plot(x2, y2[len(s)-1500:len(s)-500], 'b--')
    # putting in a line to show where the ADC overflow happened
    if overflow != capture_length:
        overflow_pos = overflow-(capture_length-1000)
        pylab.axvline(x=overflow_pos, color='r')
        pylab.annotate(
            'ADC\noverflow', xy=(overflow_pos, 1.5), xytext=(-490, 2.5),
            arrowprops=dict(facecolor='black', shrink=0.05, width=1,
            frac=0.1, headwidth=5))
    pylab.annotate(
        'Current', xy=(-300, 4), xytext=(-490, 4.4),
        arrowprops=dict(facecolor='black', shrink=0.05,
        width=1, frac=0.1, headwidth=5))
    pylab.axvline(0, color='g')
    pylab.axhline(y=1, color='r', ls='--')
    pylab.axhline(y=-1, color='r', ls='--')
    pylab.axis([-500, 500, -5, 5])
    pylab.xlabel('turns relative to post mortem event')
    pylab.ylabel('X [mm]')



fig1 = pylab.figure(1)
a = pylab.axes([0, 0, 1, 0.93], axisbg='grey')
pylab.setp(a, xticks=[], yticks=[])
pylab.title(disptime)

# X positions as overlaid curves
ax = pylab.axes([0.07, 0.08+0.45, 0.40, 0.35])
fa_plotting(fa_turnbase, xfa, ttonfa_turnbase, s)

# Y positions as overlaid curves
pylab.axes([0.55, 0.08+0.45, 0.40, 0.35])
fa_plotting(fa_turnbase, yfa, ttonfa_turnbase, s)

# X positions as overlaid curves
pylab.axes([0.07, 0.08, 0.40, 0.35])
tt_plotting(tt_turnbase, x, tt_turnbase, s, overflow)

# Y positions as overlaid curves
pylab.axes([0.55, 0.08, 0.40, 0.35])
tt_plotting(tt_turnbase, y, tt_turnbase, s, overflow)


pylab.figure(2)
a = pylab.axes([0, 0, 1, 0.93], axisbg='grey')
pylab.setp(a, xticks=[], yticks=[])
pylab.title(disptime)

#
# Trigger overflow Offsets
#
pylab.axes([0.07, 0.08, 0.40, 0.32])
pylab.plot(x_offset, numpy.linspace(1, 168, 168), '.')
pylab.plot(y_offset, numpy.linspace(1, 168, 168), '.')
pylab.plot(adc_offset, numpy.linspace(1, 168, 168), '.')
for p in numpy.arange(24):
    pylab.axhline(y=p*7, color='grey', ls='--', alpha=0.5)
pylab.axvline(x=0, color='grey')
pylab.axis([-200, 600, 0, 168])
pylab.yticks(numpy.arange(24)*7, numpy.arange(24)+1)
pylab.xlabel('Turns')
pylab.ylabel('CIA number')
pylab.title('Times overflows triggered \n (x=blue y=green ADC=red)')


# S (intensity)
pylab.axes([0.55, 0.08, 0.40, 0.32])
pylab.plot(numpy.linspace(-(capture_length-1000), 1000, capture_length), s, 'k')
pylab.yticks([-4, -2, 0, 2, 4], [0, 0.25, 0.5, 0.75, 1])
pylab.axhline(y=-2, color='grey', ls='--', alpha=0.5)
pylab.axhline(y=0, color='grey', ls='--', alpha=0.5)
pylab.axhline(y=2, color='grey', ls='--', alpha=0.5)
pylab.axvline(0)
pylab.axis([-(capture_length-1000), 1000, -4.4, 4.4])
pylab.xlabel('turns relative to post mortem event')
pylab.ylabel('Intensity')
#pylab.title('    RF <--|--> MPS')

#
# X position as an image
#
pylab.axes([0.07, 0.08+0.45, 0.40, 0.35])
pylab.imshow(abs(x), aspect='auto', interpolation=None)
pylab.axhline(y=500, color='r', ls='--')
for p in numpy.arange(24):
    pylab.axvline(x=p*7, color='grey', ls='--', alpha=0.5)
pylab.axis([0, 168, len(tt_turnbase), 0])
pylab.xticks(numpy.arange(24)*7, numpy.arange(24)+1)
pylab.yticks(numpy.arange(9)*100, numpy.arange(9)*100 -500)
pylab.xlabel('CIA number')
pylab.ylabel('<-- turns <--')

#
# Y position as an image
#
pylab.axes([0.55, 0.08+0.45, 0.40, 0.35])
pylab.imshow(abs(y), aspect='auto', interpolation=None)
pylab.axhline(y=500, color='r', ls='--')
for p in numpy.arange(24):
    pylab.axvline(x=p*7, color='grey', ls='--', alpha=0.5)
pylab.axis([0, 168, len(tt_turnbase), 0])
pylab.xticks(numpy.arange(24)*7, numpy.arange(24)+1)
pylab.yticks(numpy.arange(9)*100, numpy.arange(9)*100-500)
pylab.xlabel('CIA number')
pylab.ylabel('<-- turns <--')

pylab.show()
qt_app.exec_()
