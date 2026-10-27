"""21 distinct expressive actions, keeping the approved 19 clips and 27 memes intact."""
from pathlib import Path
import sys,json,math,subprocess,shutil,hashlib
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'work'))
import build_lulu_clean_edges as old
rig=old.rig;FF=rig.FF
OUT=ROOT/'outputs/xigua-lulu-pet-40';CLIPS=OUT/'clips';CLIPS.mkdir(parents=True,exist_ok=True)
SOURCE=ROOT/'outputs/xigua-lulu-pet-v6'
NEW={
 'nod':('点头认可','互动'), 'no':('摇头拒绝','互动'), 'wink':('歪头眨眼','互动'),
 'kiss':('飞吻送心','互动'), 'hug':('抱心心','互动'), 'clap':('拍手鼓励','互动'),
 'cheer':('举拳加油','互动'), 'beckon':('招手过来','互动'), 'shrug':('摊手耸肩','互动'),
 'surprise':('瞪眼后仰','情绪'), 'sneeze':('打喷嚏','日常'), 'yawn':('大口哈欠','日常'),
 'wake':('瞌睡惊醒','情绪'), 'listen':('侧耳倾听','互动'), 'disco':('交替举手舞','运动'),
 'twist':('扭腰摆胯','运动'), 'squat':('蹲起锻炼','运动'), 'balance':('单脚平衡','运动'),
 'kick':('向前踢腿','运动'), 'shakeoff':('抖抖甩水','日常'), 'thank':('合手致谢','互动')}
