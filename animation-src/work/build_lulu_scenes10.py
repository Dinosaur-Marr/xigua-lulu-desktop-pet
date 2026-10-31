"""Whole-character v1.1 footage + independent scene choreography. No limb rig."""
from pathlib import Path
import json,math,subprocess,hashlib,sys
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter
ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT.parent;OUT=ROOT/'outputs/lulu-scene-actions-10'
CLIPS=OUT/'clips';CLIPS.mkdir(parents=True,exist_ok=True)
import os,shutil
FF=os.environ.get('FFMPEG_BINARY') or shutil.which('ffmpeg')
if not FF:raise RuntimeError('Set FFMPEG_BINARY or install FFmpeg on PATH')
W,H,FPS,N=640,360,24,120
COSTUMES=['watermelon','orange','star']
NEW={
 'cloudride':('乘云兜风','idle','踩上绵软小云，随风绕一个小弧线，再稳稳落下。'),
 'bubbletrip':('泡泡旅行','look','被一颗大泡泡轻轻托起，左右好奇张望，泡泡散成小水珠。'),
 'skateboard':('滑板兜一圈','sway','踩着西瓜滑板左右巡游，身体跟随节奏摆动，回到原位。'),
 'mooncradle':('月亮摇篮','shy','乘着月牙摇篮轻轻荡两回，闭眼露出满足的笑。'),
 'springbounce':('弹簧垫蹦高','giggle','弹簧垫蓄力、起跳、落地压缩，两次弹跳后稳稳站住。'),
 'rocketboots':('火箭靴启航','look','脚底小推进器点火，升空短暂停留，减速落地。'),
 'leafboat':('落叶小船','sway','站上弯弯的秋叶船，在小小波纹中悠悠漂过。'),
 'firefly':('追着萤火虫看','look','好奇地左右探看萤火虫，最后萤火虫在头顶聚成一圈。'),
 'musicstep':('节拍小舞台','sway','灯光音符跟随节拍弹起，角色踏着小舞台左右轻摆。'),
 'starwish':('对流星许愿','bow','流星划过时闭眼低头许愿，抬头时两侧绽出小星星。')
}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def smooth(x):x=max(0.,min(1.,x));return x*x*(3-2*x)
def env(t):return smooth((t-.25)/.65)*smooth((4.75-t)/.7)
def pulse(t,c,w):return max(0.,1-abs(t-c)/w)**2
def source_path(kind,costume):
 return SRC/('assets/clips/'+kind+'.webm' if costume=='watermelon' else f'assets/wardrobe/lulu-{costume}-{kind}.webm')
def decode(p):
 r=subprocess.run([str(FF),'-v','error','-c:v','libvpx-vp9','-i',str(p),'-f','rawvideo','-pix_fmt','rgba','-'],capture_output=True,check=True)
 a=np.frombuffer(r.stdout,np.uint8).reshape(-1,H,W,4);assert len(a)==N;return a
def motion(kind,t):
 e=env(t);u=max(0,min(1,(t-.7)/3.6));s=1.;dx=0.;up=0.
 if kind=='cloudride':s=1-.10*e;dx=50*math.sin(2*math.pi*u)*e;up=(20+8*math.sin(math.pi*u))*e
 elif kind=='bubbletrip':s=1-.13*e;dx=34*math.sin(2*math.pi*u)*e;up=(25+8*math.sin(2*math.pi*u))*e
 elif kind=='skateboard':s=1-.035*e;dx=58*math.sin(2*math.pi*u)*e;up=18*e
 elif kind=='mooncradle':s=1-.10*e;dx=34*math.sin(4*math.pi*u)*e;up=(28+7*abs(math.sin(4*math.pi*u)))*e
 elif kind=='springbounce':
  jump=sum(max(0,math.sin(math.pi*(t-a)/.8))**1.35 if a<t<a+.8 else 0 for a in [1.15,2.7]);compression=sum(pulse(t,c,.22) for c in [1.1,1.95,2.65,3.5]);s=1-.12*e;up=(16-6*compression)*e+33*jump
 elif kind=='rocketboots':s=1-.12*e;dx=6*math.sin(8*t)*e;up=36*e
 elif kind=='leafboat':s=1-.07*e;dx=44*math.sin(2*math.pi*u)*e;up=(29+3*math.sin(4*math.pi*u))*e
 elif kind=='firefly':dx=11*math.sin(2*math.pi*u)*e
 elif kind=='musicstep':s=1-.035*e;dx=17*math.sin(6*math.pi*u)*e;up=(12+3*abs(math.sin(6*math.pi*u)))*e
 return e,s,round(dx),up
