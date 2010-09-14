# Postmortem plotting function support

import pylab
import numpy
import bpms

PLOT_TITLE = 'Interlock trigger times\n (X=blue Y=green ADC=red)'

def plot_offsets(enabled, x, y, adc, title=PLOT_TITLE, xlabel='Turns'):
    ids = numpy.array(bpms.BPM_ids)[enabled]
    pylab.plot(x[enabled],   ids, '.')
    pylab.plot(y[enabled],   ids, '.')
    pylab.plot(adc[enabled], ids, '.')

    a24 = numpy.arange(24) + 1
    for p in a24:
        pylab.axhline(y=p, color='grey', ls='--', alpha=0.5)
    pylab.axvline(x=0, color='grey')
    pylab.axis([-200, 600, 0.9, 24.9])
    pylab.yticks(a24, a24)

    pylab.xlabel('Turns')
    pylab.ylabel('CIA number')
    pylab.title(title)


def plot_positions(axis, units, t_x, x, t_s, s, show_mps=False):
    x_lines = pylab.plot(t_x, x)
    for l, c in zip(x_lines, bpms.BPM_colours):
        l.set_color(c)
    pylab.plot(t_s, s, 'b--')
    pylab.axvline(0, color='g')
    pylab.axhline(y=1, color='r', ls='--')
    pylab.axhline(y=-1, color='r', ls='--')
    pylab.axis([t_x[0], t_x[len(t_x)-1], -5, 5])
    pylab.annotate(
        'Current', xy=(t_x[50], 4), xytext=(t_x[2], 4.4),
        arrowprops =dict(facecolor='black', shrink=0.05, width=1,
        frac=0.1, headwidth=5))
    if show_mps:
        pylab.annotate(
            'MPS\nlimit', xy=(t_x[50], 1), xytext=(t_x[10], 1.4),
            arrowprops=dict(facecolor='black', shrink=0.05, width=1,
            frac=0.1, headwidth=5))
        pylab.annotate(
            'MPS\nlimit', xy=(t_x[50], -1), xytext=(t_x[10], -2.5),
            arrowprops=dict(facecolor='black', shrink=0.05, width=1,
            frac=0.1, headwidth=5))
    pylab.xlabel('%s relative to post mortem event' % units)
    pylab.ylabel('%s [mm]' % axis)
