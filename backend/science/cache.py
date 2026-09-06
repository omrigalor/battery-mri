"""Validate saved data before presenting any scientific claims."""
import json
import numpy as np
from .inference import eig,posterior
from .waveform import validate

def read_cache(path):
    d=json.loads(path.read_text());assert d['schema']==1
    c=d['config'];prior=[.5,.5]
    assert len(d['probes'])==2
    baseline=d['baseline']
    assert abs(eig(baseline['a']['voltage'],baseline['b']['voltage'],c['sigma'])-baseline['score'])<1e-9
    for r in [d['baseline']]+[p['prediction'] for p in d['probes']]:
        validate(r['amplitudes'],c['max_c'],c['duration'])
        t=np.array(r['time']);assert len(t)>1 and np.all(np.diff(t)>0)
        for h in ['a','b']:
            v=np.array(r[h]['voltage']);assert len(v)==len(t) and np.all(np.isfinite(v))
    for p in d['probes']:
        assert np.allclose(p['prior'],prior)
        r=p['prediction'];y=p['observation'];sigma=c['sigma']
        assert len(y)==len(r['time']) and np.all(np.isfinite(y))
        calculated=posterior([r['a']['voltage'],r['b']['voltage']],y,sigma,prior)
        assert np.allclose(calculated,p['posterior'],atol=1e-10)
        assert abs(eig(r['a']['voltage'],r['b']['voltage'],sigma,prior)-p['score'])<1e-9
        prior=p['posterior']
    return d
