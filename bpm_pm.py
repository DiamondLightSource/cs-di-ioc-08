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
require('cothread==2.10')
require('scipy==0.10.1')
require('iocbuilder==3.45')
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
from softioc import pvlog

import elog
import decimate
import plotserv
import bpms


# Controlling definitions
POSTMORTEM_TIMEOUT = 30
QUIESCENT_TIMEOUT = 120
TIMESTAMP_MARGIN = 0.1          # 100ms timestamp discrepancy ignored


MATLAB_EPOCH = 719529           # Days from 1970/1/1 to 1990/1/1


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
    '%(missing_message)s%(bad_timestamps_message)s'


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


# Much the same as camonitor, but with callback arguments in reverse order for
# compatibility with camonitor2d.
def camonitor1d(pvs, action, **kargs):
    for n, pv in enumerate(pvs):
        catools.camonitor(pv, lambda v, n=n: action(n, v), **kargs)

# Camonitor over a two dimensional array of PVs (list of lists).
def camonitor2d(pvss, action, **kargs):
    for n1, pvs in enumerate(pvss):
        for n2, pv in enumerate(pvs):
            catools.camonitor(pv,
                lambda v, n1=n1, n2=n2: action(n1, n2, v), **kargs)


class Result:
    tt_length = 1000
    fa_length = 307
    capture_length = 16384

    def __init__(self, filter, on_start, pvs):
        self.filter = filter
        self.on_start = on_start
        xy_pvs, s_pvs, offsets_pvs, limits_pvs, enabled_pvs = pvs

        bpm_count = len(s_pvs)
        self.valid   = numpy.zeros((2, bpm_count), dtype = bool)
        self.stamps  = numpy.zeros((2, bpm_count), dtype = float)
        self.xy      = numpy.zeros(
            (2, bpm_count, self.tt_length), dtype = float)
        self.xyfa    = numpy.zeros(
            (2, bpm_count, self.fa_length), dtype = float)
        self.s       = numpy.zeros(
            (bpm_count, self.capture_length), dtype = float)
        self.offsets = numpy.zeros((3, bpm_count), dtype = int)
        self.limits  = numpy.zeros((4, bpm_count), dtype = float)
        self.enabled = numpy.zeros(bpm_count, dtype = bool)

        camonitor2d(xy_pvs,      self.update_xy, format = catools.FORMAT_TIME)
        camonitor1d(s_pvs,       self.update_s)
        camonitor2d(offsets_pvs, self.update_offsets)
        camonitor2d(limits_pvs,  self.update_limits)
        camonitor1d(enabled_pvs, self.update_enabled, notify_disconnect = True)


    def update_xy(self, xy, bpm, value):
        sys.stderr.write('[')
        self.valid [xy, bpm] = self.on_start()
        self.stamps[xy, bpm] = value.timestamp
        self.xy    [xy, bpm] = value[-1500:-500]
        self.xyfa  [xy, bpm] = self.filter.tt2fa(value)

    def update_s(self, bpm, value):
        sys.stderr.write('<')
        self.s[bpm] = value

    def update_offsets(self, index, bpm, value):
        self.offsets[index, bpm] = value

    def update_limits(self, index, bpm, value):
        sys.stderr.write('#')
        self.limits[index, bpm] = value

    def update_enabled(self, bpm, value):
        print '%s: %s' % (value.name, value)
        self.enabled[bpm] = value.ok and value == 1


    def timestamp(self):
        return self.stamp

    # Called on completion of capture before finally writing out
    def complete(self):
        self.stamp = numpy.median(self.stamps[self.valid])

    # Returns list of BPM ids with discrepancies in their time stamps and a list
    # of missing bpms
    def faulty_bpms(self):
        # Flag up any BPM with a timestamp discrepancy
        valid = self.valid[0] & self.valid[1]
        errors = numpy.abs(self.stamps - self.stamp) > TIMESTAMP_MARGIN
        bad_timestamps = numpy.flatnonzero((errors[0] | errors[1]) & valid)
        missing = numpy.flatnonzero(~valid)
        return missing, bad_timestamps


    def get_data(self):
        return dict(
            valid       = self.valid,
            time        = unix_to_matlab(self.stamp),
            stamps      = unix_to_matlab(self.stamps),
            x           = 1e-6 * self.xy[0].T,
            y           = 1e-6 * self.xy[1].T,
            xfa         = 1e-6 * self.xyfa[0].T,
            yfa         = 1e-6 * self.xyfa[1].T,
            s           = 1e-6 * self.s.mean(0),
            x_offset    = self.offsets[0],
            y_offset    = self.offsets[1],
            adc_offset  = self.offsets[2],
            bpm_id      = numpy.array(bpms.BPM_ids),
            maxx        = self.limits[0],
            minx        = self.limits[1],
            maxy        = self.limits[2],
            miny        = self.limits[3],
            enabled     = self.enabled)

    def reset(self):
        self.valid[:] = False
        self.stamps[:] = 0
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


