"""Forty new choreographies, sharing the approved continuous body/shorts rig."""
from pathlib import Path
import sys, math, json, hashlib, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'work'))
import build_lulu_stars as wardrobe
w=wardrobe.w; b=w.b; rig=w.rig; refined=w.refined
# Opaque skin with a subpixel cut edge, rather than a broad transparent upper arm.
# Remove source-image colour fringes without shrinking the silhouette.
ARM_ASSETS=[]; FRONT_ARMS=[]
ay,ax=np.mgrid[:360,:640]
for i,(asset,pivot) in enumerate(zip(rig.arms,rig.pivots)):
    data=np.asarray(asset).copy()
    matte=asset.getchannel('A')
    # Preserve the limb silhouette and shoulder overlap. Clean its bright rim
    # by extending interior skin colours, not by shrinking the limb.
    valid=np.asarray(matte.filter(ImageFilter.MinFilter(5)))>245
    rgb=data[:,:,:3].astype(float)
    for _ in range(4):
        total=np.zeros_like(rgb);count=np.zeros(valid.shape,float)
        for dy,dx in [(-1,0),(1,0),(0,-1),(0,1)]:
            v=np.roll(valid,(dy,dx),(0,1));total+=np.roll(rgb,(dy,dx),(0,1))*v[:,:,None];count+=v
        fill=(~valid)&(count>0);rgb[fill]=total[fill]/count[fill,None];valid|=fill
    data[:,:,:3]=np.clip(rgb,0,255).astype('uint8')
    data[:,:,3]=np.minimum(255,data[:,:,3].astype(float)*255/250).astype('uint8')
    solid=Image.fromarray(data.copy());ARM_ASSETS.append(solid)
    handpos=rig.pos(165 if i==0 else 872,1045)
    vx,vy=handpos[0]-pivot[0],handpos[1]-pivot[1]
    along=((ax-pivot[0])*vx+(ay-pivot[1])*vy)/math.hypot(vx,vy)
    across=(-(ax-pivot[0])*vy+(ay-pivot[1])*vx)/math.hypot(vx,vy)
    # Round the hidden end of the forearm: a hard straight cut exposes a cuff
    # when a hand crosses the face. Only the actual silhouette is antialiased.
    frontmask=rig.smooth((along-39)/1.25)
    data[:,:,3]=(data[:,:,3]*frontmask).astype('uint8')
    FRONT_ARMS.append(Image.fromarray(data))
