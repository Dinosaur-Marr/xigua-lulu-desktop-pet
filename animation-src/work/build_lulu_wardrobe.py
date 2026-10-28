"""Two persistent costumes, preserving the approved rig, silhouettes and all 40 poses."""
from pathlib import Path
import sys,json,math,subprocess,hashlib
import numpy as np
from PIL import Image,ImageDraw,ImageFilter
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'work'))
import refine_lulu_arms as refined
b=refined.b;rig=b.rig
normal_params=rig.parameters
import build_lulu_walk_v6 as gait
rig.parameters=normal_params
OUT=ROOT/'outputs/xigua-lulu-wardrobe';CLIPS=OUT/'clips';CLIPS.mkdir(exist_ok=True)
watermelon=rig.base.copy()
edited=Image.open(OUT/'rig/orange-clean-generated.png').convert('RGBA')
old=np.asarray(rig.clean);new=np.asarray(edited.resize(rig.clean.size)).copy()
# Find the existing garment boundaries, so only clothing RGB changes. Keep original
# alpha and all original skin/feet, rather than using a regenerated body silhouette.
r,g,blue=[old[:,:,i].astype(float) for i in range(3)]
candidate=((g>r*1.03)|(blue>g*.72))&(old[:,:,3]>12)
candidate[:1000]=False;candidate[1320:]=False;candidate[:,:170]=False;candidate[:,855:]=False
mask=np.zeros(candidate.shape,dtype=np.uint8)
for x in range(170,855):
    yy=np.flatnonzero(candidate[:,x])
    if len(yy)>4:mask[yy.min():yy.max()+1,x]=255
maskim=Image.fromarray(mask).filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(.45))
weight=np.asarray(maskim,dtype=float)/255
combined=old.copy();combined[:,:,:3]=np.clip(old[:,:,:3]*(1-weight[:,:,None])+new[:,:,:3]*weight[:,:,None],0,255).astype('uint8')
orange=rig.normalize(Image.fromarray(combined))
Image.fromarray(combined).save(OUT/'rig/orange-clean.png');maskim.save(OUT/'rig/garment-mask.png')
orange.save(OUT/'rig/orange-base.png')
assert np.array_equal(np.asarray(orange)[:,:,3],np.asarray(watermelon)[:,:,3])
assert np.array_equal(combined[:980],old[:980])
saved_params=b.params
COSTUMES={'watermelon':watermelon,'orange':orange}

def costume_frame(kind,t,costume='orange'):
    rig.base=COSTUMES[costume]
    if kind in gait.gaits:
        rig.parameters=gait.params
        try:return gait.frame(kind,t)
        finally:rig.parameters=normal_params
    if kind in b.NEW:return b.frame(kind,t)
    return b.old.frame(kind,t)

def change_params(kind,t):
    p=saved_params('nod',0)
    inspect=b.E(t,.3,.9,1.25,1.8)
    crouch=b.P(t,2.25,.68)
    proud=b.E(t,2.75,3.3,3.8,4.7)
    p.update(nod=5*inspect+3*crouch,dip=15*crouch,la=-16*inspect-38*crouch-24*proud,
      ra=16*inspect+38*crouch+24*proud,close=max(.4*inspect,.9*crouch,.7*proud),
      mx=1-.2*inspect,my=1-.3*inspect+.15*proud,angle=.025*math.sin(t*5)*proud,front=False)
    return p

def transition(t,to):
    rig.base=(orange if to=='orange' else watermelon) if t>=2.25 else (watermelon if to=='orange' else orange)
    b.params=change_params
    try:im=b.frame('wardrobe',t)
    finally:b.params=saved_params
    # A brief small glimmer hides the material change, not the face or the feet.
    flash=b.P(t,2.25,.23)
    if flash>.001:
        layer=Image.new('RGBA',im.size);d=ImageDraw.Draw(layer)
        d.ellipse((225,248,416,322),fill=(255,242,188,round(230*flash)))
        layer=layer.filter(ImageFilter.GaussianBlur(8));im.alpha_composite(layer)
    k=b.E(t,1.8,2.15,2.65,3.1)
    if k>.001:
        d=ImageDraw.Draw(im)
        for i,(x,y) in enumerate([(217,253),(424,265),(227,304),(415,311)]):
            radius=(4+2*math.sin(t*8+i))*k
            d.polygon([(x,y-radius),(x+radius*.3,y-radius*.3),(x+radius,y),(x+radius*.3,y+radius*.3),(x,y+radius),(x-radius*.3,y+radius*.3),(x-radius,y),(x-radius*.3,y-radius*.3)],fill=(255,211,71,round(240*k)))
    return im

