#!/usr/bin/env python2.4

# This is the postmortem back end for the BPMs
#
# The program waits for a reponse on all the monitored channels, then it
# checks the time stamps are all the same. If not it will continue waiting
# checking the timestamps each time a channel is updated. Once all timestamps
# agree the data is written to a mat file. The program then waits for 5 sec
# before looking again.  The program masks out data with timestamps before 1
# jan 1990 as this indicates a machine has been restarted after the postmortem
# signal occured.
#
# Currently it can't cope with a nonresponsive machine ( adding a timeout)
# Authors Alun Morgan and Michael Abbot


if __name__ == "__main__":
    from pkg_resources import require as Require
    Require('cothread')

# Sets the max waveform size for EPICS.  This needs to be set *before* we
# load the cothread library so that CA pays attention to it!
import os, datetime, time
os.environ["EPICS_CA_MAX_ARRAY_BYTES"] = "3000000"

import sys
from cothread import *
from cothread.catools import *
from cothread.cothread import Timer
from numpy import *
from scipy.io import savemat,loadmat
from scipy.signal import lfilter

from decimate import decimate

PMDIR = "/home/ops/BPMs/BPM_postmortems"
FNAME = "bpm_postmortem"


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
    def __init__(self, pv_count, filter):
        self.filter = filter
        
        tt_length = 1000
        fa_length = 307
        
        self.xy = zeros((pv_count, tt_length), dtype = float)
        self.xyfa = zeros((pv_count, fa_length), dtype = float)
#        self.good = arange(168)

    def update(self, waveform, index):
        self.xy[index] = waveform[-1500:-500]
        self.xyfa[index] = self.filter.tt2fa(waveform)

    def write(self, time, filename):
        savemat(filename, {
            'x':   1e-6 * self.xy[::2].T,
            'y':   1e-6 * self.xy[1::2].T,
            'xfa': 1e-6 * self.xyfa[::2].T,
            'yfa': 1e-6 * self.xyfa[1::2].T,
#            'good': self.good,
            'time': time }, appendmat=True)

    def reset(self):
        self.xy[:] = 0
        self.xyfa[:] = 0
        

class Saver:

    # object constructor
    def __init__(self, pv_list, wf_len, filter):
        self.pv_list = pv_list
        self.pv_count = len(pv_list)
        self.results = Result(self.pv_count, filter)
        # lookup index name from channel name
        self.stamps = zeros(self.pv_count)    
        self.seen = zeros(self.pv_count, dtype = bool)
        # adding a mask as some machines may have been restarted 
        #or have dropped off the network
        self.mask = zeros(self.pv_count, dtype = bool)
        self.seen[:] = False
        self.mask[:] = True
        # initialising stopwatch
        #self.stopwatch=Timer(5,self.mask_timeout()) 
        #self.stopwatch.cancel()
        #connect pvs

        camonitor(
            self.pv_list, self.update_array_entry, format = FORMAT_TIME)      

    def update_array_entry(self, new_value, index):
        sys.stderr.write('[')

        # Record the incoming data.
        self.results.update(new_value, index)
        self.stamps[index] = new_value.timestamp
        self.seen[index] = True

        # if a machine is restarted the postmortem timestamp is 1 jan 1990 or
        # 1 Jan 1970. Therefore if the timestamp is prior to 1 jan 1990 mask
        # it out.
        if (new_value.timestamp < 631152001.0):
            self.mask[index] = False
        else:
            self.mask[index] = True   

        #(Re)start timer
#        print 'Resetting timer'
       # self.stopwatch.cancel()
       # self.stopwatch=Timer(5,self.mask_timeout())
       
        self.check_array()
        
        sys.stderr.write('.')


    def check_array(self):
#        print 'Checking if all the non masked PVs have been seen'
        a = self.seen & self.mask
        b = ~self.mask
        c = a | b
        if alltrue(c):
            print ' Yes they have'
           # self.stopwatch.cancel()
            if alltrue(b):
                print 'No valid timestamps'
                self.reset()
            else:
                print ' Valid timestamps'
                # If we've seen them all then check that they've all got the
                # same timestamp. (within 1 sec and for the valid machines)
                if True:        
                    # Compute the filename as the timestamp in UTC format in
                    # seconds.
                    self.write_result(
                        self.stamps[0],
                        self.filename(self.stamps[0]))
                    self.reset()
                else:
                    # If the timestamps don't match keep on watching until they
                    # do.
                    print 'Timestamps don\'t match'
        else:
            pass
#            print 'No they haven\'t '
        
    def mask_timeout(self):
    # if timeout occours mask out missing PVs
        print 'Timed out setting all non responsive channel masks to false'
        self.mask = logical_and(self.seen, self.mask)

    def filename(self, new_value):
        # Computes the filename from the timestamp.
        datestring = datetime.datetime.utcfromtimestamp(
            new_value).replace(microsecond = 0).isoformat()
        return os.path.join(PMDIR,
            '%s-%s.mat' % (FNAME, datestring))

    def write_result(self, time, filename):
        if os.path.isfile(filename):
            print 'File %s already exists' % filename
        else:
            print 'Writing pm', filename
            self.results.write(time, filename)
        
    def reset(self):
        print 'Resetting'
        self.results.reset()
        self.stamps[:] = 0
        self.seen[:] = False
        self.mask[:] = True
        Sleep(5)
            
  
# epics channels for RF
pv_list = [
    'SR%02dC-DI-EBPM-%02d:PM:WF%c' % (cell, position, xy)
        for cell in range(1,25) 
        for position in range(1,8)
        for xy in 'XY']


filter = Filter('liberafilter.mat')

# save task
if __name__ == "__main__":
    Saver(pv_list, 2**14, filter)
    WaitForQuit()
