"""Search modest perturbations using a saved real optimized candidate as a calibration witness."""
import sys,pathlib,json
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from backend.science.simulator import Simulator
from backend.science.inference import eig
from backend.science.waveform import BASELINE
root=pathlib.Path(__file__).resolve().parents[1]
a=json.loads((root/'backend/data/demo.json').read_text())['probes'][0]['prediction']['amplitudes']
rows=[]
for sei in [2,3,4,5]:
 for diffusion in [.7,.8,.9]:
    s=Simulator({'sei_multiplier':sei,'diffusion_multiplier':diffusion})
    b=s.run(BASELINE);p=s.run(a)
    bs=eig(b['a']['voltage'],b['b']['voltage'],.02);ps=eig(p['a']['voltage'],p['b']['voltage'],.02)
    row={'sei_multiplier':sei,'diffusion_multiplier':diffusion,'baseline_bits':bs,'candidate_bits':ps};rows.append(row);print(row,flush=True)
valid=[r for r in rows if r['baseline_bits']<.03 and .25<r['candidate_bits']<.65]
best=min(valid,key=lambda r:abs(r['candidate_bits']-.45))
(root/'backend/data/calibration.json').write_text(json.dumps({'search':rows,'selected':best,'witness_amplitudes':a},indent=2))
print('SELECTED',best)
