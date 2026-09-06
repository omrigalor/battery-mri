import json,pathlib
import numpy as np
import pytest
from backend.science.waveform import validate,current_amperes,BASELINE
from backend.science.inference import posterior,eig
from backend.science.simulator import Simulator
ROOT=pathlib.Path(__file__).resolve().parents[2]
@pytest.fixture(scope='module')
def data():return json.loads((ROOT/'backend/data/demo.json').read_text())
def test_waveform():
    validate(BASELINE)
    assert current_amperes(1)==5 and current_amperes(-1)==-5
    for a,d in [([3]*6,120),([0]*5,120),([float('nan')]*6,120),([0]*6,0)]:
        with pytest.raises(ValueError):validate(a,duration=d)
def test_inference():
    assert posterior([[0,0],[1,1]],[0,0],1e-6)[0]>.999999
    assert posterior([[1,1],[1,1]],[2,2],.01,[.3,.7])==pytest.approx([.3,.7])
    assert eig([1,1],[1,1],.01)==pytest.approx(0)
    assert 0<=eig([0,0],[1,1],.5)<=1
    assert sum(posterior([[0,1],[1,0]],[.2,.7],.1))==pytest.approx(1)
def test_cached_science(data):
    b=data['baseline'];p,q=data['probes']
    assert p['score']>1.25*b['score']
    assert q['prior']==p['posterior']
    assert .5<p['posterior'][0]<.95
    assert q['posterior'][0]>p['posterior'][0]
    assert np.linalg.norm(np.array(p['prediction']['amplitudes'])-q['prediction']['amplitudes'])>.1
    for r in [b,p['prediction'],q['prediction']]:
        validate(r['amplitudes'])
        assert len(r['time'])==len(r['a']['voltage'])==len(r['b']['voltage'])
        for h in ['a','b']:
            assert np.isfinite(r[h]['voltage']).all()
            s=r[h]['safety'];assert 2.5<=s['voltage_min']<=s['voltage_max']<=4.2
            assert s['temperature_max_K']<=313.15 and .2<=s['soc_min']<=s['soc_max']<=.8
    rng=np.random.default_rng(data['config']['measurement_seed'])
    prior=[.5,.5]
    for probe in data['probes']:
        r=probe['prediction'];y=np.array(r['a']['voltage'])+rng.normal(0,data['config']['sigma'],len(r['time']))
        assert y==pytest.approx(probe['observation'],abs=1e-12)
        prior=posterior([r['a']['voltage'],r['b']['voltage']],y,data['config']['sigma'],prior)
        assert prior==pytest.approx(probe['posterior'],abs=1e-12)
def test_fresh_physics(data):
    sim=Simulator(data['config'])
    for cached in [data['baseline'],data['probes'][0]['prediction'],data['probes'][1]['prediction']]:
        fresh=sim.run(cached['amplitudes'])
        for h in ['a','b']:assert fresh[h]['voltage']==pytest.approx(cached[h]['voltage'],abs=2e-5)
def test_api():
    from fastapi.testclient import TestClient
    from backend.main import app
    c=TestClient(app)
    assert c.get('/api/health').json()['status']=='ok'
    assert 'ground_truth' not in c.get('/api/demo').json()
    assert c.get('/api/demo/result').json()['ground_truth']=='A'
    assert c.post('/api/lab/optimize',json={'max_c':9}).status_code==422
    assert c.get('/api/lab/jobs/missing').status_code==404

def test_cache_rejects_tampered_posterior(data,tmp_path):
    from backend.science.cache import read_cache
    data['probes'][0]['posterior']=[.5,.5]
    p=tmp_path/'demo.json';p.write_text(json.dumps(data))
    with pytest.raises(AssertionError):read_cache(p)