LABELS=dict(rig.LABELS);LABELS.update({k:v[0] for k,v in NEW.items()})
assert len(LABELS)==40
def E(t,a=.25,b=.8,c=4.1,d=4.9):return rig.ease(t,a,b)*(1-rig.ease(t,c,d))
def P(t,c,w):return rig.pulse(t,c,w)
def params(kind,t):
    e=E(t);u=np.clip((t-.8)/3.2,0,1);s=math.sin(2*math.pi*u)
    p=dict(sx=1.,sy=1.,up=0.,lean=0.,angle=0.,la=0.,ra=0.,close=max(P(t,1.35,.16),P(t,3.8,.18)),wink=0.,gaze=0.,mx=1.,my=1.,laugh=0.,eye=1.,nod=0.,dip=0.,front=False,prop=None,hip=0.,legx=0.,legup=0.)
    if kind=='nod':
        n=(P(t,1.25,.45)+P(t,2.45,.45)+P(t,3.65,.45));p.update(nod=8*n,close=.42*n,my=1-.28*n,la=10*e,ra=-10*e,lean=2*n)
    elif kind=='no':p.update(angle=.13*math.sin(6*math.pi*u)*e,lean=4*math.sin(6*math.pi*u)*e,gaze=-2*math.sin(6*math.pi*u)*e,mx=1-.48*e,my=1-.7*e,la=(-75+14*math.sin(8*math.pi*u))*e,ra=10*e)
    elif kind=='wink':p.update(angle=.13*e,lean=6*e,wink=max(P(t,1.5,.55),P(t,3.2,.55)),gaze=1.5*e,mx=1+.06*e,my=1+.12*e,la=-28*e,ra=12*e)
    elif kind=='kiss':
        hold=E(t,.3,1,2,2.7);release=E(t,1.7,2.1,3.7,4.4)
        p.update(la=128*hold,ra=8*e,front=True,mx=1-.69*hold,my=1-.52*hold,close=.55*hold,angle=-.08*hold,prop='kiss',lean=-4*hold)
    elif kind=='hug':p.update(la=65*e,ra=-65*e,front=True,prop='heart',close=.78*e,angle=.055*s*e,lean=5*s*e,my=1+.14*e)
    elif kind=='clap':
        beat=sum(P(t,c,.24) for c in [1.25,2.25,3.25]);p.update(la=(56+26*beat)*e,ra=-(56+26*beat)*e,front=True,close=.55*beat,my=1+.25*beat,nod=3*beat,prop='clap')
    elif kind=='cheer':
        beat=sum(P(t,c,.36) for c in [1.35,2.65,3.75]);p.update(ra=(92+40*beat)*e,la=12*e,angle=-.045*beat,lean=-4*beat,close=.6*beat,my=1+.35*beat,dip=3*beat)
    elif kind=='beckon':p.update(la=(-70+25*math.sin(6*math.pi*u))*e,ra=15*e,angle=.055*e,gaze=-2*e,my=1+.13*e,nod=2*math.sin(6*math.pi*u)*e)
    elif kind=='shrug':
        k=E(t,.4,1.2,3.2,4.4);p.update(la=-67*k,ra=67*k,lean=3*s*k,angle=.075*s*k,nod=-4*k,mx=1-.5*k,my=1-.35*k,eye=1+.055*k)
    elif kind=='surprise':
        k=E(t,.8,1.05,2.8,4.2);p.update(eye=1+.13*k,mx=1-.55*k,my=1+.3*k,la=-52*k,ra=52*k,angle=-.075*k,lean=-8*k,nod=-5*k,dip=3*P(t,1.1,.25),close=P(t,3.5,.17))
    elif kind=='sneeze':
        a=E(t,.3,1.4,1.55,1.85);burst=P(t,2.05,.27)
        p.update(mx=1-.45*a+.05*burst,my=1+.2*a-.55*burst,close=max(.5*a,burst),nod=-4*a+10*burst,dip=10*burst,lean=-3*a+8*burst,angle=.035*math.sin(t*28)*burst,la=50*burst,ra=-50*burst,front=True,prop='sneeze')
    elif kind=='yawn':
        k=E(t,.4,1.6,3.15,4.4);p.update(close=.95*k,mx=1-.25*k,my=1+.58*k,nod=-4*k,angle=-.055*k,la=-30*k,ra=32*k,lean=-3*k)
    elif kind=='wake':
        sleepy=E(t,.15,.75,2.1,2.45);startled=E(t,2.18,2.37,2.75,3.5)
        p.update(close=max(sleepy,P(t,3.65,.15),P(t,4.1,.15)),nod=10*sleepy-4*startled,angle=.1*sleepy,eye=1+.14*startled,mx=1-.52*sleepy-.25*startled,my=1-.4*sleepy+.36*startled,la=-65*startled,ra=65*startled,dip=5*sleepy)
    elif kind=='listen':p.update(angle=-.17*e,lean=-8*e,gaze=-2.5*e,ra=83*e,la=5*e,mx=1-.25*e,my=1-.35*e,eye=1+.04*e,nod=1.4*math.sin(8*math.pi*u)*e)
    elif kind=='disco':
        beat=math.sin(6*math.pi*u)*e;p.update(la=(-65-58*math.sin(6*math.pi*u))*e,ra=(65-58*math.sin(6*math.pi*u))*e,lean=8*beat,angle=.065*beat,hip=6*beat,close=.55*abs(beat),my=1+.2*abs(beat),dip=3*abs(beat))
    elif kind=='twist':
        beat=math.sin(8*math.pi*u)*e;p.update(la=28*e,ra=-28*e,front=True,hip=11*beat,lean=-6*beat,angle=-.07*beat,close=.5*e,my=1+.15*math.cos(8*math.pi*u)*e,dip=2*abs(beat))
    elif kind=='squat':
        dip=sum(P(t,c,.7) for c in [1.35,3.35]);p.update(dip=27*dip,la=(-65)*dip,ra=65*dip,nod=3*dip,close=.48*dip,mx=1-.24*dip,my=1-.42*dip)
    elif kind=='balance':
        k=E(t,.4,1.2,3.7,4.6);w=math.sin(5*math.pi*u)*k
        p.update(legup=23*k,legx=5*k,hip=5*k,la=-61*k+8*w,ra=61*k+8*w,angle=.055*w,lean=-3*w,mx=1-.4*k,my=1-.5*k,gaze=-1.5*k)
    elif kind=='kick':
        k=P(t,1.5,.65)+P(t,3.25,.65);p.update(legup=16*k,legx=21*k,hip=4*k,la=-40*k,ra=35*k,lean=-6*k,angle=-.035*k,close=.4*k,my=1+.2*k)
    elif kind=='shakeoff':
        k=E(t,.55,1,3.6,4.4);w=math.sin(18*math.pi*u)*k;p.update(lean=5*w,angle=.075*w,la=-37*k+13*w,ra=37*k+13*w,close=.8*k,my=1-.55*k,mx=1-.25*k,hip=-3*w,prop='water')
    elif kind=='thank':
        k=E(t,.3,1,3.9,4.7);bow=P(t,2.2,1.1);p.update(la=78*k,ra=-78*k,front=True,nod=6*bow,dip=13*bow,close=.85*bow,my=1-.45*bow,mx=1-.15*bow)
    return p