OUT=ROOT/'outputs/xigua-lulu-pet-80'; CLIPS=OUT/'clips'
CLIPS.mkdir(parents=True,exist_ok=True)
NEW={
 'salute':('认真敬礼','互动','抬手敬礼，挺胸停顿，再轻轻放下。'),
 'highfive':('隔空击掌','互动','伸出小手等你击掌，接触时轻轻回弹。'),
 'peekaboo':('捉迷藏探头','互动','躲到两只手后面，再左右探头逗你笑。'),
 'hush':('轻声嘘嘘','互动','小手靠近嘴边，眯眼提醒保持安静。'),
 'gift':('送你小礼物','互动','双手捧出礼盒，往前递一递，再收好。'),
 'bellyrub':('吃饱揉肚子','心情','轮流揉揉圆肚子，满足地眯眼。'),
 'selfhug':('抱抱自己','心情','双手抱住自己，轻轻挤一挤再松开。'),
 'sob':('委屈擦眼泪','心情','垂头吸鼻子，抬手擦去小泪珠。'),
 'relief':('松口气拍拍胸','心情','先紧张绷住，呼气后拍拍胸口。'),
 'eureka':('灵光一现','心情','低头想一想，看到灯泡亮起后举手示意。'),
 'drink':('抱杯喝果汁','美食','捧起果汁杯凑近嘴边，喝两口再放下。'),
 'melonbite':('啃一口西瓜','美食','托起西瓜咬一口，鼓动嘴巴开心咀嚼。'),
 'icecream':('舔舔冰淇淋','美食','举起甜筒舔两下，冷得眯眼又笑开。'),
 'cookie':('咔嚓吃饼干','美食','举起饼干咬一口，轻轻嚼完。'),
 'flower':('闻闻小花','美食','凑近花朵轻轻闻，闭眼露出满足表情。'),
 'readbook':('翻书认真读','专注','捧书低头看，视线随翻页移动。'),
 'notebook':('记下小灵感','专注','一手托本，一手写两笔，再满意点头。'),
 'magnify':('放大镜找线索','专注','拿放大镜左右检查，发现线索后睁大眼。'),
 'camera':('给你拍张照','专注','举起相机瞄准，按快门后放下查看。'),
 'binoculars':('望远镜看远方','专注','举起望远镜，慢慢向两边观察。'),
 'fan':('热得扇扇风','日常','拿小扇子给自己扇风，身体渐渐放松。'),
 'umbrella':('撑伞躲小雨','日常','撑起小伞，看着落雨，最后收伞。'),
 'watering':('给小苗浇水','日常','拿壶向小盆栽倾斜，水珠落下后小苗舒展。'),
 'sweep':('扫扫小纸屑','日常','握住小扫帚来回扫，把纸屑聚到一起。'),
 'brush':('认真刷刷牙','日常','小手拿牙刷来回刷，眯眼露出干净笑容。'),
 'tambourine':('拍拍铃鼓','音乐','一手托铃鼓，一手按节拍拍打。'),
 'maracas':('摇摇沙锤','音乐','左右沙锤轮流摇，头跟着节拍摆动。'),
 'drum':('咚咚敲小鼓','音乐','两只手交替敲鼓，身体跟着小幅起伏。'),
 'conduct':('小小指挥家','音乐','抬起指挥棒，画出上下左右的节拍。'),
 'harmonica':('吹一段口琴','音乐','把口琴放到嘴边，闭眼吹出短短旋律。'),
 'balloon':('牵住小气球','玩耍','抓住气球绳，看它飘动，再把它拉回来。'),
 'bubbles':('吹出小泡泡','玩耍','举起泡泡棒，鼓嘴吹气，目送泡泡飘走。'),
 'butterfly':('追看小蝴蝶','玩耍','眼睛追着蝴蝶，伸手让它停一会儿。'),
 'catchstar':('接住小星星','玩耍','抬头看星星落下，双手接住再举起展示。'),
 'ball':('拍两下皮球','玩耍','小手随皮球落下回弹，最后抱住皮球。'),
 'boxing':('左右练拳','运动','左右交替出拳，有收拳和身体重心回摆。'),
 'dumbbell':('举举小哑铃','运动','双手举起小哑铃，用力时眯眼，放下时呼气。'),
 'sidebend':('左右压压腰','运动','一手上举，左右各做一次侧腰伸展。'),
 'tiptoe':('踮脚够星星','运动','伸手向上够星星，踮起后慢慢放下。'),
 'skater':('左右滑步练习','运动','交替抬脚向侧边伸出，手臂反向维持平衡。'),
}
assert len(NEW)==40
BASE_PARAMS=b.params
E=b.E; P=b.P
def params(kind,t):
    p=BASE_PARAMS('nod',0)
    e=E(t,.2,.85,4.05,4.85); u=float(np.clip((t-.85)/3.2,0,1)); s=math.sin(2*math.pi*u)
    beat=math.sin(6*math.pi*u); hit=sum(P(t,c,.28) for c in (1.4,2.4,3.4))
    p.update(close=max(P(t,1.15,.14),P(t,3.95,.16)),front=True,prop=None,reach=e,hold=e)
    if kind=='salute':p.update(la=-143*e,ra=8*e,nod=-2*e,my=1-.45*e,close=.25*e)
    elif kind=='highfive':
        contact=P(t,2.3,.24);p.update(la=(-105+19*contact)*e,ra=-6*e,lean=-6*e+5*contact,my=1+.2*e,close=.72*contact,wink=P(t,3.2,.35))
    elif kind=='peekaboo':
        hide=E(t,.3,1,1.7,2.15)+.7*E(t,2.7,3,3.4,3.8)
        p.update(la=112*hide,ra=-112*hide,close=.95*hide,mx=1-.35*hide,my=1-.55*hide,lean=9*s*e,angle=.075*s*e,nod=3*hide)
    elif kind=='hush':p.update(la=119*e,ra=4*e,close=.35*e,mx=1-.65*e,my=1-.62*e,angle=-.07*e,gaze=2*e)
    elif kind=='gift':p.update(la=(59+7*P(t,2.6,.7))*e,ra=-(59+7*P(t,2.6,.7))*e,nod=3*P(t,2.6,.7),my=1+.18*e,close=.65*P(t,3,.6))
    elif kind=='bellyrub':p.update(la=(52+12*beat)*e,ra=(-52+12*beat)*e,close=.8*e,my=1-.15*e,angle=.025*s*e,dip=2*hit)
    elif kind=='selfhug':p.update(la=(87+5*hit)*e,ra=-(87+5*hit)*e,close=.9*e,mx=1-.15*e,my=1-.28*e,nod=4*e,dip=5*e,lean=3*s*e,rootblend=40)
    elif kind=='sob':p.update(la=(114+6*hit)*e,ra=12*e,close=.8*e,nod=6*e,dip=3*hit,mx=1-.6*e,my=1-.72*e,angle=.04*e)
    elif kind=='relief':
        worry=E(t,.15,.7,1.4,2);release=E(t,1.6,2.2,3.5,4.5)
        p.update(la=(74+9*hit)*release,ra=10*worry,nod=-3*worry+4*release,close=.85*release,mx=1-.5*worry,my=1-.6*worry-.2*release,dip=5*release)
    elif kind=='eureka':
        thinking=E(t,.2,.7,1.7,2.15);idea=E(t,1.9,2.2,3.7,4.6)
        p.update(angle=.1*thinking-.03*idea,nod=3*thinking-3*idea,la=-119*idea,ra=8*thinking,eye=1+.09*idea,my=1-.5*thinking+.2*idea)
    elif kind in ('drink','melonbite','icecream','cookie','flower'):
        lift=E(t,.65,1.55,2.95,3.65); chew=(.5+.5*math.sin(t*15))*E(t,2,2.4,3.5,4)
        p.update(la=(59+46*lift)*e,ra=-(59+46*lift)*e,nod=3*lift,close=(.7 if kind=='flower' else .35)*lift,mx=1-.25*lift,my=1-.35*lift-.16*chew,gaze=1.5*lift,lift=lift,chew=chew)
        if kind=='icecream':p.update(wink=P(t,2.8,.4),my=1-.55*lift+.2*P(t,2,.25))
        if kind=='flower':p.update(nod=4*lift,angle=-.04*lift,close=.9*lift,my=1-.5*lift)
    elif kind=='readbook':p.update(la=61*e,ra=-61*e,nod=5*e,gaze=2.4*s*e,my=1-.45*e,close=P(t,3.5,.16))
    elif kind=='notebook':p.update(la=61*e,ra=(-75+7*beat)*e,nod=(5+hit)*e,gaze=1.5*e,my=1-.5*e,angle=-.025*e)
    elif kind=='magnify':p.update(la=(85+22*s)*e,ra=7*e,lean=6*s*e,angle=.055*s*e,eye=1+.08*P(t,3,.5),my=1-.45*e,gaze=-2*s*e)
    elif kind=='camera':
        lift=E(t,.5,1.35,2.8,3.4);p.update(la=(61+43*lift)*e,ra=-(61+43*lift)*e,nod=2*e,close=P(t,2.1,.13),my=1-.45*lift,lift=lift)
    elif kind=='binoculars':p.update(la=122*e,ra=-122*e,angle=.09*s*e,lean=7*s*e,gaze=2*s*e,my=1-.6*e)
    elif kind=='fan':p.update(la=(-53+24*beat)*e,ra=14*e,my=1-.55*e,close=.6*e,nod=2*e,angle=.025*s*e)
    elif kind=='umbrella':p.update(la=-65*e,ra=15*e,gaze=-2.5*e,angle=-.04*e,my=1-.15*e,close=max(P(t,1.2,.15),P(t,3.5,.15)))
    elif kind=='watering':p.update(la=(10+22*P(t,2.3,1.2))*e,ra=-40*e,nod=5*e,lean=-5*e,gaze=-2*e,my=1-.25*e)
    elif kind=='sweep':p.update(la=(9+20*s)*e,ra=(-18+20*s)*e,lean=5*s*e,nod=5*e,hip=-3*s*e,my=1-.35*e,gaze=-2*s*e)
    elif kind=='brush':p.update(la=(112+6*math.sin(t*18))*e,ra=8*e,my=1-.6*e,mx=1-.2*e,close=.55*e,nod=2*e)
    elif kind=='tambourine':p.update(la=54*e,ra=(-58-25*hit)*e,dip=2*hit,nod=2*hit,close=.5*hit,my=1+.15*hit)
    elif kind=='maracas':p.update(la=(-45-30*beat)*e,ra=(45-30*beat)*e,angle=.04*beat*e,lean=5*beat*e,my=1+.15*abs(beat)*e)
    elif kind=='drum':p.update(la=(47+25*max(0,beat))*e,ra=-(47+25*max(0,-beat))*e,nod=2*abs(beat)*e,dip=2*abs(beat)*e,close=.4*abs(beat)*e,my=1+.13*e)
    elif kind=='conduct':p.update(la=(-60-30*beat)*e,ra=(35+24*math.cos(6*math.pi*u))*e,nod=2*hit,lean=4*s*e,my=1-.3*e)
    elif kind=='harmonica':p.update(la=105*e,ra=-105*e,close=.8*e,mx=1-.35*e,my=1-.55*e,angle=.045*s*e,lean=3*s*e)
    elif kind=='balloon':p.update(la=(-58+12*s)*e,ra=9*e,nod=-3*e,gaze=-2*e,angle=-.035*e,my=1+.1*e)
    elif kind=='bubbles':p.update(la=106*e,ra=-40*e,mx=1-.6*e,my=1-.65*e,nod=-2*e,close=.2*e,gaze=-2*e)
    elif kind=='butterfly':p.update(la=-74*e,ra=12*e,gaze=3*s*e,angle=.09*s*e,nod=-2*e,my=1+.12*e,eye=1+.04*e)
    elif kind=='catchstar':
        catch=P(t,2.15,.55);p.update(la=(76-18*catch)*e,ra=-(76-18*catch)*e,dip=6*catch,nod=-3*e+5*catch,close=.65*catch,my=1+.14*e)
    elif kind=='ball':p.update(la=(12+25*beat)*e,ra=-17*e,nod=4*e,lean=-5*e,my=1+.12*e,gaze=-2*e,dip=2*max(0,beat)*e)
    elif kind=='boxing':
        left=P(t,1.3,.4)+P(t,3.1,.4);right=P(t,2.2,.4)
        p.update(la=(43+48*left)*e,ra=-(43+48*right)*e,lean=5*(right-left),angle=.045*(right-left),close=.3*max(left,right),my=1-.5*e,dip=3*max(left,right))
    elif kind=='dumbbell':p.update(la=(10+80*hit)*e,ra=-(10+80*hit)*e,close=.65*hit,my=1-.6*hit,dip=4*hit,nod=3*hit)
    elif kind=='sidebend':p.update(la=-119*max(0,s)*e,ra=119*max(0,-s)*e,angle=.14*s*e,lean=12*s*e,hip=-3*s*e,close=.6*abs(s)*e,my=1-.3*abs(s)*e)
    elif kind=='tiptoe':
        reach=P(t,1.8,.8)+P(t,3.4,.65);p.update(la=-132*reach,ra=104*reach,nod=-5*reach,legup=8*reach,legx=-2*reach,lean=-4*reach,my=1-.45*reach,eye=1+.05*reach,close=.25*reach)
    elif kind=='skater':p.update(legup=17*abs(s)*e,legx=14*s*e,hip=6*s*e,lean=-9*s*e,angle=-.055*s*e,la=-45*s*e,ra=-45*s*e,my=1+.12*abs(s)*e,mirrorleg=s<0)
    targets={}
    if kind=='salute':targets={0:((248,144),e)}
    elif kind=='peekaboo':targets={0:((299,137),hide),1:((371,140),hide)}
    elif kind=='hush':targets={0:((336,197),e)}
    elif kind=='sob':targets={0:((293+3*hit,146+4*hit),e)}
    elif kind=='binoculars':targets={0:((307,147),e),1:((375,147),e)}
    elif kind=='camera':targets={0:((307,195),lift*e),1:((374,195),lift*e)}
    elif kind=='harmonica':targets={0:((316,197),e),1:((371,197),e)}
    elif kind=='flower':targets={0:((316,255-38*lift),e),1:((334,259-38*lift),e)}
    elif kind=='icecream':targets={0:((312,255-38*lift),e),1:((338,255-38*lift),e)}
    elif kind=='selfhug':targets={0:((345,237-3*hit),e),1:((307,258-3*hit),e)}
    elif kind=='boxing':targets={0:((294-73*left,244-33*left),e),1:((354+73*right,244-33*right),e)}
    elif kind=='dumbbell':targets={0:((225,253-50*hit),e),1:((423,253-50*hit),e)}
    elif kind=='ball':
        phase=float(np.clip((t-.9)/2.5,0,1));bounce=abs(math.cos(phase*2*math.pi));hold=rig.ease(t,3.4,3.9)
        p['ballxy']=(233*(1-hold)+324*hold,(328-57*bounce)*(1-hold)+245*hold)
        x,y=p['ballxy'];targets={0:((x-20*hold,y-20+20*hold),e),1:((x+22,y),hold*e)}
    p['targets']=targets
    if kind=='tiptoe':p.update(legup=0,legx=0,rise=6*reach)
    return p

