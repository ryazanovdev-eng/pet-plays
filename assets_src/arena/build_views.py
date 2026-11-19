"""Presentation cameras and immutable snapshots of the shared HUD."""
from PIL import Image, ImageDraw
from build_world import Scene, sprite, size, ROOT, OUT, GAME, COURT, WALL, ROUTES, CENTER, EDGE, HERO_C, HERO_E, v, num, curve

UI='assets/ui/hud/';HEALTH='assets/ui/health/'

def label(s,name,text,x,y,ww,hh,pt):
    s.node(name,'Label',props=f'offset_left = {num(x-ww/2)}\noffset_top = {num(y-hh/2)}\noffset_right = {num(x+ww/2)}\noffset_bottom = {num(y+hh/2)}\nmouse_filter = 2\ntheme_override_colors/font_color = Color(1, 0.935, 0.79, 1)\ntheme_override_colors/font_outline_color = Color(0.12, 0.055, 0.12, 1)\ntheme_override_constants/outline_size = 3\ntheme_override_font_sizes/font_size = {pt}\ntext = "{text}"\nhorizontal_alignment = 1\nvertical_alignment = 1')

def project(x,y):return 1196+(x-2420)*.022,636+(y-1710)*.022
def points(pts):return 'PackedVector2Array('+', '.join(num(v) for p in pts for v in p)+')'
def line(s,name,pts,color,width):s.node(name,'Line2D',props=f'points = {points(pts)}\nwidth = {width}\ndefault_color = {color}\nantialiased = true')
def progress(s,name,path,rect,x,y,sx,sy,value,atlas=None):
    res=s.ref(path)
    if atlas:
        s.sub.append(f'[sub_resource type="AtlasTexture" id="{name}Crop"]\natlas = {res}\nregion = Rect2({", ".join(str(n) for n in atlas)})');res=f'SubResource("{name}Crop")'
    width,height=rect
    s.node(name,'TextureProgressBar',props=f'offset_left = {num(x)}\noffset_top = {num(y)}\noffset_right = {num(x+width)}\noffset_bottom = {num(y+height)}\nscale = {v(sx,sy)}\nmouse_filter = 2\nvalue = {value}\ntexture_progress = {res}')

def hud():
    h=Scene('BattleHUD','CanvasLayer')
    # Recompose the clean source key artwork: the static demo has no E interaction.
    im=Image.open(ROOT/UI/'controls_help_panel.png').convert('RGBA');width,height=im.size
    # Shorten only the empty decorative side margins continuously; omit one whole
    # key row in the interior. No cutting through the painted mouse or candles.
    cut=58;dest=Image.new('RGBA',(width,height-cut));src=im.load();px=dest.load()
    for u in range(width):
        center=max(0,min(1,(u-160)/35,(632-u)/15))
        for b in range(dest.height):
            t=max(0,min(1,(b-113)/167));side=t*t*(3-2*t);sy=b+cut*(center*(b>=239)+(1-center)*side)
            px[u,b]=src[u,min(height-1,round(sy))]
    ImageDraw.Draw(dest).rectangle((775,125,789,174),fill=(0,0,0,0));dest.save(OUT/'controls.png')
    sprite(h,'Controls',COURT+'controls.png',17,585,.35, .35,offset=(0,0))
    k=.37; x=16;y=4
    sprite(h,'HeroPortraitAndFrame',HEALTH+'runtime_layers/hero_empty_frame.png',x,y,k,k,offset=(0,0))
    progress(h,'HeroHealth',HEALTH+'runtime_layers/hero_full_red_overlay.png',(538,61),x+282*k,y+125*k,k,k,78,atlas=(282,125,538,61))
    sprite(h,'RoundedFillEnd',HEALTH+'runtime_layers/hero_rounded_right_cap.png',x+(282+538*.78-1)*k,y+125*k,k,k,offset=(0,0))
    label(h,'HitPoints','78 / 100',x+550*k,y+154*k,163,31,19)
    label(h,'Level','6',x+249*k,y+231*k,32,29,19)
    # Experience below the health bar, clear of the circular level medallion.
    line(h,'ExperienceTrack',[(138,91),(318,91)],'Color(0.18,0.095,0.19,1)',5)
    line(h,'ExperienceFill',[(138,91),(237,91)],'Color(0.98,0.69,0.24,1)',3)
    sprite(h,'WavePlate',UI+'wave_panel_blank.png',640,55,.443)
    label(h,'Wave','Волна 3/5',640,61,168,37,24)
    sprite(h,'BonePlate',UI+'currency_bones_panel.png',817,61,.237)
    label(h,'Currency','24',831,61,49,29,18)
    # Portrait-less bar. No extra title or health text.
    sprite(h,'BossFrame',HEALTH+'standalone_sprites/empty_frame.png',1116,61,.56,.38)
    progress(h,'BossHealth',HEALTH+'standalone_sprites/red_fill.png',(469,70),992,49.2,.532,.326,68)
    sprite(h,'Cartouche',UI+'minimap_empty_frame.png',1196,631,.39)
    fence=[project(*pt) for pt in WALL];line(h,'MinimapWall',fence+[fence[0]],'Color(0.68,0.46,0.31,0.95)',1.8)
    for i,(_,route) in enumerate(ROUTES[:5]):
        pts=[project(*p) for p in curve(route)[::12] if 600<p[0]<4220 and 490<p[1]<2960]
        line(h,'MapWalk'+str(i),pts,'Color(0.59,0.44,0.51,0.73)',1.25)
    for i,(x,y) in enumerate([(2130,1598),(2632,1775),(2830,1877),(3255,667),(3604,755),(3350,945)]):
        u,b=project(x,y);h.node('Hostile'+str(i),'Polygon2D',props=f'position = {v(u,b)}\ncolor = Color(0.98,0.36,0.34,1)\npolygon = {points([(0,-2.5),(2.5,0),(0,2.5),(-2.5,0)])}')
    h.save(GAME/'hud.tscn')

def hero():
    s=Scene('HeroMark');sprite(s,'Shadow',COURT+'contact.png',0,0,.72,.43)
    s.node('DisplayScale','Node2D',props='scale = Vector2(1.78, 1.78)')
    s.node('FrogKnight',None,'DisplayScale','animation = &"attack"\nautoplay = ""\nframe = 2', 'game/cast/frog_knight.tscn');s.save(GAME/'hero_mark.tscn')

def view(name,cam,hero):
    s=Scene('MeridianView' if name=='arena' else 'LamplighterView');s.node('World',None,instance='game/arena_parts/world.tscn');s.node('Hero',None,props=f'position = {v(*hero)}',instance='game/arena_parts/hero_mark.tscn');s.node('FixedCamera','Camera2D',props=f'position = {v(*cam)}\nposition_smoothing_enabled = false');s.node('HUD',None,instance='game/arena_parts/hud.tscn');s.node('PlayerPointer','Polygon2D','HUD',f'position = {v(*project(*hero))}\ncolor = Color(1, 0.85, 0.28, 1)\npolygon = {points([(-3,-4),(5,0),(-3,4),(-1,0)])}');s.save(ROOT/f'game/{name}.tscn')

if __name__=='__main__':
    hud();hero();view('arena',CENTER,HERO_C);view('arena_edge',EDGE,HERO_E)
