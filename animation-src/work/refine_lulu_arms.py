"""Natural shoulder occlusion and staged hand gestures for the 40-action pack."""
from pathlib import Path
import sys,json,shutil,math
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'work'))
import build_lulu_40 as b
rig=b.rig
SOURCE=b.OUT;OUT=ROOT/'outputs/xigua-lulu-pet-40-refined';CLIPS=OUT/'clips';CLIPS.mkdir(parents=True,exist_ok=True)
original_params=b.params
original_compose=b.compose
CHANGED=['kiss','hug','clap','sneeze','twist','thank']
forearms=[]
yy,xx=np.mgrid[:360,:640]
for i,(asset,pivot) in enumerate(zip(rig.arms,rig.pivots)):
    # The upper shoulder remains behind the body. Only the soft elbow-to-hand section
    # can come forward, avoiding an exposed round shoulder cap under the cheek.
    hand=rig.pos(165 if i==0 else 872,1045)
    vx,vy=hand[0]-pivot[0],hand[1]-pivot[1];length=math.hypot(vx,vy)
    along=((xx-pivot[0])*vx+(yy-pivot[1])*vy)/length
    mask=rig.smooth((along-12)/22)
    a=np.asarray(asset).copy();a[:,:,3]=(a[:,:,3]*mask).astype('uint8');forearms.append(Image.fromarray(a))

def params(kind,t):
    p=original_params(kind,t)
    if kind=='sneeze':
        anticipation=b.E(t,.3,1.25,1.55,1.95)
        hand=b.E(t,.8,1.55,2.35,3.25)
        burst=b.P(t,1.95,.24);recovery=b.P(t,2.36,.4)
        p.update(la=-9*anticipation-17*burst,ra=9*anticipation+17*burst,front=False,prop=None,
                 close=max(.25*anticipation,burst,.38*recovery,b.P(t,3.5,.17)),
                 mx=1-.36*anticipation-.2*burst,my=1+.1*anticipation-.36*burst,
                 nod=-2*anticipation+5*burst,dip=6*burst+1.5*recovery,
                 lean=-2*anticipation+3.5*burst,angle=-.025*hand+.018*burst)
    elif kind=='hug':
        hold=b.E(t,.25,1.3,3.65,4.8);rock=math.sin(2*math.pi*np.clip((t-1.3)/2.5,0,1))*hold
        p.update(la=58*hold,ra=-58*hold,front=True,close=.78*hold,
                 angle=.028*rock,lean=2.5*rock,my=1+.08*hold)
    elif kind=='clap':
        hold=b.E(t,.25,.85,3.85,4.8)
        contact=sum(b.P(t,c,.22) for c in [1.25,2.35,3.4])
        p.update(la=(53+23*contact)*hold,ra=-(53+23*contact)*hold,
                 nod=1.6*contact,close=.38*contact,my=1+.16*contact,prop=None)
    elif kind=='thank':
        hold=b.E(t,.25,1.05,3.9,4.8);bow=b.P(t,2.3,1.)
        p.update(la=74*hold,ra=-74*hold,nod=3.5*bow,dip=9*bow,close=.85*bow)
    elif kind=='twist':
        # Hands stay naturally at the sides while the hips move; no forward overlay.
        p.update(front=False,la=-12*b.E(t),ra=12*b.E(t),hip=p['hip']*.7,lean=p['lean']*.7)
    elif kind=='kiss':
        hold=b.E(t,.3,1,2,2.7)
        p.update(la=-25*hold,ra=25*hold,front=False)
    return p

def compose(kind,t,p):
    if kind not in CHANGED:return original_compose(kind,t,p)
    im=Image.new('RGBA',(640,360));front=[]
    for i,(asset,angle,pivot) in enumerate(zip(rig.arms,(p['la'],p['ra']),rig.pivots)):
        moved=asset.rotate(angle,resample=Image.Resampling.BICUBIC,center=pivot)
        im.alpha_composite(moved)
        # At rest, both arms are exactly in their normal depth layer. Entering or
        # leaving the foreground is continuous and specific to each inward arm.
        inward=angle if i==0 else -angle
        depth=float(rig.smooth((inward-18)/32)) if p['front'] else 0
        if depth>.001 and kind not in ['kiss','sneeze']:
            fg=forearms[i].rotate(angle,resample=Image.Resampling.BICUBIC,center=pivot)
            fg.putalpha(fg.getchannel('A').point(lambda a:round(a*depth)));front.append(fg)
    im.alpha_composite(rig.base)
    for i in range(2):
        close=max(p['close'],p['wink'] if i==0 else 0)
        if close<.65:rig.paste_feature(im,rig.eyes[i],sx=p['eye'],sy=max(.12,1-1.12*close)*p['eye'],dx=p['gaze'])
        else:rig.paste_feature(im,rig.closed[i])
    rig.paste_feature(im,rig.mouth,sx=p['mx'],sy=p['my'])
    if kind=='hug':
        appearance=b.E(t,.85,1.3,3.7,4.3)
        if appearance>.01:b.heart(im,322,239,34*appearance,255*appearance)
    else:b.props(im,kind,t,p)
    for fg in front:im.alpha_composite(fg)
    return im

