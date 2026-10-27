"""Separate-arm and animated-face rig; approved character, 640x360 transparent VP9."""
from pathlib import Path
import sys, json, math, subprocess, hashlib
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'work'))
import build_lulu_pet as v1
OUT=ROOT/'outputs/xigua-lulu-pet-v2'
CLIPS=OUT/'clips'; CLIPS.mkdir(parents=True,exist_ok=True)
FF=v1.FF; LABELS=v1.LABELS
original=Image.open(ROOT/'outputs/watermelon-lulu-no-helmet.png').convert('RGBA')
clean=Image.open(ROOT/'work/lulu-v2-rig/clean.png').convert('RGBA').resize(original.size,Image.Resampling.LANCZOS)
happy=Image.open(ROOT/'work/lulu-v2-rig/happy.png').convert('RGBA').resize(original.size,Image.Resampling.LANCZOS)
crop=v1.crop; scale=v1.scale; left=(640-v1.char.width)//2

def normalize(im):
    c=im.crop(crop).resize(v1.char.size,Image.Resampling.LANCZOS)
    out=Image.new('RGBA',(640,360));out.alpha_composite(c,(left,22));return out

def pos(x,y): return (left+(x-crop[0])*scale,22+(y-crop[1])*scale)
def smooth(x): x=np.clip(x,0,1);return x*x*(3-2*x)
def ease(t,a,b): return float(smooth((t-a)/(b-a)))
def pulse(t,c,w): return float(max(0,math.cos((t-c)/w*math.pi/2))**2) if abs(t-c)<w else 0.
def envelope(t): return ease(t,0,.5)*(1-ease(t,4.4,5))

# Original textured arms as independently rotating layers. Inner edges remain hidden under the torso.
def arm(points):
    mask=Image.new('L',original.size);ImageDraw.Draw(mask).polygon(points,fill=255)
    mask=mask.filter(ImageFilter.GaussianBlur(.8))
    pixels=np.asarray(original,dtype=np.float32)
    r,g,b=pixels[:,:,0],pixels[:,:,1],pixels[:,:,2]
    # The polygon encloses the hand but can also contain the adjoining green waistband,
    # white cloth and red print. Refine this arm-only matte at source resolution before
    # downsampling, so clothing cannot rotate with the hand or bleed into its edge.
    skin=np.minimum.reduce([np.clip((r-g-5)/10,0,1),np.clip((g-b-20)/20,0,1),np.clip((g-.43*r)/12,0,1)])
    coverage=pixels[:,:,3]*(np.asarray(mask,dtype=float)/255)*skin
    im=original.copy(); im.putalpha(Image.fromarray(np.clip(coverage,0,255).astype('uint8')))
    return normalize(im)
arms=[arm([(266,806),(321,870),(276,948),(248,990),(251,1042),(219,1069),(203,1100),(154,1117),(104,1091),(73,1044),(70,977),(98,907),(167,843),(228,806)]),
      arm([(756,814),(814,809),(865,860),(910,940),(936,1034),(928,1094),(899,1119),(850,1119),(817,1090),(815,1053),(802,1034),(782,962),(761,905)])]
pivots=[pos(266,842),pos(789,845)]
base=normalize(clean)

def feature(image,cx,cy,rx,ry):
    box=(int(cx-rx),int(cy-ry),int(cx+rx),int(cy+ry))
    a=np.asarray(image.crop(box)).copy().astype(float)
    b=np.asarray(clean.crop(box)).astype(float)
    y,x=np.mgrid[:a.shape[0],:a.shape[1]]
    r=np.sqrt(((x-rx)/rx)**2+((y-ry)/ry)**2)
    ring=(r>.87)&(r<.98)
    # Match local skin on the patch rim; full original eye and mouth stay intact inside.
    offset=(b[ring,:3]-a[ring,:3]).mean(axis=0)
    a[:,:,:3]=np.clip(a[:,:,:3]+offset,0,255)
    a[:,:,3]*=1-smooth((r-.73)/.27)
    patch=Image.fromarray(a.astype('uint8')).resize((round(2*rx*scale),round(2*ry*scale)),Image.Resampling.LANCZOS)
    return patch,pos(cx,cy)
eyes=[feature(original,455,405,108,88),feature(original,767,421,93,88)]
closed=[feature(happy,455,405,108,88),feature(happy,767,421,93,88)]
mouth=feature(original,611,727,192,123)
laugh=feature(happy,611,727,192,123)

