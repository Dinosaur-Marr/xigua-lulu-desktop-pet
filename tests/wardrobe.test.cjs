const fs=require('fs'),vm=require('vm'),assert=require('assert/strict'),path=require('path');
const out=path.resolve(__dirname,'..');
const aliases=JSON.parse(fs.readFileSync(path.join(out,'config/mapping.json'),'utf8'));
const code=fs.readFileSync(path.join(out,'runtime/lulu-wardrobe.js'),'utf8');
let now=0,id=0;const saved=new Map();
class PetSprite {
 constructor(name='西瓜噜',costume='watermelon'){this.pet={id:String(id++),name};saved.set('xigua-lulu-wardrobe-v1:'+this.pet.id,costume);Object.assign(this,{assetRoot:'main',front:0,animations:{idle:['待机呼吸休闲'],categories:[]},dragState:{active:false},videoA:{src:'',currentTime:0},videoB:{src:'',currentTime:0}});}
 switchTo(name,once){this.videoA.src=name+'.webm';this.videoA.currentTime=0;this.loaded=name;this.once=once;}
 playOnce(name){this.anim=name;this.switchTo(name,true);}
 playIdle(){this.playOnce(this.animations.idle[0]);}
 handleEnded(){this.playIdle();}
 stopMove(){this.moveRef=null;this.pendingMove=null;}
 resumeWorkStatusAnim(){return false;}
 onContextMenu(){this.menuTree=structuredClone(this.animations);}
}
const context={PetSprite,window:{},Date:{now:()=>now},Math:Object.assign(Object.create(Math),{random:()=>0}),localStorage:{getItem:k=>saved.get(k),setItem:(k,v)=>saved.set(k,v)},WeakMap};
vm.runInNewContext(code,context);const api=context.window.__luluWardrobe;
const costumes=['watermelon','orange','star'];
const route=(from,to)=>from!=='star'&&to!=='star'?'lulu-change-'+to:'lulu-change-'+from+'-'+to;
const asset=(costume,alias)=>costume==='watermelon'?alias:'lulu-'+costume+'-'+aliases[alias];
for(const from of costumes){
 const p=new PetSprite('西瓜噜',from);p.playIdle();assert.equal(p.loaded,asset(from,'待机呼吸休闲'));
 for(const [alias,kind] of Object.entries(aliases)){p.playOnce(alias);assert.equal(p.loaded,asset(from,alias));assert.equal(p.anim,alias);}
 for(const to of costumes){
  const q=new PetSprite('西瓜噜',from);q.playIdle();api.switchNow(q,to);
  if(from===to){assert.equal(api.snapshot(q).active,null);continue;}
  assert.equal(q.loaded,route(from,to));q.handleEnded();assert.equal(api.snapshot(q).costume,to);assert.equal(q.loaded,asset(to,'待机呼吸休闲'));
  assert.equal(saved.get('xigua-lulu-wardrobe-v1:'+q.pet.id),to);
  for(const time of [1,8]){
   const r=new PetSprite('西瓜噜',from);api.switchNow(r,to);r.videoA.currentTime=time;r.playOnce('点击回应-元气挥手');
   assert.equal(r.loaded,asset(time<6.6?from:to,'点击回应-元气挥手'));
  }
  const failure=new PetSprite('西瓜噜',from);api.switchNow(failure,to);failure.videoA.src='previous.webm';failure.handleEnded();assert.equal(api.snapshot(failure).costume,from);
 }
}
const p=new PetSprite();p.playIdle();
for(const to of ['orange','star','watermelon']){now+=300001;p.playIdle();assert.equal(api.snapshot(p).active.to,to);p.handleEnded();}
for(const to of ['orange','star','watermelon']){p.playOnce(api.manualAction);assert.equal(api.snapshot(p).active.to,to);p.handleEnded();}
for(const [choice,to] of Object.entries(api.choices)){p.playOnce(choice);if(api.snapshot(p).active)p.handleEnded();assert.equal(api.snapshot(p).costume,to);}
p.onContextMenu({});assert.equal(p.animations.categories.length,0);assert.equal(p.menuTree.categories[0].actions.length,4);
for(const flag of ['menuOpen','chatOpen','pending','throwRef']){now+=300001;p[flag]=true;p.playIdle();assert.equal(api.snapshot(p).active,null);p[flag]=false;}
p.workState='thinking';p.playIdle();assert.equal(api.snapshot(p).active,null);p.workState=null;
p.dragState.active=true;p.playIdle();assert.equal(api.snapshot(p).active,null);p.dragState.active=false;
const other=new PetSprite('another pet');other.playIdle();now+=400000;other.playIdle();assert.equal(other.loaded,'待机呼吸休闲');
const invalid=new PetSprite('西瓜噜','unknown');invalid.playIdle();assert.equal(api.snapshot(invalid).costume,'watermelon');
console.log('Three-costume checks passed: six routes, 441 alias mappings, persistence, interruption and menu guards.');
