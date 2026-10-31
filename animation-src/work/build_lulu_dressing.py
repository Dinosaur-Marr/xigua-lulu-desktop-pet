"""Visible take-off / step-out / step-in / pull-up choreography (10 seconds)."""
from pathlib import Path
import sys,math,json,subprocess,hashlib
import numpy as np
from PIL import Image,ImageDraw,ImageFilter
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'work'))
import build_lulu_wardrobe as w
b=w.b;rig=w.rig;OUT=w.OUT;CLIPS=w.CLIPS
garment=rig.normalize(w.maskim.convert('RGBA')).getchannel('R')
# Imagegen provided the modest underlayer; only the garment region is used.
gen=rig.normalize(Image.open(OUT/'rig/underlayer-generated.png').convert('RGBA'))
under=Image.composite(gen,w.watermelon,garment)
under.save(OUT/'rig/underlayer-base.png')
clothes={}
for key,base in [('watermelon',w.watermelon),('orange',w.orange)]:
    a=np.asarray(base).copy();a[:,:,3]=(a[:,:,3].astype(float)*np.asarray(garment)/255).astype('uint8')
    clothes[key]=Image.fromarray(a).transpose(Image.Transpose.FLIP_LEFT_RIGHT)
arms=list(rig.arms)
yy,xx=np.mgrid[:360,:640]
saved_params=b.params
def ease(t,a,z):return rig.ease(t,a,z)
def mix(a,z,k):return a+(z-a)*k
def pulse(t,c,d):return b.P(t,c,d)
def posture(t):
    crouch=55*ease(t,.45,1.6)*(1-ease(t,8.05,9.3))
    stand_between=18*ease(t,3.1,3.6)*(1-ease(t,4.5,5.1))
    return dict(dip=crouch-stand_between,nod=3*ease(t,.3,1.3)*(1-ease(t,8.5,9.4)))
def forward_y(y,p):
    q=y
    for _ in range(12):q=y+p['dip']*float(rig.smooth((352-q)/145))+p['nod']*float(rig.smooth((252-q)/50))
    return q
def body_params(kind,t):
    p=saved_params('nod',0);pose=posture(t)
    p.update(**pose,mx=1-.15*ease(t,.8,1.5)*(1-ease(t,7.9,9)),my=1-.25*ease(t,.8,1.5)*(1-ease(t,7.9,9)),close=.35*pulse(t,2.4,.65)+.55*pulse(t,8.8,.5))
    return p
def body(t):
    rig.base=under;rig.arms=[];b.params=lambda kind,_:body_params(kind,t)
    try:im=b.frame('dressing',min(t,4.999))
    finally:rig.arms=arms;b.params=saved_params
    # Alternating visible feet clear the lowered waistband on removal/insertion.
    lifts=[15*pulse(t,3.25,.4)+15*pulse(t,5.55,.38),15*pulse(t,3.95,.4)+15*pulse(t,6.3,.38)]
    if max(lifts)<.01:return im
    a=np.asarray(im,dtype=float);a[:,:,:3]*=a[:,:,3:4]/255
    y,x=np.mgrid[:360,:640].astype(float);qy=y.copy();qx=x.copy()
    for i,lift in enumerate(lifts):
        weight=np.exp(-((x-(270 if i==0 else 370))/37)**4)*rig.smooth((y-295)/38)
        qy+=lift*weight;qx+=(3 if i==0 else -3)*lift/15*weight
    qy=np.clip(qy,0,358.999);qx=np.clip(qx,0,638.999);ix=qx.astype(int);iy=qy.astype(int);fx=(qx-ix)[...,None];fy=(qy-iy)[...,None]
    out=(a[iy,ix]*(1-fx)+a[iy,ix+1]*fx)*(1-fy)+(a[iy+1,ix]*(1-fx)+a[iy+1,ix+1]*fx)*fy
    out[:,:,:3]=np.divide(out[:,:,:3]*255,out[:,:,3:4],out=np.zeros_like(out[:,:,:3]),where=out[:,:,3:4]>.1)
    return Image.fromarray(np.clip(out,0,255).astype('uint8'))