class Art:
 def __init__(self):self.im=Image.new('RGBA',(W*2,H*2));self.d=ImageDraw.Draw(self.im)
 def ellipse(self,b,fill,outline=None,width=1):self.d.ellipse(tuple(round(v*2) for v in b),fill=fill,outline=outline,width=width*2)
 def poly(self,p,fill):self.d.polygon([(round(x*2),round(y*2)) for x,y in p],fill=fill)
 def line(self,p,fill,width=2):self.d.line([(round(x*2),round(y*2)) for x,y in p],fill=fill,width=width*2,joint='curve')
 def arc(self,b,start,end,fill,width=2):self.d.arc(tuple(round(v*2) for v in b),start,end,fill=fill,width=width*2)
 def star(self,x,y,r,fill):
  self.poly([(x+(r if i%2==0 else r*.43)*math.cos(-math.pi/2+i*math.pi/5),y+(r if i%2==0 else r*.43)*math.sin(-math.pi/2+i*math.pi/5)) for i in range(10)],fill)
 def finish(self):return self.im.resize((W,H),Image.Resampling.LANCZOS)
def scene(kind,t,e,cx,foot,s,top):
 a=Art();alpha=round(255*e)
 if alpha<1:return a.finish()
 if kind=='cloudride':
  y=foot+1
  a.ellipse((cx-105*s,y-4,cx+105*s,y+16),(187,218,248,alpha))
  for off,rad in [(-69,24),(-35,27),(3,30),(42,25),(74,20)]:a.ellipse((cx+(off-rad)*s,y-10,cx+(off+rad)*s,y+13),(248,252,255,alpha))
  for j in range(3):
   x=cx-155-10*math.sin(t*4+j);yy=foot-80-j*38;a.line([(x,yy),(x+26,yy)],(129,202,226,alpha),2)
 elif kind=='bubbletrip':
  cy=(top+foot)/2;rx=143*s;ry=(foot-top)/2+12
  a.ellipse((cx-rx,cy-ry,cx+rx,cy+ry),(158,222,255,round(alpha*.16)),(109,202,244,alpha),3)
  a.arc((cx-rx+6,cy-ry+5,cx+rx-6,cy+ry-5),192,238,(255,255,255,alpha),4)
  for j in range(5):
   x=cx+(-1 if j%2 else 1)*(150+9*math.sin(t*3+j));y=foot-30-j*39;a.ellipse((x-5,y-5,x+5,y+5),(186,231,253,round(alpha*.4)),(97,193,239,alpha),1)
 elif kind=='skateboard':
  y=foot+2
  for dx in [-62,62]:a.ellipse((cx+dx-6,y+3,cx+dx+6,y+15),(50,87,88,alpha));a.ellipse((cx+dx-2,y+7,cx+dx+2,y+11),(184,233,197,alpha))
  a.ellipse((cx-105,y-4,cx+105,y+8),(40,146,99,alpha));a.ellipse((cx-98,y-4,cx+98,y+3),(255,106,108,alpha))
  for dx in [-80,-40,0,40,80]:a.ellipse((cx+dx-2,y-3,cx+dx+2,y),(73,70,55,alpha))
  for j in range(2):a.line([(cx-145-j*15,y-14-j*9),(cx-117-j*15,y-14-j*9)],(114,204,173,alpha),2)
 elif kind=='mooncradle':
  y=foot+2
  upper=[(cx-114,y-42),(cx-88,y-17),(cx-50,y-3),(cx,y),(cx+50,y-3),(cx+88,y-17),(cx+114,y-42)]
  lower=[(cx+92,y+1),(cx+55,y+17),(cx,y+22),(cx-55,y+17),(cx-92,y+1)]
  a.poly(upper+lower,(251,201,79,alpha));a.line(upper,(255,239,157,alpha),3)
  for j in range(4):a.star(cx+(-1 if j%2 else 1)*(134+j*6),100+j*48+4*math.sin(t*3+j),5,(255,210,88,alpha))
 elif kind=='springbounce':
  ground=350;compression=sum(pulse(t,c,.22) for c in [1.1,1.95,2.65,3.5]);h=12-6*compression
  for dx in [-62,62]:a.line([(cx+dx+(-4 if k%2 else 4),ground-h+k*h/6) for k in range(7)],(111,129,183,alpha),2)
  a.ellipse((cx-98,ground-h-4,cx+98,ground-h+3),(162,122,230,alpha),(214,192,255,alpha),2)
  a.line([(cx-84,ground+1),(cx+84,ground+1)],(111,93,165,alpha),3)
  if compression>.25:
   for dx in [-119,119]:a.star(cx+dx,ground-10,6*compression,(255,184,89,alpha))
 elif kind=='rocketboots':
  # Entire feet remain intact. Jets appear underneath, with no boot masking.
  for dx in [-54*s,54*s]:
   x=cx+dx;y=foot+1;length=(14+5*math.sin(32*t+dx))*e
   a.poly([(x-12,y),(x+12,y),(x+7,y+length*.65),(x,y+length),(x-7,y+length*.65)],(255,148,58,alpha))
   a.poly([(x-6,y),(x+6,y),(x,y+length*.7)],(255,235,133,alpha))
  for j in range(4):
   y=foot-20-j*58;x=cx+(-1 if j%2 else 1)*135;a.line([(x,y),(x,y+15)],(125,209,240,alpha),2)
 elif kind=='leafboat':
  y=foot+1
  outline=[(cx-116,y-14),(cx-68,y-2),(cx,y),(cx+68,y-2),(cx+116,y-14),(cx+78,y+12),(cx+25,y+18),(cx-36,y+15),(cx-87,y+5)]
  a.poly(outline,(219,133,54,alpha));a.line([(cx-104,y-9),(cx,y+7),(cx+103,y-9)],(255,205,99,alpha),2)
  for j in [-2,-1,1,2]:a.line([(cx+j*33,y+4),(cx+j*39,y+10)],(247,183,75,alpha),1)
  for j in range(2):a.arc((cx-140-j*12,y+9+j*5,cx+140+j*12,y+19+j*5),8,172,(91,193,213,round(alpha*.8)),2)
 elif kind=='firefly':
  for j in range(3):
   phase=t*1.8+j*2.1;x=cx+math.cos(phase)*(145+8*j);y=145+math.sin(phase)*72
   a.ellipse((x-9,y-9,x+9,y+9),(239,233,111,round(alpha*.18)))
   a.ellipse((x-3,y-3,x+3,y+3),(255,232,114,alpha))
   a.ellipse((x-8,y-5,x-1,y-1),(165,221,218,alpha));a.ellipse((x+1,y-5,x+8,y-1),(165,221,218,alpha))
 elif kind=='musicstep':
  y=foot+3;a.ellipse((cx-109,y-3,cx+109,y+8),(126,112,205,alpha))
  for j in range(6):
   x=cx+(-1 if j<3 else 1)*(128+(j%3)*18);y=160+(j%3)*40-8*math.sin(t*8+j)
   color=[(244,131,167,alpha),(126,201,229,alpha),(245,197,92,alpha)][j%3]
   a.ellipse((x-5,y-3,x+5,y+3),color);a.line([(x+4,y),(x+4,y-19),(x+11,y-16)],color,3)
 elif kind=='starwish':
  for j in range(2):
   u=(t-.55-j*.55)/1.3
   if 0<u<1:
    x=120+370*u;y=65+55*u;a.line([(x-25,y-8),(x,y)],(255,219,144,alpha),3);a.star(x,y,7,(255,199,79,alpha))
  for j in range(6):
   k=pulse(t,3.4+(j%3)*.18,.8)
   if k:a.star(cx+(-1 if j%2 else 1)*(140+(j%3)*10),115+(j%3)*65,8*k,(255,204,91,alpha))
 props=a.finish()
 if e<.999:
  # Props grow from the support plane; they never emerge below the canvas.
  scaled=props.convert('RGBa').resize((W,max(1,round(H*e))),Image.Resampling.LANCZOS).convert('RGBA')
  props=Image.new('RGBA',(W,H));props.alpha_composite(scaled,(0,round(foot*(1-e))))
 return props