def hand(i,angle):
    root=rig.pivots[i]; x,y=rig.pos(165 if i==0 else 872,1065)
    dx=x-root[0];dy=y-root[1];a=math.radians(angle)
    return root[0]+dx*math.cos(a)+dy*math.sin(a),root[1]-dx*math.sin(a)+dy*math.cos(a)

def actual_hand(i,p):
    old=np.array(hand(i,p['la'] if i==0 else p['ra']))
    if i in p['targets']:
        target,amount=p['targets'][i];old=old*(1-amount)+np.array(target)*amount
    return tuple(old)

def reaching_arm(i,p):
    root=np.array(rig.pivots[i]);old=np.array(rig.pos(165 if i==0 else 872,1065))-root
    new=np.array(actual_hand(i,p))-root;ratio=np.linalg.norm(new)/np.linalg.norm(old)
    u=old/np.linalg.norm(old);v=new/max(.001,np.linalg.norm(new))
    matrix=np.outer(u,v)/ratio+np.outer([-u[1],u[0]],[-v[1],v[0]])
    offset=root-matrix@root;coeff=(*matrix[0],offset[0],*matrix[1],offset[1])
    return [a.transform((640,360),Image.Transform.AFFINE,coeff,Image.Resampling.BICUBIC) for a in (ARM_ASSETS[i],FRONT_ARMS[i])]

