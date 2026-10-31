"""Second ten scenes: narrative events synchronized to intact expressive footage."""
from pathlib import Path
import sys,json,math
import numpy as np
from PIL import Image,ImageDraw
import build_lulu_scenes10 as b
OUT=b.ROOT/'outputs/lulu-story-actions-10';CLIPS=OUT/'clips';CLIPS.mkdir(parents=True,exist_ok=True)
NEW={
 'rainbowrain':('雨停啦见彩虹','look','小雨落下时眨眼张望，雨停后彩虹慢慢展开，身体轻轻转向两侧。'),
 'snowchill':('雪花亲亲脸','shy','雪花飘近，噜噜眯眼缩一缩，雪花旋转着散开，最后放松站好。'),
 'alarmwake':('小闹钟叫醒我','wake','先打瞌睡，闹钟响起的瞬间睁大眼睛、张嘴惊醒，再恢复精神。'),
 'chickhatch':('咦小鸡出壳了','surprise','蛋壳咔嚓裂开，噜噜后仰睁大眼；小鸡探头、跳一下，噜噜放松微笑。'),
 'popcornparty':('爆米花蹦蹦派对','giggle','小玉米锅接连爆出爆米花，噜噜跟着一抖一笑，最后锅盖轻轻合上。'),
 'papercrane':('纸鹤带来一封信','look','纸鹤从左边飞过，噜噜转头张望；纸鹤留下小信封，从另一侧飞走。'),
 'flowerbow':('一鞠躬花就开','bow','噜噜闭眼鞠躬，两侧的小芽依次开花，抬头时花朵轻轻点头回应。'),
 'thundercloud':('雷声吓一小跳','surprise','小乌云先鼓起来，闪电亮起时身体后仰、眼睛睁大，乌云散去后放松。'),
 'minigarden':('误入迷你蘑菇园','think','蘑菇慢慢长高，噜噜变成小小一只，好奇歪头观察，再恢复原来的大小。'),
 'treasurechest':('宝箱里藏着快乐','giggle','宝箱轻轻晃动，盖子打开飞出金币与星星，噜噜开心笑抖，最后宝箱合上。')
}
TIMING={
 'alarmwake':{'sleep':[.4,2.05],'ring':[2.12,2.75],'wideEyes':2.35,'recover':3.5},
 'chickhatch':{'crack':.85,'startle':1.0,'chickAppears':1.35,'chickHop':3.45,'smile':3.5},
 'thundercloud':{'gather':.5,'flash':1.45,'startle':1.45,'clear':3.0,'smile':3.2},
 'flowerbow':{'bow':1.2,'bloom':[1.2,3.1],'recover':4.2},
 'rainbowrain':{'rain':[.5,2.2],'rainbow':[2.35,4.2]},
 'snowchill':{'snow':[.5,3.7],'squint':[.6,3.8]},
 'popcornparty':{'pop':[.8,1.35,1.9,2.45,3.0],'laugh':[.8,3.8]},
 'papercrane':{'left':1.1,'letter':2.5,'right':3.5},
 'minigarden':{'shrink':[.5,1.6],'look':[1.6,3.5],'restore':[3.6,4.6]},
 'treasurechest':{'open':[.7,1.15],'coins':[1.2,2.0,2.8],'close':[3.6,4.4]}
}
def E(t,a,beg,c,d):return b.smooth((t-a)/(beg-a))*(1-b.smooth((t-c)/(d-c)))
def motion(kind,t):
 e=b.env(t);s=1.;dx=0.;up=0.
 if kind=='rainbowrain':s=1-.025*e;dx=5*math.sin(t*2)*e
 elif kind=='snowchill':s=1-.035*E(t,.5,1,3.5,4.5);dx=3*math.sin(t*5)*e
 elif kind=='alarmwake':s=1-.045*e;up=9*b.pulse(t,2.42,.28)
 elif kind=='chickhatch':s=1-.035*e;dx=9*E(t,.8,1.05,2.8,3.6)
 elif kind=='popcornparty':s=1-.025*e;dx=3*math.sin(t*9)*e
 elif kind=='papercrane':dx=7*math.sin((t-2.5)*1.3)*e
 elif kind=='flowerbow':s=1-.015*e
 elif kind=='thundercloud':s=1-.04*e;dx=9*E(t,1.3,1.5,2.5,3.15);up=4*b.pulse(t,1.5,.25)
 elif kind=='minigarden':s=1-.40*E(t,.45,1.6,3.5,4.6);dx=12*math.sin(t*2)*e
 elif kind=='treasurechest':s=1-.025*e
 return e,s,round(dx),up
