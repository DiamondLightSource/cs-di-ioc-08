# This is the postmortem back end for the BPMs
#
# The program waits for POSTMORTEM_TIMEOUT and then returns the data it has
# recieved. It uses the good/bad data from the concentrator to remove spurious
# data.
#
# Authors Alun Morgan and Michael Abbott

from pkg_resources import require
require('cothread==1.16')
require('scipy==0.8.0b1')
require('iocbuilder==3.0')


# Sets the max waveform size for EPICS.  This needs to be set *before* we
# load the cothread library so that CA pays attention to it!
import os, datetime, time
os.environ['EPICS_CA_MAX_ARRAY_BYTES'] = '1000000'

import sys
import cothread
from cothread import catools
import numpy
from scipy.io import savemat, loadmat
from scipy.signal import lfilter

# Python soft IOC imports
import builder
import softioc

import elog
import decimate


# Controlling definitions
POSTMORTEM_TIMEOUT = 30
QUIESCENT_TIMEOUT = 120


DEBUG = 'D' in sys.argv

if DEBUG:
    PMDIR = '/tmp/BPM_postmortems'
else:
    PMDIR = '/dls/ops-data/Postmortems/BPM_postmortems'
FNAME = 'bpm_postmortem'


# The following message is written to e-log on successful writing of a
# postmortem file.
PM_MESSAGE = \
    'Saved in %(filename)s\n' + \
    'Run the following command in a terminal window to view it:\n' + \
    '%(where)s/bpm_frontend.py %(filename)s'


class Filter:
    def __init__(self, filename):
        taps = loadmat(filename, squeeze_me=True)
        for name in taps.keys():
            setattr(self, name, taps[name])
        self.fir_sum = sum(self.fir)
        assert self.fir.ndim == 1

    def tt2fa(self, waveform):
        # This filters the data from FA to TT to mimic what the BPMs do.

        # First apply the polyphase low pass filter and decimate the data
        # 1:53.
        waveform = decimate.decimate(waveform, self.fir, 53) / self.fir_sum
        # Then pass the decimated data through two notch filters (to remove
        # the remaining switching frequencies)
        return lfilter(
            self.n2n, self.n2d,
            lfilter(self.n1n, self.n1d, waveform))


class Result:
    tt_length = 1000
    fa_length = 307
    capture_length = 16384

    def __init__(self, bpm_count, filter):
        self.filter = filter

        self.stamp = 0
        self.xy      = numpy.zeros(
            (2, bpm_count, self.tt_length), dtype = float)
        self.xyfa    = numpy.zeros(
            (2, bpm_count, self.fa_length), dtype = float)
        self.s       = numpy.zeros(
            (bpm_count, self.capture_length), dtype = float)
        self.offsets = numpy.zeros((3, bpm_count), dtype = int)
        self.enabled = numpy.zeros(bpm_count, dtype = bool)

    def update_xy(self, xy, bpm, waveform):
        self.stamp = waveform.timestamp
        self.xy[xy, bpm] = waveform[-1500:-500]
        self.xyfa[xy, bpm] = self.filter.tt2fa(waveform)

    def update_s(self, waveform, bpm):
        self.s[bpm] = waveform

    def update_offset(self, index, bpm, offset):
        self.offsets[index, bpm] = offset

    def update_enabled(self, enabled):
        self.enabled = enabled == 0

    def timestamp(self):
        return self.stamp

    def write(self, filename):
        data = dict(
            time        = self.stamp,
            x           = 1e-6 * self.xy[0].T,
            y           = 1e-6 * self.xy[1].T,
            xfa         = 1e-6 * self.xyfa[0].T,
            yfa         = 1e-6 * self.xyfa[1].T,
            s           = 1e-6 * self.s.mean(0),
            x_offset    = self.offsets[0],
            y_offset    = self.offsets[1],
            adc_offset  = self.offsets[2],
            enabled     = self.enabled)
        savemat(filename, data, appendmat=True, oned_as='column')

    def reset(self):
        self.xy[:] = 0
        self.xyfa[:] = 0
        self.s[:] = 0
        self.offsets[:] = 0



