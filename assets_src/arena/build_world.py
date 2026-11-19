"""Bake the diorama into editable, ordinary Godot nodes; not part of runtime."""
from collections import defaultdict
from functools import lru_cache
from math import sin, cos, pi, hypot, atan2
from random import Random
from PIL import Image, ImageDraw, ImageFilter
from build_ground import ROOT, OUT, WALL, SIZE, ROUTES, curve

GAME=ROOT/'game/arena_parts'; ENV='assets/environment/'; COURT='assets/arena/court/'
R=Random(481); OCC=[]; ACTORS=[]

def num(n): return f'{n:.5f}'.rstrip('0').rstrip('.') or '0'
def v(x,y):return f'Vector2({num(x)}, {num(y)})'
def title(s):return ''.join(x.capitalize() for x in s.split('_'))

class Scene:
    def __init__(self,name,kind='Node2D',props=''):
        self.paths={};self.sub=[];self.nodes=[]; self.count=defaultdict(int)
        self.node(name,kind,None,props)
    def node(self,name,kind,parent='.',props='',instance=None):
        header=f'[node name="{name}"'; header+=(f' type="{kind}"' if kind else '')+(f' parent="{parent}"' if parent else '')
        if instance:header+=f' instance={self.ref(instance)}'
        self.nodes.append(header+']'+ ('\n'+props if props else ''));return name
    def unique(self,key):
        self.count[key]+=1;return key+str(self.count[key]) if self.count[key]>1 else key
    def ref(self,path):
        if path not in self.paths:
            assert (ROOT/path).exists(),path
            self.paths[path]='r'+str(len(self.paths)+1)
        return f'ExtResource("{self.paths[path]}")'
    def save(self,path):
        refs=[f'[ext_resource type="{"PackedScene" if p.endswith(".tscn") else "Texture2D"}" path="res://{p}" id="{i}"]' for p,i in self.paths.items()]
        path.write_text('\n\n'.join(['[gd_scene format=3]','\n'.join(refs),*self.sub,*self.nodes])+'\n',encoding='utf8')

@lru_cache(None)
def size(path):
    with Image.open(ROOT/path) as im:return im.size

def sprite(scene,name,path,x,y,sx=1,sy=None,parent='.',offset=None,extra=''):
    sy=sx if sy is None else sy
    props=f'position = {v(x,y)}\nscale = {v(sx,sy)}\ntexture = {scene.ref(path)}'
    if offset:props+=f'\ncentered = false\noffset = {v(*offset)}'
    return scene.node(scene.unique(name),'Sprite2D',parent,props+extra)

def contact_texture():
    im=Image.new('RGBA',(120,48));d=ImageDraw.Draw(im)
    for i in range(18):d.ellipse((4+i*1.8,3+i*.68,116-i*1.8,45-i*.68),fill=(38,24,37,8+i*6))
    im.filter(ImageFilter.GaussianBlur(2)).save(OUT/'contact.png')

w=Scene('VesperCourt');sort='y_sort_enabled = true';w.node('Depth','Node2D',props=sort)
def group(name):w.node(name,'Node2D','Depth',sort);return 'Depth/'+name

def prop(parent,kind,x,y,height,flip=False,shadow=True,sub='props',reserve=True):
    path=ENV+sub+'/'+kind+'.png'; a,b=size(path); k=height/b
    if shadow:sprite(w,'Shade',COURT+'contact.png',x,y-2,min(height*.88,a*k*.9)/120,max(9,height*.13)/48,parent,extra='\nz_index = -1')
    sprite(w,title(kind),path,x,y,-k if flip else k,k,parent,offset=(-a/2,-b+3))
    if reserve:OCC.append((x,y,min(a*k*.47,110),height*.46))

def pickup(parent,id,x,y,h):prop(parent,id,x,y,h,sub='pickups')
def actor(parent,id,x,y,m,clip='idle',frame=0,flip=False,play=False):
    ACTORS.append((x,y,id));OCC.append((x,y,82,55));name=w.unique(title(id)+'Mark')
    sprite(w,'Footfall',COURT+'contact.png',x,y,min(135,55*m)/120,18*m/48,parent,extra='\nz_index = -1')
    w.node(name,'Node2D',parent,f'position = {v(x,y)}\nscale = {v(m,m)}')
    w.node(title(id),None,parent+'/'+name,f'animation = &"{clip}"\nautoplay = "{clip if play else ""}"\nframe = {frame}\nflip_h = {str(flip).lower()}',f'game/cast/{id}.tscn')

