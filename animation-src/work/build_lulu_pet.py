"""Build a reversible, transparent dsh-pet animation pack from the approved PNG.
No installed package files are changed. --deploy is handled separately.
"""
from pathlib import Path
import json, math, subprocess, hashlib, shutil
from collections import Counter
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'outputs' / 'xigua-lulu-pet'
OUT.mkdir(parents=True, exist_ok=True)
CLIPS = OUT / 'clips'
CLIPS.mkdir(exist_ok=True)
USER = ROOT / 'config'
import os
FF = os.environ.get('FFMPEG_BINARY', 'ffmpeg')
W,H,FPS = 640,360,24
raw = Image.open(ROOT/'outputs/watermelon-lulu-no-helmet.png').convert('RGBA')
a = np.asarray(raw)[:,:,3]
y,x = np.where(a>40)
crop = (int(x.min()),int(y.min()),int(x.max()+1),int(y.max()+1))
char = raw.crop(crop)
scale = 330 / char.height
char = char.resize((round(char.width*scale),330),Image.Resampling.LANCZOS)
base = Image.new('RGBA',(W,H))
base.alpha_composite(char,((W-char.width)//2,22))
base.save(OUT/'character.png')
source=np.asarray(base,dtype=np.float32)
source[:,:,:3] *= source[:,:,3:4]/255
Y,X=np.mgrid[0:H,170:471].astype(np.float32)
head=np.clip((252-Y)/46,0,1); head=head*head*(3-2*head)
root=np.clip((352-Y)/190,0,1)

def smooth(t):
    t=max(0,min(1,t)); return t*t*(3-2*t)
def env(t): return smooth(t/.6)*smooth((5-t)/.65)
def bump(t,c,w): return max(0,1-abs(t-c)/w)**2
def gaussian(x,y,cx,cy,rx,ry): return np.exp(-((x-cx)/rx)**2-((y-cy)/ry)**2)

LABELS={
 'idle':'轻轻呼吸','look':'左右张望','sway':'哼歌摇摆','wave':'短手挥三下',
 'jump':'开心双跳','shy':'害羞缩一缩','angry':'跺脚小脾气','giggle':'挠痒笑抖',
 'drag':'悬空轻晃','walk':'左右小碎步','run':'元气快步','float':'轻轻浮动',
 'stretch':'舒展身体','bow':'点头致意','think':'歪头思考','busy':'忙碌点按',
 'celebrate':'双跳星星庆祝','sad':'垂头叹气','sleep':'困倦打盹',
}

def frame(kind,t):
    if t >= 5: t=0.0
    e=env(t); s=math.sin(2*math.pi*t/5)
    sx,sy,up,lean,angle=1.,1.,0.,0.,0.
    armx,army=0.,0.; step=0.
    if kind=='idle': sx=1+.004*(1-math.cos(2*math.pi*t/5)); sy=1+.006*(1-math.cos(2*math.pi*t/5))
    if kind in ('look','think'):
        angle=(.065 if kind=='look' else .105)*math.sin(2*math.pi*t/5)*e
        lean=3*math.sin(2*math.pi*t/5)*e
    if kind=='sway': lean=8*s*e; angle=.025*s*e
    if kind=='wave':
        lift=smooth((t-.4)/.7)*smooth((4.65-t)/.65)
        armx=-16*lift-5*math.sin(6*math.pi*max(0,min(1,(t-1.1)/2.9)))*lift
        army=-19*lift
    if kind in ('jump','celebrate'):
        for start in (.6,2.55):
            u=t-start
            if 0<=u<.3: sy-=.055*math.sin(math.pi*u/.6); sx+=.035*math.sin(math.pi*u/.6)
            elif .3<=u<1.05:
                phase=(u-.3)/.75; up=15*math.sin(math.pi*phase); army=-9*math.sin(math.pi*phase); armx=-5*math.sin(math.pi*phase)
            elif 1.05<=u<1.4: sy-=.045*math.sin(math.pi*(u-1.05)/.35); sx+=.025*math.sin(math.pi*(u-1.05)/.35)
    if kind=='shy': sy-=.025*e; sx+=.012*e; angle=.055*e; army=-4*e
    if kind=='angry': lean=2*math.sin(12*math.pi*t/5)*e; sy-=.018*e; step=4*math.sin(8*math.pi*t/5)*e
    if kind=='giggle': sx+=.018*math.sin(16*math.pi*t/5)*e; sy-=.015*math.sin(16*math.pi*t/5)*e; angle=.02*math.sin(12*math.pi*t/5)*e
    if kind=='drag': lean=7*s*e; angle=-.035*s*e; sy+=.012*e; army=-5*e
    if kind in ('walk','run'):
        freq=4 if kind=='walk' else 7
        phase=2*math.pi*freq*t/5
        step=(4 if kind=='walk' else 6)*math.sin(phase)*e
        lean=(3 if kind=='walk' else 5)*math.sin(phase)*e
        up=2*(1-math.cos(phase*2))*e; armx=2*math.sin(phase)*e
    if kind=='float': up=7*(1-math.cos(2*math.pi*t/5))/2; lean=3*s*e
    if kind=='stretch': sy+=.018*e; sx-=.014*e; armx=-8*e; army=-10*e
    if kind=='bow': sy-=.035*math.sin(math.pi*t/5)**2; angle=.025*e
    if kind=='busy': army=-8*(.5+.5*math.sin(12*math.pi*t/5))*e; angle=.015*math.sin(6*math.pi*t/5)*e
    if kind in ('sad','sleep'): sy-=(.025 if kind=='sad' else .018)*e; angle=.05*e; lean=2*e
    # Inverse smooth deformation, rooted at the feet. Same source scale for every action.
    qx=(X-320)/sx+320-lean*root
    qy=(Y-352+up)/sy+352
    theta=-angle*head
    dx=qx-320; dy=qy-220
    qx=320+dx*np.cos(theta)-dy*np.sin(theta)
    qy=220+dx*np.sin(theta)+dy*np.cos(theta)
    # Local hand motion falls off at shoulders; three fixed-point steps invert the smooth displacement.
    ux=qx.copy(); uy=qy.copy()
    for _ in range(3):
        left=gaussian(qx,qy,231,258,24,30)
        right=gaussian(qx,qy,411,258,22,29)
        qx=ux-armx*left+(armx*.3 if kind!='wave' else 0)*right
        qy=uy-army*left-(army*.7 if kind not in ('wave','busy') else 0)*right
    qy-=step*(gaussian(qx,qy,271,339,28,16)-gaussian(qx,qy,374,339,28,16))
    qx=np.clip(qx,0,W-1.001); qy=np.clip(qy,0,H-1.001)
    ix=qx.astype(np.int32); iy=qy.astype(np.int32)
    fx=(qx-ix)[:,:,None]; fy=(qy-iy)[:,:,None]
    p=(source[iy,ix]*(1-fx)+source[iy,ix+1]*fx)*(1-fy)+(source[iy+1,ix]*(1-fx)+source[iy+1,ix+1]*fx)*fy
    alpha=p[:,:,3:4]
    p[:,:,:3]=np.divide(p[:,:,:3]*255,alpha,out=np.zeros_like(p[:,:,:3]),where=alpha>0.1)
    out=np.zeros((H,W,4),np.uint8); out[:,170:471]=np.clip(p,0,255).astype(np.uint8)
    im=Image.fromarray(out)
    # Small drawn reaction accents stay outside the body and do not replace the approved face.
    draw=ImageDraw.Draw(im)
    opacity=int(235*e)
    if opacity and kind in ('think','sleep'):
        for i in range(3):
            cy=126-i*17-3*math.sin(t*2+i); cx=454+i*12
            r=3+i
            draw.ellipse((cx-r,cy-r,cx+r,cy+r),fill=(190,222,234,opacity),outline=(91,137,161,opacity))
    if opacity and kind in ('celebrate','shy'):
        for i in range(4):
            cx=191 if i%2==0 else 454; cy=95+(i//2)*94-8*math.sin(t*2+i)
            r=5+2*math.sin(t*3+i)
            draw.polygon([(cx,cy-r),(cx+2,cy-2),(cx+r,cy),(cx+2,cy+2),(cx,cy+r),(cx-2,cy+2),(cx-r,cy),(cx-2,cy-2)],fill=(255,191,83,opacity))
    if opacity and kind=='sad':
        cx=437; cy=119+5*e
        draw.polygon([(cx,cy-8),(cx-4,cy+3),(cx+4,cy+3)],fill=(112,204,244,opacity))
        draw.ellipse((cx-4,cy,cx+4,cy+7),fill=(112,204,244,opacity))
    return im

def encode(kind):
    path=CLIPS/(kind+'.webm')
    cmd=[str(FF),'-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgba','-s','640x360','-r',str(FPS),'-i','-',
         '-c:v','libvpx-vp9','-pix_fmt','yuva420p','-b:v','0','-crf','24','-deadline','realtime','-cpu-used','4',
         '-auto-alt-ref','0','-row-mt','1','-threads','4','-an',str(path)]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    boxes=[]
    for i in range(120):
        im=frame(kind,5*i/119)
        al=np.asarray(im)[:,:,3]; yy,xx=np.where(al>30)
        boxes.append([int(xx.min()),int(yy.min()),int(xx.max()),int(yy.max())])
        proc.stdin.write(im.tobytes())
        if i==47: im.save(CLIPS/(kind+'.png'))
    proc.stdin.close()
    if proc.wait()!=0: raise RuntimeError(kind)
    box=np.asarray(boxes)
    assert box[:,0].min()>0 and box[:,1].min()>0 and box[:,2].max()<639 and box[:,3].max()<359, (kind,box.min(0),box.max(0))
    assert np.array_equal(np.asarray(frame(kind,0)),np.asarray(frame(kind,5))),kind+' endpoints'
    return {'kind':kind,'label':LABELS[kind],'frames':120,'fps':24,'size':[640,360],
            'bounds':[box[:,0].min().item(),box[:,1].min().item(),box[:,2].max().item(),box[:,3].max().item()],
            'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}

def pick(name):
    exact={'待机呼吸休闲':'idle','东张西望':'look','被鼠标拖拽悬空反馈':'drag',
      '点击回应-开心跃动':'jump','点击回应-害羞惊讶':'shy','点击回应-傲娇生气':'angry',
      '点击回应-挠痒咯咯笑':'giggle','点击回应-元气挥手':'wave','螃蟹走路':'walk',
      '原地左转奔跑':'run','原地漂浮踏步':'float','工作状态-思考冒泡':'think',
      '工作状态-忙碌点按':'busy','工作状态-清点归档':'bow','工作状态-原地踱步张望':'look',
      '工作状态-雀跃庆祝':'celebrate','工作状态-垂头叹气冒汗':'sad'}
    if name in exact:return exact[name]
    for terms,kind in [(['睡','哈欠','小憩'],'sleep'),(['伸懒腰'],'stretch'),(['跳','被吓'],'jump'),
       (['舞','哼歌','摇摆'],'sway'),(['气急','袋空','分文'],'angry'),(['思考','皱眉','照镜'],'think'),
       (['写','记录','敲击','魔方','五子','归档'],'busy'),(['满溢','叮当','烟花','礼物','红包'],'celebrate'),
       (['屈膝','下蹲','压缩'],'bow'),(['漂浮','秋千','风筝','泡泡','幽灵','孔明'],'float')]:
        if any(t in name for t in terms): return kind
    return 'sway' if '吃' in name else 'look'

if __name__=='__main__':
    stats=[]
    for kind in LABELS:
        result=encode(kind); stats.append(result); print(json.dumps(result,ensure_ascii=False),flush=True)
    names=sorted(p.stem for p in (USER/'main-animation/webm').glob('*.webm'))
    mapping={name:pick(name) for name in names}
    (OUT/'mapping.json').write_text(json.dumps(mapping,ensure_ascii=False,indent=2),encoding='utf-8')
    (OUT/'validation.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2),encoding='utf-8')
    cfg=json.loads((USER/'main-config.jsonc').read_text(encoding='utf-8-sig'))
    cfg['pets'][0]['name']='西瓜噜'
    cfg['whisperPrompt']='你是主人桌面上的西瓜噜，圆滚滚的黄色小伙伴，头顶小橙子，穿西瓜短裤。偶尔碎碎念一句，20字以内，活泼温暖、带点贪吃的小俏皮。说话自然，不解释身份，不提自己是AI。'
    cfg['animations']['categories']=[{'id':'西瓜噜日常','weight':20,'actions':['悠闲哼歌','超大伸懒腰','原地小憩沉眠','原地重力下蹲压缩','写代码','轻快摇摆舞','照镜子','女仆屈膝礼仪']}]
    (OUT/'main-config.jsonc').write_text(json.dumps(cfg,ensure_ascii=False,indent=2),encoding='utf-8')
    html='''<!doctype html><meta charset="utf-8"><title>西瓜噜 · 动作预览</title><style>body{background:#14232c;color:#ebf4f5;font:16px system-ui;margin:30px}h1{font-size:26px}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:18px}article{background:#223742;border-radius:16px;padding:16px}video{width:100%;background:repeating-conic-gradient(#334852 0% 25%,#2b404b 0% 50%) 50%/24px 24px;border-radius:10px}p{color:#bfd3da}button{background:#ffd25b;border:0;padding:9px 16px;border-radius:10px;cursor:pointer}</style><h1>西瓜噜 · 19 组动作</h1><p>全透明素材 · 统一角色比例 · 点击卡片播放 / 暂停。点击回应五种动作各不相同。</p><main>'''
    for kind,label in LABELS.items():
        html+=f'<article><h3>{label}</h3><video src="clips/{kind}.webm" poster="clips/{kind}.png" muted loop playsinline controls></video></article>'
    html+='</main>'
    (OUT/'preview.html').write_text(html,encoding='utf-8')
    print('DONE',len(mapping),'aliases',len(stats),'unique clips',flush=True)