ARM_CACHE={}
def continuous_arm(i,p):
    """One continuous textured strip from shoulder to palm, with a bent centreline."""
    source_root=np.array(rig.pivots[i]);target=np.array(actual_hand(i,p))
    source_hand=np.array(hand(i,0));axis=source_hand-source_root;source_len=np.linalg.norm(axis);axis/=source_len
    angle=p['la'] if i==0 else -p['ra']
    amount=float(rig.smooth((angle-12)/55))
    if i in p['targets']:amount=max(amount,p['targets'][i][1])
    root=source_root+np.array([8 if i==0 else -8,12])
    # The elbow bows down/outward; never hide its connection behind the muzzle.
    delta=target-root;distance=np.linalg.norm(delta);normal=np.array([-delta[1],delta[0]])/max(distance,.001)
    if normal[1]<0:normal=-normal
    control=(root+target)/2+normal*min(10,distance*.12)*amount
    u=np.linspace(0,1,17)[:,None]
    points=(1-u)**2*root+2*u*(1-u)*control+u*u*target
    seg=np.diff(points,axis=0);lengths=np.linalg.norm(seg,axis=1);arc=np.r_[0,np.cumsum(lengths)];total=arc[-1]
    first=seg[0]/lengths[0];last=seg[-1]/lengths[-1]
    points=np.vstack([root-first*24,points,target+last*24]);arc=np.r_[-24,arc,total+24]
    x0=max(0,int(points[:,0].min())-22);x1=min(640,int(points[:,0].max())+23)
    y0=max(0,int(points[:,1].min())-22);y1=min(360,int(points[:,1].max())+23)
    gy,gx=np.mgrid[y0:y1,x0:x1];closest=np.full(gx.shape,np.inf);along=np.zeros(gx.shape);across=np.zeros(gx.shape)
    for j in range(len(points)-1):
        start,end=points[j:j+2];v=end-start;length=np.linalg.norm(v);unit=v/length
        projection=np.clip(((gx-start[0])*v[0]+(gy-start[1])*v[1])/(length*length),0,1)
        dx=gx-start[0]-projection*v[0];dy=gy-start[1]-projection*v[1];d2=dx*dx+dy*dy
        use=d2<closest;closest[use]=d2[use]
        along[use]=arc[j]+projection[use]*length
        across[use]=(-dx*unit[1]+dy*unit[0])[use]
    # Preserve the distal hand's size; distribute reach through the upper arm.
    split=total-22
    s=np.where(along<0,along,np.where(along<split,along*(source_len-22)/split,source_len-22+along-split))
    sx=source_root[0]+axis[0]*s-axis[1]*across;sy=source_root[1]+axis[1]*s+axis[0]*across
    sx=np.clip(sx,0,638.999);sy=np.clip(sy,0,358.999);ix=sx.astype(int);iy=sy.astype(int);fx=(sx-ix)[...,None];fy=(sy-iy)[...,None]
    src=np.asarray(ARM_ASSETS[i],dtype=float).copy();src[:,:,:3]*=src[:,:,3:4]/255
    pix=(src[iy,ix]*(1-fx)+src[iy,ix+1]*fx)*(1-fy)+(src[iy+1,ix]*(1-fx)+src[iy+1,ix+1]*fx)*fy
    pix[:,:,:3]=np.divide(pix[:,:,:3]*255,pix[:,:,3:4],out=np.zeros_like(pix[:,:,:3]),where=pix[:,:,3:4]>.1)
    pix[closest>22**2]=0
    # The back of the shoulder remains inside the torso, never as a stray cap.
    bodyalpha=np.asarray(w.COSTUMES['watermelon'].getchannel('A'))[y0:y1,x0:x1]/255
    # The first few millimetres of the shoulder are embedded in the torso.
    # Keep their exterior contour inside the body, but retain the opaque
    # centreline and the entire visible forearm beyond the shoulder joint.
    shoulder=np.maximum(rig.smooth((s-6)/8),1-rig.smooth((np.abs(across)-8)/3))
    pix[:,:,3]*=np.maximum(bodyalpha,shoulder)
    # Match skin colour at the embedded shoulder joint, while keeping the limb
    # opaque. This removes a cut-out collar without fading the forearm itself.
    joint=(1-rig.smooth((s+2)/p.get('rootblend',16)))*(bodyalpha>.95)
    skin=np.asarray(w.COSTUMES['watermelon']) [y0:y1,x0:x1,:3]
    pix[:,:,:3]=pix[:,:,:3]*(1-joint[:,:,None])+skin*joint[:,:,None]
    whole=np.zeros((360,640,4),dtype='uint8');whole[y0:y1,x0:x1]=np.clip(pix,0,255).astype('uint8')
    # Remove one-pixel slivers created where inverse curve segments meet.
    # Opening keeps the broad silhouette and does not erode the arm as a whole.
    whole[:,:,3]=np.asarray(Image.fromarray(whole[:,:,3]).filter(ImageFilter.MinFilter(3)).filter(ImageFilter.MaxFilter(3)))
    front=whole.copy();front[y0:y1,x0:x1,3]=(front[y0:y1,x0:x1,3]*rig.smooth((s+2)/4)).astype('uint8')
    return Image.fromarray(whole),Image.fromarray(front)

