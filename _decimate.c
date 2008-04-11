/* Very simple decimation filter. */

#import <stdio.h>


/* Convolves Filter with input waveform In, simultaneously decimating by the
 * decimation factor specified by Interval.  The result is written to Out
 * which must be of the correct length: require
 *
 *      length(Out) >= 1 + (InLength - FilterLength) // Interval .
 */
void decimate(
    const double *In, const double *Filter, double *Out,
    int InLength, int FilterLength, int Interval)
{
    int end = InLength - FilterLength;
    for (int start = 0; start <= end; start += Interval, In += Interval)
    {
        double Result = 0.0;
        for (int i = 0; i < FilterLength; i ++)
            Result += In[i] * Filter[i];
        *Out++ = Result;
    }
}
