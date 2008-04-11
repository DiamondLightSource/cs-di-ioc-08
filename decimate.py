'''Simple wrapper for decimation and filtering.'''

import ctypes
from numpy import *

decimate_lib = ctypes.cdll.LoadLibrary('./_decimate.so')
_decimate = decimate_lib.decimate


def decimate(waveform, filter, interval=1):
    '''Filters waveform with filter, possibly performing decimation by the
    factory specified by interval at the same time.  Only points entirely
    within waveform will be filtered.'''

    # First ensure the inputs are compatible.  We only allow one dimensional
    # arrays, and the underlying conversion function only operates on aligned
    # and contiguous float64 values.
    assert waveform.ndim == 1  and  filter.ndim == 1, \
        'Only one dimensional waveforms supported'
    waveform = require(waveform, requirements = 'CA', dtype = float64)
    filter   = require(filter,   requirements = 'CA', dtype = float64)

    # Compute the result waveform.
    waveform_n = len(waveform)
    filter_n = len(filter)
    if waveform_n < filter_n:
        # If the waveform is shorter than the filter then nothing at all is
        # going to be returned
        return array([], dtype = float64)
    else:
        output_length = 1 + (waveform_n - filter_n) // interval
        result = empty(output_length, dtype = float64)
        _decimate(
            waveform.ctypes.data, filter.ctypes.data, result.ctypes.data,
            waveform_n, filter_n, interval)
        return result


__all__ = ['decimate']