def pants(key,cx,top,bottom,width,opacity=1):
    src=clothes[key];box=src.getbbox();cut=src.crop(box)
    im=cut.resize((max(1,round(width)),max(1,round(bottom-top))),Image.Resampling.LANCZOS)
    if opacity<1:im.putalpha(im.getchannel('A').point(lambda a:round(a*opacity)))
    layer=Image.new('RGBA',(640,360));layer.alpha_composite(im,(round(cx-width/2),round(top)))
    # Grasp the actual curved waistband rather than the outer bounding-box corner.
    return layer,[(cx-width*.40,top+(bottom-top)*.10),(cx+width*.40,top+(bottom-top)*.10)]
def arm_layer(i,target,p,front=False):
    source=arms[i].transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    pivot=np.array([639-rig.pivots[i][0],rig.pivots[i][1]])
    hand0=rig.pos(165 if i==0 else 872,1045);hand=np.array([639-hand0[0],hand0[1]])
    # The attachment follows the torso exactly; a separate vertical shoulder
    # offset exposes the cutout seam below the neck when crouching.
    shoulder=np.array([pivot[0],forward_y(pivot[1],p)])
    old=hand-pivot;new=np.array(target)-shoulder
    ratio=np.linalg.norm(new)/np.linalg.norm(old)
    ratio=max(.65,min(1.35,ratio))
    u=old/np.linalg.norm(old);v=new/max(.001,np.linalg.norm(new))
    # Stretch only along the arm, keeping its thickness and hand width stable.
    matrix=np.outer(u,v)/ratio+np.outer([-u[1],u[0]],[-v[1],v[0]])
    offset=pivot-matrix@shoulder
    coeff=(*matrix[0],offset[0],*matrix[1],offset[1])
    moved=source.transform((640,360),Image.Transform.AFFINE,coeff,Image.Resampling.BICUBIC)
    if front:
        # Blend over skin in torso coordinates, reaching full coverage before
        # the waistband. Rotating this blend with the arm can reveal underwear.
        start=shoulder[1]+1
        end=min(start+20,forward_y(249,p)-4)
        coverage=rig.smooth((yy-start)/max(1,end-start))
        pixels=np.asarray(moved).copy()
        pixels[:,:,3]=(pixels[:,:,3]*coverage).astype('uint8')
        moved=Image.fromarray(pixels)
    return moved
def frame(t,to,before=None):
    if before is None:before='watermelon' if to=='orange' else 'orange'
    if t<=.15:return w.costume_frame('idle',0,before)
    if t>=9.85:return w.costume_frame('idle',0,to)
    p=posture(t);natural_top=forward_y(249,p);natural_bottom=forward_y(322,p)
    pull=ease(t,1.6,2.9);aside=ease(t,3.65,4.65)
    old_cx=mix(320,196,aside);old_width=mix(164,72,aside)
    old_top=mix(mix(natural_top,323,pull),328,aside);old_bottom=mix(mix(natural_bottom,351,pull),351,aside)
    old_opacity=1-ease(t,8.9,9.7)
    old_layer,old_grips=pants(before,old_cx,old_top,old_bottom,old_width,old_opacity)
    pickup=ease(t,4.6,5.35);raise_pants=ease(t,6.6,8.05)
    new_cx=mix(440,320,pickup);new_width=mix(72,164,pickup)
    new_top=mix(328,323,pickup);new_bottom=351
    new_top=mix(new_top,natural_top,raise_pants);new_bottom=mix(new_bottom,natural_bottom,raise_pants)
    new_visible=ease(t,.2,.65)
    new_layer,new_grips=pants(to,new_cx,new_top,new_bottom,new_width,new_visible)
    # Each hand follows a waistband edge; release before stepping out, then grasp new pair.
    targets=[]
    for i in range(2):
        original_hand=rig.pos(165 if i==0 else 872,1045)
        normal=np.array([639-original_hand[0],forward_y(original_hand[1],p)])
        side=1 if i==0 else 0
        old_hold=ease(t,.6,1.55)*(1-ease(t,4.45,4.8) if i==1 else 1-ease(t,3.0,3.5))
        old_grip=np.array(old_grips[side])
        if i==1:old_grip=old_grip*(1-aside)+np.array(old_grips[1])*aside
        new_hold=ease(t,4.05 if i==0 else 5.0,4.65 if i==0 else 5.45)*(1-ease(t,8.65,9.45))
        new_grip=np.array(new_grips[side])
        if i==0:new_grip=np.array(new_grips[0])*(1-pickup)+new_grip*pickup
        target=normal*(1-old_hold)+old_grip*old_hold
        target=target*(1-new_hold)+new_grip*new_hold
        targets.append(target)
    result=Image.new('RGBA',(640,360))
    for i in range(2):result.alpha_composite(arm_layer(i,targets[i],p))
    torso=body(t)
    # Blend the torso's baked rim into the attached arm only over opaque skin.
    # This removes the duplicate bright silhouette; clothing is excluded.
    pixels=np.asarray(torso).copy()
    soft=np.asarray(torso.getchannel('A').filter(ImageFilter.MinFilter(7)).filter(ImageFilter.GaussianBlur(2)))
    rear_alpha=np.asarray(result)[:,:,3]
    skin=rig.smooth((pixels[:,:,1].astype(float)/np.maximum(pixels[:,:,0],1)-.68)/.16)
    region=rig.smooth((rear_alpha.astype(float)-230)/25)*skin*(yy<forward_y(249,p)-4)
    pixels[:,:,3]=(pixels[:,:,3]*(1-region)+np.minimum(pixels[:,:,3],soft)*region).astype('uint8')
    result.alpha_composite(Image.fromarray(pixels))
    # A set-down pair remains a separate, folded object, never a color dissolve.
    result.alpha_composite(old_layer)
    result.alpha_composite(new_layer)
    for i in range(2):result.alpha_composite(arm_layer(i,targets[i],p,True))
    # Exact neutral endpoints avoid a garment seam when the idle chain resumes.
    blend=ease(t,.15,.45)*(1-ease(t,9.45,9.85))
    if blend<1:
        neutral=w.costume_frame('idle',0,before if t<1 else to)
        result=Image.blend(neutral,result,blend)
    return result
