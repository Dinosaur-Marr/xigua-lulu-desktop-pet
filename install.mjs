// Copyright (c) 2026 西瓜噜噜桌宠 contributors. MIT.
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import crypto from 'node:crypto';
import { fileURLToPath } from 'node:url';

export const ROOT = path.dirname(fileURLToPath(import.meta.url));
const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const json = file => JSON.parse(fs.readFileSync(file, 'utf8').replace(/^\uFEFF/, ''));
const inside = (root, target) => { const rel=path.relative(root,target); return rel==='' || (!rel.startsWith('..'+path.sep) && rel!=='..' && !path.isAbsolute(rel)); };
function safe(root, relative) {
  if (typeof relative !== 'string' || path.isAbsolute(relative) || relative.includes('\\') || relative.split('/').some(x=>!x || x==='.' || x==='..' || x.includes(':'))) throw Error('Unsafe relative path');
  const dest=path.resolve(root,relative);
  if (!inside(root,dest)) throw Error('Path escapes destination');
  // Reject symlink/junction traversal, including an existing destination file.
  for (let p=dest;;p=path.dirname(p)) {
    if (fs.existsSync(p) && fs.lstatSync(p).isSymbolicLink()) throw Error('Symlink/junction destination: '+p);
    if (path.dirname(p)===p) break;
  }
  return dest;
}
export function parseJsonc(text) {
  text=text.replace(/^\uFEFF/,'');let out='',quote=false,escape=false;
  for(let i=0;i<text.length;i++) {
    const c=text[i],n=text[i+1];
    if(quote){out+=c;if(escape)escape=false;else if(c==='\\')escape=true;else if(c==='"')quote=false;continue;}
    if(c==='"'){quote=true;out+=c;continue;}
    if(c==='/'&&n==='/'){while(i<text.length&&text[i]!=='\n')i++;out+='\n';continue;}
    if(c==='/'&&n==='*'){i+=2;while(i<text.length&&!(text[i]==='*'&&text[i+1]==='/'))i++;if(i>=text.length)throw Error('Unclosed JSONC comment');i++;out+=' ';continue;}
    out+=c;
  }
  let clean='';quote=false;escape=false;
  for(let i=0;i<out.length;i++){
    const c=out[i];
    if(quote){clean+=c;if(escape)escape=false;else if(c==='\\')escape=true;else if(c==='"')quote=false;continue;}
    if(c==='"')quote=true;
    if(c===',' && /^[\s]*[}\]]/.test(out.slice(i+1)))continue;
    clean+=c;
  }
  return JSON.parse(clean);
}
export function verifyPack(root=ROOT) {
  const manifest=json(path.join(root,'manifest.json'));
  for(const [relative,hash] of Object.entries(manifest.files)) {
    if(sha(fs.readFileSync(safe(root,relative)))!==hash)throw Error('Package checksum mismatch: '+relative);
  }
  const actions=json(path.join(root,'config/actions.json')),mapping=json(path.join(root,'config/mapping.json')),memes=json(path.join(root,'config/memes.json'));
  if(actions.length!==40 || new Set(actions.map(a=>a.id)).size!==40 || Object.keys(mapping).length!==127 || Object.keys(memes).length!==27)throw Error('Incomplete asset pack');
  for(const id of Object.values(mapping)) if(!actions.some(a=>a.id===id))throw Error('Unknown animation: '+id);
  for(const a of actions)if(!manifest.files['assets/clips/'+a.id+'.webm'])throw Error('Unverified clip');
  for(const name of Object.keys(memes))if(!manifest.files['assets/memes/'+name+'.png'])throw Error('Unverified meme');
  for(const name of ['animations','direction-patches','mapping','memes','actions'])if(!manifest.files['config/'+name+'.json'])throw Error('Unverified config');
  if(!manifest.files['config/wardrobe.json'] || !manifest.files['runtime/lulu-wardrobe.js'])throw Error('Unverified wardrobe runtime');
  const wardrobe=json(path.join(root,'config/wardrobe.json'));
  if(wardrobe.length!==86 || new Set(wardrobe.map(a=>a.name)).size!==86)throw Error('Incomplete wardrobe');
  for(const entry of wardrobe)if(!/^lulu-(?:(?:orange|star)-[a-z]+|change-(?:orange|watermelon)|change-(?:orange|watermelon)-star|change-star-(?:orange|watermelon))$/.test(entry.name)||entry.file!==`assets/wardrobe/${entry.name}.webm`||!manifest.files[entry.file])throw Error('Unverified wardrobe clip');
  return {manifest,actions,mapping,memes};
}
const defaultPet = {id:'main',name:'西瓜噜噜',size:462,balanceEnabled:false,whisperEnabled:false,workStatusEnabled:true,fixedEnabled:false,display:'desktop',position:{corner:'bottom-right',marginX:24,marginY:24}};
export function planInstall({root=ROOT,dshHome=process.env.DSH_HOME||path.join(os.homedir(),'.dsh'),profile='desktop'}={}) {
  if(!/^[a-zA-Z0-9_-]+$/.test(profile))throw Error('Invalid profile');
  dshHome=path.resolve(dshHome);
  const {mapping,memes}=verifyPack(root);
  const pluginRoot=safe(dshHome,`profiles/${profile}/node_modules/dsh-pet`);
  const pkg=json(path.join(pluginRoot,'package.json'));
  if(pkg.name!=='dsh-pet'||pkg.version!=='0.3.7')throw Error('This release supports dsh-pet 0.3.7 only; no files were changed.');
  const changes=[];
  function add(relative,bytes){const target=safe(dshHome,relative);if(fs.existsSync(target)&&!fs.statSync(target).isFile())throw Error('Expected file: '+target);changes.push({relative,target,bytes:Buffer.from(bytes)});}
  for(const [name,id] of Object.entries(mapping)){
    if(/[\\/:*?"<>|]/.test(name)||!/^[a-z]+$/.test(id))throw Error('Invalid asset name');
    add(`dsh-pet/main-animation/webm/${name}.webm`,fs.readFileSync(path.join(root,'assets/clips',id+'.webm')));
  }
  for(const name of Object.keys(memes)){
    if(/[\\/:*?"<>|]/.test(name))throw Error('Invalid meme name');
    add(`dsh-pet/memes/${name}.png`,fs.readFileSync(path.join(root,'assets/memes',name+'.png')));
  }
  for(const entry of json(path.join(root,'config/wardrobe.json')))add(`dsh-pet/main-animation/webm/${entry.name}.webm`,fs.readFileSync(safe(root,entry.file)));
  const helper=`profiles/${profile}/node_modules/dsh-pet/runtime/electron-helper`;
  const index=fs.readFileSync(safe(dshHome,helper+'/index.html'),'utf8');
  const anchor='<script src="./sprite.js"></script>';
  if(!index.includes('<script src="./lulu-wardrobe.js"></script>')){
    if(index.split(anchor).length!==2)throw Error('Unsupported desktop helper entry; no files were changed.');
    add(helper+'/index.html',index.replace(anchor,anchor+'\n    <script src="./lulu-wardrobe.js"></script>'));
  }
  add(helper+'/lulu-wardrobe.js',fs.readFileSync(path.join(root,'runtime/lulu-wardrobe.js')));
  for(const patch of json(path.join(root,'config/direction-patches.json'))){
    const relative=`profiles/${profile}/node_modules/dsh-pet/${patch.file}`,target=safe(dshHome,relative);
    if(!fs.existsSync(target)&&patch.file.startsWith('src/'))continue;
    const text=fs.readFileSync(target,'utf8');
    if(text.includes(patch.after))continue;
    if(text.split(patch.before).length!==2)throw Error('Unsupported movement code: '+patch.file+'; no files were changed.');
    add(relative,text.replace(patch.before,patch.after));
  }
  const cfgFile=safe(dshHome,'dsh-pet/main-config.jsonc');
  const config=fs.existsSync(cfgFile)?parseJsonc(fs.readFileSync(cfgFile,'utf8')):{};
  if(config.pets!==undefined&&!Array.isArray(config.pets))throw Error('Invalid existing pets configuration');
  config.animations=json(path.join(root,'config/animations.json'));
  // Make all 40 unique actions available by name in the manual menu.
  config.memes=memes;
  config.whisperPrompt='你是主人桌面上的西瓜噜噜，圆滚滚的黄色小伙伴，头顶小橙子，穿西瓜短裤。偶尔碎碎念一句，20字以内，活泼温暖、带点贪吃的小俏皮。';
  config.pets=config.pets?.length?config.pets.map(p=>({...p,name:'西瓜噜噜'})):[defaultPet];
  config.whisperImageEnabled=true;config.chatImageEnabled=true;
  add('dsh-pet/main-config.jsonc',JSON.stringify(config,null,2)+'\n');
  return {dshHome,profile,changes};
}
export function install(options={}) {
  const plan=planInstall(options);
  if(options.dryRun)return {dryRun:true,files:plan.changes.length,dshHome:plan.dshHome};
  const backup=safe(plan.dshHome,'xigua-lulu-backups/'+new Date().toISOString().replace(/[:.]/g,'-')+'-'+crypto.randomBytes(3).toString('hex'));
  fs.mkdirSync(backup,{recursive:true});
  const receipt={version:1,dshHome:plan.dshHome,profile:plan.profile,state:'prepared',files:[]};
  for(const c of plan.changes){
    const existed=fs.existsSync(c.target),previous=existed?fs.readFileSync(c.target):null;
    if(existed){const b=safe(backup,'files/'+c.relative);fs.mkdirSync(path.dirname(b),{recursive:true});fs.writeFileSync(b,previous);}
    receipt.files.push({relative:c.relative,existed,before:previous?sha(previous):null,after:sha(c.bytes)});
  }
  const receiptFile=path.join(backup,'receipt.json');
  fs.writeFileSync(receiptFile,JSON.stringify(receipt,null,2));
  const completed=[];
  try {
    for(const c of plan.changes){
      // Record before writing so even a partially written file is restored on failure.
      completed.push(c);fs.mkdirSync(path.dirname(c.target),{recursive:true});fs.writeFileSync(c.target,c.bytes);
      if(sha(fs.readFileSync(c.target))!==sha(c.bytes))throw Error('Installed file verification failed: '+c.relative);
    }
    receipt.state='installed';fs.writeFileSync(receiptFile,JSON.stringify(receipt,null,2));
  } catch(error) {
    for(const c of completed.reverse()){
      const record=receipt.files.find(r=>r.relative===c.relative);
      if(record.existed)fs.copyFileSync(safe(backup,'files/'+c.relative),c.target);
      else if(fs.existsSync(c.target))fs.unlinkSync(c.target);
    }
    receipt.state='rolled-back';fs.writeFileSync(receiptFile,JSON.stringify(receipt,null,2));throw error;
  }
  return {installed:true,files:plan.changes.length,backup,actions:40,costumes:3,dressingRoutes:6,memes:27,restartRequired:true};
}
export function restore(backup,{dshHome=process.env.DSH_HOME||path.join(os.homedir(),'.dsh')}={}) {
  dshHome=path.resolve(dshHome);backup=path.resolve(backup);
  const backupRoot=safe(dshHome,'xigua-lulu-backups');
  if(!inside(backupRoot,backup)||backup===backupRoot)throw Error('Backup must belong to this DSH home');
  const receipt=json(safe(backup,'receipt.json'));
  if(path.resolve(receipt.dshHome)!==dshHome||receipt.state!=='installed')throw Error('Invalid or already restored receipt');
  // Check every file before modifying anything; preserve changes made since installation.
  for(const record of receipt.files){
    const target=safe(dshHome,record.relative);
    if(!fs.existsSync(target)||sha(fs.readFileSync(target))!==record.after)throw Error('File changed after installation; restore stopped: '+record.relative);
    if(record.existed&&sha(fs.readFileSync(safe(backup,'files/'+record.relative)))!==record.before)throw Error('Backup checksum mismatch');
  }
  for(const record of [...receipt.files].reverse()){
    const target=safe(dshHome,record.relative);
    if(record.existed)fs.copyFileSync(safe(backup,'files/'+record.relative),target);
    else fs.unlinkSync(target); // Only a recorded, unchanged file created by this installer.
  }
  receipt.state='restored';fs.writeFileSync(path.join(backup,'receipt.json'),JSON.stringify(receipt,null,2));
  return {restored:true,restartRequired:true};
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
  try{
    const args=process.argv.slice(2),options={};let restoreDir=null,verify=false;
    for(let i=0;i<args.length;i++){
      if(args[i]==='--dry-run')options.dryRun=true;
      else if(args[i]==='--verify')verify=true;
      else if(['--dsh-home','--profile','--restore'].includes(args[i])){
        const key=args[i],value=args[++i];if(!value||value.startsWith('--'))throw Error('Missing option value');
        if(key==='--restore')restoreDir=value;else options[key==='--profile'?'profile':'dshHome']=value;
      }else throw Error('Unknown argument: '+args[i]);
    }
    const result=verify?(verifyPack(),{verified:true,actions:40,memes:27}):restoreDir?restore(restoreDir,options):install(options);
    console.log(JSON.stringify(result,null,2));
    if(result.restartRequired)console.log('请完全退出并重新打开 DeepSeek Harness，使新素材与朝向修复生效。');
  }catch(error){console.error(error.message);process.exitCode=1;}
}