def encode(kind,costume='orange'):
    is_change=kind.startswith('change-')
    path=CLIPS/(kind+'.webm')
    ff=rig.FF
    proc=subprocess.Popen([str(ff),'-v','error','-y','-f','rawvideo','-pix_fmt','rgba','-s','640x360','-r','24','-i','-',
      '-c:v','libvpx-vp9','-pix_fmt','yuva420p','-b:v','0','-crf','20','-deadline','realtime','-cpu-used','4','-threads','3','-auto-alt-ref','0','-row-mt','1','-an',str(path)],stdin=subprocess.PIPE)
    max_alpha_delta=0
    for i in range(120):
        t=i*5/119
        im=transition(t,kind.split('-')[1]) if is_change else costume_frame(kind,t,costume)
        a=np.asarray(im);yy,xx=np.where(a[:,:,3]>40)
        assert yy.min()>3 and yy.max()<358 and xx.min()>4 and xx.max()<635,(kind,i,'edge')
        # RGB edits must not affect body/arm/leg silhouettes in any frame.
        if not is_change:
            reference=np.asarray(costume_frame(kind,t,'watermelon'))
            delta=int(np.abs(a[:,:,3].astype(int)-reference[:,:,3].astype(int)).max())
            max_alpha_delta=max(max_alpha_delta,delta)
            assert delta==0,(kind,i,'silhouette')
        proc.stdin.write(b.clean_encoding_edges(im).tobytes())
        if i in [0,24,48,72,96,119]:im.save(CLIPS/f'{kind}-{i:03d}.png')
    proc.stdin.close();assert proc.wait()==0
    data=subprocess.run([str(ff),'-v','error','-c:v','libvpx-vp9','-i',str(path),'-f','rawvideo','-pix_fmt','rgba','-'],capture_output=True,check=True).stdout
    a=np.frombuffer(data,np.uint8).reshape(-1,360,640,4)
    assert len(a)==120
    edge=int(max(a[:,:3,:,3].max(),a[:,-2:,:,3].max(),a[:,:,:3,3].max(),a[:,:,-3:,3].max()));assert edge<20,(kind,edge)
    result={'id':kind,'frames':120,'decodedEdgeAlpha':edge,'silhouetteMaxDelta':max_alpha_delta,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
    print(json.dumps(result),flush=True)
    return result

def inspect():
    sheet=Image.new('RGB',(1200,720),'#edf2e9');d=ImageDraw.Draw(sheet)
    for col,costume in enumerate(['watermelon','orange']):
        for row,kind in enumerate(['idle','walk']):
            im=costume_frame(kind,1.25,costume)
            bg=Image.new('RGBA',im.size,'#edf2e9');bg.alpha_composite(im)
            sheet.paste(bg.convert('RGB'),(col*600,row*360));d.text((col*600+15,row*360+10),costume+' '+kind,fill='#152')
    sheet.save(OUT/'costume-check.jpg')

if __name__=='__main__':
    inspect()
    if '--inspect' in sys.argv:sys.exit()
    kinds=[sys.argv[sys.argv.index('--action')+1]] if '--action' in sys.argv else list(b.LABELS)+['change-orange','change-watermelon']
    validation=OUT/'validation.json';records=json.loads(validation.read_text()) if validation.exists() else []
    kinds=[k for k in kinds if not ('--resume' in sys.argv and any(r['id']==k and (CLIPS/(k+'.webm')).exists() for r in records))]
    if '--workers' in sys.argv:
        from concurrent.futures import ProcessPoolExecutor
        with ProcessPoolExecutor(max_workers=int(sys.argv[sys.argv.index('--workers')+1])) as pool:
            for record in pool.map(encode,kinds):
                records=[r for r in records if r['id']!=record['id']]+[record]
                validation.write_text(json.dumps(records,indent=2),encoding='utf8')
    else:
        for kind in kinds:
            record=encode(kind);records=[r for r in records if r['id']!=kind]+[record]
            validation.write_text(json.dumps(records,indent=2),encoding='utf8')