def ellipse(a,x,y,rx,ry,c,outline=None,width=1):a.ellipse((x-rx,y-ry,x+rx,y+ry),c,outline,width)
def cloud(a,x,y,size,color):
 for dx,dy,r in [(-.55,0,.42),(0,-.22,.52),(.55,.03,.38),(0,.15,.65)]:ellipse(a,x+dx*size,y+dy*size,r*size,r*size*.7,color)
def flower(a,x,ground,size,color,alpha,t):
 stemtop=ground-size;lean=4*math.sin(t*3+x)*size/60
 a.line([(x,ground),(x+lean*.4,ground-size*.45),(x+lean,stemtop)],(70,145,90,alpha),3)
 a.poly([(x,ground-size*.3),(x-17,ground-size*.6),(x-5,ground-size*.6)],(100,182,101,alpha))
 rad=10*min(1,size/50)
 for j in range(6):
  ang=j*math.pi/3;ellipse(a,x+lean+rad*math.cos(ang),stemtop+rad*math.sin(ang),rad*.74,rad*.74,(*color,alpha))
 ellipse(a,x+lean,stemtop,rad*.7,rad*.7,(255,209,89,alpha))
def rounded(a,bounds,fill,r=5,outline=None):a.d.rounded_rectangle(tuple(round(v*2) for v in bounds),radius=r*2,fill=fill,outline=outline,width=2)
def scene(kind,t,e,cx,foot,s,top):
 a=b.Art();alpha=round(255*e)
 if alpha<1:return a.finish()
 if kind=='rainbowrain':
  rain=E(t,.25,.65,1.9,2.55);cloud(a,138,91,38,(157,191,216,round(alpha*rain)))
  for j in range(11):
   x=102+(j%4)*22;y=132+((t*88+j*23)%175)
   a.line([(x,y),(x-3,y+9)],(88,174,220,round(alpha*rain)),2)
  sun=E(t,2.1,2.7,4.1,4.7);ellipse(a,495,94,22,22,(255,208,93,round(alpha*sun)))
  for j in range(8):
   ang=j*math.pi/4;a.line([(495+28*math.cos(ang),94+28*math.sin(ang)),(495+34*math.cos(ang),94+34*math.sin(ang))],(255,202,77,round(alpha*sun)),2)
  for j,c in enumerate([(244,137,147),(246,187,113),(245,218,119),(131,195,148),(121,184,221),(173,155,214)]):
   a.arc((128+j*6,65+j*6,512-j*6,395-j*6),180,360,(*c,round(alpha*sun)),5)
 elif kind=='snowchill':
  for j in range(14):
   x=105+(j%2)*418+math.sin(t*1.6+j)*24;y=48+((t*35+j*31)%265);r=4+(j%3)
   for ang in [0,math.pi/3,2*math.pi/3]:
    a.line([(x-r*math.cos(ang),y-r*math.sin(ang)),(x+r*math.cos(ang),y+r*math.sin(ang))],(150,201,225,alpha),2)
  for x in [137,503]:
   ellipse(a,x,343,37,8,(213,233,245,alpha));ellipse(a,x-10,339,18,10,(245,251,255,alpha))
 elif kind=='alarmwake':
  ring=E(t,2.1,2.2,2.65,2.95);x=139+3*math.sin(48*t)*ring;y=305
  a.line([(x-19,y+25),(x-26,y+39)],(98,115,138,alpha),4);a.line([(x+19,y+25),(x+26,y+39)],(98,115,138,alpha),4)
  ellipse(a,x,y,32,32,(240,156,149,alpha));ellipse(a,x,y,25,25,(255,251,231,alpha),(154,100,108,alpha),2)
  for j in range(12):
   an=j*math.pi/6;a.line([(x+20*math.cos(an),y+20*math.sin(an)),(x+23*math.cos(an),y+23*math.sin(an))],(99,108,133,alpha),1)
  a.line([(x-7,y-13),(x,y),(x+12,y-4)],(83,102,129,alpha),3)
  for dx in [-23,23]:ellipse(a,x+dx,y-27,12,8,(239,172,123,alpha))
  if ring>.05:
   for sign in [-1,1]:a.line([(x+sign*44,y-25),(x+sign*50,y-35)],(235,174,61,round(alpha*ring)),3)
  sleepy=E(t,.4,.8,1.8,2.12)
  for j in range(3):
   xx=461+j*17;yy=159-j*30-5*math.sin(t*2);r=8+j*2
   a.line([(xx-r,yy-r),(xx+r,yy-r),(xx-r,yy+r),(xx+r,yy+r)],(141,165,206,round(alpha*sleepy)),2)
 elif kind=='chickhatch':
  x=139;y=320;open_=b.smooth((t-.9)/.7);hop=11*b.pulse(t,3.45,.38)
  eggalpha=round(alpha*(1-open_));ellipse(a,x,y,27,32,(250,242,215,eggalpha))
  # Chick rises from inside the stationary shell, then hops once.
  if open_>0:
   yy=y-30*open_-hop;ellipse(a,x,yy,19,21,(255,215,98,alpha));ellipse(a,x-6,yy-3,2,3,(73,66,57,alpha));ellipse(a,x+6,yy-3,2,3,(73,66,57,alpha));a.poly([(x-4,yy+3),(x+4,yy+3),(x,yy+8)],(236,143,56,alpha))
   for sign in [-1,1]:a.line([(x+sign*17,yy+5),(x+sign*(24+3*math.sin(t*11)),yy-1)],(246,192,77,alpha),4)
  a.poly([(x-27,y),(x-18,y-6),(x-9,y+2),(x,y-7),(x+10,y+1),(x+20,y-5),(x+27,y),(x+21,y+23),(x+11,y+31),(x-12,y+31),(x-22,y+22)],(255,246,220,alpha))
  if .78<t<1.22:a.line([(x-5,y-25),(x+3,y-16),(x-3,y-9),(x+4,y)],(181,151,118,alpha),2)
  if t>1.3:
   for j in range(3):a.star(102+j*36,241-12*math.sin(j),3,(255,208,88,alpha))
 elif kind=='popcornparty':
  x=145;y=323
  rounded(a,(x-34,y-18,x+34,y+22),(224,134,139,alpha),9);a.line([(x-43,y-6),(x-34,y-6)],(120,100,123,alpha),4);a.line([(x+34,y-6),(x+43,y-6)],(120,100,123,alpha),4)
  for off in [-20,-7,7,20]:a.line([(x+off,y-12),(x+off,y+17)],(255,230,204,alpha),3)
  lift=E(t,.6,.9,3.35,4.1);ellipse(a,x,y-19-18*lift,38,7,(124,145,171,alpha));ellipse(a,x,y-28-18*lift,7,5,(104,123,149,alpha))
  for j,launch in enumerate([.8,1.35,1.9,2.45,3.]):
   u=(t-launch)/.95
   if 0<u<1:
    xx=x+(-1 if j%2 else 1)*44*u;yy=y-24-105*math.sin(math.pi*u)
    for dx,dy in [(-5,0),(4,0),(0,-5),(0,4)]:ellipse(a,xx+dx,yy+dy,6,6,(255,238,183,alpha),(232,196,133,alpha),1)
 elif kind=='papercrane':
  x=320+177*math.sin((t-2.35)*1.05);y=74+16*math.cos(t*2);wing=20+13*math.sin(t*8)
  a.poly([(x-23,y),(x,y-8),(x+24,y+1),(x+5,y+7)],(167,214,226,alpha))
  a.poly([(x-4,y),(x-17,y-wing),(x+12,y-5)],(215,238,242,alpha));a.poly([(x+3,y+2),(x+12,y+wing*.65),(x-16,y+1)],(127,187,208,alpha))
  a.poly([(x+20,y),(x+29,y-17),(x+36,y-15),(x+29,y-11),(x+26,y+2)],(182,225,234,alpha))
  letter=E(t,2.25,2.6,3.7,4.6);xx=482;yy=245-12*math.sin(t*2)
  rounded(a,(xx-24,yy-16,xx+24,yy+16),(255,239,196,round(alpha*letter)),3)
  a.line([(xx-23,yy-15),(xx,yy+3),(xx+23,yy-15)],(209,166,110,round(alpha*letter)),2);a.star(xx,yy+4,5,(239,148,135,round(alpha*letter)))
 elif kind=='flowerbow':
  for j,x in enumerate([96,139,180,460,501,544]):
   growth=b.smooth((t-1.05-(j%3)*.3)/.8)*b.smooth((4.8-t)/.65)
   if growth>0:flower(a,x,347,(49+(j%3)*16)*growth,[(240,147,168),(164,156,215),(246,190,121)][j%3],alpha,t)
 elif kind=='thundercloud':
  cloudalpha=round(alpha*E(t,.25,.65,2.5,3.2));cloud(a,133,90,43,(132,149,180,cloudalpha))
  flash=max(b.pulse(t,1.45,.17),.65*b.pulse(t,1.8,.15))
  if flash>0:a.poly([(139,112),(123,145),(137,141),(126,171),(155,130),(140,133),(153,112)],(255,216,96,round(alpha*flash)))
  for j in range(6):
   x=97+j*14;y=173+((t*80+j*17)%112);a.line([(x,y),(x-3,y+7)],(121,181,220,cloudalpha),2)
  sunny=E(t,3,3.4,4.2,4.75);ellipse(a,492,100,23,23,(255,210,107,round(alpha*sunny)))
  for dx in [-7,7]:ellipse(a,492+dx,99,2,2,(166,128,87,round(alpha*sunny)))
  a.arc((482,99,502,113),0,180,(166,128,87,round(alpha*sunny)),2)
 elif kind=='minigarden':
  grow=E(t,.45,1.6,3.5,4.6)
  for j,x in enumerate([130,191,454,516]):
   h=(72+(j%2)*35)*grow;y=348-h;r=(31+(j%2)*9)*grow
   if r<1:continue
   rounded(a,(x-r*.25,y,x+r*.25,348),(248,227,188,alpha),max(1,round(r*.2)))
   a.poly([(x-r,y+4),(x-r*.8,y-r*.5),(x-r*.35,y-r*.8),(x+r*.3,y-r*.8),(x+r*.8,y-r*.5),(x+r,y+4)],[(236,135,131,alpha),(194,161,218,alpha)][j%2])
   for off in [-.5,.1,.55]:ellipse(a,x+off*r,y-r*.25-(.25 if off==.1 else 0)*r,max(1,r*.10),max(1,r*.10),(255,240,216,alpha))
   a.line([(x-r*.8,y+4),(x+r*.8,y+4)],(255,209,179,alpha),2)
 elif kind=='treasurechest':
  x=493;y=315;opened=E(t,.65,1.1,3.5,4.3)
  rounded(a,(x-38,y-1,x+38,y+30),(178,126,96,alpha),5,(117,94,89,alpha));rounded(a,(x-38,y-22-30*opened,x+38,y+3-30*opened),(215,160,97,alpha),8)
  for dx in [-24,24]:a.line([(x+dx,y),(x+dx,y+28)],(250,208,118,alpha),5)
  rounded(a,(x-7,y+5,x+7,y+19),(250,210,116,alpha),2)
  if opened>.4:
   for j,launch in enumerate([1.15,1.55,2.05,2.55,2.95]):
    u=(t-launch)/1.0
    if 0<u<1:
     xx=x+(j-2)*17*u;yy=y-10-102*math.sin(math.pi*u)
     if j%2: a.star(xx,yy,8,(255,216,105,alpha))
     else:ellipse(a,xx,yy,6+2*math.cos(u*14),9,(255,207,95,alpha),(221,164,62,alpha),1)
 return a.finish()
