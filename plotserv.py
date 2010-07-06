import sys, os

if __name__ == '__main__':
    os.environ['MPLCONFIGDIR'] = '/tmp'
    from pkg_resources import require
    require('matplotlib == 0.99.1.1-r0')
    require('scipy==0.8.0b1')

import matplotlib
matplotlib.use('Agg')

# from pylab import *
# from numpy import *
import pylab
import numpy
import cStringIO, elog

import plotting


# Machine revolution frequency
F_T = 533818.
# Decimation factor for FF
FA_DEC = 53
# Trigger point in original waveform
TRIGGER_DELAY = 15384


# Handy little helper class to convert dictionary into a class
class wrap_dict:
    def __init__(self, d):
        for k, v in d.items():
            setattr(self, k, v)


def display_waveforms(pm):
    pm = wrap_dict(pm)

    # Knock out the disabled waveforms so they don't confuse the display
    disabled = pm.enabled == 0
    pm.x[:, disabled] = numpy.NaN
    pm.y[:, disabled] = numpy.NaN
    pm.xfa[:, disabled] = numpy.NaN
    pm.yfa[:, disabled] = numpy.NaN

    # Prepare the beam current waveforms.  Strange scaling of s so that it fits
    # nicely on the same axes as X and Y, +- 4mm.
    s_fa = 8 * (pm.s / numpy.max(pm.s)) - 4
    s_tt = s_fa[-1500:-500]

    # Common timebases for the various plots
    tt_timebase = numpy.arange(1000) - 500
    fa_timebase = 1e3 / F_T * (
        FA_DEC * numpy.arange(len(pm.xfa)) - TRIGGER_DELAY)
    sfa_timebase = 1e3 / F_T * (numpy.arange(len(pm.s)) - TRIGGER_DELAY)

    pylab.figure(figsize=(13, 8), facecolor='#C0C0C0')

    pylab.axes([0.05, 0.07, 0.3, 0.4])
    plotting.plot_positions('X', 'turns', tt_timebase, pm.x, tt_timebase, s_tt)

    pylab.axes([0.40, 0.07, 0.3, 0.4])
    plotting.plot_positions('Y', 'turns', tt_timebase, pm.y, tt_timebase, s_tt)

    pylab.axes([0.05, 0.55, 0.3, 0.4])
    plotting.plot_positions(
        'X', 'ms', fa_timebase, pm.xfa, sfa_timebase, s_fa, show_mps=True)

    pylab.axes([0.40, 0.55, 0.3, 0.4])
    plotting.plot_positions('Y', 'ms', fa_timebase, pm.yfa, sfa_timebase, s_fa)

    pylab.axes([0.75, 0.1, 0.22, 0.8])
    plotting.plot_offsets(~disabled,
        pm.x_offset - 15384, pm.y_offset - 15384, pm.adc_offset - 15384)

    # print png to string buffer
    buf = cStringIO.StringIO()
    pylab.gcf().canvas.print_png(buf)
    return buf.getvalue()


if __name__ == '__main__':
    file_name = '/dls/ops-data/Postmortems/BPM_postmortems/2010-07/' \
        'bpm_postmortem-2010-07-05T08:17:08.mat'
    from scipy.io import loadmat
    buf = display_waveforms(loadmat(file_name, squeeze_me=True))

    # post to elog
#     elog.entry('BPM postmortem', 'BPM Postmortem test', buf, True)
#     # Write to .png file for review
    file('buf.png', 'w').write(buf)
