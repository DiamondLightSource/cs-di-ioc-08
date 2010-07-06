# Postmortem plotting function suppor

import pylab
import numpy

def plot_offsets(enabled, x, y, adc):
    bpms = (numpy.arange(168) + 1)[enabled]
    pylab.plot(x[enabled], bpms, '.')
    pylab.plot(y[enabled], bpms, '.')
    pylab.plot(adc[enabled], bpms, '.')

    a24 = numpy.arange(24)
    for p in a24:
        pylab.axhline(y=p*7, color='grey', ls='--', alpha=0.5)
    pylab.axvline(x=0, color='grey')
    pylab.axis([-200, 600, 0, 168])
    pylab.yticks(a24*7, a24+1)

    pylab.xlabel('Turns')
    pylab.ylabel('CIA number')
    pylab.title('Overflow trigger times\n (x=blue y=green ADC=red)')


def plot_positions(axis, units, t_x, x, t_s, s, show_mps=False):
    pylab.plot(t_x, x)
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
