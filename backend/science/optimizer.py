import numpy as np
from scipy.optimize import differential_evolution
from .inference import eig

def optimize(sim,prior=(.5,.5),seed=731,iterations=5,progress=None):
    history=[]; candidates=[]; best=-1.; count=0; failures=0
    def objective(a):
        nonlocal best,count,failures
        count+=1
        try:
            r=sim.run(a); score=eig(r['a']['voltage'],r['b']['voltage'],sim.config['sigma'],prior)
        except Exception:
            failures+=1
            return 1e6
        candidates.append({'amplitudes':list(map(float,a)),'score':score})
        if score>best:best=score
        return -score
    def callback(x,convergence):
        entry={'generation':len(history)+1,'score':-objective(x),'amplitudes':list(map(float,x)),'evaluations':count}
        history.append(entry)
        if progress:progress(entry)
    result=differential_evolution(objective,[(-sim.config['max_c'],sim.config['max_c'])]*6,seed=seed,popsize=4,maxiter=iterations,polish=False,callback=callback,tol=.0001)
    if result.fun>=0:raise ValueError('No informative safe probe found')
    return {'prediction':sim.run(result.x),'score':float(-result.fun),'history':history,'top_candidates':sorted(candidates,key=lambda c:-c['score'])[:8],'evaluations':count,'failed_candidates':failures,'prior':list(prior),'seed':seed}
