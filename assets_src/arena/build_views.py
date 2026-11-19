"""Presentation cameras and immutable snapshots of the shared HUD."""
from PIL import Image, ImageDraw
from build_world import Scene, sprite, ROOT, OUT, GAME, COURT, WALL, ROUTES, CENTER, EDGE, HERO_C, HERO_E, CENTER_CAST, EDGE_CAST, v, num, curve

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

def controls_texture():
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

def marker(h,name,x,y,boss=False):
    # The same authored placement feeds the world and the map; no runtime tracking.
    r=3.5 if boss else 2
    color='Color(0.86,0.48,1,1)' if boss else 'Color(0.98,0.36,0.34,1)'
    h.node(name,'Polygon2D',props=f'position = {v(*project(x,y))}\ncolor = {color}\npolygon = {points([(0,-r),(r,0),(0,r),(-r,0)])}')

def hud():
    h=Scene('BattleHUD','CanvasLayer')
    sprite(h,'Controls',COURT+'controls.png',17,585,.35, .35,offset=(0,0))
    k=.37; x=16;y=4
    sprite(h,'HeroPortraitAndFrame',HEALTH+'runtime_layers/hero_empty_frame.png',x,y,k,k,offset=(0,0))
    progress(h,'HeroHealth',HEALTH+'runtime_layers/hero_full_red_overlay.png',(538,61),x+282*k,y+125*k,k,k,78,atlas=(282,125,538,61))
    sprite(h,'RoundedFillEnd',HEALTH+'runtime_layers/hero_rounded_right_cap.png',x+(282+538*.78-1)*k,y+125*k,k,k,offset=(0,0))
    label(h,'HitPoints','78 / 100',x+550*k,y+154*k,163,31,19)
    label(h,'Level','4',x+249*k,y+231*k,32,29,19)
    sprite(h,'WavePlate',UI+'wave_panel_blank.png',640,55,.443)
    label(h,'Wave','Волна 2/5',640,61,168,37,24)
    sprite(h,'BonePlate',UI+'currency_bones_panel.png',1057,679,.237)
    label(h,'Currency','15',1071,679,49,29,18)
    sprite(h,'Cartouche',UI+'minimap_empty_frame.png',1196,631,.39)
    fence=[project(*pt) for pt in WALL];line(h,'MinimapWall',fence+[fence[0]],'Color(0.68,0.46,0.31,0.95)',1.8)
    for i,(_,route) in enumerate(ROUTES[:5]):
        pts=[project(*p) for p in curve(route)[::12] if 600<p[0]<4220 and 490<p[1]<2960]
        line(h,'MapWalk'+str(i),pts,'Color(0.59,0.44,0.51,0.73)',1.25)
    regular_positions=[(x,y) for id,x,y,*_ in CENTER_CAST+EDGE_CAST if not id.startswith('boss_')]
    for i,(x,y) in enumerate(regular_positions): marker(h,'Hostile'+str(i+1),x,y)
    h.save(GAME/'hud.tscn')

    wave=Scene('ClearanceHUD',base='game/arena_parts/hud.tscn')
    # Two lines inside a single cartouche; neither text draws over the actors.
    wave.node('WavePlate',None,props='position = Vector2(640, 57)\nscale = Vector2(0.58, 0.66)')
    wave.node('Wave',None,props='offset_top = 36\noffset_bottom = 73')
    label(wave,'EnemiesRemaining',f'Осталось врагов: {len(regular_positions)}',640,77,208,24,16)
    wave.save(GAME/'clearance_hud.tscn')

    boss=Scene('GiantHUD',base='game/arena_parts/hud.tscn')
    for name,text in [('Wave','Волна 3/5'),('Level','6'),('Currency','24')]:
        boss.node(name,None,props=f'text = "{text}"')
    # The original empty frame includes the giant's illustrated medallion.
    k=.37; x=1280-16-869*k; y=4
    prefix=HEALTH+'runtime_layers/rotten_giant_'
    sprite(boss,'BossPortraitAndFrame',prefix+'empty_frame.png',x,y,k,offset=(0,0))
    progress(boss,'BossHealth',prefix+'full_red_overlay.png',(538,61),x+282*k,y+125*k,k,k,68,atlas=(282,125,538,61))
    sprite(boss,'BossFillEnd',prefix+'rounded_right_cap.png',x+(282+538*.68-1)*k,y+125*k,k,offset=(0,0))
    for id,x,y,*_ in CENTER_CAST:
        if id.startswith('boss_'): marker(boss,'BossPointer',x,y,True)
    boss.save(GAME/'giant_hud.tscn')

def hero():
    s=Scene('HeroMark');sprite(s,'Shadow',COURT+'contact.png',0,0,.72,.43)
    s.node('DisplayScale','Node2D',props='scale = Vector2(1.78, 1.78)')
    s.node('FrogKnight',None,'DisplayScale','animation = &"attack"\nautoplay = ""\nframe = 2', 'game/cast/frog_knight.tscn');s.save(GAME/'hero_mark.tscn')

def views():
    part='game/arena_parts/'
    clear=Scene('ClearedCourt')
    clear.node('World',None,instance=part+'world.tscn')
    clear.node('Hero',None,props=f'position = {v(*HERO_C)}',instance=part+'hero_mark.tscn')
    clear.node('FrogKnight',None,'Hero/DisplayScale','animation = &"idle"\nframe = 0')
    clear.node('FixedCamera','Camera2D',props=f'position = {v(*CENTER)}\nposition_smoothing_enabled = false')
    clear.save(GAME/'cleared_court.tscn')

    for name,boss in [('arena',True),('arena_wave',False)]:
        s=Scene('MeridianView' if boss else 'ClearanceWave',base=part+'cleared_court.tscn')
        s.node('FrogKnight',None,'Hero/DisplayScale','animation = &"attack"\nframe = 2')
        s.node('Regulars',None,'World/Depth',instance=part+'regulars_and_drops.tscn')
        if boss: s.node('Giant',None,'World/Depth',instance=part+'giant_encounter.tscn')
        s.node('HUD',None,instance=part+('giant_hud.tscn' if boss else 'clearance_hud.tscn'))
        s.node('PlayerPointer','Polygon2D','HUD',f'position = {v(*project(*HERO_C))}\ncolor = Color(1, 0.85, 0.28, 1)\npolygon = {points([(-3,-4),(5,0),(-3,4),(-1,0)])}')
        s.save(ROOT/f'game/{name}.tscn')

    edge=Scene('LamplighterView',base='game/arena.tscn')
    edge.node('Hero',None,props=f'position = {v(*HERO_E)}')
    edge.node('FixedCamera',None,props=f'position = {v(*EDGE)}')
    edge.node('PlayerPointer',None,'HUD',f'position = {v(*project(*HERO_E))}')
    edge.save(ROOT/'game/arena_edge.tscn')

if __name__=='__main__':
    controls_texture();hud();hero();views()
