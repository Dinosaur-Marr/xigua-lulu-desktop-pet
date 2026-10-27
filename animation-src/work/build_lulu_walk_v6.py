"""Continuous cloth/hip/leg deformation: no detached foot layers or cut seams."""
from pathlib import Path
import sys, json, math, shutil, subprocess
import numpy as np
from PIL import Image, ImageDraw
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'work'))
import build_lulu_clean_edges as old
rig=old.rig; FF=rig.FF
OUT=ROOT/'outputs/xigua-lulu-pet-v6'; CLIPS=OUT/'clips'
CLIPS.mkdir(parents=True,exist_ok=True)
SOURCE=ROOT/'outputs/xigua-lulu-pet-v5'
gaits={'walk':dict(cycles=4,stride=12,lift=13,arm=16),
       'run':dict(cycles=6,stride=17,lift=18,arm=23),
       'float':dict(cycles=3,stride=9,lift=10,arm=13)}
original_params=rig.parameters
def activity(t):return rig.ease(t,.5,.8)*(1-rig.ease(t,4.2,4.5))
def phase(kind,t):return max(0,min(4,t-.5))*gaits[kind]['cycles']/4
def pose(kind,t,leg):
    e=activity(t); o=gaits[kind]; q=(phase(kind,t)+leg*.5)%1
    if q<.5:
        u=q*2; dx=-o['stride']*math.cos(math.pi*u); lift=o['lift']*math.sin(math.pi*u)**1.25
    else:
        u=(q-.5)*2; dx=o['stride']*(1-2*u); lift=0
    return dx*e,lift*e
def params(kind,t):
    p=original_params('idle',t); e=activity(t); a=2*math.pi*phase(kind,t)
    # Same signed rotations give opposite outward/inward arm movement in a frontal view.
    p.update(sy=1,sx=1,up=0,step=0,lean=0,angle=.012*math.sin(a)*e,
             la=gaits[kind]['arm']*math.cos(a)*e,ra=gaits[kind]['arm']*math.cos(a)*e,
             my=1-.045*math.sin(a)**2*e)
    return p
rig.parameters=params
Y,X=np.mgrid[:360,:640].astype(np.float32)

def displacement(x,y,kind,t):
    """One continuous field from torso through waistband, both cloth panels and soles."""
    e=activity(t); ph=2*math.pi*phase(kind,t)
    left_dx,left_lift=pose(kind,t,0); right_dx,right_lift=pose(kind,t,1)
    # Shift hips toward the planted leg. The upper body counterbalances slightly.
    hip_x=3.2*math.sin(ph)*e
    bob=-1.8*abs(math.sin(ph))*e
    hip_roll=.016*math.sin(ph)*e
    # Cloth starts responding at the waistband and reaches full leg movement at the ankle.
    lower=rig.smooth((y-258)/78)
    split=rig.smooth((x-287)/78)
    foot_dx=left_dx*(1-split)+right_dx*split
    lift=left_lift*(1-split)+right_lift*split
    # Bend the knee forward midway down the shorts instead of moving a rigid foot cutout.
    knee=np.maximum(0,np.sin(np.pi*np.clip((y-258)/94,0,1)))**2
    knee_dx=2.8*(lift/max(1,gaits[kind]['lift']))*knee
    torso=1-rig.smooth((y-284)/60)
    counter=1-.4*rig.smooth((230-y)/110)
    dx=hip_x*torso*counter+foot_dx*lower+knee_dx
    dy=(bob+hip_roll*(x-322))*torso-lift*lower
    return dx,dy

def warp(im,kind,t):
    # Invert the smooth forward deformation; shared mapping keeps skin and print joined.
    qx=X.copy(); qy=Y.copy()
    for _ in range(7):
        dx,dy=displacement(qx,qy,kind,t); qx=X-dx; qy=Y-dy
    a=np.asarray(im,dtype=np.float32); a[:,:,:3]*=a[:,:,3:4]/255
    qx=np.clip(qx,0,638.999); qy=np.clip(qy,0,358.999)
    ix=qx.astype(np.int32);iy=qy.astype(np.int32); fx=(qx-ix)[...,None]; fy=(qy-iy)[...,None]
    b=(a[iy,ix]*(1-fx)+a[iy,ix+1]*fx)*(1-fy)+(a[iy+1,ix]*(1-fx)+a[iy+1,ix+1]*fx)*fy
    b[:,:,:3]=np.divide(b[:,:,:3]*255,b[:,:,3:4],out=np.zeros_like(b[:,:,:3]),where=b[:,:,3:4]>.1)
    return Image.fromarray(np.clip(b,0,255).astype('uint8'))
def frame(kind,t):
    if t>=5:t=0
    # Retain the complete original legs and shorts, in their original proportions.
    result=warp(old.frame_right(kind,t),kind,t).transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    # Contact constraint: the planted sole stays at the same floor height throughout.
    # The continuous cloth blend can otherwise lift its inner edge by 1-2 pixels.
    yy,xx=np.where(np.asarray(result)[:,:,3]>100)
    correction=351-int(yy.max())
    if correction:
        grounded=Image.new('RGBA',result.size);grounded.alpha_composite(result,(0,correction));result=grounded
    return result

