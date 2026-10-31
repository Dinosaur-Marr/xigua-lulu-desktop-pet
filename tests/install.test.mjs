import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import {ROOT,verifyPack,parseJsonc,install,restore,planInstall} from '../install.mjs';
const read=p=>JSON.parse(fs.readFileSync(p,'utf8'));
function fixture(t,version='0.3.7'){
 const home=fs.mkdtempSync(path.join(os.tmpdir(),'lulu-test-'));
 t.after(()=>fs.rmSync(home,{recursive:true,force:true}));
 const plugin=path.join(home,'profiles/desktop/node_modules/dsh-pet');fs.mkdirSync(plugin,{recursive:true});
 fs.writeFileSync(path.join(plugin,'package.json'),JSON.stringify({name:'dsh-pet',version}));
 for(const p of read(path.join(ROOT,'config/direction-patches.json'))){const f=path.join(plugin,p.file);fs.mkdirSync(path.dirname(f),{recursive:true});fs.writeFileSync(f,p.before);}
 fs.writeFileSync(path.join(plugin,'runtime/electron-helper/index.html'),'<script src="./sprite.js"></script>');
 fs.mkdirSync(path.join(home,'dsh-pet'),{recursive:true});
 const cfg='// preserve settings\n{"chatModel":{"provider":"my-provider","model":"my-model"},"custom":"https://example.com/a//b", "pets":[{"id":"custom-id","size":555,"display":"web","name":"old"}],}\n';
 fs.writeFileSync(path.join(home,'dsh-pet/main-config.jsonc'),cfg);
 fs.writeFileSync(path.join(home,'dsh-pet/memory.json'),'PRIVATE-MEMORY');
 return {home,plugin,cfg};
}
test('package has 60 unique clips, 147 aliases, 27 memes; hashes match',()=>{verifyPack();});
test('JSONC handles comments, quoted URLs and trailing commas',()=>{
 assert.deepEqual(parseJsonc('{/*x*/"url":"https://a//b", "a":[1,2,],}'),{url:'https://a//b',a:[1,2]});
 assert.throws(()=>parseJsonc('{/* incomplete'));
});
test('dry run, install, idempotence and exact restoration preserve user data',t=>{
 const {home,plugin,cfg}=fixture(t);
 const dry=install({dshHome:home,dryRun:true});assert.equal(dry.dryRun,true);assert(!fs.existsSync(path.join(home,'xigua-lulu-backups')));
 const first=install({dshHome:home});
 const config=read(path.join(home,'dsh-pet/main-config.jsonc'));
 assert.equal(config.pets[0].size,555);assert.equal(config.pets[0].id,'custom-id');assert.equal(config.pets[0].display,'web');
 assert.equal(config.chatModel.provider,'my-provider');assert.equal(config.custom,'https://example.com/a//b');
 assert.equal(config.pets[0].name,'西瓜噜噜');assert.equal(config.animations.events.workStatus.length,6);
 assert.equal(fs.readdirSync(path.join(home,'dsh-pet/main-animation/webm')).length,273);
 assert.equal(fs.readdirSync(path.join(home,'dsh-pet/memes')).length,27);
 for(const p of read(path.join(ROOT,'config/direction-patches.json')))assert.equal(fs.readFileSync(path.join(plugin,p.file),'utf8'),p.after);
 assert(fs.readFileSync(path.join(plugin,'runtime/electron-helper/index.html'),'utf8').includes('lulu-wardrobe.js'));
 assert(fs.existsSync(path.join(home,'dsh-pet/main-animation/webm/lulu-star-idle.webm')));
 const second=install({dshHome:home});restore(second.backup,{dshHome:home});restore(first.backup,{dshHome:home});
 assert.equal(fs.readFileSync(path.join(home,'dsh-pet/main-config.jsonc'),'utf8'),cfg);
 assert.equal(fs.readFileSync(path.join(home,'dsh-pet/memory.json'),'utf8'),'PRIVATE-MEMORY');
 assert.equal(fs.readdirSync(path.join(home,'dsh-pet/main-animation/webm')).length,0);
});
test('unsupported plugin fails before writes',t=>{const {home,cfg}=fixture(t,'0.9.9');assert.throws(()=>install({dshHome:home}),/supports/);assert(!fs.existsSync(path.join(home,'xigua-lulu-backups')));assert.equal(fs.readFileSync(path.join(home,'dsh-pet/main-config.jsonc'),'utf8'),cfg);});
test('unknown patch and invalid profile fail before writes',t=>{const {home,plugin}=fixture(t);assert.throws(()=>planInstall({dshHome:home,profile:'../bad'}));fs.writeFileSync(path.join(plugin,'lib/client.js'),'unknown code');assert.throws(()=>install({dshHome:home}),/Unsupported movement/);assert(!fs.existsSync(path.join(home,'xigua-lulu-backups')));});
test('restore refuses to overwrite edits made after install',t=>{const {home}=fixture(t);const result=install({dshHome:home});const file=path.join(home,'dsh-pet/main-config.jsonc');fs.appendFileSync(file,'\n');assert.throws(()=>restore(result.backup,{dshHome:home}),/changed after installation/);assert.equal(fs.readdirSync(path.join(home,'dsh-pet/main-animation/webm')).length,273);});
test('install refuses a symlink to a different directory',t=>{const {home}=fixture(t);const external=fs.mkdtempSync(path.join(os.tmpdir(),'lulu-external-'));t.after(()=>fs.rmSync(external,{recursive:true,force:true}));try{fs.symlinkSync(external,path.join(home,'dsh-pet/memes'),process.platform==='win32'?'junction':'dir');}catch(error){if(error.code==='EPERM'){t.skip('This environment does not permit creating junctions');return;}throw error;}assert.throws(()=>install({dshHome:home}),/Symlink/);assert.equal(fs.readdirSync(external).length,0);});

test('unknown wardrobe entry fails before writes',t=>{const {home,plugin}=fixture(t);fs.writeFileSync(path.join(plugin,'runtime/electron-helper/index.html'),'unsupported');assert.throws(()=>install({dshHome:home}),/Unsupported desktop/);assert(!fs.existsSync(path.join(home,'xigua-lulu-backups')));});
