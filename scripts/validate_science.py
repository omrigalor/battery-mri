import sys,pathlib,json,subprocess
root=pathlib.Path(__file__).resolve().parents[1]
r=subprocess.run([sys.executable,'-m','pytest','backend/tests','-q'],cwd=root)
if r.returncode:sys.exit(r.returncode)
d=json.loads((root/'backend/data/demo.json').read_text())
print('PyBaMM',d['pybamm_version'],'Baseline bits:',d['baseline']['score'])
for i,p in enumerate(d['probes'],1):
 print('Probe',i,'EIG bits:',p['score'],'posterior:',p['posterior'])
 for h in ['a','b']:print(' ',h,p['prediction'][h]['safety'])