CENTER=(2390,1700); EDGE=(3450,640); HERO_C=(2320,1768); HERO_E=(3438,720)

def build_world():
    # Ground is not downsampled to a thumbnail: each pixel is a world unit at zoom 1.
    w.node('Terrain','Node2D',props='z_index = -3')
    for row in range(2):
        for col in range(2):sprite(w,'Quadrant',COURT+f'ground_{row}{col}.jpg',col*2432,row*1728,parent='Terrain',offset=(0,0))
    p=group('MeridianCourt');
    for b in [('crypt_small_glowing',1890,1515,152),('brazier',2010,1518,68),('grave_round',1830,1558,68),('candle_cluster',1947,1543,31),('twisted_tree',2870,1510,182),('skull_pile',2785,1520,42),('hanging_lantern',1880,1872,121),('stone_altar',2672,1995,79),('candle_cluster',2605,2010,32),('angel_statue',2975,1930,139),('grave_cracked',2080,2020,85),('open_grave',2780,1420,64),('red_mushrooms',2810,1555,39)]:prop(p,*b)
    for b in [('skeleton_lavender',2130,1598,1.19,'walk',1,False,True),('ghost_blue',2018,1740,1.13,'idle',1),('zombie_blue',2240,1970,1.16,'walk',2),('boss_rotten_giant',2632,1775,1.30,'attack1',1,True),('skeleton_turquoise',2830,1877,1.23,'walk',0,True),('ghost_purple',2490,1513,1.10,'walk',2,True,True)]:actor(p,*b)
    for b in [('health_potion',2125,1814,39),('speed_potion',2755,1660,38),('bone',2214,1690,21),('bone',2460,1876,24),('bone',2430,1912,18)]:pickup(p,*b)
    p=group('LamplighterWalk');
    for b in [('wagon',2970,752,117),('coffin',3040,795,51),('signpost',3100,668,71),('grave_celtic',3650,908,82),('red_mushrooms',3704,907,39),('candle_cluster',3625,918,28),('twisted_tree',3878,731,172),('stone_cluster',3814,736,34),('open_grave',3190,958,69),('hanging_lantern',2864,873,113),('skull_pile',2955,794,34),('stone_altar',3020,543,57)]:prop(p,*b)
    for b in [('skeleton_bone',3255,667,1.17,'walk',2,False,True),('zombie_pink',3604,755,1.26,'hurt',1,True),('ghost_green',3730,610,1.17,'idle',2,True,True),('skeleton_turquoise',3350,945,1.17,'walk',3),('zombie_green',3055,880,1.13,'walk',1)]:actor(p,*b)
    for b in [('speed_potion',3230,805,40),('health_potion',3645,622,41),('bone',3515,853,23),('bone',3160,716,22)]:pickup(p,*b)
    p=group('BeyondTheIron');
    prop(p,'wide_stained_glass_mausoleum',3375,397,175,sub='wide_crypts')
    for b in [('twisted_tree',3095,395,159),('angel_statue',3635,415,104),('grave_round',2910,377,60),('grave_cracked',2966,360,62),('grave_celtic',3770,332,76),('brazier',3252,398,62),('brazier',3490,403,62),('candle_cluster',3542,384,31),('grave_cracked',3910,421,78),('grave_round',4005,461,73),('twisted_tree',4125,568,174),('stone_cluster',4000,606,43),('hanging_lantern',2915,316,99)]:prop(p,*b)
    # Outlying districts are actual placements, not duplicates of either photographed section.
    sites=[('WestReliquary',1190,1040,'wide_domed_mausoleum',('angel_statue','grave_round','grave_celtic','brazier')),('CandleOrchard',1300,2420,'crypt_small_closed',('twisted_tree','candle_cluster','hanging_lantern','grave_round')),('AshenQuarry',3010,2310,'wide_skull_mausoleum',('obelisk','skull_pile','grave_cracked','stone_cluster')),('PilgrimSteps',3230,2600,'wide_statue_mausoleum',('angel_statue','stone_altar','brazier','stone_cluster')),('ThornGarden',2020,780,'twisted_tree',('thorn_brambles','poison_puddle','bare_bush','red_mushrooms')),('WestBarrows',820,1650,'crypt_small_glowing',('grave_celtic','grave_round','grave_cracked','skull_pile')),('EastBarrows',4110,1680,'crypt_small_closed',('grave_celtic','coffin','grave_round','candle_cluster')),('FuneralLanding',2260,2730,'wagon',('coffin','open_grave','hanging_lantern','bone_pile'))]
    for name,x,y,lm,kinds in sites:
        p=group(name);prop(p,lm,x,y,168,sub='wide_crypts' if lm.startswith('wide_') else 'props')
        for j,(ox,oy,h) in enumerate([(-170,-35,86),(135,28,57),(-190,120,71),(188,90,54),(-255,85,63),(260,-35,76),(152,145,62),(-115,171,75)]):prop(p,kinds[j%4],x+ox,y+oy,h,j%3==0)
    # Out-of-bounds continuation around every side, not just the north overlook.
    for x,y in [(440,1000),(720,390),(1580,250),(2250,310),(4670,1550),(4260,2650),(3700,3200),(2410,3170),(1180,3180),(480,2420)]:
        p='Depth/BeyondTheIron';prop(p,'twisted_tree',x,y,R.randint(135,190));prop(p,'grave_cracked',x+98,y+21,66);prop(p,'stone_cluster',x-86,y+26,39)
    build_perimeter();plant()
    w.save(GAME/'world.tscn')