def maybe_report(bpm_list, message):
    n = len(bpm_list)
    if n > 0:
        if n > 1:
            plural = 's are'
        else:
            plural = ' is'
        return '\nThe following BPM%s %s: %s\n' % (
            plural, message, ', '.join(bpms.BPMS[i] for i in bpm_list))
    else:
        return ''


# Converts Unix timestamp to Matlab format.
def unix_to_matlab(datetime):
    SECS_PER_DAY = 24 * 60 * 60
    return datetime / SECS_PER_DAY + MATLAB_EPOCH


class Saver:
    # Set of timer states
    TIMER_OFF = 0           # Waiting for first data to arrive
    TIMER_RUNNING = 1       # Waiting for all data to arrive
    TIMER_QUIESCENT = 2     # Ignoring further updates for a bit...

    # object constructor
    def __init__(self, filter, sr_pvs):
        self.results = Result(filter, self.StartTimer, sr_pvs)

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
        self.results.complete()

        # Ensure we only generate something with a valid timestamp
        timestamp = self.results.timestamp()
        if numpy.isnan(timestamp):
            print 'Ignoring PM: no valid timestamp!'
        else:
            self.write_result(timestamp)

        # Needs to be done after preparing image and writing e-log
        self.results.reset()

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

    def write_result(self, timestamp):
        dirname, filename = self.filename(timestamp)
        if os.path.isfile(filename):
            print 'File %s already exists' % filename
        else:
            if not os.path.isdir(dirname):
                print 'Creating', dirname
                os.mkdir(dirname)
            print 'Writing pm', filename
            data = self.results.get_data()
            savemat(filename, data, appendmat=True, oned_as='column')

            # Write a log entry into e-log.  Done as background to avoid
            # matplotlib memory leak.
            safe_fork(self.write_elog_entry,
                filename, data, self.results.faulty_bpms())

    def write_elog_entry(self, filename, data, discrepancies):
        missing, bad_timestamps = discrepancies
        buf = plotserv.display_waveforms(data)
        where = os.path.abspath(os.path.dirname(__file__))
        missing_message = maybe_report(missing, 'missing from this postmortem')
        bad_timestamps_message = maybe_report(bad_timestamps, 'out of sync')
        pm_message = PM_MESSAGE % locals()

        elog.entry('BPM postmortem recorded', pm_message, buf, DEBUG)
        print 'Logged BPM postmortem'


def PV_list(pvs):
    return [
        [pvs('PM:WFX'), pvs('PM:WFY')],     # X and Y positions
        pvs('PM:WFS'),                      # Raw beam intensity
        [pvs('PM:%s_OFFSET' % name)
         for name in ['X', 'Y', 'ADC']],    # Interlock offsets
        [pvs('IL:%s%s' % (mm, xy))          # Interlock limits
         for xy in 'XY' for mm in ['MAX', 'MIN']],
        pvs('CF:ENABLED_S'),                # Enabled flags
    ]


# save task
saver = Saver(Filter('liberafilter.mat'), PV_list(bpms.BPMpvs))


# A couple of identification PVs
builder.SetDeviceName('CS-DI-IOC-08')
builder.stringIn('WHOAMI', VAL = 'EBPM Postmortem Server')
builder.stringIn('HOSTNAME', VAL = os.uname()[1])

builder.LoadDatabase()
softioc.iocInit()

softioc.interactive_ioc(globals())
