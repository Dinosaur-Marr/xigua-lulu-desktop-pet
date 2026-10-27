"""Render an editable action without needing a developer's old output folders."""
from pathlib import Path
import argparse,sys,subprocess
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'work'))
parser=argparse.ArgumentParser()
parser.add_argument('--action',default='hug')
parser.add_argument('--output',required=True)
args=parser.parse_args()
if args.action in ['walk','run','float']:
    import build_lulu_walk_v6 as module
    frame=module.frame
    import build_lulu_40 as b
else:
    import refine_lulu_arms as module
    b=module.b
    frame=b.frame if args.action in b.NEW else b.old.frame
if args.action not in b.LABELS:parser.error('Unknown action: '+args.action)
target=Path(args.output).resolve();target.parent.mkdir(parents=True,exist_ok=True)
p=subprocess.Popen([str(b.FF),'-y','-f','rawvideo','-pix_fmt','rgba','-s','640x360','-r','24','-i','-','-an','-c:v','libvpx-vp9','-pix_fmt','yuva420p','-b:v','0','-crf','28','-auto-alt-ref','0',str(target)],stdin=subprocess.PIPE)
try:
    for i in range(120):p.stdin.write(b.clean_encoding_edges(frame(args.action,i/24)).tobytes())
finally:p.stdin.close()
if p.wait():raise SystemExit('FFmpeg failed')
print(target)
