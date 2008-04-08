#!/usr/bin/env python2.4

# This is the postmortem back end for the BPMs
#
# The program waits for a reponse on all the monitored channels, then it
# checks the time stamps are all the same. If not it will continue waiting
# checking the timestamps each time a channel is updated. Once all timestamps
# agree the data is written to a mat file. The program then
# waits for 5 sec before looking again. 
# The program masks out data with timestamps before 1 jan 1990 as this indicates
# a machine has been restarted after the postmortem signal occured.
#
# Currently it can't cope with a nonresponsive machine ( adding a timeout)
# Author Alun Morgan


if __name__ == "__main__":
    from pkg_resources import require as Require
    Require('cothread')

# Sets the max waveform size for EPICS.  This needs to be set *before* we
# load the cothread library so that CA pays attention to it!
import os, datetime, time
os.environ["EPICS_CA_MAX_ARRAY_BYTES"] = "3000000"

from cothread import *
from cothread.catools import *
from cothread.cothread import Timer
from numpy import *
from scipy.io import savemat,loadmat
from scipy.signal import lfilter
#from time import time

PMDIR = "/tmp"
FNAME = "bpm_postmortem"
taps = loadmat("/tmp/liberafilter.mat")


class Saver:

    # object constructor
    def __init__(self, id, pv_list, wf_len, taps):
        self.taps = taps
        self.id = id
        self.pv_list = pv_list
        self.pv_count = len(pv_list)
        self.results = zeros((self.pv_count, wf_len), dtype = float)
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
        camonitor(self.pv_list, self.update_array_entry, format = FORMAT_TIME)      

    def update_array_entry(self, new_value, index):
        print 'Updating array'
        # Record the incoming data.
        self.results[index] = new_value
        self.stamps[index] = new_value.timestamp
        self.seen[index] = True
        # if a machine is restarted the postmortem timestamp is 1 jan 1990 or 1 Jan 1970. Therefore if the timestamp is prior to 1 jan 1990 mask it out.
        if (new_value.timestamp < 631152001.0):
            self.mask[index] = False
        else:
            self.mask[index] = True   

        #(Re)start timer
        print 'Resetting timer'
       # self.stopwatch.cancel()
       # self.stopwatch=Timer(5,self.mask_timeout())   
        self.check_array()       

    def check_array(self):
      #  print 'mask'
      #  print self.mask
       # Sleep(10)
        print 'Checking if all the non masked PVs have been seen'
        a=logical_and(self.seen, self.mask)
        b=logical_not(self.mask)
#        print b
#        Sleep(10)
        c=logical_or(a, b)
        if alltrue(c):
            print ' Yes they have'
           # self.stopwatch.cancel()
            if alltrue(b):
                print 'No valid timestamps'
                self.reset()
            else:
                print ' Valid timestamps'
                t = 0
                masked_stamps = zeros(self.pv_count)
               # masked_results = zeros((self.pv_count, len(self.results)), dtype = float)  
                masked_results = self.results              
                #print self.mask
                for h in range(len(self.results)):
                    if self.mask[h] == True:
                        # removing the timestamps with a false mask
                        masked_stamps[t] = self.stamps[h]
                        t = t + 1
                    else:
                        # setting all results with a false mask to zero
                        masked_results[h] = 0

            
                masked_stamps = masked_stamps[0:t-1]
                # If we've seen them all then check that they've all got the same
                # timestamp. (within 1 sec and for the valid machines)
                if (abs(masked_stamps - masked_stamps[0]) < 1000000).all():
                    # Compute the filename as the timestamp in UTC format in
                    # seconds.
                    self.filtering()
                    self.write_result(
                        self.stamps[0], self.filename(masked_stamps[0]),masked_results)
                    self.reset()
                else:
                    # If the timestamps don't match keep on watching until they
                    # do.
                    print 'Timestamps don\'t match'
        else:
            print 'No they haven\'t '
        
    def mask_timeout(self):
    # if timeout occours mask out missing PVs
        #print self.mask
        print 'Timed out setting all non responsive channel masks to false'
        self.mask = logical_and(self.seen, self.mask)
        #print self.mask
        #self.check_array()

    def filename(self, new_value):
        # Computes the filename from the timestamp.
        datestring = datetime.datetime.utcfromtimestamp(new_value).replace(microsecond = 0).isoformat()
        return os.path.join(PMDIR,
            '%s-%02d-%s.mat' % (FNAME, self.id, datestring))

    def filtering(self):
        # this filters the data from FA to TT to mimic what the BPMs do 
        # FIR filter        
        self.fir_out = lfilter(self.taps['fir'],1,self.results)/131072
        # IIR filter (needs more work)
        self.iir_out = lfilter(self.taps['n2n'],self.taps['n2d'],lfilter(self.taps['n1n'],self.taps['n1d'],self.fir_out[26:53:len(self.fir_out),:]))
            
    def write_result(self, time, filename, results):
        if os.path.isfile(filename):
            print 'File %s already exists' % filename
        else:
            print 'Writing pm', filename
            savemat(filename, {'pm': results, 'time': time, 'iir': self.iir_out, 'fir': self.fir_out} , appendmat=True)
        
    def reset(self):
        print 'Resetting'
        Sleep(5)
        self.results[:] = 0
        self.stamps[:] = 0
        self.seen[:] = False
        self.mask[:] = True
            
  
# epics channels for RF
pv_lists = [
    (id, ['SR%02dC-DI-EBPM-%02d:PM:WF%c' % (cell, position, xy)
        for cell in range(1,25) 
        for position in range(1,8)
        for xy in 'XY'])
    for id in [1]]


# save task
if __name__ == "__main__":
    savers = [
        Saver(id, pv_list, 2**14, taps)
        for id, pv_list in pv_lists]
    WaitForQuit()
