"""Simple wrapper for decimation and filtering."""

import numpy as np


def decimate(waveform, filter, interval=1):
    """Convolves waveform with filter, possibly performing decimation by the
    factor specified by interval at the same time.  Only points entirely
    within waveform will be filtered."""

    # First ensure the inputs are compatible.  We only allow one dimensional
    # arrays, and the underlying conversion function only operates on aligned
    # and contiguous float64 values.
    assert waveform.ndim == 1 and filter.ndim == 1, (
        "Only one dimensional waveforms supported"
    )
    waveform = np.require(waveform, requirements=["C", "A"], dtype=np.float64)
    filter = np.require(filter, requirements=["C", "A"], dtype=np.float64)

    # Compute the result waveform.
    waveform_n = len(waveform)
    filter_n = len(filter)
    if waveform_n < filter_n:
        # If the waveform is shorter than the filter then nothing at all is
        # going to be returned
        return np.array([], dtype=np.float64)
    else:
        result = np.convolve(waveform, filter, mode="valid")[::interval]
        return result


__all__ = ["decimate"]