def paste_feature(canvas,item,sx=1.,sy=1.,dx=0.,dy=0.,opacity=1.):
    im,(cx,cy)=item
    if opacity<=.001:return
    im=im.resize((max(1,round(im.width*sx)),max(1,round(im.height*sy))),Image.Resampling.BICUBIC)
    if opacity<.999:
        im=im.copy();im.putalpha(im.getchannel('A').point(lambda p:round(p*opacity)))
    canvas.alpha_composite(im,(round(cx-im.width/2+dx),round(cy-im.height/2+dy)))

Y,X=np.mgrid[:360,145:495].astype(np.float32)
head=smooth((256-Y)/48)
root=np.clip((352-Y)/185,0,1)

def parameters(kind,t):
    e=envelope(t); s=math.sin(2*math.pi*t/5)
    p=dict(sx=1.,sy=1.,up=0.,lean=0.,angle=0.,la=0.,ra=0.,step=0.,close=0.,wink=0.,gaze=0.,mx=1.,my=1.,laugh=0.)
    blink=max(pulse(t,1.45,.18),pulse(t,3.85,.19))
    p['close']=blink
    p['sy']=1+.008*(1-math.cos(2*math.pi*t/5))
    if kind=='idle':p['my']=1-.08*math.sin(math.pi*t/5)**2;p['gaze']=.6*s
    elif kind=='wave':
        lift=ease(t,.22,.8)*(1-ease(t,4.15,4.8))
        u=np.clip((t-.9)/3,0,1)
        p.update(la=(-108+25*math.sin(6*math.pi*u))*lift,ra=8*lift,
          lean=7*math.sin(6*math.pi*u)*lift,angle=.065*math.sin(6*math.pi*u+.5)*lift,
          laugh=.8*lift,mx=1+.07*lift+.03*math.sin(6*math.pi*u)*lift,my=1+.14*math.sin(6*math.pi*u+.4)*lift,close=max(pulse(t,1.42,.2),pulse(t,3.55,.26)),wink=pulse(t,2.45,.34),
          sy=1-.025*lift+.015*math.sin(6*math.pi*u)*lift)
    elif kind in ('jump','celebrate'):
        for start in (.35,2.45):
            u=t-start
            if 0<=u<.35:
                k=ease(u,0,.35);p.update(sx=1+.08*k,sy=1-.11*k,mx=.9,my=.68,close=.35*k,la=-15*k,ra=15*k)
            elif .35<=u<1.2:
                k=(u-.35)/.85; lift=math.sin(math.pi*k)
                p.update(sx=1-.025*lift,sy=1-.035*lift,up=24*lift,la=-95*lift,ra=88*lift,close=.78*lift,laugh=lift,mx=1+.1*lift,my=1+.18*lift)
            elif 1.2<=u<1.65:
                k=math.sin(math.pi*(u-1.2)/.45);p.update(sx=1+.07*k,sy=1-.09*k,close=.8*k,laugh=.5*k)
    elif kind=='giggle':
        k=math.sin(14*math.pi*t/5)*e
        p.update(sx=1+.035*k,sy=1-.025*k,angle=.045*k,la=-25*e+8*k,ra=25*e-8*k,close=.95*e,laugh=e,my=1+.23*k,mx=1+.08*e)
    elif kind=='shy':p.update(sy=1-.055*e,sx=1+.02*e,angle=.12*e,lean=-6*e,close=.7*e,gaze=-2*e,mx=1-.25*e,my=1-.48*e,la=15*e,ra=-15*e)
    elif kind=='angry':
        k=math.sin(10*math.pi*t/5)*e
        p.update(lean=4*k,angle=.04*k,step=5*k,sx=1+.02*e,sy=1-.04*e,la=-27*e,ra=27*e,close=.55*e,mx=1-.5*e,my=1-.45*e)
    elif kind in ('look','think'):
        p.update(angle=(.1 if kind=='look' else .14)*s*e,lean=6*s*e,gaze=2.2*s*e,my=1-.55*e,mx=1-.18*e,la=-10*e)
    elif kind=='sway':p.update(lean=15*s*e,angle=.09*s*e,la=-22*s*e,ra=-22*s*e,laugh=.45*e,close=max(blink,.45*e),my=1+.12*math.sin(6*math.pi*t/5)*e)
    elif kind=='drag':p.update(lean=12*s*e,angle=-.08*s*e,sy=1+.02*e,la=-48*e+12*s*e,ra=48*e+12*s*e,mx=1-.48*e,my=1+.1*e,gaze=2*s*e)
    elif kind in ('walk','run'):
        k=math.sin((8 if kind=='walk' else 14)*math.pi*t/5)*e
        p.update(step=(5 if kind=='walk' else 7)*k,lean=6*k,up=4*abs(k),la=27*k,ra=-27*k,angle=.022*k,sy=1-.012*abs(k),my=1-.1*abs(k))
    elif kind=='float':p.update(up=9*(1-math.cos(2*math.pi*t/5))/2,lean=6*s*e,la=-28*e,ra=28*e,close=.5*e,laugh=.5*e)
    elif kind=='stretch':p.update(sy=1+.018*e,sx=1-.035*e,la=-115*e,ra=112*e,close=.92*e,mx=1-.2*e,my=1+.22*e)
    elif kind=='bow':p.update(sy=1-.085*e,angle=.045*e,la=18*e,ra=-18*e,close=.85*e,my=1-.35*e)
    elif kind=='busy':
        k=math.sin(10*math.pi*t/5)*e;p.update(la=-25*e-14*k,ra=18*e-10*k,angle=.03*k,gaze=-1.5*e,my=1-.45*e,mx=1-.2*e)
    elif kind=='celebrate':pass
    elif kind=='sad':p.update(sy=1-.06*e,angle=.1*e,lean=4*e,close=.7*e,mx=1-.48*e,my=1-.65*e,la=7*e,ra=-7*e)
    elif kind=='sleep':p.update(sy=1-.055*e+.008*math.sin(4*math.pi*t/5)*e,angle=(.09+.012*s)*e,lean=6*e,close=e,mx=1-.57*e,my=1+.35*e*math.sin(math.pi*t/5)**2)
    return p

