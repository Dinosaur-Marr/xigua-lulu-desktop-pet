"""V4: clean hand cutouts, retaining the v3 left-facing asset convention."""
from pathlib import Path
import sys,json,shutil,subprocess
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'work'))
import build_lulu_v2 as rig
OUT=ROOT/'outputs/xigua-lulu-pet-v4';CLIPS=OUT/'clips';CLIPS.mkdir(parents=True,exist_ok=True)
arm_asset=Image.open(OUT/'rig/arms.png').convert('RGBA').resize(rig.original.size,Image.Resampling.LANCZOS)
rig.arms=[]
for x0,x1 in [(0,512),(512,1024)]:
    layer=Image.new('RGBA',rig.original.size)
    layer.alpha_composite(arm_asset.crop((x0,0,x1,1536)),(x0,0))
    rig.arms.append(rig.normalize(layer))
frame_right=rig.frame
def frame(kind,t):return frame_right(kind,t).transpose(Image.Transpose.FLIP_LEFT_RIGHT)
rig.frame=frame;rig.OUT=OUT;rig.CLIPS=CLIPS

def inspect_hands():
    checks=[]
    for i,arm in enumerate(rig.arms):
        a=np.asarray(arm);opaque=a[:,:,3]>24;r,g,b=[a[:,:,j].astype(float) for j in range(3)]
        contamination=opaque&((g>r)|((b>150)&(abs(r-g)<14))|((r>100)&(r>3*g)&(g<80)))
        assert int(contamination.sum())==0,(i,int(contamination.sum()))
        # A single connected arm component must remain after removing clothing.
        mask=a[:,:,3]>40;seen=np.zeros(mask.shape,bool);components=[]
        for y,x in zip(*np.where(mask)):
            if seen[y,x]:continue
            todo=[(y,x)];seen[y,x]=True;n=0
            while todo:
                yy,xx=todo.pop();n+=1
                for ny,nx in [(yy-1,xx),(yy+1,xx),(yy,xx-1),(yy,xx+1)]:
                    if 0<=ny<360 and 0<=nx<640 and mask[ny,nx] and not seen[ny,nx]:seen[ny,nx]=True;todo.append((ny,nx))
            if n>3:components.append(n)
        assert len(components)==1,(i,components)
        checks.append({'arm':i,'coloredResiduePixels':0,'connectedComponents':len(components),'opaquePixels':int(opaque.sum())})
    (OUT/'hand-matte-validation.json').write_text(json.dumps(checks,indent=2),encoding='utf8')
    cases=[('stretch',1.4),('wave',1.4),('jump',.95),('celebrate',3.15)]
    sheet=Image.new('RGB',(1200,1440),'#f3f5f6');d=ImageDraw.Draw(sheet)
    for i,(kind,t) in enumerate(cases):
        for j,bgcolor in enumerate(['#ffffff','#17212b']):
            im=frame(kind,t).crop((140,80,500,285)).resize((600,342),Image.Resampling.LANCZOS)
            bg=Image.new('RGBA',im.size,bgcolor);bg.alpha_composite(im)
            x=j*600;y=i*360
            sheet.paste(bg.convert('RGB'),(x,y+18));d.text((x+8,y+3),kind,fill='#203040')
    sheet.save(OUT/'hand-edge-review.jpg')

if __name__=='__main__':
    inspect_hands()
    if '--inspect' in sys.argv:sys.exit()
    stats=[]
    for kind in rig.LABELS:
        record=rig.encode(kind);stats.append(record);print(json.dumps(record),flush=True)
    (OUT/'validation.json').write_text(json.dumps(stats,indent=2),encoding='utf8')
    for name in ['mapping.json','main-config.jsonc']:shutil.copy2(ROOT/'outputs/xigua-lulu-pet-v3'/name,OUT/name)
    html=(ROOT/'outputs/xigua-lulu-pet-v3/preview.html').read_text(encoding='utf8').replace('朝向修正版','手部边缘修正版').replace('?v=3','?v=4')
    (OUT/'preview.html').write_text(html,encoding='utf8')
