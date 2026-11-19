"""Surveyed road layout and iron fence artwork; paint_churchyard.py bakes the current ground."""
from pathlib import Path
from math import sin, cos, pi, hypot, ceil, floor
from random import Random
from PIL import Image, ImageDraw, ImageFilter, ImageChops, ImageEnhance

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'assets/arena/court'
SIZE = W, H = 4864, 3456
WALL = [(1110,480),(3730,480),(4580,1710),(3730,2980),(1110,2980),(260,1710)]
# Processional route with two forks, a sexton's path and a road outside the walls.
ROUTES = [
 (114,[(0,1830),(620,1730),(1040,1550),(1550,1530),(1960,1590),(2300,1750),(2650,1790),(3030,1650),(3390,1500),(3870,1490),(4864,1860)]),
 (92,[(1320,3200),(1520,2660),(1810,2370),(2150,2200),(2300,1960),(2360,1740),(2570,1380),(2750,1280),(3110,1190),(3310,960),(3350,710),(3500,570)]),
 (66,[(580,2210),(1030,2350),(1390,2520),(1580,2640),(2240,2710),(2630,2560),(3030,2470),(3420,2500),(3900,2690)]),
 (62,[(1030,1540),(1180,1210),(1450,1000),(1690,960),(1980,780),(2300,820),(2550,1120),(2710,1300)]),
 (55,[(3020,2480),(3100,2180),(3100,1940),(3030,1650)]),
 (54,[(2480,0),(2740,245),(3010,325),(3420,315),(3700,230),(4200,255),(4864,400)])]


def curve(pts):
    q=[pts[0],*pts,pts[-1]]; out=[]
    for a,b,c,d in zip(q,q[1:],q[2:],q[3:]):
        n=ceil(hypot(c[0]-b[0],c[1]-b[1])/6)
        for j in range(n):
            t=j/n
            out.append(tuple((2*v+(-u+w)*t+(2*u-5*v+4*w-z)*t*t+(-u+3*v-3*w+z)*t**3)/2 for u,v,w,z in zip(a,b,c,d)))
    return out+[pts[-1]]