def frame(kind,t):
    if t>=5:t=0.
    p=parameters(kind,t)
    im=Image.new('RGBA',(640,360))
    for i,(arm,angle,pivot) in enumerate(zip(arms,(p['la'],p['ra']),pivots)):
        moved=arm.rotate(angle,resample=Image.Resampling.BICUBIC,center=pivot)
        reach=min(1,abs(angle)/85)*10*(-1 if i==0 else 1)
        im.alpha_composite(moved,(round(reach),0))
    im.alpha_composite(base)
    for i in range(2):
        c=max(p['close'],p['wink'] if i==0 else 0.)
        if c<.65: paste_feature(im,eyes[i],sy=max(.12,1-1.12*c),dx=p['gaze'])
        else: paste_feature(im,closed[i])
    paste_feature(im,mouth,sx=p['mx'],sy=p['my']*(1+.12*p['laugh']))
    a=np.asarray(im,dtype=np.float32);a[:,:,:3]*=a[:,:,3:4]/255
    qx=(X-320)/p['sx']+320-p['lean']*root
    qy=(Y-352+p['up'])/p['sy']+352
    theta=-p['angle']*head;dx=qx-320;dy=qy-220
    qx=320+dx*np.cos(theta)-dy*np.sin(theta);qy=220+dx*np.sin(theta)+dy*np.cos(theta)
    qy-=p['step']*(np.exp(-((qx-271)/28)**2-((qy-339)/16)**2)-np.exp(-((qx-374)/28)**2-((qy-339)/16)**2))
    qx=np.clip(qx,0,638.999);qy=np.clip(qy,0,358.999)
    ix=qx.astype(np.int32);iy=qy.astype(np.int32);fx=(qx-ix)[:,:,None];fy=(qy-iy)[:,:,None]
    b=(a[iy,ix]*(1-fx)+a[iy,ix+1]*fx)*(1-fy)+(a[iy+1,ix]*(1-fx)+a[iy+1,ix+1]*fx)*fy
    b[:,:,:3]=np.divide(b[:,:,:3]*255,b[:,:,3:4],out=np.zeros_like(b[:,:,:3]),where=b[:,:,3:4]>.1)
    output=np.zeros((360,640,4),dtype=np.uint8);output[:,145:495]=np.clip(b,0,255).astype('uint8')
    result=Image.fromarray(output)
    if kind=='celebrate':
        e=envelope(t)
        if e>.01:
            d=ImageDraw.Draw(result)
            for i in range(4):
                cx=163 if i%2==0 else 479;cy=91+(i//2)*91-8*math.sin(t*2+i);r=5+2*math.sin(t*3+i)
                d.polygon([(cx,cy-r),(cx+2,cy-2),(cx+r,cy),(cx+2,cy+2),(cx,cy+r),(cx-2,cy+2),(cx-r,cy),(cx-2,cy-2)],fill=(255,195,74,int(235*e)))
    return result

def encode(kind):
    dest=CLIPS/(kind+'.webm')
    proc=subprocess.Popen([str(FF),'-y','-v','error','-f','rawvideo','-pix_fmt','rgba','-s','640x360','-r','24','-i','-',
       '-c:v','libvpx-vp9','-pix_fmt','yuva420p','-b:v','0','-crf','22','-deadline','realtime','-cpu-used','4','-auto-alt-ref','0','-row-mt','1','-threads','4','-an',str(dest)],stdin=subprocess.PIPE)
    boxes=[]
    for i in range(120):
        im=frame(kind,i*5/119);a=np.asarray(im)[:,:,3];y,x=np.where(a>30);boxes.append([int(x.min()),int(y.min()),int(x.max()),int(y.max())])
        proc.stdin.write(im.tobytes())
        if i==47:im.save(CLIPS/(kind+'.png'))
    proc.stdin.close();assert proc.wait()==0
    b=np.array(boxes);assert b[:,1].min()>0 and b[:,3].max()<358,(kind,b.min(0),b.max(0))
    return {'kind':kind,'frames':120,'bounds':[int(b[:,0].min()),int(b[:,1].min()),int(b[:,2].max()),int(b[:,3].max())],'bytes':dest.stat().st_size}

def samples():
    times=[0,.65,1.4,2.15,2.5,3.45,4.2,5]
    sheet=Image.new('RGB',(1280,760),'#e5ecef')
    for i,t in enumerate(times):
        im=frame('wave',t);bg=Image.new('RGBA',im.size,'#e5ecef');bg.alpha_composite(im)
        sheet.paste(bg.convert('RGB'),((i%2)*640,(i//2)*190))
    # compact chronological strip, keeping readable faces
    sheet=Image.new('RGB',(1280,760),'#e5ecef');d=ImageDraw.Draw(sheet)
    for i,t in enumerate(times):
        im=frame('wave',t).crop((170,0,470,360));bg=Image.new('RGBA',im.size,'#e5ecef');bg.alpha_composite(im)
        sheet.paste(bg.convert('RGB'),((i%4)*320,(i//4)*380+20));d.text(((i%4)*320+10,(i//4)*380+4),str(t)+'s',fill='#233')
    sheet.save(OUT/'wave-storyboard.jpg')

if __name__=='__main__':
    samples()
    if '--samples' in sys.argv:sys.exit()
    kinds=['wave'] if '--wave' in sys.argv else list(LABELS)
    stats=[]
    for kind in kinds:
        r=encode(kind);stats.append(r);print(json.dumps(r),flush=True)
    (OUT/'validation.json').write_text(json.dumps(stats,indent=2),encoding='utf8')
    (OUT/'mapping.json').write_bytes((ROOT/'outputs/xigua-lulu-pet/mapping.json').read_bytes())
    # Keep current live behavioral preferences; update only the animation assets.
    (OUT/'main-config.jsonc').write_bytes((v1.USER/'main-config.jsonc').read_bytes())
    html='''<!doctype html><meta charset="utf-8"><title>西瓜噜 · 生动表情版</title><style>body{margin:32px;background:#14232c;color:#edf6f6;font:16px system-ui}h1{font-size:28px}p{color:#bdd3da}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:18px}article{background:#243b46;border-radius:18px;padding:16px}video{width:100%;background:repeating-conic-gradient(#324e5d 0% 25%,#29434e 0% 50%) 50%/24px 24px;border-radius:10px}.hero{max-width:900px;margin:auto auto 30px}.hero video{width:100%}</style><h1>西瓜噜 · 生动表情版</h1><p>抬手大幅挥动三次 · 笑眼与眨眼 · 嘴形变化 · 头部与身体跟随。全部 19 组动作已更新。</p><article class="hero"><h2>先看新版挥手</h2><video src="clips/wave.webm?v=2" autoplay muted loop playsinline controls></video></article><main>'''
    for k,label in LABELS.items():html+=f'<article><h3>{label}</h3><video src="clips/{k}.webm?v=2" poster="clips/{k}.png" controls muted loop playsinline></video></article>'
    (OUT/'preview.html').write_text(html+'</main>',encoding='utf8')