def review():
    times=[0,1.5,2.7,3.25,3.95,4.8,5.55,6.3,7.4,9.85]
    sheet=Image.new('RGB',(1500,800),'#e9f0e3');d=ImageDraw.Draw(sheet)
    for j,t in enumerate(times):
        im=frame(t,'orange').crop((100,0,540,360)).resize((300,245));bg=Image.new('RGBA',im.size,'#e9f0e3');bg.alpha_composite(im)
        x=j%5*300;y=j//5*400;sheet.paste(bg.convert('RGB'),(x,y+25));d.text((x+10,y+7),f'{t:.2f}s',fill='#243')
        lower=frame(t,'orange').crop((170,235,475,357)).resize((300,120));bg=Image.new('RGBA',lower.size,'#27332d');bg.alpha_composite(lower);sheet.paste(bg.convert('RGB'),(x,y+275))
    sheet.save(OUT/'dressing-review.jpg')
def encode(to):
    name='change-'+to;path=CLIPS/(name+'.webm');ff=w.rig.FF
    proc=subprocess.Popen([str(ff),'-v','error','-y','-f','rawvideo','-pix_fmt','rgba','-s','640x360','-r','24','-i','-',
      '-an','-c:v','libvpx-vp9','-pix_fmt','yuva420p','-crf','20','-b:v','0','-deadline','realtime','-cpu-used','4','-threads','4','-auto-alt-ref','0',str(path)],stdin=subprocess.PIPE)
    for i in range(240):
        im=frame(i*10/239,to);a=np.asarray(im);yy,xx=np.where(a[:,:,3]>30)
        assert yy.min()>3 and yy.max()<358 and xx.min()>4 and xx.max()<635,(i,yy.min(),yy.max(),xx.min(),xx.max())
        proc.stdin.write(b.clean_encoding_edges(im).tobytes())
    proc.stdin.close();assert proc.wait()==0
    data=subprocess.run([str(ff),'-v','error','-c:v','libvpx-vp9','-i',str(path),'-f','rawvideo','-pix_fmt','rgba','-'],capture_output=True,check=True).stdout
    a=np.frombuffer(data,np.uint8).reshape(-1,360,640,4);assert len(a)==240
    edge=int(max(a[:,:3,:,3].max(),a[:,-2:,:,3].max()));assert edge<20
    records=json.loads((OUT/'validation.json').read_text());records=[r for r in records if r['id']!=name]
    records.append({'id':name,'frames':240,'seconds':10,'decodedEdgeAlpha':edge,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'physicalDressing':True})
    (OUT/'validation.json').write_text(json.dumps(records,indent=2));print(name+' verified: 240 frames',flush=True)
if __name__=='__main__':
    review()
    if '--inspect' not in sys.argv:
        encode('orange');encode('watermelon')