def paint_ground():
    rng=Random(711)
    def tile(kind, size):
        im=Image.open(ROOT/f'raw/FrogKnight_Enviroments/terrain/ground/{kind}_256.png').convert('RGB').resize(size,Image.Resampling.LANCZOS)
        sheet=Image.new('RGB',SIZE)
        for y in range(0,H,size[1]):
            for x in range(0,W,size[0]): sheet.paste(im,(x,y))
        return sheet
    grass=tile('grass',(170,124)); earth=tile('dirt',(225,158)); stone=tile('stone',(165,106))
    # Painted route shoulders meander continuously, not one straight tile per bend.
    mask=Image.new('L',SIZE); draw=ImageDraw.Draw(mask)
    for k,(width,pts) in enumerate(ROUTES):
        for i,(x,y) in enumerate(curve(pts)):
            r=width*(.57+.12*sin(i*.052+k)+.06*cos(i*.13))+rng.uniform(-4,4)
            draw.ellipse((x-r,y-r*.68,x+r,y+r*.68),fill=255)
    def apron(x,y,rx,ry,n=100):
        return [(x+cos(i*2*pi/n)*rx*(1+.035*sin(i*.35)), y+sin(i*2*pi/n)*ry*(1+.045*cos(i*.31))) for i in range(n)]
    pave=Image.new('L',SIZE); pd=ImageDraw.Draw(pave)
    for x,y,rx,ry in [(1900,1520,146,63),(2360,1740,192,95),(3010,2310,190,80),(1190,1040,205,104),(3380,360,173,75),(2860,750,130,58),(1300,2420,180,72),(3230,2600,160,70),(3630,900,100,45)]:
        pd.polygon(apron(x,y,rx,ry),fill=255)
    # Coordinate-locked noise eats into dirt/stone margin instead of a fuzzy radial blur.
    noise=Image.frombytes('L',(W//8,H//8),rng.randbytes(W//8*(H//8))).resize(SIZE,Image.Resampling.BICUBIC)
    def ragged(m):
        m=ImageChops.add(m.filter(ImageFilter.GaussianBlur(9)),noise,scale=1.6)
        return m.point(lambda n:max(0,min(255,(n-152)*14)))
    land=Image.composite(earth,grass,ragged(mask));land=Image.composite(stone,land,ragged(pave))
    # Heterogeneous, low-frequency colour unifies the small repeating brushwork.
    light=Image.frombytes('L',(43,32),rng.randbytes(43*32)).resize(SIZE,Image.Resampling.BICUBIC)
    land=Image.composite(land,ImageEnhance.Brightness(land).enhance(.70),light.point(lambda n:60+n*.62))
    outside=Image.new('L',SIZE,255);ImageDraw.Draw(outside).polygon(WALL,fill=0)
    dusk=Image.blend(ImageEnhance.Color(land).enhance(.73),Image.new('RGB',SIZE,(32,37,63)),.18)
    land=Image.composite(dusk,land,outside.filter(ImageFilter.GaussianBlur(13)))
    # Inlaid compass in an old cobblestone roundel; separate weathered tesserae.
    d=ImageDraw.Draw(land);cx,cy=2360,1740
    for i in range(40):
        a=i*pi/20; b=a+pi/20*.89
        def arc(a,rx,ry): return (cx+cos(a)*rx,cy+sin(a)*ry)
        corners=[arc(a,175,83),arc(b,175,83),arc(b,167,79),arc(a,167,79)]
        d.polygon(corners,fill=rng.choice(['#a68664','#a39078','#87796a']),outline='#574c4e')
    for i in range(8):
        a=i*pi/4;v=1 if i%2==0 else .71
        p=[arc(a,140*v,69*v),arc(a+.75,27,18),arc(a+pi,10,6),arc(a-.75,27,18)]
        d.polygon(p,fill='#aa9276',outline='#59494b'); d.polygon([p[0],p[1],p[2]],fill='#796974')
    for row in range(2):
        for col in range(2):
            x,y=col*W//2,row*H//2
            land.crop((x,y,x+W//2,y+H//2)).save(OUT/f'ground_{row}{col}.jpg',quality=95,subsampling=0,optimize=True)


def fence_module(name,dx,dy):
    """Each cell has open rails up to the exact next cell origin; pickets stay upright."""
    ss=4; top=min(dy,0)-84; bottom=max(dy,0)+8
    im=Image.new('RGBA',((abs(dx)+16)*ss,(bottom-top)*ss));d=ImageDraw.Draw(im)
    def pt(x,y):return (round((x+8)*ss),round((y-top)*ss))
    def poly(pts, fill):d.polygon([pt(x,y) for x,y in pts],fill=fill)
    def line(pts, fill, w):d.line([pt(x,y) for x,y in pts],fill=fill,width=max(1,round(w*ss)))
    for height in [13,46]:
        # Small end overlap removes subpixel cracks between adjacent rail cells.
        a=-1.5;b=dx+1.5
        poly([(a,dy*a/dx-height),(b,dy*b/dx-height),(b,dy*b/dx-height+8),(a,dy*a/dx-height+8)],'#241b29')
        line([(a,dy*a/dx-height+1.5),(b,dy*b/dx-height+1.5)],'#94748c',2)
        line([(a,dy*a/dx-height+4),(b,dy*b/dx-height+4)],'#59415b',2)
    for i in range(4):
        t=(i+.5)/4;x=t*dx;y=t*dy; w=3.7 if dx>80 else 3.2
        h=64+(7 if i%2==0 else 0)
        poly([(x-w,y-2),(x-w,y-h+17),(x+w,y-h+17),(x+w,y-2),(x,y)],'#201822')
        line([(x-1,y-4),(x-1,y-h+17)],'#735674',2.2)
        poly([(x,y-h),(x+w*1.7,y-h+12),(x+w,y-h+16),(x,y-h+19),(x-w,y-h+16),(x-w*1.7,y-h+12)],'#281f30')
        poly([(x,y-h+2),(x+.3,y-h+15),(x-w*1.35,y-h+12)],'#b191a5')
        poly([(x,y-h+2),(x+w*1.38,y-h+12),(x,y-h+16)],'#684c70')
        line([(x-w-1,y-h+20),(x+w+1,y-h+20)],'#b89582',2)
    im.resize((im.width//ss,im.height//ss),Image.Resampling.LANCZOS).save(OUT/f'{name}.png')


if __name__=='__main__':
    OUT.mkdir(parents=True,exist_ok=True)
    for name,dx,dy in [('iron_straight',131,0),('iron_rising',61,-88),('iron_falling',61,88)]: fence_module(name,dx,dy)
