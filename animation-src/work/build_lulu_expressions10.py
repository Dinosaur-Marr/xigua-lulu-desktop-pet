"""New facial acting and continuous full-body motion from one neutral pose.
No previously animated frames, separate arm layers, or arm opacity controls.
"""
from pathlib import Path
import sys,json,math
import numpy as np
from PIL import Image,ImageDraw,ImageFilter
import build_lulu_stories10 as story
b=story.b;ROOT=b.ROOT;OUT=ROOT/'outputs/lulu-expression-actions-10';CLIPS=OUT/'clips';CLIPS.mkdir(parents=True,exist_ok=True)
NEW={k:(v[0],'idle',v[2]) for k,v in story.NEW.items()}
W,H=640,360;Y,X=np.mgrid[:H,:W].astype(np.float32)
def smooth(v):v=np.clip(v,0,1);return v*v*(3-2*v)
raw=Image.open(ROOT/'outputs/watermelon-lulu-no-helmet.png').convert('RGBA');yy,xx=np.where(np.asarray(raw)[:,:,3]>40)
crop=(int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1));sz=(round((crop[2]-crop[0])*330/(crop[3]-crop[1])),330)
clean=Image.open(ROOT/'work/lulu-v2-rig/clean.png').convert('RGBA').resize(raw.size).crop(crop).resize(sz,Image.Resampling.LANCZOS)
CLEAN=Image.new('RGBA',(W,H));CLEAN.alpha_composite(clean,((W-sz[0])//2,22));CLEAN=np.asarray(CLEAN.transpose(Image.Transpose.FLIP_LEFT_RIGHT))
FACE_MASK=np.zeros((H,W),np.float32)
for cx,cy,rx,ry in [(257,105,25,23),(331,103,29,23),(296,184,52,32)]:
 r=np.sqrt(((X-cx)/rx)**2+((Y-cy)/ry)**2);FACE_MASK=np.maximum(FACE_MASK,1-smooth((r-.75)/.25))
FACE_MASK[(Y>216)|(Y<73)]=0
NEUTRAL={};FEATURES={}
def features(frame):
 eyes=[]
 for cx,cy in [(257,105),(331,103)]:
  p=np.asarray(Image.fromarray(frame).crop((cx-27,cy-23,cx+27,cy+23))).copy();r,g,bl=[p[:,:,j].astype(float) for j in range(3)]
  yy,xx=np.mgrid[:46,:54];mask=((r<174)|((bl>135)&(g>150)))&((((xx-27)/23)**2+((yy-23)/19)**2)<1)
  alpha=Image.fromarray((mask*255).astype('uint8')).filter(ImageFilter.GaussianBlur(.35));p[:,:,3]=np.asarray(alpha)
  iris=((r<145)&(g<155))&mask;imask=Image.fromarray((iris*255).astype('uint8')).filter(ImageFilter.GaussianBlur(.35));iris_im=p.copy();iris_im[:,:,3]=np.asarray(imask)
  eye=p.copy();weight=np.asarray(imask)/255.;white=np.stack([234-yy*.18,241-yy*.16,239-yy*.16],axis=2)
  eye[:,:,:3]=np.clip(eye[:,:,:3]*(1-weight[:,:,None])+white*weight[:,:,None],0,255)
  eyes.append((Image.fromarray(eye),Image.fromarray(iris_im),(cx,cy)))
 p=np.asarray(Image.fromarray(frame).crop((243,151,350,217))).copy();r,g,bl=[p[:,:,j].astype(float) for j in range(3)];yy,xx=np.mgrid[:66,:107]
 mask=(((r<213)&(g<132)&(bl<160))|((bl>155)&(g>160)&(r>170)))&((((xx-53)/49)**2+((yy-33)/28)**2)<1)
 p[:,:,3]=np.asarray(Image.fromarray((mask*255).astype('uint8')).filter(ImageFilter.GaussianBlur(.4)))
 return eyes,Image.fromarray(p)
def params(kind,t):
 e=b.env(t);P=b.pulse;E=story.E
 p=dict(gx=0.,gy=0.,left=0.,right=0.,wide=1.,mx=1.,my=1.,smirk=0.,closed=0.,teeth=0.,stars=0.,brow=0.,browtilt=0.,nod=0.,tilt=0.,lean=0.,dip=0.,squash=0.,cheek=0.)
 blink=max(P(t,4.38,.15),P(t,.43,.12))
 p['left']=p['right']=blink
 if kind=='rainbowrain':
  wet=E(t,.55,.9,1.9,2.4);wow=E(t,2.4,2.8,3.6,4.45)
  p.update(gx=(-3*wet+3.7*wow),gy=-2*wow,left=max(blink,.65*wet),right=max(blink,.42*wet),wide=1+.10*wow,mx=1-.38*wet+.08*wow,my=1-.68*wet+.18*wow,brow=3*wow,tilt=-.045*wet+.07*wow,lean=-4*wet+5*wow,nod=-3*wow,cheek=2*wow)
 elif kind=='snowchill':
  chill=E(t,.55,1.1,2.8,3.65);wink=P(t,3.7,.32)
  p.update(gx=-2.8*chill,left=max(blink,.88*chill),right=max(blink,.58*chill,wink),teeth=chill,my=1-.82*chill,mx=1-.25*chill,browtilt=.25*chill,tilt=.035*math.sin(t*17)*chill,lean=2*math.sin(t*17)*chill,dip=7*chill,squash=.025*chill,cheek=3*chill)
 elif kind=='alarmwake':
  sleepy=E(t,.3,.8,2.05,2.25);shock=E(t,2.13,2.32,2.85,3.45);smile=E(t,3.2,3.6,4.2,4.7)
  p.update(left=max(blink,.92*sleepy,P(t,3.2,.12)),right=max(blink,.70*sleepy,P(t,3.35,.12)),gx=-1*sleepy-3.5*shock,gy=2*sleepy,wide=1+.14*shock,mx=1-.56*sleepy-.4*shock+.12*smile,my=1-.75*sleepy+.2*shock,closed=.65*sleepy,smirk=7*smile,brow=4*shock,nod=7*sleepy-5*shock,tilt=.08*sleepy-.065*shock,lean=-6*shock,dip=9*sleepy,squash=.03*sleepy)
 elif kind=='chickhatch':
  peek=E(t,.25,.55,.78,1.1);shock=E(t,.82,1.1,1.8,2.35);soft=E(t,2.3,2.8,4.1,4.65)
  p.update(gx=-4*e,gy=2.8*e,wide=1+.13*shock,left=max(blink,.18*peek,.35*soft),right=max(blink,.35*peek,.12*soft),mx=1-.5*shock+.08*soft,my=1+.18*shock-.55*soft,brow=4*shock,browtilt=.2*peek,tilt=-.075*peek+.06*shock-.045*soft,lean=-5*peek+7*shock,nod=3*soft,dip=3*soft,cheek=2*soft)
 elif kind=='popcornparty':
  bursts=sum(P(t,v,.19) for v in [.95,1.5,2.05,2.6,3.15]);hold=E(t,.35,.7,1.7,2.25);laugh=E(t,2,2.45,3.65,4.5)
  p.update(gx=-3.5*e,gy=2*e,left=max(blink,.92*laugh),right=max(blink,.8*laugh),closed=hold,mx=1-.4*hold+.10*laugh,my=1-.7*hold+.28*bursts*laugh,cheek=5*hold,tilt=.04*math.sin(t*13)*laugh,lean=3*math.sin(t*13)*laugh,dip=4*bursts,squash=.018*bursts,browtilt=.2*hold)
 elif kind=='papercrane':
  track=E(t,.45,.8,2.8,3.3);read=E(t,2.65,3.1,3.8,4.45);wink=P(t,4.05,.25)
  p.update(gx=4*math.sin((t-2.35)*1.05)*track+3*read,gy=-2.7*track+2.3*read,left=max(blink,.16*read),right=max(blink,wink),mx=1-.35*track+.05*read,my=1-.58*track-.35*read,smirk=8*read,brow=1.5*track,tilt=.065*math.sin((t-2.35)*1.05)*track+.06*read,nod=-3*track+3*read,lean=4*math.sin((t-2.35)*1.05)*track)
 elif kind=='flowerbow':
  inhale=E(t,.6,1.25,2.2,2.8);joy=E(t,2.5,3,4,4.7)
  p.update(gx=-2*inhale,left=max(blink,inhale,.65*joy),right=max(blink,inhale,.65*joy),mx=1-.48*inhale+.15*joy,my=1-.85*inhale-.3*joy,closed=.7*inhale,cheek=3*inhale,brow=1.8*joy,nod=7*inhale-2*joy,tilt=-.045*inhale+.055*joy,dip=8*inhale,squash=.03*inhale,lean=-3*inhale)
 elif kind=='thundercloud':
  nervous=E(t,.4,.75,1.3,1.6);shock=E(t,1.4,1.53,1.9,2.3);recover=E(t,2.8,3.3,4,4.7)
  p.update(gx=-4*e,gy=-2.5*nervous,wide=1+.18*shock,left=max(blink,.4*nervous,.90*P(t,2.4,.25)),right=max(blink,.1*nervous,.90*P(t,2.4,.25)),mx=1-.48*shock-.25*nervous,my=1-.6*nervous+.22*shock-.45*recover,smirk=7*recover,brow=5*shock,browtilt=.35*nervous,tilt=-.05*nervous+.075*shock,lean=9*shock,dip=4*recover,nod=-5*shock+4*recover)
 elif kind=='minigarden':
  wonder=E(t,.8,1.5,3.5,4.5);look=math.sin((t-1.2)*2)*wonder
  p.update(gx=4.2*look,gy=-3.2*wonder,left=max(blink,.12*wonder),right=max(blink,.38*wonder),mx=1-.5*wonder,my=1-.25*wonder,brow=1.5*wonder,browtilt=.4*look,tilt=.07*look,lean=4*look,nod=-4*wonder)
 elif kind=='treasurechest':
  curious=E(t,.3,.7,1.05,1.45);delight=E(t,1.15,1.55,3.1,3.7);smile=E(t,3.2,3.6,4.1,4.7)
  p.update(gx=4*e,gy=2.7*curious,wide=1+.10*delight,left=max(blink,.15*curious,.75*smile),right=max(blink,.35*curious,.75*smile),mx=1-.35*curious+.15*delight,my=1-.6*curious+.2*delight,stars=delight,brow=3*delight,cheek=2*delight,tilt=.07*curious-.04*delight,lean=5*curious,nod=3*curious-3*delight,dip=3*math.sin(t*10)**2*delight)
 return p
def place(canvas,im,cx,cy,sx=1,sy=1,opacity=1,angle=0):
 if opacity<=0:return
 im=im.convert('RGBa').resize((max(1,round(im.width*sx)),max(1,round(im.height*sy))),Image.Resampling.LANCZOS).convert('RGBA')
 if angle:im=im.rotate(angle,resample=Image.Resampling.BICUBIC,expand=True)
 if opacity<1:im.putalpha(im.getchannel('A').point(lambda q:round(q*opacity)))
 canvas.alpha_composite(im,(round(cx-im.width/2),round(cy-im.height/2)))
def face(neutral,p,parts):
 out=neutral.copy();w=FACE_MASK[:,:,None];out[:,:,:3]=np.clip(out[:,:,:3]*(1-w)+CLEAN[:,:,:3]*w,0,255)
 im=Image.fromarray(out);eyes,mouth=parts
 for idx,(white,iris,(cx,cy)) in enumerate(eyes):
  eye=white.copy();moved=Image.new('RGBA',eye.size);moved.alpha_composite(iris,(round(p['gx']),round(p['gy'])));ar=np.asarray(moved).copy();ar[:,:,3]=np.minimum(ar[:,:,3],np.asarray(white)[:,:,3]);eye.alpha_composite(Image.fromarray(ar))
  if p['stars']>.01:
   star=Image.new('RGBA',eye.size);d=ImageDraw.Draw(star);weights=np.asarray(iris)[:,:,3].astype(float);iy,ix=np.mgrid[:weights.shape[0],:weights.shape[1]];px=float((ix*weights).sum()/weights.sum())+p['gx'];py=float((iy*weights).sum()/weights.sum())+p['gy'];r=7
   d.polygon([(px+(r if j%2==0 else r*.43)*math.cos(-math.pi/2+j*math.pi/5),py+(r if j%2==0 else r*.43)*math.sin(-math.pi/2+j*math.pi/5)) for j in range(10)],fill=(255,217,104,round(255*p['stars'])))
   star_pixels=np.asarray(star).copy();star_pixels[:,:,3]=np.minimum(star_pixels[:,:,3],ar[:,:,3]);eye.alpha_composite(Image.fromarray(star_pixels))
  close=p['left' if idx==0 else 'right'];mix=float(smooth((close-.76)/.24))
  place(im,eye,cx,cy,p['wide'],max(.09,1-close*.94)*p['wide'],1-mix)
  draw=ImageDraw.Draw(im)
  if mix>0:
   layer=Image.new('RGBA',im.size);d=ImageDraw.Draw(layer);rx=10 if idx==0 else 13
   d.line([(cx+rx*u,cy-4*(1-u*u)) for u in np.linspace(-1,1,26)],fill=(92,61,31,round(255*mix)),width=2);im.alpha_composite(layer)
  # This character has no eyebrows. Expressions use only eyes and mouth.
 special=max(p['closed'],p['teeth']);place(im,mouth,296,184,p['mx'],p['my'],1-special,p['smirk'])
 if special>0:
  layer=Image.new('RGBA',im.size);d=ImageDraw.Draw(layer)
  if p['teeth']>.1:
   jitter=round(p['nod']*.1);d.rounded_rectangle((281,181+jitter,311,188+jitter),radius=4,fill=(120,47,22,round(255*p['teeth'])));d.rounded_rectangle((283,182+jitter,309,186+jitter),radius=2,fill=(255,245,218,round(255*p['teeth'])))
  else:d.line([(296+17*u,184+3*(1-u*u)) for u in np.linspace(-1,1,40)],fill=(126,51,21,round(255*p['closed'])),width=2)
  im.alpha_composite(layer)
 result=np.asarray(im).copy();result[:,:,3]=neutral[:,:,3]
 assert np.array_equal(result[Y>219],neutral[Y>219]),'Face edit touched body/arms'
 return result
def body_map(a,p):
 root=smooth((351-Y)/150);head=smooth((250-Y)/72)
 qx=320+(X-320)/(1+p['squash']*.6)-p['lean']*root
 qy=351+(Y-351)/(1-p['squash'])-p['dip']*root-p['nod']*head
 angle=-p['tilt']*head;dx=qx-320;dy=qy-214
 qx=320+dx*np.cos(angle)-dy*np.sin(angle);qy=214+dx*np.sin(angle)+dy*np.cos(angle)
 # Gentle cheek inflation is one continuous map, with no feature/limb cutouts.
 cheek=np.exp(-((qy-163)/37)**2);qx-=p['cheek']*np.tanh((qx-302)/48)*cheek*np.exp(-((qx-302)/110)**4)
 if p['cheek'] or p['tilt'] or p['squash']:
  jac=np.gradient(qx,axis=1)*np.gradient(qy,axis=0)-np.gradient(qx,axis=0)*np.gradient(qy,axis=1)
  assert jac.min()>0 and jac[:,170:470].min()>.4,'Folded body map'
 qx=np.clip(qx,0,638.999);qy=np.clip(qy,0,358.999);ix=qx.astype('int32');iy=qy.astype('int32');fx=(qx-ix)[...,None];fy=(qy-iy)[...,None]
 src=a.astype(np.float32);src[:,:,:3]*=src[:,:,3:4]/255
 dst=(src[iy,ix]*(1-fx)+src[iy,ix+1]*fx)*(1-fy)+(src[iy+1,ix]*(1-fx)+src[iy+1,ix+1]*fx)*fy
 dst[:,:,:3]=np.divide(dst[:,:,:3]*255,dst[:,:,3:4],out=np.zeros_like(dst[:,:,:3]),where=dst[:,:,3:4]>.1)
 return Image.fromarray(np.clip(dst,0,255).astype('uint8'))
def frame(kind,i,frames):
 t=i*5/119;neutral=frames[0];key=hash(neutral.tobytes())
 if key not in FEATURES:FEATURES[key]=features(neutral)
 p=params(kind,t);e,s,dx,up=story.motion(kind,t)
 if i in (0,119):sprite=Image.fromarray(neutral);e=0;s=1;dx=0;up=0
 else:sprite=body_map(face(neutral,p,FEATURES[key]),p)
 if s!=1:sprite=sprite.convert('RGBa').resize((round(W*s),round(H*s)),Image.Resampling.LANCZOS).convert('RGBA')
 yy,xx=np.where(np.asarray(sprite)[:,:,3]>80);x=round((W-sprite.width)/2)+dx;y=round(351-up-int(yy.max()))
 character=Image.new('RGBA',(W,H));character.alpha_composite(sprite,(x,y));top=int(yy.min())+y;foot=int(yy.max())+y
 result=story.scene(kind,t,e,320+dx,foot,s,top);result.alpha_composite(character)
 ca=np.asarray(character);out=np.asarray(result);opaque=ca[:,:,3]==255;assert np.array_equal(ca[opaque],out[opaque])
 return result,character,{'x':x,'y':y,'scale':s,'top':top,'foot':foot,'dx':dx}
b.OUT=OUT;b.CLIPS=CLIPS;b.NEW=NEW;b.frame=frame
if __name__=='__main__':
 todo=sys.argv[1:] or list(NEW)
 if '--sample' in todo:
  from PIL import ImageFont
  font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',18);sheet=Image.new('RGB',(1440,900),'#e8eee9');d=ImageDraw.Draw(sheet);frames=b.decode(b.source_path('idle','watermelon'))
  for row,k in enumerate(['alarmwake','snowchill','treasurechest']):
   for col,i in enumerate([24,50,65,87]):
    im,_,_=frame(k,i,frames);bg=Image.new('RGBA',im.size,'#fffaf0' if col%2==0 else '#1e2b3b');bg.alpha_composite(im);sheet.paste(bg.crop((160,30,440,240)).resize((360,270)).convert('RGB'),(col*360,row*300+25));d.text((col*360+6,row*300+4),NEW[k][0]+f' {i/24:.2f}s',font=font,fill='#234635')
  sheet.save(OUT/'new-expression-pilot.jpg',quality=95);sys.exit()
 records=json.loads((OUT/'validation.json').read_text()) if (OUT/'validation.json').exists() else []
 for k in todo:
  records=[r for r in records if r['id']!=k]+b.encode(k);(OUT/'validation.json').write_text(json.dumps(records,indent=2),encoding='utf8')
 if len(records)==30:
  b.preview();p=OUT/'preview.html';p.write_text(p.read_text(encoding='utf8').replace('10个场景动作','10个新表情故事').replace('沿用 v1.1 完整角色表演，新增场景与道具编排。角色不重新拆分肢体。','全新眼神、嘴型和身体反应，与故事事件同步。手臂和躯干保持连续。'),encoding='utf8')