def build_perimeter():
    p=group('IronProcession');w.node('Perimeter','StaticBody2D',props='collision_layer = 1\ncollision_mask = 1')
    for i,(a,b) in enumerate(zip(WALL,WALL[1:]+WALL[:1])):
        dx,dy=b[0]-a[0],b[1]-a[1];length=hypot(dx,dy)
        shp=f'Boundary{i}';w.sub.append(f'[sub_resource type="RectangleShape2D" id="{shp}"]\nsize = {v(length+16,18)}')
        w.node(shp,'CollisionShape2D','Perimeter',f'position = {v((a[0]+b[0])/2,(a[1]+b[1])/2)}\nrotation = {num(atan2(dy,dx))}\nshape = SubResource("{shp}")')
        left,right=sorted((a,b)); dx,dy=right[0]-left[0],right[1]-left[1];n=20 if not dy else 14
        mod='iron_straight' if not dy else 'iron_rising' if dy<0 else 'iron_falling'; unit=131 if not dy else 61
        for j in range(n):
            x,y=left[0]+dx*j/n,left[1]+dy*j/n
            sprite(w,'Span',COURT+mod+'.png',x,y,dx/n/unit,abs(dy/n/88) if dy else 1,p,(-8,min(0,(-88 if dy<0 else 0))-84))
            if j and j%3==0:prop(p,'stone_lantern_post',x,y+3,101,sub='fences',reserve=False)
    for x,y in WALL:prop(p,'stone_lantern_post',x,y+3,115,sub='fences',reserve=False)

def plant():
    paths=[curve(pts)[::5] for _,pts in ROUTES]; samples=[p for path in paths for p in path]
    p=group('WildBorders'); occ=OCC+[(x,y,100,69) for x,y in (HERO_C,HERO_E)]
    def veg(x,y,row,col,h):prop(p,'vegetation_r%02d_c%02d'%(row,col),x,y,h,R.random()<.45,False,'vegetation',False)
    # Scattered stands, not a grid of uniformly spaced potted bushes. Skip the open routes.
    for i in range(730):
        x,y=R.randrange(48,4816),R.randrange(36,3420)
        if any(abs(x-xx)<75 and abs(y-yy)<46 for xx,yy in samples):continue
        if any(abs(x-xx)<rx+23 and abs(y-(yy-ry*.48))<ry+14 for xx,yy,rx,ry in occ):continue
        row=R.choices([1,2,3,4,5,6,7],[6,5,3,3,3,2,2])[0];h=R.randint(18,33) if row<5 else R.randint(23,45)
        if x>3000 and y<1000 and row==5:col=R.choice([4,5,7,8]);h+=9
        else:col=R.randint(1,8)
        veg(x,y,row,col,h)
        if R.random()<.49:veg(x+R.randint(24,46),y+R.randint(-12,10),R.choice([1,2,3]),R.randint(1,8),R.randint(13,23))
    # Group flowers and leaves at architectural feet to seat the monuments in the grass.
    for xx,yy,rx,ry in OCC.copy():
        if ry<24 or R.random()<.34 or (xx,yy) in [(x,y) for x,y,_ in ACTORS]:continue
        x=xx+R.choice([-1,1])*(rx+15);veg(x,yy+4,5,R.randint(1,8),R.randint(28,51));veg(x+20,yy+14,2,R.randint(3,8),R.randint(16,24))

if __name__=='__main__':
    GAME.mkdir(exist_ok=True);contact_texture();build_world()