def star(d,x,y,r,fill):
    pts=[(x+math.sin(i*math.pi/5)*r*(1 if i%2==0 else .44),y-math.cos(i*math.pi/5)*r*(1 if i%2==0 else .44)) for i in range(10)]
    d.polygon(pts,fill=fill)

def draw_props(im,kind,t,p):
    e=p['hold']
    if e<.002:return
    layer=Image.new('RGBA',im.size); d=ImageDraw.Draw(layer)
    l=actual_hand(0,p); r=actual_hand(1,p); cx=(l[0]+r[0])/2;cy=(l[1]+r[1])/2-7
    ink='#605542'; gold='#ffc74f'; blue='#7ccbdd'; cream='#fff6da'; pink='#f18ba3'
    def line(points,fill=ink,width=2):d.line(points,fill=fill,width=width,joint='curve')
    def ellipse(box,fill,outline=None,width=1):d.ellipse(box,fill=fill,outline=outline,width=width)
    def rect(box,fill,radius=4,outline=None):d.rounded_rectangle(box,radius,fill=fill,outline=outline,width=2)
    def note(x,y):
        ellipse((x-4,y-1,x+3,y+4),ink);line([(x+3,y+1),(x+3,y-14),(x+10,y-11)],ink,2)
    if kind=='gift':
        cy-=4;rect((cx-30,cy-21,cx+30,cy+20),'#f28b95',6,'#cb657d');rect((cx-33,cy-25,cx+33,cy-15),'#f5a5ab');rect((cx-4,cy-25,cx+4,cy+20),gold,1)
        d.arc((cx-20,cy-40,cx+1,cy-21),0,330,fill=gold,width=4);d.arc((cx-1,cy-40,cx+20,cy-21),210,540,fill=gold,width=4)
    elif kind=='eureka':
        k=E(t,1.8,2.2,3.7,4.3)
        if k>0:ellipse((410,72,434,99),(255,215,67,round(255*k)));rect((417,99,427,105),(140,119,86,round(255*k)),2)
        for a in range(0,360,60):
            rad=math.radians(a);line([(422+19*math.cos(rad),85+19*math.sin(rad)),(422+25*math.cos(rad),85+25*math.sin(rad))],(255,205,60,round(255*k)),2)
    elif kind=='sob':
        for x,delay in [(293,0),(365,.5)]:
            v=((t+delay)%1)/1; y=141+32*v;ellipse((x-2,y-4,x+2,y+3),(111,199,238,round(200*e*(1-v))))
    elif kind=='drink':
        cy-=6;rect((cx-19,cy-25,cx+19,cy+24),blue,7,'#4f9cac');rect((cx-15,cy-8,cx+15,cy+18),'#fdbb57',5)
        line([(cx+6,cy+3),(cx+6,cy-19),(cx+18,cy-22)],cream,3);ellipse((cx-10,cy-17,cx-4,cy-12),'#d9f4f4')
    elif kind=='melonbite':
        cy-=6;d.pieslice((cx-35,cy-43,cx+35,cy+19),0,180,fill='#33865b');d.pieslice((cx-31,cy-39,cx+31,cy+14),0,180,fill=cream);d.pieslice((cx-27,cy-35,cx+27,cy+10),0,180,fill='#ef6566')
        for dx,dy in [(-17,-9),(0,-2),(17,-9)]:ellipse((cx+dx-1,cy+dy-2,cx+dx+1,cy+dy+2),'#503d36')
        if t>2:ellipse((cx+10,cy-17,cx+24,cy-5),(0,0,0,0))
    elif kind=='icecream':
        d.polygon([(cx-15,cy-13),(cx+15,cy-13),(cx,cy+30)],fill='#d99a52');line([(cx-11,cy-5),(cx+5,cy+12)],'#edbb79');line([(cx+11,cy-5),(cx-4,cy+13)],'#edbb79')
        ellipse((cx-20,cy-43,cx+20,cy-7),pink,'#db7993');ellipse((cx-12,cy-40,cx+4,cy-32),'#ffced5')
    elif kind=='cookie':
        ellipse((cx-24,cy-31,cx+24,cy+15),'#dda65c','#bd8240',2)
        for dx,dy in [(-11,-18),(7,-22),(-14,0),(0,-3),(15,-2)]:ellipse((cx+dx-2,cy+dy-2,cx+dx+2,cy+dy+2),'#79523b')
        if t>2:ellipse((cx+13,cy-30,cx+31,cy-12),(0,0,0,0))
    elif kind=='flower':
        line([(cx,cy+24),(cx,cy-28)],'#4c9562',3);ellipse((cx,cy+2,cx+15,cy+10),'#70b76b')
        for a in range(0,360,60):
            x=cx+10*math.cos(math.radians(a));y=cy-28+10*math.sin(math.radians(a));ellipse((x-8,y-8,x+8,y+8),pink)
        ellipse((cx-7,cy-35,cx+7,cy-21),gold)
    elif kind in ('readbook','notebook'):
        rect((cx-35,cy-21,cx+35,cy+23),'#729dab',3);d.polygon([(cx-31,cy-22),(cx,cy-17),(cx+31,cy-22),(cx+31,cy+18),(cx,cy+23),(cx-31,cy+18)],fill=cream);line([(cx,cy-17),(cx,cy+22)],'#cfbfa1')
        for dy in [-10,-2,6]:line([(cx-26,cy+dy),(cx-6,cy+dy+3)],'#b3a48c');line([(cx+6,cy+dy+3),(cx+26,cy+dy)],'#b3a48c')
        if kind=='readbook':
            flip=P(t,2.5,.65);d.polygon([(cx,cy-17),(cx+29*(1-2*flip),cy-25),(cx+29*(1-2*flip),cy+14),(cx,cy+23)],fill='#fffae9')
        else:line([(r[0]-4,r[1]-3),(r[0]-18,r[1]-30)],'#dd8e4a',4)
    elif kind=='magnify':
        x,y=l;line([(x,y),(x+9,y-23)],'#9a7252',5);ellipse((x-6,y-54,x+28,y-20),(175,226,236,130),'#577e8b',4);d.arc((x-2,y-50,x+24,y-24),195,270,fill='#f3ffff',width=2)
    elif kind=='camera':
        rect((cx-34,cy-21,cx+34,cy+18),'#64758b',5,'#424e63');rect((cx-18,cy-27,cx+7,cy-17),'#64758b');ellipse((cx-16,cy-17,cx+16,cy+14),'#33425b','#a7c5d7',3);ellipse((cx-10,cy-11,cx+10,cy+8),'#648aaf');rect((cx+20,cy-15,cx+28,cy-9),cream,1)
        flash=P(t,2.1,.12)
        if flash>.1:star(d,cx+25,cy-16,14*flash,'#fff9bb')
    elif kind=='binoculars':
        cy-=28
        for x in [cx-22,cx+22]:rect((x-6,cy+2,x+6,cy+35),'#6b8772',5)
        rect((cx-36,cy-20,cx+36,cy+10),'#6b8772',7);ellipse((cx-37,cy-17,cx-7,cy+15),'#a4d4df','#486c61',4);ellipse((cx+7,cy-17,cx+37,cy+15),'#a4d4df','#486c61',4)
    elif kind=='fan':
        x,y=l; d.pieslice((x-32,y-53,x+32,y+7),180,360,fill='#efb8a7',outline='#bc8b6c',width=2)
        for dx in [-26,-13,0,13,26]:line([(x,y),(x+dx,y-27)],'#c38973',1)
        line([(x,y+4),(x,y-24)],'#b38258',3)
    elif kind=='umbrella':
        x,y=l;ux=x+105;uy=76
        line([(x,y+12),(x,y-13),(ux,uy)],'#b68b5b',3)
        d.pieslice((ux-110,uy-62,ux+110,uy+62),180,360,fill='#83bdce',outline='#538f9f',width=2)
        line([(ux-110,uy),(ux+110,uy)],'#538f9f',2)
        for j in range(7):
            rx=180+j*12;ry=55+((t*60+j*31)%145);line([(rx,ry),(rx-2,ry+7)],(127,190,218,160),2)
    elif kind=='watering':
        x,y=l;rect((x-31,y+5,x+7,y+33),blue,6,'#5799aa');line([(x-28,y+13),(201,281),(201,286)],blue,6);d.arc((x-10,y-13,x+16,y+16),180,360,fill='#5799aa',width=4)
        rect((190,328,215,351),'#c98960',3);line([(202,329),(202,299)],'#659b59',3);ellipse((188,298,202,306),'#83b867');ellipse((202,293,217,302),'#83b867')
        wet=P(t,2.3,1.2)
        for j in range(4):
            if wet>.1:ellipse((202+j*3,284+(t*42+j*12)%28,204+j*3,289+(t*42+j*12)%28),blue)
    elif kind=='sweep':
        x,y=l;bx=x-24;line([(x+12,y-25),(bx,334)],'#b48a57',4);d.polygon([(bx-8,330),(bx+8,333),(bx+13,348),(bx-17,348)],fill='#dfb667')
        gather=rig.ease(t,.9,3.8)
        for j in range(5):
            px=(188+j*12)*(1-gather)+(204+j*3)*gather;rect((px,347,px+4,349),'#c4c3b4',1)
    elif kind=='brush':
        x,y=l;line([(x-2,y),(x+27,y-18)],blue,4);rect((x+20,y-24,x+34,y-17),cream,2)
        for j in range(4):ellipse((335+j*4,191,339+j*4,195),(255,251,233,210))
    elif kind=='tambourine':
        x,y=l;ellipse((x-9,y-35,x+43,y+9),'#f3dca6','#b68153',4)
        for a in range(0,360,60):
            sx=x+17+23*math.cos(math.radians(a));sy=y-13+18*math.sin(math.radians(a));ellipse((sx-3,sy-2,sx+3,sy+2),'#b5c5c9')
    elif kind=='maracas':
        for x,y in (l,r):line([(x,y+3),(x,y-20)],'#b78957',4);ellipse((x-11,y-43,x+11,y-18),pink,'#bf6880');line([(x-8,y-28),(x+8,y-28)],gold,3)
    elif kind=='drum':
        rect((287,246,362,277),'#e59787',5,'#ba6e69');ellipse((287,236,362,256),cream,'#ba6e69',2)
        for x,y in (l,r):
            tip=(x+(-17 if x>324 else 17),y-8);line([(x,y),tip],'#987250',3);ellipse((tip[0]-2,tip[1]-2,tip[0]+2,tip[1]+2),'#c49a68')
    elif kind=='conduct':
        x,y=l;line([(x,y),(x-25,y-44)],cream,3)
        for j in range(3):note(414+j*12,190-j*21+3*math.sin(t*3+j))
    elif kind=='harmonica':rect((cx-29,cy-13,cx+29,cy+3),'#aac8d1',3,'#638590');[rect((cx-22+j*8,cy-8,cx-18+j*8,cy-2),'#526b82',1) for j in range(6)];note(420,162+6*math.sin(t*3))
    elif kind=='balloon':
        x,y=l;bx=x-15+9*math.sin(t*2);by=y-100+4*math.cos(t*2);line([(x,y),(x-8,y-50),(bx,by+27)],'#b7a48b',1);ellipse((bx-22,by-29,bx+22,by+26),pink,'#d57793',2);ellipse((bx-12,by-18,bx-6,by-4),'#ffd5df')
    elif kind=='bubbles':
        x,y=l;line([(x,y),(x-7,y-24)],'#bd8a64',3);ellipse((x-17,y-44,x+3,y-24),None,blue,3)
        for j in range(4):
            age=(t-1.2-j*.4)/2.8
            if 0<age<1:
                bx=x-7-70*age;by=y-34-85*age-9*j*age;radius=(7+5*j)*min(1,age*8);ellipse((bx-radius,by-radius,bx+radius,by+radius),(183,224,237,35),(155,211,226,round(220*(1-age))),2)
                if radius>4:d.arc((bx-radius+3,by-radius+3,bx+radius-3,by+radius-3),200,270,fill='#ecfbff',width=1)
    elif kind=='butterfly':
        k=E(t,2,2.4,3.2,3.5);x=252+65*math.sin(t*1.5);y=121+15*math.cos(t*2);x=x*(1-k)+l[0]*k;y=y*(1-k)+(l[1]-27)*k;wing=4+6*abs(math.sin(t*14));ellipse((x-wing*2,y-10,x,y+8),pink);ellipse((x,y-10,x+wing*2,y+8),'#f8c26a');line([(x,y-7),(x,y+8)],ink,2)
    elif kind=='catchstar':
        q=rig.ease(t,.7,2.1);x=324+30*(1-q);y=65*(1-q)+cy*q;star(d,x,y,22,gold);star(d,x-3,y-4,9,'#ffe89d')
    elif kind=='ball':
        x,y=p['ballxy']
        ellipse((x-23,y-23,x+23,y+23),'#ee9d70','#c77957',2);d.arc((x-23,y-23,x+23,y+23),75,260,fill=cream,width=3);line([(x-22,y),(x+22,y)],cream,2)
    elif kind=='dumbbell':
        for x,y in (l,r):line([(x-24,y-5),(x+24,y-5)],'#a2aeb1',5);rect((x-31,y-18,x-20,y+8),blue,3);rect((x+20,y-18,x+31,y+8),blue,3)
    elif kind=='tiptoe':star(d,219,85-5*P(t,1.8,.8),12,gold)
    elif kind=='highfive':
        k=P(t,2.3,.24)
        if k>.05:
            for dx,dy in [(-18,0),(-13,-16),(4,-21)]:line([(l[0]+dx,l[1]+dy),(l[0]+dx*1.4,l[1]+dy*1.4)],(255,193,61,round(k*240)),2)
    layer.putalpha(layer.getchannel('A').point(lambda a:round(a*e)))
    im.alpha_composite(layer)