def articulated(i,target,reach):
    root=np.array(rig.pivots[i],float)
    source_hand=np.array(rig.pos(165 if i==0 else 872,1065),float)
    vec=source_hand-root;length=float(np.linalg.norm(vec));axis=vec/length
    hand=source_hand*(1-reach)+np.array(target)*reach
    delta=hand-root;distance=float(np.linalg.norm(delta));unit=delta/max(.001,distance)
    total=max(length*(1+.12*reach),distance+1e-3);half=total/2
    h=math.sqrt(max(0,half*half-distance*distance/4));normal=np.array([-unit[1],unit[0]])
    elbows=[(root+hand)/2+normal*h,(root+hand)/2-normal*h]
    elbow=max(elbows,key=lambda x:x[1])
    source_elbow=(root+source_hand)/2
    longitudinal=(xx-root[0])*axis[0]+(yy-root[1])*axis[1]
    uppermask=1-rig.smooth((longitudinal-length*.46)/(length*.16))
    lowermask=rig.smooth((longitudinal-length*.38)/(length*.16))
    def segment(mask,s0,s1,d0,d1):
        v1=s1-s0;v2=d1-d0;scale=np.linalg.norm(v2)/np.linalg.norm(v1)
        theta=math.atan2(v2[1],v2[0])-math.atan2(v1[1],v1[0])
        co=math.cos(theta)/scale;si=math.sin(theta)/scale
        coeff=(co,si,s0[0]-co*d0[0]-si*d0[1],-si,co,s0[1]+si*d0[0]-co*d0[1])
        data=np.asarray(rig.arms[i]).copy();data[:,:,3]=(data[:,:,3]*mask).astype('uint8')
        return Image.fromarray(data).transform((640,360),Image.Transform.AFFINE,coeff,resample=Image.Resampling.BICUBIC)
    upper=segment(uppermask,root,source_elbow,root,elbow)
    lower=segment(lowermask,source_elbow,source_hand,elbow,hand)
    whole=Image.new('RGBA',(640,360));whole.alpha_composite(upper);whole.alpha_composite(lower)
    lower.putalpha(lower.getchannel('A').point(lambda a:round(a*float(rig.smooth(reach/.55)))))
    return whole,lower
b.params=params;b.compose=compose;b.OUT=OUT;b.CLIPS=CLIPS

def review():
    font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',20)
    for j,group in enumerate([['sneeze','hug','clap'],['kiss','twist','thank']]):
        sheet=Image.new('RGB',(1280,1020),'#e9f0ec');d=ImageDraw.Draw(sheet)
        for row,kind in enumerate(group):
            d.text((10,row*340+6),b.NEW[kind][0],font=font,fill='#284735')
            for col,t in enumerate([0,.8,1.95,3.4]):
                im=b.frame(kind,t).crop((190,140,445,294)).resize((280,170))
                bg=Image.new('RGBA',im.size,'#fffef6' if col<2 else '#202a34');bg.alpha_composite(im)
                sheet.paste(bg.convert('RGB'),(col*320+15,row*340+45))
                full=b.frame(kind,t).crop((150,0,490,360)).resize((102,108));small=Image.new('RGBA',full.size,'#e9f0ec');small.alpha_composite(full)
                sheet.paste(small.convert('RGB'),(col*320+95,row*340+220))
                d.text((col*320+15,row*340+27),f'{t:.2f}s',fill='#284735')
        sheet.save(OUT/f'shoulder-review-{j+1}.jpg')
if __name__=='__main__':
    review()
    if '--inspect' in sys.argv:sys.exit()
    for p in (SOURCE/'clips').iterdir():
        if p.suffix in ['.webm','.png']:shutil.copy2(p,CLIPS/p.name)
    checks=json.loads((SOURCE/'decoded-validation.json').read_text(encoding='utf8'))
    records=[b.encode(k) for k in CHANGED]
    records += [r for r in checks if r['kind'] not in CHANGED]
    (OUT/'decoded-validation.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf8')
    for name in ['mapping.json','actions.json','new-actions.json']:
        shutil.copy2(SOURCE/name,OUT/name)
    # All new motions must share the same neutral starting pose and shoulder depth.
    neutral=np.asarray(b.frame('nod',0)).astype(float)
    diffs={k:float(np.abs(np.asarray(b.frame(k,0)).astype(float)-neutral).mean()) for k in b.NEW}
    assert all(d<.01 for d in diffs.values()),diffs
    (OUT/'neutral-pose-check.json').write_text(json.dumps(diffs,indent=2),encoding='utf8')
