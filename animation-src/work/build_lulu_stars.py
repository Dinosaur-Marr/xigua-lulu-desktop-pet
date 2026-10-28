"""Star shorts on all approved poses, plus four physical dressing routes."""
from pathlib import Path
import sys,json,subprocess,hashlib
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'work'))
import build_lulu_dressing as d
w=d.w;rig=d.rig
OUT=ROOT/'outputs/xigua-lulu-wardrobe-three';CLIPS=OUT/'clips'
generated=Image.open(OUT/'rig/star-clean-generated.png').convert('RGBA').resize(rig.clean.size)
old=np.asarray(rig.clean);new=np.asarray(generated)
weight=w.weight[:,:,None]
combined=old.copy();combined[:,:,:3]=np.clip(old[:,:,:3]*(1-weight)+new[:,:,:3]*weight,0,255).astype('uint8')
assert np.array_equal(combined[:,:,3],old[:,:,3])
assert np.array_equal(combined[:980],old[:980])
star=rig.normalize(Image.fromarray(combined))
w.COSTUMES['star']=star
pixels=np.asarray(star).copy();pixels[:,:,3]=(pixels[:,:,3].astype(float)*np.asarray(d.garment)/255).astype('uint8')
d.clothes['star']=Image.fromarray(pixels).transpose(Image.Transpose.FLIP_LEFT_RIGHT)
w.CLIPS=CLIPS
ROUTES=[('watermelon','star'),('orange','star'),('star','watermelon'),('star','orange')]

def encode(kind):
    if not kind.startswith('change-'):return w.encode(kind,'star')
    _,before,to=kind.split('-');path=CLIPS/(kind+'.webm')
    proc=subprocess.Popen([str(rig.FF),'-v','error','-y','-f','rawvideo','-pix_fmt','rgba','-s','640x360','-r','24','-i','-',
        '-an','-c:v','libvpx-vp9','-pix_fmt','yuva420p','-crf','20','-b:v','0','-deadline','realtime','-cpu-used','4','-threads','2','-auto-alt-ref','0',str(path)],stdin=subprocess.PIPE)
    for i in range(240):
        im=d.frame(i*10/239,to,before);a=np.asarray(im);y,x=np.where(a[:,:,3]>30)
        assert y.min()>3 and y.max()<358 and x.min()>4 and x.max()<635,(kind,i,'edge')
        proc.stdin.write(w.b.clean_encoding_edges(im).tobytes())
    proc.stdin.close();assert proc.wait()==0
    assert np.array_equal(np.asarray(d.frame(0,to,before)),np.asarray(w.costume_frame('idle',0,before)))
    assert np.array_equal(np.asarray(d.frame(10,to,before)),np.asarray(w.costume_frame('idle',0,to)))
    data=subprocess.run([str(rig.FF),'-v','error','-c:v','libvpx-vp9','-i',str(path),'-f','rawvideo','-pix_fmt','rgba','-'],capture_output=True,check=True).stdout
    a=np.frombuffer(data,np.uint8).reshape(-1,360,640,4);assert len(a)==240
    edge=int(max(a[:,:3,:,3].max(),a[:,-2:,:,3].max()));assert edge<20
    record=dict(id=kind,frames=240,seconds=10,decodedEdgeAlpha=edge,physicalDressing=True,source=before,target=to,sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    print(json.dumps(record),flush=True);return record

def inspect():
    Image.fromarray(combined).save(OUT/'rig/star-clean.png');star.save(OUT/'rig/star-base.png')
    sheet=Image.new('RGB',(1200,720),'#e9efdf');draw=ImageDraw.Draw(sheet)
    for j,(kind,t) in enumerate([('idle',0),('wave',1.4),('walk',1.25),('hug',2.5)]):
        im=w.costume_frame(kind,t,'star');bg=Image.new('RGBA',im.size,'#e9efdf');bg.alpha_composite(im)
        sheet.paste(bg.convert('RGB'),(j%2*600,j//2*360));draw.text((j%2*600+10,j//2*360+10),kind,fill='#234')
    sheet.save(OUT/'star-costume-check.jpg')

if __name__=='__main__':
    inspect()
    if '--inspect' in sys.argv:sys.exit()
    kinds=list(w.b.LABELS)+[f'change-{a}-{b}' for a,b in ROUTES]
    path=OUT/'validation.json';records=json.loads(path.read_text()) if path.exists() else []
    if '--resume' in sys.argv:kinds=[k for k in kinds if not any(r['id']==k and (CLIPS/(k+'.webm')).exists() and hashlib.sha256((CLIPS/(k+'.webm')).read_bytes()).hexdigest()==r['sha256'] for r in records)]
    from concurrent.futures import ProcessPoolExecutor
    with ProcessPoolExecutor(max_workers=3) as pool:
        for record in pool.map(encode,kinds):
            records=[r for r in records if r['id']!=record['id']]+[record]
            path.write_text(json.dumps(records,indent=2),encoding='utf8')