def preview():
    times=[0,.75,1,1.25,1.5,1.75,2,2.25]
    sheet=Image.new('RGB',(1280,900),'#e8eef2');d=ImageDraw.Draw(sheet)
    for i,t in enumerate(times):
        im=frame('walk',t).crop((170,0,470,360)); bg=Image.new('RGBA',im.size,'#e8eef2');bg.alpha_composite(im)
        x=(i%4)*320;y=(i//4)*450
        sheet.paste(bg.convert('RGB'),(x,y+20));d.text((x+10,y+4),f'{t:.2f}s',fill='#233')
        crop=bg.crop((45,245,255,360)).resize((210,115))
        # The main frame already shows the feet clearly; reserved margin separates each phase.
    sheet.save(OUT/'gait-review.jpg')
def encode(kind):
    p=subprocess.Popen([str(FF),'-v','error','-y','-f','rawvideo','-pix_fmt','rgba','-s','640x360','-r','24','-i','-',
      '-c:v','libvpx-vp9','-pix_fmt','yuva420p','-b:v','0','-crf','20','-deadline','realtime','-cpu-used','4','-auto-alt-ref','0','-row-mt','1','-an',str(CLIPS/f'{kind}.webm')],stdin=subprocess.PIPE)
    for i in range(120):
        im=frame(kind,i*5/119); a=np.asarray(im); yy,xx=np.where(a[:,:,3]>40)
        assert yy.max()<355 and yy.min()>3 and xx.min()>0 and xx.max()<639
        p.stdin.write(im.tobytes())
        if i==47:im.save(CLIPS/f'{kind}.png')
    p.stdin.close();assert p.wait()==0
    data=subprocess.run([str(FF),'-v','error','-c:v','libvpx-vp9','-i',str(CLIPS/f'{kind}.webm'),'-f','rawvideo','-pix_fmt','rgba','-'],capture_output=True,check=True).stdout
    a=np.frombuffer(data,np.uint8).reshape(-1,360,640,4);assert len(a)==120
    assert a[:,-1,:,3].max()<8 and a[:,0,:,3].max()<8
    assert np.abs(a[0].astype(float)-a[-1].astype(float)).mean()<2
    # At swing peak the hem must rise with its foot, not remain motionless as in v5.
    t=.5+5/gaits[kind]['cycles']
    _,hem_dy=displacement(np.array([275.,370.]),np.array([309.,309.]),kind,t)
    _,foot_dy=displacement(np.array([275.,370.]),np.array([344.,344.]),kind,t)
    assert abs(hem_dy[0])>gaits[kind]['lift']*.45 and abs(foot_dy[0])>gaits[kind]['lift']*.85
    # Mapping must not fold: positive forward Jacobian preserves cloth continuity.
    min_jac=1.
    for t in np.linspace(.6,4.3,20):
        dx,dy=displacement(X,Y,kind,t)
        dxx=np.gradient(dx,axis=1);dxy=np.gradient(dx,axis=0)
        dyx=np.gradient(dy,axis=1);dyy=np.gradient(dy,axis=0)
        j=(1+dxx)*(1+dyy)-dxy*dyx;min_jac=min(min_jac,float(j[250:354,220:430].min()))
    assert min_jac>.2,(kind,min_jac)
    result=dict(kind=kind,frames=120,alpha=True,clothHemLift=abs(float(hem_dy[0])),footLift=abs(float(foot_dy[0])),minJacobian=min_jac)
    print(json.dumps(result),flush=True);return result
if __name__=='__main__':
    preview()
    if '--inspect' in sys.argv:sys.exit()
    for p in (SOURCE/'clips').iterdir():
        if p.suffix in ['.png','.webm']:shutil.copy2(p,CLIPS/p.name)
    records=[encode(k) for k in gaits]
    previous=json.loads((SOURCE/'decoded-validation.json').read_text(encoding='utf8'))
    records += [r for r in previous if r['kind'] not in gaits]
    (OUT/'decoded-validation.json').write_text(json.dumps(records,indent=2),encoding='utf8')
    shutil.copy2(SOURCE/'mapping.json',OUT/'mapping.json')
    def travel(k):
        d=4*gaits[k]['stride']*gaits[k]['cycles']*462/640
        return dict(minDist=round(d*.98),maxDist=round(d*1.02),leadSec=.5,tailSec=.5)
    settings=dict(default=travel('walk'),actions={n:travel(k) for n,k in [('螃蟹走路','walk'),('原地漂浮踏步','float'),('原地左转奔跑','run')]})
    (OUT/'move-settings.json').write_text(json.dumps(settings,ensure_ascii=False,indent=2),encoding='utf8')
