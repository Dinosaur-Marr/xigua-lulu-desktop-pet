"""Render one of the 20 v1.2 scene/expression actions from bundled inputs."""
from pathlib import Path
import argparse,sys,subprocess
ROOT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT/'work'))
p=argparse.ArgumentParser();p.add_argument('--action',required=True);p.add_argument('--costume',choices=['watermelon','orange','star'],default='watermelon');p.add_argument('--output',required=True);a=p.parse_args()
import build_lulu_scenes10 as b
if a.action in b.NEW:module=b
else:
 import build_lulu_expressions10 as module
 if a.action not in module.NEW:p.error('Unknown extra action')
frames=b.decode(b.source_path(module.NEW[a.action][1],a.costume))
target=Path(a.output).resolve();target.parent.mkdir(parents=True,exist_ok=True)
proc=subprocess.Popen([str(b.FF),'-v','error','-y','-f','rawvideo','-pix_fmt','rgba','-s','640x360','-r','24','-i','-','-an','-c:v','libvpx-vp9','-pix_fmt','yuva420p','-lossless','1','-deadline','realtime','-cpu-used','5','-threads','1','-auto-alt-ref','0',str(target)],stdin=subprocess.PIPE)
try:
 for i in range(120):proc.stdin.write(module.frame(a.action,i,frames)[0].tobytes())
 proc.stdin.close();assert proc.wait()==0
except BaseException:proc.kill();raise
print(target)
