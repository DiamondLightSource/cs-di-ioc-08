#!/usr/bin/env python2.4

# This is the postmortem back end for the BPMs
#
# The program waits for POSTMORTEM_TIMEOUT and then returns the data it has recieved. It uses the good/bad data from the concentrator to remove spurious data.
#
# Authors Alun Morgan and Michael Abbot


if __name__ == '__main__':
    from pkg_resources import require as Require
    Require('numpy==1.1.0')
    Require('cothread==1.9')


# Controlling definitions
POSTMORTEM_TIMEOUT = 15
QUIESCENT_TIMEOUT = 120


# Sets the max waveform size for EPICS.  This needs to be set *before* we
# load the cothread library so that CA pays attention to it!
import os, datetime, time
os.environ['EPICS_CA_MAX_ARRAY_BYTES'] = '1000000'

import sys
from cothread import *
from cothread.catools import *
from numpy import *
from scipy.io import savemat, loadmat
from scipy.signal import lfilter

from decimate import decimate


DEBUG = 'D' in sys.argv

if DEBUG:
    PMDIR = '/tmp/BPM_postmortems'
else:
    PMDIR = '/dls/ops-data/Postmortems/BPM_postmortems'
FNAME = 'bpm_postmortem'


class Filter:
    def __init__(self, filename):
        taps = loadmat(filename)
        for name in taps.keys():
            setattr(self, name, taps[name])
        self.fir_sum = sum(self.fir)

    def tt2fa(self, waveform):
        # This filters the data from FA to TT to mimic what the BPMs do.

        # First apply the polyphase low pass filter and decimate the data
        # 1:53.  
        waveform = decimate(waveform, self.fir, 53) / self.fir_sum
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
        self.xy   = zeros((2, bpm_count, self.tt_length), dtype = float)
        self.xyfa = zeros((2, bpm_count, self.fa_length), dtype = float)
        self.s  = zeros((bpm_count, self.capture_length), dtype = float)
        self.offsets = zeros((3, bpm_count), dtype = int)

    def update_xy(self, xy, bpm, waveform):
        self.stamp = waveform.timestamp
        self.xy[xy, bpm] = waveform[-1500:-500]
        self.xyfa[xy, bpm] = self.filter.tt2fa(waveform)
        
    def update_s(self, waveform, bpm):
        self.s[bpm] = waveform
        
    def update_offset(self, index, bpm, offset):
        self.offsets[index, bpm] = offset

    def timestamp(self):
        return self.stamp
        
    def RemoveDisabled(self):
    # Getting the enabled/disabled status of the BPMs from the concentrator
        self.good = caget('SR-DI-EBPM-01:ENABLED')
        good = self.good > 0
        s =   self.s
        x =   1e-6 * self.xy[0]
        y =   1e-6 * self.xy[1]
        xfa = 1e-6 * self.xyfa[0]
        yfa = 1e-6 * self.xyfa[1]
        x_offset = self.offsets[0]
        y_offset = self.offsets[1]
        adc_offset = self.offsets[2]
        

        good_select = good == False
        # remove the bad BPM data
        s = s[good_select]   
        #setting the data for the disabled position to NaN 
        x[good] = NaN
        y[good] = NaN
        xfa[good] = NaN        
        yfa[good] = NaN
        x_offset[good] = NaN
        y_offset[good] = NaN
        adc_offset[good] = NaN
        
        # getting things in the correct format for writing
        self.s_out = s.mean(0)
        self.x = x.T
        self.y = y.T
        self.xfa = xfa.T
        self.yfa = yfa.T
        self.x_offset = x_offset
        self.y_offset = y_offset
        self.adc_offset = adc_offset
                                
    def write(self, time, filename):
       savemat(filename, dict(
            x = self.x,
            y = self.y,
            s = self.s_out,
            xfa = self.xfa,
            yfa = self.yfa,
            x_offset = self.x_offset,
            y_offset = self.y_offset,
            adc_offset = self.adc_offset,
            time = time ), appendmat=True)    

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

        camonitor(s_pvs, self.update_s, format = FORMAT_TIME)
        self.camonitor_group(xy_pvs,     self.results.update_xy)
        self.camonitor_group(offset_pvs, self.results.update_offset)


    def camonitor_group(self, group_list, action):
        for group, pvs in enumerate(group_list):
            for bpm, pv in enumerate(pvs):
                camonitor(pv,
                    lambda value, group=group, bpm=bpm:
                        self.update_group(group, bpm, value, action),
                    format = FORMAT_TIME)

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
            Timer(POSTMORTEM_TIMEOUT, self.CaptureComplete)
        return True

    def CaptureComplete(self):
        print 'Capture complete triggered!'
        self.timer_state = self.TIMER_QUIESCENT
        # Write out whatever we have now.
        self.results.RemoveDisabled()
        self.write_result()
        self.results.reset()

        # Now ignore any further updates for a little while.  This prevents
        # insanity if something busy is going on!  We'll trigger at most once
        # every two minutes...
        Sleep(QUIESCENT_TIMEOUT)

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
        time = self.results.timestamp()
        dirname, filename = self.filename(time)
        if os.path.isfile(filename):
            print 'File %s already exists' % filename
        else:
            if not os.path.isdir(dirname):
                print 'Creating', dirname
                os.mkdir(dirname)
            print 'Writing pm', filename
            self.results.write(time, filename)

            
  

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
if __name__ == '__main__':
    Saver(filter, xy_pvs, s_pvs, offset_pvs, good_pvs)
    WaitForQuit()
