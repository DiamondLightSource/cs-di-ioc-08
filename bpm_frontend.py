#!/usr/bin/env dls-python

# This is the frontend for the BPM postmortem.

import requires

import numpy
import pylab
import scipy.io
import scipy.interpolate
import sys
from datetime import datetime
from PyQt4 import QtGui

import plotting
import bpms


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
s = (s / numpy.max(s))*8 -4

# As of late 2019 the size of x/y data increased from 1,000 to 16,384 samples.
# Cope with this.
if len(x) > 1000:
    x = x[-1500:-500]
    y = y[-1500:-500]

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
        a[:, disabled] = numpy.NaN

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


pylab.ioff()

def fa_plotting(axis, value):
    plotting.plot_positions(
        axis, 'ms', colours,
        fa_turnbase, value, ttonfa_turnbase, s, show_mps=True)

def tt_plotting(axis, value):
    plotting.plot_positions(
        axis, 'turns', colours,
        tt_turnbase, value, tt_turnbase, s[-1500:-500])

    # Figure out if there was an ADC overflow, and if so show it.
    # We are only interested in visible triggers.
    valid_offset = adc_offset[(-1000 < adc_offset) & (adc_offset < 1000)]
    if len(valid_offset):
        # putting in a line to show where the ADC overflow happened
        overflow_pos = numpy.min(valid_offset)
        pylab.axvline(x = overflow_pos, color = 'r')
        pylab.annotate(
            'ADC\noverflow',
            xy = (overflow_pos, -1.5), xytext = (-490, -4),
            arrowprops = dict(
                facecolor = 'black', shrink = 0.05, width = 1,
                frac = 0.1, headwidth = 5))

def im_plotting(axis, value):
    pylab.imshow(abs(value), aspect='auto', interpolation=None)
    pylab.axhline(y=500, color='r', ls='--')
    for p in numpy.arange(24):
        pylab.axvline(x=p*7, color='grey', ls='--', alpha=0.5)
    pylab.axis([0, 168, len(tt_turnbase), 0])
    pylab.xticks(numpy.arange(24)*7, numpy.arange(24)+1)
    pylab.yticks(numpy.arange(9)*100, numpy.arange(9)*100 -500)
    pylab.xlabel('CIA number')
    pylab.ylabel('<-- turns <--')
    pylab.title(axis)


def plot_offsets(enabled, x, y, adc):
    m = min([numpy.min(t[enabled]) for t in [x, y, adc]])
    for t in [x, y, adc]:
        n = numpy.nonzero(t[enabled] == m)[0]
        if len(n) > 0:
            bpm_num = n[0]
            break

    plotting.plot_offsets(
        enabled, x, y, adc,
        title =
            'Interlock trigger times (X=blue, Y=green, ADC=red)'
            ' First trigger %s' % bpms.BPMS[bpm_num],
        xlabel = 'Turns relative to post mortem event')

    a24 = numpy.arange(24) + 1
    for p in a24:
         for rs in 0.1 * (numpy.arange(7) + 1):
            pylab.axhline(y=p+rs, color='grey', ls=':', alpha=0.15)


colours = numpy.array(bpms.BPM_colours)[~disabled]

fig1 = pylab.figure(1)
a = pylab.axes([0, 0, 1, 0.95], axisbg='grey')
pylab.setp(a, xticks=[], yticks=[])
pylab.title(disptime)

# X positions as overlaid curves
ax = pylab.axes([0.07, 0.08+0.60, 0.41, 0.25])
fa_plotting('X', xfa)

# Y positions as overlaid curves
pylab.axes([0.53, 0.08+0.60, 0.41, 0.25])
fa_plotting('Y', yfa)

# X positions as overlaid curves
pylab.axes([0.07, 0.08+0.30, 0.41, 0.25])
tt_plotting('X', x)

# Y positions as overlaid curves
pylab.axes([0.53, 0.08+0.30, 0.41, 0.25])
tt_plotting('Y', y)

# X position as an image
pylab.axes([0.07, 0.05, 0.18, 0.25])
im_plotting('X',x)

# Y position as an image
pylab.axes([0.30, 0.05, 0.18, 0.25])
im_plotting('Y',y)

# Trigger overflow Offsets
pylab.axes([0.53, 0.05, 0.41, 0.25])
plot_offsets(~disabled, x_offset, y_offset, adc_offset)

pylab.show()
qt_app.exec_()
