/* 西瓜噜噜：persistent three-costume desktop wardrobe. */
(() => {
  'use strict';
  const ALIASES = {"三球抛接": "look", "下五子棋": "busy", "东张西望": "look", "中秋赏月吃月饼": "sway", "优雅女仆舞": "sway", "余额-分文不剩": "angry", "余额-数金皱眉": "think", "余额-袋空如洗": "angry", "余额-金袋叮当": "celebrate", "余额-钱袋如常": "look", "余额-钱袋满溢": "celebrate", "偷吃零食被抓住": "sway", "写代码": "busy", "写福字": "busy", "凭空生花": "look", "动物环绕": "look", "原地专心玩魔方": "busy", "原地小憩沉眠": "sleep", "原地左转奔跑": "run", "原地敲击桌面互动": "busy", "原地漂浮踏步": "float", "原地跳跃抓碎头顶物品": "jump", "原地蹲下玩玩具汽车": "look", "原地重力下蹲压缩": "squat", "变鸽子": "look", "可爱宅舞": "disco", "吃Token": "sway", "吃冰淇淋融化": "sway", "吃午餐": "sway", "吃大闸蟹": "sway", "吃年糕": "sway", "吃早餐": "sway", "吃晚餐": "sway", "吃汤圆": "sway", "吃白饭": "sway", "吃粽子": "sway", "吃糖葫芦": "sway", "吃腊八粥": "sway", "吃西瓜": "sway", "吃重阳糕": "sway", "吃长寿面": "sway", "吃青团": "sway", "吃饺子": "sway", "吹气球": "look", "吹笛子": "look", "哈欠连天": "yawn", "堆雪人": "look", "大口吃零食": "sway", "女仆屈膝礼仪": "bow", "小幅度原地360度旋转展示": "look", "小提琴演奏": "look", "工作状态-原地踱步张望": "look", "工作状态-垂头叹气冒汗": "sad", "工作状态-忙碌点按": "busy", "工作状态-思考冒泡": "think", "工作状态-清点归档": "bow", "工作状态-雀跃庆祝": "celebrate", "待机呼吸休闲": "idle", "悠闲哼歌": "sway", "扑克魔术": "look", "打瞌睡被惊醒": "wake", "抽陀螺": "look", "拆礼物": "celebrate", "插茱萸赏菊": "look", "摇扇纳凉": "look", "撸猫": "look", "收红包": "celebrate", "放孔明灯": "float", "放河灯": "look", "放烟花": "celebrate", "放风筝": "float", "整体换装试色": "look", "是啊，吃什么": "sway", "晨间刷牙": "look", "涮火锅": "look", "深度思考碎碎念": "think", "点击回应-傲娇生气": "angry", "点击回应-元气挥手": "wave", "点击回应-害羞惊讶": "shy", "点击回应-开心跃动": "jump", "点击回应-挠痒咯咯笑": "giggle", "照镜子": "think", "玩水枪": "look", "玩游戏气急败坏": "angry", "用鲸鱼尾巴拍打地面": "look", "碎碎念-发呆碎碎念": "look", "碎碎念-对屏碎碎念": "look", "碎碎念-擦桌碎碎念": "look", "穿针乞巧": "look", "舞狮头": "sway", "荡秋千": "float", "萌化小幽灵": "float", "蓝鲸现世": "look", "蝴蝶蜜蜂环绕头顶开花": "look", "螃蟹走路": "walk", "被吓一跳": "surprise", "被落叶淹没": "look", "被鼠标拖拽悬空反馈": "drag", "装点圣诞树": "look", "讨糖南瓜灯": "look", "超大伸懒腰": "stretch", "踢毽子": "look", "轻快摇摆舞": "sway", "轻快记录": "busy", "骑木马": "look", "鲸鱼吐泡泡特效": "float", "西瓜噜-点头认可": "nod", "西瓜噜-摇头拒绝": "no", "西瓜噜-歪头眨眼": "wink", "西瓜噜-飞吻送心": "kiss", "西瓜噜-抱心心": "hug", "西瓜噜-拍手鼓励": "clap", "西瓜噜-举拳加油": "cheer", "西瓜噜-招手过来": "beckon", "西瓜噜-摊手耸肩": "shrug", "西瓜噜-瞪眼后仰": "surprise", "西瓜噜-打喷嚏": "sneeze", "西瓜噜-大口哈欠": "yawn", "西瓜噜-瞌睡惊醒": "wake", "西瓜噜-侧耳倾听": "listen", "西瓜噜-交替举手舞": "disco", "西瓜噜-扭腰摆胯": "twist", "西瓜噜-蹲起锻炼": "squat", "西瓜噜-单脚平衡": "balance", "西瓜噜-向前踢腿": "kick", "西瓜噜-抖抖甩水": "shakeoff", "西瓜噜-合手致谢": "thank", "西瓜噜-认真敬礼": "salute", "西瓜噜-隔空击掌": "highfive", "西瓜噜-捉迷藏探头": "peekaboo", "西瓜噜-轻声嘘嘘": "hush", "西瓜噜-送你小礼物": "gift", "西瓜噜-吃饱揉肚子": "bellyrub", "西瓜噜-抱抱自己": "selfhug", "西瓜噜-委屈擦眼泪": "sob", "西瓜噜-松口气拍拍胸": "relief", "西瓜噜-灵光一现": "eureka", "西瓜噜-抱杯喝果汁": "drink", "西瓜噜-啃一口西瓜": "melonbite", "西瓜噜-舔舔冰淇淋": "icecream", "西瓜噜-咔嚓吃饼干": "cookie", "西瓜噜-闻闻小花": "flower", "西瓜噜-翻书认真读": "readbook", "西瓜噜-记下小灵感": "notebook", "西瓜噜-放大镜找线索": "magnify", "西瓜噜-给你拍张照": "camera", "西瓜噜-望远镜看远方": "binoculars", "西瓜噜-热得扇扇风": "fan", "西瓜噜-撑伞躲小雨": "umbrella", "西瓜噜-给小苗浇水": "watering", "西瓜噜-扫扫小纸屑": "sweep", "西瓜噜-认真刷刷牙": "brush", "西瓜噜-拍拍铃鼓": "tambourine", "西瓜噜-摇摇沙锤": "maracas", "西瓜噜-咚咚敲小鼓": "drum", "西瓜噜-小小指挥家": "conduct", "西瓜噜-吹一段口琴": "harmonica", "西瓜噜-牵住小气球": "balloon", "西瓜噜-吹出小泡泡": "bubbles", "西瓜噜-追看小蝴蝶": "butterfly", "西瓜噜-接住小星星": "catchstar", "西瓜噜-拍两下皮球": "ball", "西瓜噜-左右练拳": "boxing", "西瓜噜-举举小哑铃": "dumbbell", "西瓜噜-左右压压腰": "sidebend", "西瓜噜-踮脚够星星": "tiptoe", "西瓜噜-左右滑步练习": "skater"};
  const MANUAL = '西瓜噜噜-换一条裤子';
  const COSTUMES = ['watermelon','orange','star'];
  const CHOICES = {'西瓜噜噜-换上西瓜裤':'watermelon','西瓜噜噜-换上橙色裤':'orange','西瓜噜噜-换上星星裤':'star'};
  const transitionName = (from,to) => from!=='star' && to!=='star' ? 'lulu-change-'+to : 'lulu-change-'+from+'-'+to;
  const states = new WeakMap();
  const delay = () => (180 + Math.random() * 120) * 1000;
  const enabled = pet => pet.assetRoot === 'main' && /^西瓜/.test(pet.pet?.name || '');
  // Fresh URLs for this revision; preserve user data and other pets' caches.
  function refreshMediaRevision(pet) {
    if(typeof HTMLMediaElement==='undefined')return;
    const descriptor=Object.getOwnPropertyDescriptor(HTMLMediaElement.prototype,'src');
    if(!descriptor?.get || !descriptor?.set)return;
    for(const video of [pet.videoA,pet.videoB]) {
      if(!video || video.__luluMediaRevision)continue;
      Object.defineProperty(video,'src',{configurable:true,
        get(){return descriptor.get.call(this);},
        set(value){const url=String(value);descriptor.set.call(this,url.endsWith('.webm')?url+'?lulu-arm=20261031-solid1':url);}
      });
      video.__luluMediaRevision=true;
    }
  }
  const key = pet => 'xigua-lulu-wardrobe-v1:' + pet.pet.id;
  function state(pet) {
    if (!states.has(pet)) {
      let costume = 'watermelon';
      try { const stored=localStorage.getItem(key(pet));if(COSTUMES.includes(stored))costume=stored; } catch (_) {}
      states.set(pet, { costume, active: null, nextAt: Date.now() + delay() });
    }
    return states.get(pet);
  }
  function save(pet, s) { try { localStorage.setItem(key(pet), s.costume); } catch (_) {} }
  function front(pet) { return pet.front === 0 ? pet.videoA : pet.videoB; }
  function showing(pet, name) { const video=front(pet);return !!video && String(video.currentSrc || video.src || '').includes(name); }
  function settleInterruption(pet, s) {
    if (!s.active) return;
    s.costume = showing(pet,s.active.name) && front(pet).currentTime >= 6.6 ? s.active.to : s.active.from;
    s.active = null;s.nextAt=Date.now()+delay();save(pet,s);
  }
  const originalSwitch=PetSprite.prototype.switchTo;
  const originalPlay=PetSprite.prototype.playOnce;
  const originalIdle=PetSprite.prototype.playIdle;
  const originalEnded=PetSprite.prototype.handleEnded;
  const originalMenu=PetSprite.prototype.onContextMenu;
  function start(pet,requested) {
    const s=state(pet);
    if (s.active) return;
    const to=requested || COSTUMES[(COSTUMES.indexOf(s.costume)+1)%COSTUMES.length];
    if(!COSTUMES.includes(to) || to===s.costume)return;
    s.active={from:s.costume,to,name:transitionName(s.costume,to)};
    pet.stopMove();
    originalPlay.call(pet,s.active.name);
  }
  PetSprite.prototype.switchTo=function(next,once) {
    if(!enabled(this))return originalSwitch.call(this,next,once);
    refreshMediaRevision(this);
    const s=state(this);
    if(s.active && next!==s.active.name)settleInterruption(this,s);
    const asset=s.costume!=='watermelon' && ALIASES[next] ? 'lulu-'+s.costume+'-'+ALIASES[next] : next;
    return originalSwitch.call(this,asset,once);
  };
  PetSprite.prototype.playOnce=function(name) {
    if(enabled(this) && name===MANUAL){start(this);return;}
    if(enabled(this) && CHOICES[name]){start(this,CHOICES[name]);return;}
    return originalPlay.call(this,name);
  };
  PetSprite.prototype.playIdle=function() {
    if(enabled(this)) {
      const s=state(this);
      const busy=this.dragState?.active || this.dragState?.dragging || this.throwRef || this.menuOpen || this.chatOpen || this.pending ||
        (this.workState && !['success','error'].includes(this.workState));
      if(!s.active && !busy && Date.now()>=s.nextAt){start(this);return;}
    }
    return originalIdle.call(this);
  };
  PetSprite.prototype.handleEnded=function() {
    if(enabled(this)) {
      const s=state(this);
      if(s.active && this.anim===s.active.name) {
        s.costume=showing(this,s.active.name)?s.active.to:s.active.from;
        s.active=null;s.nextAt=Date.now()+delay();save(this,s);
        if(this.dragState?.active)return;
        if(this.resumeWorkStatusAnim())return;
        this.playOnce(this.animations.idle[0]);return;
      }
    }
    return originalEnded.call(this);
  };
  PetSprite.prototype.onContextMenu=function(event) {
    if(!enabled(this))return originalMenu.call(this,event);
    const original=this.animations;
    this.animations={...original,categories:[...original.categories,{id:'换装',weight:0,actions:[MANUAL,...Object.keys(CHOICES)]}]};
    try { return originalMenu.call(this,event); } finally { this.animations=original; }
  };
  window.__luluWardrobe={version:2,manualAction:MANUAL,choices:CHOICES,costumes:COSTUMES,snapshot:pet=>({...state(pet)}),switchNow:(pet,to)=>start(pet,to)};
})();