def compose(kind,t,p):
    im=Image.new('RGBA',(640,360)); front=[]
    key=(kind,t)
    if ARM_CACHE.get('key')!=key:
        ARM_CACHE.clear();ARM_CACHE.update(key=key,layers=[continuous_arm(i,p) for i in range(2)])
    for moved,fg in ARM_CACHE['layers']:
        im.alpha_composite(moved);front.append(fg)
    im.alpha_composite(rig.base)
    for i in range(2):
        c=max(p['close'],p['wink'] if i==0 else 0)
        if c<.65:rig.paste_feature(im,rig.eyes[i],sx=p['eye'],sy=max(.12,1-1.12*c)*p['eye'],dx=p['gaze'])
        else:rig.paste_feature(im,rig.closed[i])
    rig.paste_feature(im,rig.mouth,sx=p['mx'],sy=p['my'])
    if not BODY_ONLY:draw_props(im,kind,t,p)
    for fg in (front[::-1] if kind=='selfhug' else front):im.alpha_composite(fg)
    return im

BODY_ONLY=False
b.params=params;b.compose=compose
Y,X=np.mgrid[:360,100:540].astype(np.float32)
HEAD=rig.smooth((252-Y)/50);ROOTWEIGHT=rig.smooth((352-Y)/145)
FIELD_CACHE=None
def frame(kind,t,costume='watermelon',body_only=False):
    global BODY_ONLY,FIELD_CACHE
    BODY_ONLY=body_only;rig.base=w.COSTUMES[costume]
    try:
        if t>=5:t=0
        p=params(kind,t);im=compose(kind,t,p)
        if FIELD_CACHE is None or FIELD_CACHE[0]!=(kind,t):
            qx=X-p['lean']*ROOTWEIGHT
            qy=Y-p['dip']*ROOTWEIGHT-p['nod']*HEAD+p.get('rise',0)*ROOTWEIGHT
            th=-p['angle']*HEAD;dx=qx-320;dy=qy-220
            bx=320+dx*np.cos(th)-dy*np.sin(th);by=220+dx*np.sin(th)+dy*np.cos(th)
            qx=bx.copy();qy=by.copy()
            for _ in range(6):
                lower=rig.smooth((qy-258)/78);split=1-rig.smooth((qx-287)/78)
                if p.get('mirrorleg'):split=1-split
                hipweight=1-rig.smooth((qy-282)/62);knee=np.maximum(0,np.sin(np.pi*np.clip((qy-258)/94,0,1)))**2
                qx=bx-p['legx']*split*lower-p['hip']*hipweight-2*(p['legup']/23)*knee*split
                qy=by+p['legup']*split*lower
            qx=np.clip(qx,0,638.999);qy=np.clip(qy,0,358.999);ix=qx.astype('int32');iy=qy.astype('int32');fx=(qx-ix)[...,None];fy=(qy-iy)[...,None]
            FIELD_CACHE=((kind,t),ix,iy,fx,fy)
        _,ix,iy,fx,fy=FIELD_CACHE
        a=np.asarray(im,dtype=np.float32);a[:,:,:3]*=a[:,:,3:4]/255
        pix=(a[iy,ix]*(1-fx)+a[iy,ix+1]*fx)*(1-fy)+(a[iy+1,ix]*(1-fx)+a[iy+1,ix+1]*fx)*fy
        pix[:,:,:3]=np.divide(pix[:,:,:3]*255,pix[:,:,3:4],out=np.zeros_like(pix[:,:,:3]),where=pix[:,:,3:4]>.1)
        result=np.zeros((360,640,4),dtype='uint8');result[:,100:540]=np.clip(pix,0,255).astype('uint8')
        return Image.fromarray(result).transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    finally:BODY_ONLY=False

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def clean_edges(im):
    # The same four-neighbour propagation on the occupied crop avoids processing
    # large empty margins. Float32 retains sub-byte accuracy and halves memory IO.
    a=np.asarray(im).copy();ys,xs=np.where(a[:,:,3]>0)
    x0=max(0,int(xs.min())-5);x1=min(640,int(xs.max())+6);y0=max(0,int(ys.min())-5);y1=min(360,int(ys.max())+6)
    crop=a[y0:y1,x0:x1];rgb=crop[:,:,:3].astype(np.float32);valid=crop[:,:,3]>=32
    for _ in range(4):
        total=np.zeros_like(rgb);count=np.zeros(valid.shape,np.float32)
        for dy,dx in [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]:
            v=np.roll(valid,(dy,dx),(0,1));total+=np.roll(rgb,(dy,dx),(0,1))*v[:,:,None];count+=v
        fill=(~valid)&(count>0);rgb[fill]=total[fill]/count[fill,None];valid|=fill
    crop[:,:,:3]=np.clip(rgb,0,255).astype('uint8');return a