base_frame=b.frame
def source_index(kind,i):
 if kind!='thundercloud':return i
 t=i*5/119
 mapped=float(np.interp(t,[0,.5,1.45,2.45,3.2,4.7,5],[0,.5,1.,2.8,3.5,4.7,5]))
 return max(0,min(119,round(mapped*119/5)))
class TimedFrames:
 def __init__(self,kind,frames):self.kind=kind;self.frames=frames
 def __getitem__(self,i):return self.frames[source_index(self.kind,i)]
def frame(kind,i,frames):return base_frame(kind,i,TimedFrames(kind,frames))
b.OUT=OUT;b.CLIPS=CLIPS;b.NEW=NEW;b.motion=motion;b.scene=scene;b.frame=frame
if __name__=='__main__':
 todo=sys.argv[1:] or list(NEW);records=json.loads((OUT/'validation.json').read_text()) if (OUT/'validation.json').exists() else []
 for k in todo:
  records=[r for r in records if r['id']!=k]+b.encode(k)
  (OUT/'validation.json').write_text(json.dumps(records,indent=2),encoding='utf8')
 (OUT/'story-timing.json').write_text(json.dumps(TIMING,ensure_ascii=False,indent=2),encoding='utf8')
 if len(records)==30:
  b.preview();p=OUT/'preview.html';p.write_text(p.read_text(encoding='utf8').replace('10个场景动作','10个故事动作').replace('新增场景与道具编排','让眼神、表情和身体反应跟随故事事件'),encoding='utf8')