def frame(kind,i,frames):
 t=i*5/(N-1);e,s,dx,up=motion(kind,t)
 src=Image.fromarray(frames[0 if i==N-1 else i])
 if s!=1:
  sprite=src.convert('RGBa').resize((round(W*s),round(H*s)),Image.Resampling.LANCZOS).convert('RGBA')
 else:sprite=src
 arr=np.asarray(sprite);yy,xx=np.where(arr[:,:,3]>80)
 # Scaling is uniform over the complete character; feet and shorts share one image.
 x=round((W-sprite.width)/2)+dx;y=round(351-up-int(yy.max()))
 character=Image.new('RGBA',(W,H));character.alpha_composite(sprite,(x,y))
 top=int(yy.min())+y;foot=int(yy.max())+y;cx=W/2+dx
 props=scene(kind,t,e,cx,foot,s,top)
 result=props.copy();result.alpha_composite(character)
 source=np.asarray(character);out=np.asarray(result)
 opaque=source[:,:,3]==255
 assert np.array_equal(source[opaque],out[opaque]),(kind,i,'character occluded')
 # Topology of the body is untouched; no per-limb transforms, masks or fades exist.
 return result,character,{'x':x,'y':y,'scale':s,'top':top,'foot':foot,'dx':dx}
def encode(kind):
 results=[];frame_stats=[]
 for costume in COSTUMES:
  src=source_path(NEW[kind][1],costume);frames=decode(src);dest=CLIPS/f'{costume}-{kind}.webm'
  proc=subprocess.Popen([str(FF),'-v','error','-y','-f','rawvideo','-pix_fmt','rgba','-s','640x360','-r','24','-i','-','-an','-c:v','libvpx-vp9','-pix_fmt','yuva420p','-lossless','1','-deadline','realtime','-cpu-used','5','-threads','1','-auto-alt-ref','0',str(dest)],stdin=subprocess.PIPE)
  sampled=[]
  try:
   for i in range(N):
    im,character,stat=frame(kind,i,frames);ar=np.asarray(im);yy,xx=np.where(ar[:,:,3]>24)
    assert xx.min()>4 and xx.max()<W-5 and yy.min()>2 and yy.max()<H-2,(kind,costume,i,'edge',xx.min(),xx.max(),yy.min(),yy.max())
    proc.stdin.write(im.tobytes())
    if i in [0,12,24,36,48,60,72,84,96,108,116,119]:
     im.save(CLIPS/f'{costume}-{kind}-{i:03}.png');sampled.append(stat)
   proc.stdin.close();assert proc.wait()==0
  except BaseException:proc.kill();raise
  decoded=decode(dest)
  assert np.array_equal(decoded[0,:,:,3],decoded[-1,:,:,3]),(kind,'endpoint alpha')
  endpoint=float(np.abs(decoded[0].astype(float)-decoded[-1].astype(float)).mean());assert endpoint<1.0
  edge=int(max(decoded[:,:2,:,3].max(),decoded[:,-2:,:,3].max(),decoded[:,:,:3,3].max(),decoded[:,:,-3:,3].max()));assert edge<8
  # Inspect alpha after actual encoding, rather than only the pre-encode render.
  for i in range(N):
   im,character,_=frame(kind,i,frames);mask=np.asarray(character)[:,:,3]
   interior=np.asarray(Image.fromarray(mask).filter(ImageFilter.MinFilter(5)))==255
   assert np.all(decoded[i,:,:,3][interior]>=254),(kind,costume,i,'body transparency')
  results.append(dict(id=kind,costume=costume,file=dest.name,frames=N,sha256=sha(dest),source=str(src.relative_to(SRC)),sourceHash=sha(src),edgeAlpha=edge,endpointError=endpoint,opaqueBodyPreserved=True))
  print(f'{kind} {costume}: 120 frames, opaque body and endpoints verified',flush=True)
 return results
