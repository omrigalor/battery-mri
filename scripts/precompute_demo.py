import sys,json, pathlib,os
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
os.environ['PYBAMM_DISABLE_TELEMETRY']='true'
import numpy as np,pybamm
from backend.science.simulator import Simulator,DEFAULT
from backend.science.waveform import BASELINE
from backend.science.inference import eig,posterior,trajectory
from backend.science.optimizer import optimize
ROOT=pathlib.Path(__file__).resolve().parents[1]
def generate(config=None,iterations=7,progress=None):
    c={**DEFAULT,**(config or {})};sim=Simulator(c)
    baseline=sim.run(BASELINE); baseline['score']=eig(baseline['a']['voltage'],baseline['b']['voltage'],c['sigma'])
    probes=[];prior=[.5,.5];rng=np.random.default_rng(c.get('measurement_seed',42))
    for n in range(2):
        probe=optimize(sim,prior,seed=c['seed']+n,iterations=iterations,progress=progress)
        r=probe['prediction'];y=np.array(r['a']['voltage'])+rng.normal(0,c['sigma'],len(r['time']))
        probe['observation']=y.tolist();probe['posterior']=posterior([r['a']['voltage'],r['b']['voltage']],y,c['sigma'],prior)
        probe['posterior_history']=trajectory(r['a']['voltage'],r['b']['voltage'],y,c['sigma'],prior)
        probes.append(probe);prior=probe['posterior']
    return {'schema':1,'config':c,'pybamm_version':pybamm.__version__,'model':'SPMe · lumped thermal · constant SEI, distributed film resistance','parameter_set':'Chen2020','solver':'IDAKLUSolver · rtol 1e-6, atol 1e-7','objective':'Expected information gain (bits), 32-point Gaussian quadrature','noise':'Independent Gaussian voltage noise; observations every 2 seconds','baseline':baseline,'probes':probes,'ground_truth':'A','reset_assumption':f"Each probe starts at the same {c['soc']*100:g}% SOC and thermal equilibrium. A physical experiment would need controlled reconditioning between probes. No SEI growth occurs during these short probes.",'adaptive_caveat':'For two fixed hypotheses with equal Gaussian noise, information gain is monotonic in voltage separation. Updating the prior changes expected information, but need not change the globally best waveform. The two bounded searches can return different near-optimal probes; this is not proof of a uniquely cell-specific waveform.'}
if __name__=='__main__':
    out=generate(progress=lambda x:print(x['generation'],round(x['score'],5),flush=True))
    temporary=ROOT/'backend/data/demo.json.tmp'
    temporary.write_text(json.dumps(out,allow_nan=False,separators=(',',':')))
    temporary.replace(ROOT/'backend/data/demo.json')
    print('BASELINE',out['baseline']['score'],'PROBES',[(p['score'],p['posterior']) for p in out['probes']])
