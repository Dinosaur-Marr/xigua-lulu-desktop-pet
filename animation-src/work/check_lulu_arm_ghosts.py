"""Contrast probe: visible forearm skin must fully occlude what is behind it."""
from pathlib import Path
import sys,json,math
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'work'))
import build_lulu_80 as m

def probes(i,p):
    root=np.array(m.rig.pivots[i]);target=np.array(m.actual_hand(i,p))
    angle=p['la'] if i==0 else -p['ra'];amount=float(m.rig.smooth((angle-12)/55))
    if i in p['targets']:amount=max(amount,p['targets'][i][1])
    root+=np.array([8 if i==0 else -8,12])
    delta=target-root;length=np.linalg.norm(delta);normal=np.array([-delta[1],delta[0]])/length
    if normal[1]<0:normal=-normal
    control=(root+target)/2+normal*min(10,length*.12)*amount
    for u in (.3,.45,.6):
        centre=(1-u)**2*root+2*u*(1-u)*control+u*u*target
        tangent=2*(1-u)*(control-root)+2*u*(target-control);tangent/=np.linalg.norm(tangent)
        for side in (-2,0,2):
            yield tuple(np.round(centre+np.array([-tangent[1],tangent[0]])*side).astype(int))

report=[];saved=m.rig.base
try:
    m.BODY_ONLY=True
    for kind in m.NEW:
        mixtures=[];tested=0
        for t in (.7,1.4,2.3,3.35,4.3):
            p=m.params(kind,t);images=[]
            for colour in ('#000000','#ffffff'):
                m.rig.base=Image.new('RGBA',(640,360),colour)
                images.append(np.asarray(m.compose(kind,t,p)).astype(int))
            diff=np.max(np.abs(images[0][:,:,:3]-images[1][:,:,:3]),axis=2)
            for i in range(2):
                for x,y in probes(i,p):
                    # Exclude the one-pixel antialiased occlusion boundary.
                    patch=diff[y-1:y+2,x-1:x+2]
                    if patch.size!=9:continue
                    value=int(diff[y,x]);tested+=1
                    if 5<value<250 and int(patch.max())-int(patch.min())<70:
                        mixtures.append(dict(t=t,arm=i,x=int(x),y=int(y),backgroundLeak=value))
        assert not mixtures,(kind,mixtures)
        report.append(dict(id=kind,interiorProbes=tested,broadTranslucentSamples=0))
    result=dict(passed=True,sourceHash=m.sha(Path(m.__file__)),actions=40,probes=sum(r['interiorProbes'] for r in report),checks=report)
    (m.OUT/'arm-ghost-check.json').write_text(json.dumps(result,indent=2),encoding='utf8')
    print(json.dumps({k:v for k,v in result.items() if k!='checks'}),flush=True)
finally:m.rig.base=saved;m.BODY_ONLY=False
