// Offline Chromium smoke test. EDGE_BIN can point to another Chromium browser.
import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {mkdtemp, readFile, rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import path from 'node:path';
import {once} from 'node:events';

const profile=await mkdtemp(path.join(tmpdir(),'frog-demo-'));
const browser=spawn(process.env.EDGE_BIN || 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
  ['--headless','--disable-extensions','--no-first-run','--disable-gpu','--remote-debugging-pipe',`--user-data-dir=${profile}`],
  {stdio:['ignore','ignore','ignore','pipe','pipe']});
const pending=new Map();let id=0,buffer='';const errors=[];
browser.stdio[4].setEncoding('utf8').on('data',s=>{buffer+=s;let i;
  while((i=buffer.indexOf('\0'))>=0){const m=JSON.parse(buffer.slice(0,i));buffer=buffer.slice(i+1);
    if(m.method==='Runtime.exceptionThrown')errors.push(m.params.exceptionDetails.text);
    if(m.id&&pending.has(m.id)){const [resolve,reject]=pending.get(m.id);pending.delete(m.id);m.error?reject(Error(m.error.message)):resolve(m.result)}
  }
});
function call(method,params={},sessionId){return new Promise((resolve,reject)=>{
  pending.set(++id,[resolve,reject]);browser.stdio[3].write(JSON.stringify({id,method,params,sessionId})+'\0');
})}
const timer=setTimeout(()=>{const error=Error('Chromium smoke test timed out');for(const [,reject] of pending.values())reject(error);pending.clear();browser.kill()},90000);
try{
  const {targetId}=await call('Target.createTarget',{url:'about:blank'});
  const {sessionId}=await call('Target.attachToTarget',{targetId,flatten:true});
  const cmd=(method,params)=>call(method,params,sessionId);
  await cmd('Runtime.enable'); await cmd('Page.navigate',{url:new URL('../demo/index.html',import.meta.url).href});
  const verify=async expression=>{const r=await cmd('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});assert.ok(!r.exceptionDetails,JSON.stringify(r.exceptionDetails));return r.result.value};
  await verify(`new Promise((resolve,reject)=>{const until=Date.now()+5000;function ready(){if(document.querySelectorAll('#roster button').length===12)resolve(true);else if(Date.now()>until)reject(Error('Roster missing'));else setTimeout(ready,40)}ready()})`);
  const result=await verify(`(async()=>{
    if(playing)$('play').click();await Promise.all([...document.images].map(i=>i.decode()));
    let clips=0,images=0;for(const b of $('roster').children){b.click();for(const o of $('clip').options){$('clip').value=o.value;$('clip').onchange();await Promise.all(loaded.map(i=>i.decode()));if(loaded.some(i=>i.naturalWidth!==clip.w||i.naturalHeight!==clip.h||i.naturalWidth<250))throw Error('Frame resolution: '+b.value+'/'+o.value);images+=loaded.length;$('step').click();if(frame!==1||playing||$('frame-link').href!==loaded[1].src)throw Error('Frame control');clips++}}
    $('rate').value='0.5';$('rate').onchange();if(!$('readout').textContent.includes(String(+(clip.fps/2).toFixed(2))+' кадр/с'))throw Error('Preview speed');
    $('light').click();if(!document.querySelector('.plate.light'))throw Error('Light background');
    for(const b of $('scenes').children){b.click();const paused=['level_up','shop'].includes(b.value);for(const checked of [false,true]){$('motion').checked=checked;showScene();await $('scene').decode();if($('scene').naturalWidth!==1280||$('scene').naturalHeight!==720)throw Error('Wrong capture resolution');if($('motion').disabled!==paused||$('scene').src.endsWith('-motion.webp')!==(!paused&&checked)||$('path').textContent!=='game/'+b.value+'.tscn')throw Error('Wrong view: '+b.value)}}
    for(const o of $('shelf').options){$('shelf').value=o.value;$('shelf').onchange();await $('sheet').decode()}
    history.replaceState(null,'','#view-shop');viewFromLink();if(sceneKey!=='shop'||!$('motion').disabled)throw Error('Direct scene link');
    history.replaceState(null,'','#sheet-08_terrain');viewFromLink();if($('shelf').value!=='08_terrain')throw Error('Direct atlas link');
    return {actors:$('actor').length,clips,images,views:[...$('scenes').children].map(b=>b.value),sheets:$('shelf').length};})()`);
  assert.equal(result.actors,12);assert.equal(result.clips,62);assert.equal(result.images,248);assert.deepEqual(result.views,['arena','arena_edge','arena_wave','level_up','shop','gallery']);assert.ok(result.sheets>=15);
  const catalog=await verify('CAST');
  const manifest=JSON.parse(await readFile(new URL('../assets/cast/manifest.json',import.meta.url),'utf8'));
  for(const [id,actor] of Object.entries(manifest.characters)) for(const [action,sequence] of Object.entries(actor.animations)){
    const clip=catalog[id][action];assert.equal(clip.fps,sequence.fps);
    // Repairs may add transparent canvas, but must not shrink the supplied cells.
    const [width,height]=id.startsWith('boss_')?[264,310]:id.startsWith('ghost_')?[400,400]:[627,627];
    assert.ok(clip.w>=width&&clip.h>=height,`${id}/${action}: reduced frame`);
    for(const [n,frame] of sequence.frames.entries()){
      const [src,published]=await Promise.all([readFile(new URL('../'+frame.path.replace('res://',''),import.meta.url)),readFile(new URL('../demo/media/'+clip.urls[n],import.meta.url))]);
      assert.ok(src.equals(published),`${id}/${action}/${n+1}: export changed native PNG`);
    }
  }
  await cmd('Emulation.setDeviceMetricsOverride',{width:375,height:812,deviceScaleFactor:2,mobile:true});
  assert.equal(await verify('document.documentElement.scrollWidth<=innerWidth'),true);
  assert.equal(await verify(`(async()=>{choose('frog_knight');await $('sprite').decode();let r=$('sprite').getBoundingClientRect();return r.width>0&&r.height>0&&r.right<=innerWidth})()`),true);
  assert.deepEqual(errors,[]);console.log('PASS',result,'offline desktop + mobile');
}finally{clearTimeout(timer);if(browser.exitCode===null&&browser.signalCode===null){const exit=once(browser,'exit');browser.kill();await exit}await rm(profile,{recursive:true,force:true,maxRetries:6,retryDelay:150})}
