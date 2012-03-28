# This is the postmortem back end for the BPMs
#
# The program waits for POSTMORTEM_TIMEOUT and then returns the data it has
# recieved. It uses the good/bad data from the concentrator to remove spurious
# data.
#
# Authors Alun Morgan and Michael Abbott

import os
os.environ['MPLCONFIGDIR'] = '/tmp'

from pkg_resources import require
require('cothread==1.17')
require('scipy==0.8.0b1')
require('iocbuilder==3.22')
require('matplotlib==0.99.3-r0')


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
from softioc import builder, softioc

import elog
import decimate
import plotserv
import bpms


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

    def __init__(self, filter, on_start, pvs):
        self.filter = filter
        self.on_start = on_start
        xy_pvs, s_pvs, offset_pvs, good_pvs = pvs

        self.stamp = 0
        bpm_count = len(s_pvs)
        self.xy      = numpy.zeros(
            (2, bpm_count, self.tt_length), dtype = float)
        self.xyfa    = numpy.zeros(
            (2, bpm_count, self.fa_length), dtype = float)
        self.s       = numpy.zeros(
            (bpm_count, self.capture_length), dtype = float)
        self.offsets = numpy.zeros((3, bpm_count), dtype = int)
        self.enabled = numpy.zeros(bpm_count, dtype = bool)

        catools.camonitor(s_pvs,         self.update_s)
        catools.camonitor(good_pvs,      self.update_enabled)
        self.camonitor_group(xy_pvs,     self.update_xy)
        self.camonitor_group(offset_pvs, self.update_offset)

    def camonitor_group(self, group_list, action):
        for group, pvs in enumerate(group_list):
            for bpm, pv in enumerate(pvs):
                catools.camonitor(pv,
                    lambda value, group=group, bpm=bpm:
                        self.update_group(group, bpm, value, action),
                    format = catools.FORMAT_TIME)

    def update_s(self, waveform, bpm):
        sys.stderr.write('<')
        if self.on_start():
            self.s[bpm] = waveform

    def update_enabled(self, enabled, bpm):
        self.enabled[bpm] = enabled == 1

    def update_group(self, group, bpm, value, action):
        sys.stderr.write('[')
        if self.on_start():
            action(group, bpm, value)

    def update_xy(self, xy, bpm, waveform):
        self.stamp = waveform.timestamp
        self.xy[xy, bpm] = waveform[-1500:-500]
        self.xyfa[xy, bpm] = self.filter.tt2fa(waveform)

    def update_offset(self, index, bpm, offset):
        self.offsets[index, bpm] = offset

    def timestamp(self):
        return self.stamp

    def get_data(self):
        return dict(
            time        = self.stamp,
            x           = 1e-6 * self.xy[0].T,
            y           = 1e-6 * self.xy[1].T,
            xfa         = 1e-6 * self.xyfa[0].T,
            yfa         = 1e-6 * self.xyfa[1].T,
            s           = 1e-6 * self.s.mean(0),
            x_offset    = self.offsets[0],
            y_offset    = self.offsets[1],
            adc_offset  = self.offsets[2],
            bpm_id      = bpms.BPM_ids,
            enabled     = self.enabled)

    def reset(self):
        self.xy[:] = 0
        self.xyfa[:] = 0
        self.s[:] = 0
        self.offsets[:] = 0


# Routine for invoking a fork with all the appropriate precautions
# Actually, in principle even this isn't safe, see:
#   http://www.linuxprogrammingblog.com/\
#       threads-and-fork-think-twice-before-using-them
# Never mind.  We'll do it anyway...
def safe_fork(fn, *args, **kargs):
    pid = os.fork()
    if pid == 0:
        try:
            fn(*args, **kargs)
        except:
            import traceback
            traceback.print_exc()

        # Rather important that we exit immediately, even if anything
        # above fails.  Also we don't want to do any extra cleaning up,
        # that's the parent process's job.
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(0)
    else:
        # We'd better wait for the fork to complete, otherwise we'll spawn
        # innumerable zombies.  Annoyingly this blocks the parent cothread, but
        # there's no real harm done.
        os.waitpid(pid, 0)



class Saver:
    # Set of timer states
    TIMER_OFF = 0           # Waiting for first data to arrive
    TIMER_RUNNING = 1       # Waiting for all data to arrive
    TIMER_QUIESCENT = 2     # Ignoring further updates for a bit...

    # object constructor
    def __init__(self, filter, sr_pvs, sr10_pvs):
        self.results = Result(filter, self.StartTimer, sr_pvs)
        self.sr10_results = Result(filter, self.StartTimer, sr10_pvs)

        self.timer_state = self.TIMER_OFF

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
            data = self.results.get_data()
            data['SR10'] = self.sr10_results.get_data()
            savemat(filename, data, appendmat=True, oned_as='column')

            # Write a log entry into e-log.  Done as background to avoid
            # matplotlib memory leak.
            safe_fork(self.write_elog_entry, filename, data)

            # Needs to be done after preparing image and writing e-log
            self.results.reset()

    def write_elog_entry(self, filename, data):
        buf = plotserv.display_waveforms(data)
        where = os.path.abspath(os.path.dirname(__file__))
        elog.entry('BPM postmortem recorded', PM_MESSAGE % locals(), buf, DEBUG)
        print 'Logged BPM postmortem'


def SR10S(name):
    return ['SR10S-DI-EBPM-%02d:%s' % (n + 1, name) for n in range(2)]


def PV_list(pvs):
    return [
        [pvs('PM:WFX'), pvs('PM:WFY')],     # X and Y positions
        pvs('PM:WFS'),                      # Raw beam intensity
        [pvs('PM:%s_OFFSET' % name)
         for name in ['X', 'Y', 'ADC']],    # Interlock offsets
        pvs('CF:ENABLED_S'),                # Enabled flags
    ]


# save task
Saver(Filter('liberafilter.mat'), PV_list(bpms.BPMpvs), PV_list(SR10S))


# A couple of identification PVs
builder.SetDeviceName('CS-DI-IOC-08')
builder.stringIn('WHOAMI', VAL = 'EBPM Postmortem Server')
builder.stringIn('HOSTNAME', VAL = os.uname()[1])

builder.LoadDatabase()
softioc.iocInit()

softioc.interactive_ioc(globals())