class Saver:
    # Set of timer states
    TIMER_OFF = 0           # Waiting for first data to arrive
    TIMER_RUNNING = 1       # Waiting for all data to arrive
    TIMER_QUIESCENT = 2     # Ignoring further updates for a bit...

    # object constructor
    def __init__(self, filter, xy_pvs, s_pvs, offset_pvs, good_pvs):
        self.results = Result(len(s_pvs), filter)

        self.timer_state = self.TIMER_OFF

        catools.camonitor(s_pvs, self.update_s, format = catools.FORMAT_TIME)
        self.camonitor_group(xy_pvs,     self.results.update_xy)
        self.camonitor_group(offset_pvs, self.results.update_offset)
        catools.camonitor('SR-DI-EBPM-01:ENABLED', self.results.update_enabled)


    def camonitor_group(self, group_list, action):
        for group, pvs in enumerate(group_list):
            for bpm, pv in enumerate(pvs):
                catools.camonitor(pv,
                    lambda value, group=group, bpm=bpm:
                        self.update_group(group, bpm, value, action),
                    format = catools.FORMAT_TIME)

    def update_group(self, group, bpm, value, action):
        sys.stderr.write('[')
        if self.StartTimer():
            action(group, bpm, value)

    def update_s(self, waveform, bpm):
        sys.stderr.write('<')
        if self.StartTimer():
            self.results.update_s(waveform, bpm)

    def StartTimer(self):
        if self.timer_state == self.TIMER_QUIESCENT:
            # In quiescent state ignore everything
            return False
        elif self.timer_state == self.TIMER_OFF:
            print 'Starting timer'
            self.timer_state = self.TIMER_RUNNING
            cothread.Timer(POSTMORTEM_TIMEOUT, self.CaptureComplete)
        return True

    def CaptureComplete(self):
        print 'Capture complete triggered!'
        self.timer_state = self.TIMER_QUIESCENT
        # Write out whatever we have now.
        self.write_result()

        # Now ignore any further updates for a little while.  This prevents
        # insanity if something busy is going on!  We'll trigger at most once
        # every two minutes...
        cothread.Sleep(QUIESCENT_TIMEOUT)

        print 'Quiescent complete triggered'
        self.timer_state = self.TIMER_OFF

    def filename(self, time):
        # Computes the filename from the timestamp.
        timestamp = datetime.datetime.utcfromtimestamp(time)
        dirname = '%4d-%02d' % (timestamp.year, timestamp.month)
        dirname = os.path.join(PMDIR, dirname)
        datestring = timestamp.replace(microsecond = 0).isoformat()
        filename = os.path.join(dirname, '%s-%s.mat' % (FNAME, datestring))
        return dirname, filename

    def write_result(self):
        dirname, filename = self.filename(self.results.timestamp())
        if os.path.isfile(filename):
            print 'File %s already exists' % filename
        else:
            if not os.path.isdir(dirname):
                print 'Creating', dirname
                os.mkdir(dirname)
            print 'Writing pm', filename
            self.results.write(filename)
            self.results.reset()

            # Write a log entry into e-log.
            where = os.path.abspath(os.path.dirname(__file__))
            elog.entry('BPM postmortem recorded', PM_MESSAGE % locals(), DEBUG)



def PVs(name):
    return ['SR%02dC-DI-EBPM-%02d:PM:%s' % (cell+1, position+1, name)
        for cell in range(24)
        for position in range(7)]

xy_pvs = [PVs('WFX'), PVs('WFY')]
offset_pvs = [PVs('%s_OFFSET' % name) for name in ['X', 'Y', 'ADC']]
s_pvs = PVs('WFS')
good_pvs = PVs('CF:ENABLED_S')

filter = Filter('liberafilter.mat')

# save task
Saver(filter, xy_pvs, s_pvs, offset_pvs, good_pvs)


# A couple of identification PVs
builder.SetDeviceName('CS-DI-IOC-08')
builder.stringIn('WHOAMI', VAL = 'EBPM Postmortem Server')
builder.stringIn('HOSTNAME', VAL = os.uname()[1])

builder.LoadDatabase()
softioc.iocInit()

from softioc import *
interactive_ioc(globals())
