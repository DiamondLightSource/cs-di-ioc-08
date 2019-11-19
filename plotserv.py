import sys, os

if __name__ == '__main__':
    os.environ['MPLCONFIGDIR'] = '/tmp'
    import requires

import matplotlib
matplotlib.use('Agg')

import pylab
import numpy
import cStringIO, elog

import plotting
import bpms


# Machine revolution frequency
F_T = 533818.
# Decimation factor for FF
FA_DEC = 53
# Trigger point in original waveform
TRIGGER_DELAY = 15384.

# This reflects the group delay of the FA stream relative to TT of around two
# samples due to filtering.
FA_DELAY = 2


# Handy little helper class to convert dictionary into a class
class wrap_dict:
    def __init__(self, d):
        for k, v in d.items():
            setattr(self, k, v)


def display_waveforms(pm):
    pm = wrap_dict(pm)

    # Select only the enabled and valid waveforms for display
    enabled = (pm.enabled == 1) & (pm.valid[0] == 1) & (pm.valid[1] == 1)
    if not enabled.any():
        # Can't do empty plots, it'll just crash
        print 'empty plot'
        return

    bpm_id = pm.bpm_id[enabled]
    x = pm.x[-1500:-500, enabled]
    y = pm.y[-1500:-500, enabled]
    xfa = pm.xfa[:, enabled]
    yfa = pm.yfa[:, enabled]

    colours = numpy.array(bpms.BPM_colours)[enabled]

    # Prepare the beam current waveforms.  Strange scaling of s so that it fits
    # nicely on the same axes as X and Y, +- 4mm.
    s_fa = 8 * (pm.s / numpy.max(pm.s)) - 4
    s_tt = s_fa[-1500:-500]

    # Common timebases for the various plots
    tt_timebase = numpy.arange(1000) - 500
    fa_t_offset = TRIGGER_DELAY - FA_DEC * FA_DELAY
    fa_timebase = 1e3 / F_T * (FA_DEC * numpy.arange(len(pm.xfa)) - fa_t_offset)
    sfa_timebase = 1e3 / F_T * (numpy.arange(len(pm.s)) - fa_t_offset)

    pylab.figure(figsize=(13, 11), facecolor='#C0C0C0')

    pylab.axes([0.05, 0.32, 0.3, 0.29])
    plotting.plot_positions(
        'X', 'Turns', colours, tt_timebase, x, tt_timebase, s_tt)

    pylab.axes([0.40, 0.32, 0.3, 0.29])
    plotting.plot_positions(
        'Y', 'Turns', colours, tt_timebase, y, tt_timebase, s_tt)

    pylab.axes([0.05, 0.67, 0.3, 0.29])
    plotting.plot_positions(
        'X', 'ms', colours, fa_timebase, xfa, sfa_timebase, s_fa,
        show_mps = True, label_mps = True)

    pylab.axes([0.40, 0.67, 0.3, 0.29])
    plotting.plot_positions(
        'Y', 'ms', colours, fa_timebase, yfa, sfa_timebase, s_fa,
        show_mps = True)

    pylab.axes([0.75, 0.32, 0.22, 0.62])
    x_offset   = pm.x_offset[enabled]   - TRIGGER_DELAY
    y_offset   = pm.y_offset[enabled]   - TRIGGER_DELAY
    adc_offset = pm.adc_offset[enabled] - TRIGGER_DELAY
    plotting.plot_offsets(bpm_id, x_offset, y_offset, adc_offset)


    # The precise instant of the interlock is a little difficult to correlate
    # precisely with the stored data, so there's a phase discrepancy.
    T_ILK_FA = int(TRIGGER_DELAY / FA_DEC - FA_DELAY)

    pylab.axes([0.07, 0.05, 0.42, 0.2])
    plotting.plot_limits(
        'X', 'b', bpm_id, pm.minx[enabled], pm.maxx[enabled], xfa[T_ILK_FA],
        (x_offset < 0) | (adc_offset < 0))

    pylab.axes([0.56, 0.05, 0.42, 0.2])
    plotting.plot_limits(
        'Y', 'g', bpm_id, pm.miny[enabled], pm.maxy[enabled], yfa[T_ILK_FA],
        (y_offset < 0) | (adc_offset < 0))


    # print png to string buffer
    buf = cStringIO.StringIO()
    pylab.gcf().canvas.print_png(buf)
    return buf.getvalue()


if __name__ == '__main__':
    file_name = sys.argv[1] if len(sys.argv) > 1 else 'test.mat'

    from scipy.io import loadmat
    buf = display_waveforms(loadmat(file_name, squeeze_me=True))

    # Write to .png file for review
    if buf:
        file('buf.png', 'w').write(buf)