def heart(im,cx,cy,size,alpha=255):
    # A small rounded, shaded prop; hands are composited in front of it.
    layer=Image.new('RGBA',im.size);d=ImageDraw.Draw(layer)
    pts=[]
    for a in np.linspace(0,2*math.pi,100):
        pts.append((cx+size*math.sin(a)**3,cy-size*(13*math.cos(a)-5*math.cos(2*a)-2*math.cos(3*a)-math.cos(4*a))/16))
    d.polygon(pts,fill=(245,86,103,int(alpha)));d.ellipse((cx-size*.6,cy-size*.62,cx-size*.2,cy-size*.4),fill=(255,161,165,int(alpha*.7)))
    im.alpha_composite(layer)
def props(im,kind,t,p):
    e=E(t)
    if p['prop']=='heart' and e>.01:heart(im,322,239,34*e,255*e)
    if p['prop']=='kiss':
        for i in range(3):
            u=(t-1.85-i*.23)/1.7
            if 0<u<1:heart(im,342-75*u+9*i,174-45*u-12*i,9*(.4+.6*math.sin(math.pi*u)),240*math.sin(math.pi*u))
    d=ImageDraw.Draw(im)
    if p['prop']=='clap':
        k=max(P(t,c,.23) for c in [1.25,2.25,3.25])
        if k>.1:
            for dx,dy in [(-22,-12),(22,-12),(0,-25)]:d.line((322+dx,230+dy,322+dx*1.35,230+dy*1.35),fill=(255,185,30,int(230*k)),width=3)
    if p['prop'] in ['water','sneeze']:
        k=E(t,.7,1.1,3.5,4.3) if p['prop']=='water' else P(t,2.12,.35)
        if k>.05:
            for i in range(6):
                side=(-1 if i%2==0 else 1);x=320+side*(140+5*math.sin(9*t+i));y=80+25*(i//2)+7*math.cos(8*t+i)
                d.ellipse((x-2,y-4,x+2,y+3),fill=(104,193,243,int(200*k)))

def compose(kind,t,p):
    im=Image.new('RGBA',(640,360));arm_layers=[]
    for i,(asset,ang,pivot) in enumerate(zip(rig.arms,(p['la'],p['ra']),rig.pivots)):
        moved=asset.rotate(ang,resample=Image.Resampling.BICUBIC,center=pivot)
        if p['front']:arm_layers.append(moved)
        else:im.alpha_composite(moved)
    im.alpha_composite(rig.base)
    for i in range(2):
        c=max(p['close'],p['wink'] if i==0 else 0)
        if c<.65:rig.paste_feature(im,rig.eyes[i],sx=p['eye'],sy=max(.12,1-1.12*c)*p['eye'],dx=p['gaze'])
        else:rig.paste_feature(im,rig.closed[i])
    rig.paste_feature(im,rig.mouth,sx=p['mx'],sy=p['my'])
    props(im,kind,t,p)
    for layer in arm_layers:im.alpha_composite(layer)
    return im

Y,X=np.mgrid[:360,150:490].astype(np.float32)
HEAD=rig.smooth((252-Y)/50);ROOTWEIGHT=rig.smooth((352-Y)/145)
def frame(kind,t):
    if t>=5:t=0
    p=params(kind,t);im=compose(kind,t,p)
    # Whole-body inverse map keeps the face and shoulder joints with the torso.
    qx=X-p['lean']*ROOTWEIGHT
    qy=Y-p['dip']*ROOTWEIGHT+p['up']-p['nod']*HEAD
    th=-p['angle']*HEAD;dx=qx-320;dy=qy-220
    qx=320+dx*np.cos(th)-dy*np.sin(th);qy=220+dx*np.sin(th)+dy*np.cos(th)
    # Shorts, hips and feet share this continuous lower-body deformation.
    for _ in range(6):
        lower=rig.smooth((qy-258)/78);split=1-rig.smooth((qx-287)/78)
        hipweight=1-rig.smooth((qy-282)/62)
        knee=np.maximum(0,np.sin(np.pi*np.clip((qy-258)/94,0,1)))**2
        lx=p['legx']*split*lower+p['hip']*hipweight+2*(p['legup']/23)*knee*split
        ly=-p['legup']*split*lower
        # The base torso map is fixed; iterate only the nonlinear lower-body field.
        baseX=320+dx*np.cos(th)-dy*np.sin(th)
        baseY=220+dx*np.sin(th)+dy*np.cos(th)
        qx=baseX-lx;qy=baseY-ly
    a=np.asarray(im,dtype=np.float32);a[:,:,:3]*=a[:,:,3:4]/255
    qx=np.clip(qx,0,638.999);qy=np.clip(qy,0,358.999)
    ix=qx.astype('int32');iy=qy.astype('int32');fx=(qx-ix)[...,None];fy=(qy-iy)[...,None]
    b=(a[iy,ix]*(1-fx)+a[iy,ix+1]*fx)*(1-fy)+(a[iy+1,ix]*(1-fx)+a[iy+1,ix+1]*fx)*fy
    b[:,:,:3]=np.divide(b[:,:,:3]*255,b[:,:,3:4],out=np.zeros_like(b[:,:,:3]),where=b[:,:,3:4]>.1)
    result=np.zeros((360,640,4),dtype='uint8');result[:,150:490]=np.clip(b,0,255).astype('uint8')
    im=Image.fromarray(result).transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    yy,xx=np.where(result[:,:,3]>100);shift=351-int(yy.max())
    if shift:
        grounded=Image.new('RGBA',im.size);grounded.alpha_composite(im,(0,shift));im=grounded
    return im

def clean_encoding_edges(im):
    # Bicubic sampling can leave arbitrary RGB at alpha 1/255. VP9 subsamples that
    # color into visible neighboring pixels; extend reliable edge colors beneath alpha.
    a=np.asarray(im).copy();rgb=a[:,:,:3].astype(float);valid=a[:,:,3]>=32
    for _ in range(4):
        total=np.zeros_like(rgb);count=np.zeros(valid.shape,float)
        for dy,dx in [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]:
            v=np.roll(valid,(dy,dx),(0,1));c=np.roll(rgb,(dy,dx),(0,1))
            total+=c*v[:,:,None];count+=v
        fill=(~valid)&(count>0)
        rgb[fill]=total[fill]/count[fill,None];valid|=fill
    a[:,:,:3]=np.clip(rgb,0,255).astype('uint8')
    return a

def encode(kind):
    path=CLIPS/f'{kind}.webm'
    proc=subprocess.Popen([str(FF),'-v','error','-y','-f','rawvideo','-pix_fmt','rgba','-s','640x360','-r','24','-i','-',
      '-c:v','libvpx-vp9','-pix_fmt','yuva420p','-b:v','0','-crf','20','-deadline','realtime','-cpu-used','4','-threads','4','-auto-alt-ref','0','-row-mt','1','-an',str(path)],stdin=subprocess.PIPE)
    signature=[]
    for i in range(120):
        im=frame(kind,i*5/119);a=np.asarray(im);yy,xx=np.where(a[:,:,3]>40)
        assert yy.min()>3 and yy.max()<355 and xx.min()>152 and xx.max()<487,(kind,i,'clip')
        encoded=clean_encoding_edges(im);proc.stdin.write(encoded.tobytes())
        if i in [24,48,72,96]:signature.append(np.asarray(im.resize((64,36))).astype(float))
        if i==48:Image.fromarray(encoded).save(CLIPS/f'{kind}.png')
    proc.stdin.close();assert proc.wait()==0
    assert np.array_equal(np.asarray(frame(kind,0)),np.asarray(frame(kind,5)))
    data=subprocess.run([str(FF),'-v','error','-c:v','libvpx-vp9','-i',str(path),'-f','rawvideo','-pix_fmt','rgba','-'],capture_output=True,check=True).stdout
    a=np.frombuffer(data,np.uint8).reshape(-1,360,640,4);assert len(a)==120
    assert a[:,:3,:,3].max()<8 and a[:,-1,:,3].max()<8
    endpoint=float(np.abs(a[0].astype(float)-a[-1].astype(float)).mean());assert endpoint<2
    soles=[]
    for i,fr in enumerate(a):
        mask=(fr[255:356,210:430,3]>100).astype('uint8')*255
        m=Image.fromarray(mask).copy();ImageDraw.floodfill(m,(110,10),128)
        assert not np.any(np.asarray(m)[65:]==255),(kind,i,'disconnected feet')
        yy,xx=np.where(fr[:,:,3]>100);soles.append(int(yy.max()))
    assert max(soles)-min(soles)<=1,(kind,min(soles),max(soles))
    np.save(CLIPS/f'{kind}-signature.npy',np.array(signature))
    r=dict(kind=kind,label=NEW[kind][0],frames=120,alpha=True,endpointError=endpoint,footConnected=True,soleRange=[min(soles),max(soles)])
    print(json.dumps(r,ensure_ascii=True),flush=True);return r

def storyboard():
    font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',20)
    sheets=[]
    for start in range(0,21,7):
        sheet=Image.new('RGB',(1280,7*200),'#e8eef2');d=ImageDraw.Draw(sheet)
        for row,(kind,(label,cat)) in enumerate(list(NEW.items())[start:start+7]):
            d.text((10,row*200+4),f'{start+row+20:02} {label}',font=font,fill='#29414a')
            for col,t in enumerate([1.2,2.1,3.1,3.8]):
                im=frame(kind,t).crop((150,0,490,360)).resize((170,180));bg=Image.new('RGBA',im.size,'#e8eef2');bg.alpha_composite(im)
                sheet.paste(bg.convert('RGB'),(190+col*270,row*200+10))
        name=f'new-actions-{start//7+1}.jpg';sheet.save(OUT/name);sheets.append(name)
    return sheets

if __name__=='__main__':
    if '--inspect' in sys.argv:storyboard();sys.exit()
    for p in (SOURCE/'clips').iterdir():
        if p.suffix in ['.webm','.png']:shutil.copy2(p,CLIPS/p.name)
    progress=OUT/'new-validation.json';records=[]
    if '--resume' in sys.argv and progress.exists():records=json.loads(progress.read_text(encoding='utf8'))
    done={r['kind'] for r in records}
    for kind in NEW:
        if kind not in done:records.append(encode(kind));progress.write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf8')
    previous=json.loads((SOURCE/'decoded-validation.json').read_text(encoding='utf8'))
    records=previous+records;assert len(records)==40
    (OUT/'decoded-validation.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf8')
    # The original 19 clips are retained byte-for-byte, including the approved walking rig.
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    assert all(sha(SOURCE/'clips'/f'{r["kind"]}.webm')==sha(CLIPS/f'{r["kind"]}.webm') for r in previous)
    assert len({sha(CLIPS/f'{k}.webm') for k in LABELS})==40
    mapping=json.loads((SOURCE/'mapping.json').read_text(encoding='utf8'))
    for k,(label,cat) in NEW.items():mapping['西瓜噜-'+label]=k
    mapping.update({'哈欠连天':'yawn','打瞌睡被惊醒':'wake','被吓一跳':'surprise','原地重力下蹲压缩':'squat','可爱宅舞':'disco'})
    (OUT/'mapping.json').write_text(json.dumps(mapping,ensure_ascii=False,indent=2),encoding='utf8')
    manifest=[dict(id=k,name=label,new=k in NEW,category=NEW[k][1] if k in NEW else '已有动作') for k,label in LABELS.items()]
    (OUT/'actions.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8')
    (OUT/'new-actions.json').write_text(json.dumps({k:dict(name='西瓜噜-'+label,category=cat) for k,(label,cat) in NEW.items()},ensure_ascii=False,indent=2),encoding='utf8')
    storyboard()