def encode(kind):
    results=[]; procs={};paths={};samples={};bounds=[];signature=[]
    for costume in w.COSTUMES:
        path=CLIPS/f'{costume}-{kind}.webm';paths[costume]=path
        procs[costume]=subprocess.Popen([str(rig.FF),'-v','error','-y','-f','rawvideo','-pix_fmt','rgba','-s','640x360','-r','24','-i','-','-an','-c:v','libvpx-vp9','-pix_fmt','yuva420p','-crf','20','-b:v','0','-deadline','realtime','-cpu-used','4','-threads','1','-auto-alt-ref','0',str(path)],stdin=subprocess.PIPE)
    try:
        for i in range(120):
            t=i*5/119;alpha=None
            for costume,proc in procs.items():
                im=frame(kind,t,costume);a=np.asarray(im);mask=a[:,:,3]>40;y,x=np.where(mask)
                assert x.min()>104 and x.max()<536 and y.min()>3 and y.max()<356,(kind,i,costume,'canvas cut',x.min(),x.max(),y.min(),y.max())
                if alpha is None:alpha=a[:,:,3];bounds.append([int(x.min()),int(y.min()),int(x.max()),int(y.max())])
                else:assert np.array_equal(alpha,a[:,:,3]),(kind,i,'costume silhouette')
                proc.stdin.write(clean_edges(im).tobytes())
                if i in (0,24,48,72,96,119):im.save(CLIPS/f'{costume}-{kind}-{i:03}.png')
                if costume=='watermelon' and i in (24,48,72,96):
                    sig=np.asarray(im.resize((64,36))).astype(float);sig[:,:,:3]*=sig[:,:,3:4]/255;signature.append(sig)
        for costume,proc in procs.items():proc.stdin.close();assert proc.wait()==0
    except BaseException:
        for proc in procs.values():proc.kill()
        raise
    for costume,path in paths.items():
        raw=subprocess.run([str(rig.FF),'-v','error','-c:v','libvpx-vp9','-i',str(path),'-f','rawvideo','-pix_fmt','rgba','-'],capture_output=True,check=True).stdout
        frames=np.frombuffer(raw,np.uint8).reshape(-1,360,640,4);assert len(frames)==120
        edge=int(max(frames[:,:3,:,3].max(),frames[:,-3:,:,3].max(),frames[:,:,:3,3].max(),frames[:,:,-3:,3].max()));assert edge<20
        delta=float(np.abs(frames[0].astype(float)-frames[-1].astype(float)).mean());assert delta<2
        results.append(dict(id=kind,costume=costume,file=path.name,frames=120,edgeAlpha=edge,endpointError=delta,sha256=sha(path)))
    np.save(CLIPS/f'{kind}-signature.npy',np.array(signature))
    print(kind+' 3 costumes / 360 frames verified',flush=True)
    return results