def preview():
 font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',19)
 for k,(name,_,desc) in NEW.items():
  sheet=Image.new('RGB',(1280,1120),'#e7ece9');d=ImageDraw.Draw(sheet);d.text((18,8),name+'  /  三款裤子 · 12 个时刻',font=font,fill='#244838')
  for j,i in enumerate([0,12,24,36,48,60,72,84,96,108,116,119]):
   c=COSTUMES[(j//4)%3];im=Image.open(CLIPS/f'{c}-{k}-{i:03}.png');bg=Image.new('RGBA',im.size,'#faf7ee' if j%2==0 else '#202c3a');bg.alpha_composite(im)
   x=(j%4)*320;y=40+(j//4)*360;im=bg.crop((90,0,550,360)).resize((320,251));sheet.paste(im.convert('RGB'),(x,y));d.text((x+8,y+259),f'{i/24:.2f}s  {c}',font=font,fill='#244838')
  sheet.save(OUT/(k+'-review.jpg'),quality=94)
 actions=[{'id':k,'name':v[0],'description':v[2],'sourceAction':v[1]} for k,v in NEW.items()]
 (OUT/'actions.json').write_text(json.dumps(actions,ensure_ascii=False,indent=2),encoding='utf8')
 cards=''.join(f'<article><h2>{v[0]}</h2><video controls loop preload="metadata" src="clips/watermelon-{k}.webm"></video><p>{v[2]}</p></article>' for k,v in NEW.items())
 html='''<!doctype html><meta charset="utf-8"><title>西瓜噜噜 · 10个场景动作</title><style>body{font:17px "Microsoft YaHei",sans-serif;background:#eef3ee;color:#234638;margin:30px}h1{margin-bottom:8px}nav{margin:24px 0}button{padding:10px 18px;margin-right:10px}main{display:grid;grid-template-columns:repeat(2,minmax(300px,1fr));gap:22px}article{background:white;border-radius:20px;padding:20px}video{width:100%;background:linear-gradient(135deg,#f3f7e9,#e9f2f3);border-radius:14px}body.dark video{background:#233042}h2{font-size:21px}p{line-height:1.7}</style><h1>西瓜噜噜 · 10个场景动作</h1><p>沿用 v1.1 完整角色表演，新增场景与道具编排。角色不重新拆分肢体。</p><nav><button onclick="costume('watermelon')">西瓜裤</button><button onclick="costume('orange')">橙色裤</button><button onclick="costume('star')">星星裤</button><button onclick="document.body.classList.toggle('dark')">深浅背景</button></nav><main>'''+cards+'''</main><script>function costume(c){document.querySelectorAll('video').forEach(v=>{v.src=v.getAttribute('src').replace(/(watermelon|orange|star)-/,c+'-')})}</script>'''
 (OUT/'preview.html').write_text(html,encoding='utf8')
if __name__=='__main__':
 kinds=sys.argv[1:] or list(NEW);records=[]
 if (OUT/'validation.json').exists():records=json.loads((OUT/'validation.json').read_text())
 for k in kinds:
  if k=='--preview':continue
  records=[r for r in records if r['id']!=k]+encode(k)
  (OUT/'validation.json').write_text(json.dumps(records,indent=2),encoding='utf8')
 if len(records)==30:preview()
