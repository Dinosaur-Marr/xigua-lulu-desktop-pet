"""Check a continuous visible limb route, not merely the pet's outer silhouette."""
from pathlib import Path
import sys,json
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'work'))
import build_lulu_80 as m
checks=[]
for kind in m.NEW:
    samples=0;minimum=255
    for t in np.linspace(.25,4.75,20):
        p=m.params(kind,float(t))
        for i in range(2):
            angle=p['la'] if i==0 else -p['ra'];amount=float(m.rig.smooth((angle-12)/55))
            if i in p['targets']:amount=max(amount,p['targets'][i][1])
            root=np.array(m.rig.pivots[i])+np.array([8 if i==0 else -8,12]);target=np.array(m.actual_hand(i,p))
            delta=target-root;length=np.linalg.norm(delta);normal=np.array([-delta[1],delta[0]])/length
            if normal[1]<0:normal=-normal
            control=(root+target)/2+normal*min(10,length*.12)*amount
            whole,front=m.continuous_arm(i,p);a=np.asarray(front)[:,:,3]
            for u in np.linspace(.15,.95,17):
                x,y=np.round((1-u)**2*root+2*u*(1-u)*control+u*u*target).astype(int)
                alpha=int(a[y,x]);minimum=min(minimum,alpha);samples+=1
                assert alpha>=240,(kind,float(t),i,float(u),alpha,'broken or translucent arm route')
    checks.append(dict(id=kind,visibleRouteSamples=samples,minimumAlpha=minimum))
    print(kind+' visible arm route PASS',flush=True)
result=dict(passed=True,sourceHash=m.sha(Path(m.__file__)),actions=40,samples=sum(x['visibleRouteSamples'] for x in checks),checks=checks)
(m.OUT/'arm-continuity-check.json').write_text(json.dumps(result,indent=2),encoding='utf8')
