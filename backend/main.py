import os
os.environ['PYBAMM_DISABLE_TELEMETRY']='true'
import json,pathlib,uuid,threading
from concurrent.futures import ThreadPoolExecutor
import pybamm
from fastapi import FastAPI,HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel,Field
from backend.science.simulator import parameters,DEFAULT
from backend.science.cache import read_cache
ROOT=pathlib.Path(__file__).resolve().parents[1]
app=FastAPI(title='Battery MRI',version='1.0')
pool=ThreadPoolExecutor(max_workers=1);jobs={};lock=threading.Lock()
parameters(DEFAULT,0);parameters(DEFAULT,1)
def cache():
    try:
        data=read_cache(ROOT/'backend/data/demo.json')
        if data.get('schema')!=1:raise ValueError('Incompatible cache schema')
        return data
    except (OSError,ValueError,KeyError,AssertionError,TypeError):raise HTTPException(503,'Scientific cache missing or invalid. Run scripts/precompute_demo.py.')
@app.get('/api/health')
def health():
    try:d=cache();valid=True
    except HTTPException:d={};valid=False
    return {'status':'ok' if valid else 'setup_required','pybamm_version':pybamm.__version__,'demo_cache_valid':valid,'frontend_build_exists':(ROOT/'frontend/dist/index.html').exists(),'cache_version_matches':d.get('pybamm_version')==pybamm.__version__}
@app.get('/api/demo')
def demo():
    d=cache();d.pop('ground_truth',None);return d
@app.get('/api/demo/result')
def result():return {'ground_truth':cache()['ground_truth'],'simulated':True}
class LabInput(BaseModel):
    soc:float=Field(.55,ge=.3,le=.7)
    max_c:float=Field(2,ge=.2,le=2)
    sigma:float=Field(.02,ge=.002,le=.1)
    sei_multiplier:float=Field(3,ge=1,le=20)
    diffusion_multiplier:float=Field(.9,ge=.2,le=1)
    duration:float=Field(120,ge=60,le=180)
    effort:str=Field('fast',pattern='^(fast|detailed)$')
@app.post('/api/lab/optimize',status_code=202)
def lab(payload:LabInput):
    with lock:
        if any(j['status']=='running' for j in jobs.values()):raise HTTPException(409,'An experiment is already running. Please wait for its result.')
        if len(jobs)>=10:
            del jobs[next(iter(jobs))]
        key=uuid.uuid4().hex;jobs[key]={'status':'running','progress':[]}
    def work():
        try:
            from scripts.precompute_demo import generate
            config=payload.model_dump();effort=config.pop('effort')
            data=generate(config,3 if effort=='fast' else 10,lambda p:jobs[key]['progress'].append(p))
            data.pop('ground_truth',None);jobs[key].update(status='complete',result=data)
        except Exception as exc:jobs[key].update(status='failed',error=f'No valid experiment completed: {type(exc).__name__}. Try less aggressive settings.')
    pool.submit(work);return {'job_id':key}
@app.get('/api/lab/jobs/{key}')
def job(key:str):
    if key not in jobs:raise HTTPException(404,'Unknown experiment')
    return jobs[key]
if (ROOT/'frontend/dist').exists():app.mount('/',StaticFiles(directory=ROOT/'frontend/dist',html=True),name='frontend')
