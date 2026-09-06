import os
os.environ['PYBAMM_DISABLE_TELEMETRY']='true'
import difflib
import numpy as np
import pybamm
from .waveform import validate

import json
from pathlib import Path
DEFAULT=json.loads((Path(__file__).resolve().parents[1]/'data/default_scenario.json').read_text())

def parameters(config,hypothesis):
    p=pybamm.ParameterValues('Chen2020')
    required=['SEI resistivity [Ohm.m]','Initial SEI thickness [m]','Negative particle diffusivity [m2.s-1]']
    for key in required:
        if key not in p: raise ValueError(f'Missing PyBaMM parameter {key}; similar: {difflib.get_close_matches(key,p.keys())}')
    if hypothesis==0: p['SEI resistivity [Ohm.m]']*=config['sei_multiplier']
    else: p['Negative particle diffusivity [m2.s-1]']*=config['diffusion_multiplier']
    p.update({'Initial temperature [K]':config['temperature'],'Ambient temperature [K]':config['temperature']})
    return p

class Simulator:
    def __init__(self,config=None):
        self.config={**DEFAULT,**(config or {})}; self.models=[]; self.cache={}
        c=self.config
        for h in range(2):
            model=pybamm.lithium_ion.SPMe(options={'thermal':'lumped','SEI':'constant','SEI film resistance':'distributed'})
            p=parameters(c,h)
            dt=c['duration']/6
            current=0
            for i in range(6):
                mask=(pybamm.t>=i*dt)*(pybamm.t<(i+1)*dt) if i<5 else (pybamm.t>=i*dt)
                current+=5*pybamm.InputParameter(f'a{i}')*mask
            p['Current function [A]']=current
            sim=pybamm.Simulation(model,parameter_values=p,solver=pybamm.IDAKLUSolver(rtol=1e-6,atol=1e-7),var_pts={'x_n':12,'x_s':8,'x_p':12,'r_n':16,'r_p':16})
            self.models.append(sim)
    def run(self,amplitudes):
        c=self.config; a=validate(amplitudes,c['max_c'],c['duration']); key=tuple(np.round(a,10))
        if key in self.cache:return self.cache[key]
        # Observe mid-bin to avoid ambiguous samples at ideal current jumps.
        t=np.arange(1,c['duration'],2.)
        results=[]
        for sim in self.models:
            sol=sim.solve(np.linspace(0,c['duration'],7),inputs={f'a{i}':float(v) for i,v in enumerate(a)},initial_soc=c['soc'],t_interp=np.unique(np.r_[0,t,c['duration']]))
            if sol.t[-1]<c['duration']-.01:raise ValueError('Voltage cutoff terminated probe')
            v=sol['Terminal voltage [V]'](t); temp=sol['Volume-averaged cell temperature [K]'](t)
            full_v=sol['Terminal voltage [V]'].entries; full_t=sol['Volume-averaged cell temperature [K]'].entries
            soc=c['soc']-sol['Discharge capacity [A.h]'].entries/5
            safety={'voltage_min':float(np.min(full_v)),'voltage_max':float(np.max(full_v)),'temperature_max_K':float(np.max(full_t)),'soc_min':float(np.min(soc)),'soc_max':float(np.max(soc))}
            if not(np.all(np.isfinite(v)) and safety['voltage_min']>=2.5 and safety['voltage_max']<=4.2 and safety['temperature_max_K']<=313.15 and safety['soc_min']>=.2 and safety['soc_max']<=.8):raise ValueError('Virtual operating bound exceeded')
            results.append({'voltage':v.tolist(),'temperature':temp.tolist(),'safety':safety})
        out={'time':t.tolist(),'a':results[0],'b':results[1],'amplitudes':a.tolist()}
        self.cache[key]=out
        return out