def storyboard(render=True):
    font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',18)
    for start in range(0,40,5):
        sheet=Image.new('RGB',(1200,1175),'#e8eee8');d=ImageDraw.Draw(sheet)
        for row,(kind,(label,cat,desc)) in enumerate(list(NEW.items())[start:start+5]):
            d.text((12,row*235+5),f'{start+row+41} {label}',font=font,fill='#234437')
            for col,t in enumerate([1,2,3,4]):
                costume=['watermelon','orange','star','watermelon'][col]
                im=frame(kind,t,costume).crop((100,0,540,360)).resize((227,186)) if render else Image.open(CLIPS/f'{costume}-{kind}-{[24,48,72,96][col]:03}.png').crop((100,0,540,360)).resize((227,186))
                bg=Image.new('RGBA',im.size,'#fffdf4' if col%2==0 else '#202c38');bg.alpha_composite(im);sheet.paste(bg.convert('RGB'),(215+col*243,row*235+30))
        sheet.save(OUT/f'review-{start//5+1}.jpg')
    old=json.loads((ROOT/'outputs/xigua-lulu-github-publish/config/actions.json').read_text(encoding='utf8'))
    actions=old+[dict(id=k,name=v[0],category=v[1],description=v[2],new=True) for k,v in NEW.items()]
    (OUT/'actions.json').write_text(json.dumps(actions,ensure_ascii=False,indent=2),encoding='utf8')
    (OUT/'new-actions.json').write_text(json.dumps({k:dict(name='西瓜噜-'+v[0],category=v[1],description=v[2]) for k,v in NEW.items()},ensure_ascii=False,indent=2),encoding='utf8')
    mapping=json.loads((ROOT/'outputs/xigua-lulu-github-publish/config/mapping.json').read_text(encoding='utf8'));mapping.update({'西瓜噜-'+v[0]:k for k,v in NEW.items()})
    (OUT/'mapping.json').write_text(json.dumps(mapping,ensure_ascii=False,indent=2),encoding='utf8')

if __name__=='__main__':
    if '--inspect' in sys.argv:storyboard();sys.exit()
    path=OUT/'validation.json';records=json.loads(path.read_text()) if path.exists() else []
    todo=[k for k in NEW if not ('--resume' in sys.argv and len([r for r in records if r['id']==k and (CLIPS/r['file']).exists() and sha(CLIPS/r['file'])==r['sha256']])==3)]
    if '--action' in sys.argv:todo=[sys.argv[sys.argv.index('--action')+1]]
    if '--actions' in sys.argv:todo=sys.argv[sys.argv.index('--actions')+1].split(',')
    from concurrent.futures import ProcessPoolExecutor,as_completed
    with ProcessPoolExecutor(max_workers=3) as pool:
        futures=[pool.submit(encode,k) for k in todo]
        for f in as_completed(futures):
            result=f.result();records=[r for r in records if r['id']!=result[0]['id']]+result
            path.write_text(json.dumps(records,indent=2),encoding='utf8')
    storyboard(False)
