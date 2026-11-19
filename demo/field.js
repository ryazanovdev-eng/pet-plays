'use strict';
const $ = id => document.getElementById(id);
const shelves={ '01_props':'Декорации','02_wide_crypts':'Склепы','03_fences':'Ограды','04_pickups':'Находки','05_ground_overlays':'Переходы грунта','06_vegetation':'Растения','07_road_tiles_concept':'Дорожные тайлы','08_terrain':'Покрытия арены','09_hud':'HUD','10_runtime_layers':'Слои интерфейса','11_standalone_sprites':'Элементы интерфейса','12_levelup':'Повышение уровня','13_shop':'Магазин','14_defeat':'Поражение','15_portraits':'Портреты'};
for(const [key,title] of Object.entries(shelves))$('shelf').add(new Option(`${key.slice(0,2)} · ${title}`,key));
$('shelf').onchange=()=>{const key=$('shelf').value;$('sheet').alt=shelves[key];$('sheet-link').href=$('sheet').src=`media/${key}.webp`};
const captions = {arena:'Центр кладбища: границы арены остаются за кадром.',arena_edge:'Край той же карты: по другую сторону ограды кладбище продолжается.',gallery:'Все двенадцать персонажей в одной сцене Godot.'};
let sceneKey='arena';
function showScene(){const key=sceneKey;
  $('large').href=$('scene').src=`media/${key}${$('motion').checked?'-motion':''}.webp`; $('scene').alt=$('caption').textContent=captions[key]; $('path').textContent=`game/${key}.tscn`;
}
$('motion').onchange=showScene;
for(const button of $('scenes').children) button.onclick=()=>{
  sceneKey=button.value;
  for(const b of $('scenes').children) b.setAttribute('aria-pressed',b===button);
  showScene();
};
const names={frog_knight:'Рыцарь-лягушка',ghost_blue:'Синий призрак',ghost_green:'Зелёный призрак',ghost_purple:'Фиолетовый призрак',skeleton_bone:'Костяной скелет',skeleton_lavender:'Лавандовый скелет',skeleton_turquoise:'Бирюзовый скелет',zombie_blue:'Синий зомби',zombie_green:'Зелёный зомби',zombie_pink:'Розовый зомби',boss_bone_king:'Костяной король',boss_rotten_giant:'Гнилой исполин'};
const actions={idle:'Покой',walk:'Ходьба',attack:'Атака',attack_1:'Атака I',attack_2:'Атака II',attack1:'Атака I',attack2:'Атака II',hurt:'Получение урона',death:'Гибель',dead:'Гибель'};
let frame=0,time=0,playing=!matchMedia('(prefers-reduced-motion: reduce)').matches,clip,loaded=[];
function render(){
  const src=loaded[frame].src;
  if($('sprite').src!==src)$('sprite').src=src;
  $('frame-link').href=src;
  $('readout').textContent=`${frame+1} / ${clip.urls.length} · ${+(clip.fps*Number($('rate').value)).toFixed(2)} кадр/с · ${clip.w}×${clip.h}`;
  $('play').textContent=playing?'Пауза':'Играть';
}
function chooseClip(){clip=CAST[$('actor').value][$('clip').value];frame=time=0;
  $('sprite').style.aspectRatio=`${clip.w}/${clip.h}`;
  loaded=clip.urls.map(url=>{const image=new Image();image.src=`media/${url}`;return image});render();}
function choose(id){$('actor').value=id;$('clip').replaceChildren();for(const key of ['idle','walk','attack','attack1','attack2','hurt','death'])if(CAST[id][key])$('clip').add(new Option(actions[key],key));$('clip').value='idle';for(const b of $('roster').children)b.setAttribute('aria-pressed',b.value===id);chooseClip()}
for(const id of Object.keys(names)){
  $('actor').add(new Option(names[id],id));
  const b=document.createElement('button'),thumb=new Image();thumb.width=88;thumb.height=72;thumb.style.objectFit='contain';thumb.alt='';thumb.src=`media/${id}-portrait.webp`;b.value=id;b.append(thumb,document.createTextNode(names[id]));b.onclick=()=>choose(id);$('roster').append(b);
}
$('actor').onchange=e=>choose(e.target.value);$('clip').onchange=chooseClip;
$('rate').onchange=render;
$('light').onchange=()=>document.querySelector('.plate').classList.toggle('light',$('light').checked);
$('play').onclick=()=>{playing=!playing;if(playing&&frame===clip.durations.length-1&&!$('repeat').checked)frame=0;time=0;render()};
$('step').onclick=()=>{playing=false;frame=(frame+1)%clip.durations.length;time=0;render()};
choose('frog_knight');let previous=0;
function tick(now){if(playing&&loaded.every(i=>i.complete&&i.naturalWidth)){time+=Math.min(100,now-previous)*Number($('rate').value);if(time>=1000*clip.durations[frame]/clip.fps){time-=1000*clip.durations[frame]/clip.fps;if(frame+1===clip.durations.length&&!$('repeat').checked){playing=false;time=0}else frame=(frame+1)%clip.durations.length;render()}}previous=now;requestAnimationFrame(tick)}requestAnimationFrame(tick);
