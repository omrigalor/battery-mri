import numpy as np
SEGMENTS=6
DURATION=20.
BASELINE=[.15,0,-.15,0,.15,0]
def validate(amplitudes,limit=2.,duration=120.):
    a=np.asarray(amplitudes,dtype=float)
    if a.shape!=(6,) or not np.all(np.isfinite(a)): raise ValueError('Six finite C-rates required')
    if np.max(np.abs(a))>limit+1e-8: raise ValueError('C-rate limit exceeded')
    if not 60<=duration<=180: raise ValueError('Duration must be 60–180 seconds')
    return a

def current_amperes(c_rate,capacity=5.):
    # PyBaMM positive = discharge; negative = charge.
    return np.asarray(c_rate)*capacity

def chart(amplitudes,duration=120.):
    return [{'c_rate':float(a),'duration':duration/6,'action':'discharge' if a>.001 else 'charge' if a<-.001 else 'rest'} for a in amplitudes]
