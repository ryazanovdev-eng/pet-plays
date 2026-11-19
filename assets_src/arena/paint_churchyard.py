"""Offline ground plates and cabinet swatches. Run with Python + Pillow.

Only writes court/ground_*.jpg and the two environment material groups.
build_ground is the *old* diorama recipe; borrow its surveyed road centrelines,
not its raster or its fence exporter. No Godot nodes are generated here.
"""
import argparse
from math import cos, floor, hypot, pi, sin
from pathlib import Path
from random import Random

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageOps
from build_ground import ROOT, OUT, SIZE, WALL, ROUTES, curve


ENV = ROOT / 'assets/environment'
LANCZOS = Image.Resampling.LANCZOS
BICUBIC = Image.Resampling.BICUBIC


def tone(c, dr=0, dg=None, db=None):
    return tuple(max(0, min(255, int(v + d))) for v, d in zip(c, (dr, dr if dg is None else dg, dr if db is None else db)))


def mix(c, d, amount):
    return tuple(round(v + (w - v) * amount) for v, w in zip(c, d))


def wash(size, rng, spacing):
    # Periodic at the margins, even on a 256 px repeat swatch.
    w, h = (max(2, round(n / s)) for n, s in zip(size, spacing))
    im = Image.frombytes('L', (w, h), rng.randbytes(w * h))
    padded = Image.new('L', (w+4, h+4))
    for j in (-1, 0, 1):
        for i in (-1, 0, 1):
            padded.paste(im, (2+i*w, 2+j*h))
    return padded.resize(size, BICUBIC, box=(2, 2, w+2, h+2))


def pigment(size, rng, palette):
    # A few cut shapes, not a cloud texture. The small field nicks the edge
    # of the large one; colour within a shape stays almost constant.
    big = wash(size, rng, (115, 73))
    torn = Image.blend(wash(size, rng, (27, 15)), wash(size, rng, (9, 6)), .35)
    value = Image.blend(big, torn, .36)
    cuts=(0,66,104,148,193,256)
    table=[]
    for i,c in enumerate(palette):
        lo,hi=cuts[i:i+2]
        for v in range(lo,hi):
            t=(v-lo)/(hi-lo)
            col=tone(c,5*t-2,4*t-2,3*t-1)
            if i and v-lo<5: col=mix(tone(palette[i-1],2),col,.35+.13*(v-lo))
            table.extend(col)
    value.putpalette(table)
    return value.convert('RGB')


class Brush:
    """Local polylines/polygons; wrap only on small repeatable specimens."""
    def __init__(self, im, repeat):
        self.im = im
        self.d = ImageDraw.Draw(im)
        self.repeat = repeat
        self.w, self.h = im.size

    def draw(self, pts, color, width=0):
        if self.repeat:
            xs, ys = zip(*pts)
            offsets = [(-i*self.w, -j*self.h)
                       for i in range(floor(min(xs)/self.w), floor(max(xs)/self.w)+1)
                       for j in range(floor(min(ys)/self.h), floor(max(ys)/self.h)+1)]
        else:
            offsets = [(0, 0)]
        for dx, dy in offsets:
            p = [(round(x+dx), round(y+dy)) for x,y in pts]
            if width:
                self.d.line(p, fill=color, width=width)
            else:
                self.d.polygon(p, fill=color)


# Drawing vocabulary: chipped lamina, a low hummock, a scuffed patch and
# the darker side of a lifted flake. Not stamped ellipses or speckle noise.
MARKS = [
    [(-1,.2),(-.61,-.04),(-.52,-.46),(.11,-.66),(.33,-.34),(.65,-.43),(1,-.12),(.43,.18),(.15,.5),(-.4,.4)],
    [(-1,.04),(-.55,-.57),(-.38,-.47),(-.05,-.93),(.45,-.63),(.4,-.27),(.89,-.38),(1,-.12),(.38,.27),(-.19,.32)],
    [(-1,.16),(-.65,-.18),(-.33,-.15),(.05,-.54),(.32,-.47),(.78,-.24),(1,-.35),(.77,.08),(.05,.31),(-.36,.18)],
]


def mark(b, rng, x, y, w, h, c):
    b.draw([(x+a*w, y+v*h) for a,v in rng.choice(MARKS)], c)


def soil_marks(im, rng, mud, repeat=False):
    w,h = im.size
    b = Brush(im, repeat)
    def point():
        x, y = rng.randrange(w), rng.randrange(h)
        return x,y, im.getpixel((x,y)), mud.getpixel((x,y))/255

    # Broken colour, broad dry-brush strokes with satellite flecks.
    for _ in range(w*h//1850):
        x,y,c,m = point(); turf=m < .43
        ink = mix(c,rng.choice(((45,81,66),(91,104,43),(156,135,54)) if turf else
                               ((154,85,61),(219,157,81),(205,135,67))), .72)
        for j in range(rng.randint(2,5)):
            a=rng.uniform(-1,1); xx=x+a*35; yy=y+rng.gauss(-a*8,5)
            sx=rng.uniform(7,24)*(1-abs(a)*.45); sy=sx*rng.uniform(.31,.72)
            mark(b,rng,xx,yy,sx,sy,ink)
            if j%2==0: mark(b,rng,xx-sx*.27,yy-sy*.36,sx*.63,sy*.36,tone(ink,14,11,2))

    # Gravel: clustered, with an exfoliated top plane and a buried lower lip.
    for _ in range(w*h//3900):
        x,y,c,m = point()
        if rng.random() > .38+.57*m: continue
        for j in range(rng.choice((1,2,2,3,5))):
            xx=x+rng.gauss(0,8); yy=y+rng.gauss(0,4)
            r = rng.uniform(3.2,9.6) * (1 if not j else .60)
            p = [(xx-r,yy+.4*r),(xx-r*.73,yy-r*.29),(xx+.16*r,yy-r*.67),(xx+r*.85,yy-r*.28),(xx+r,yy+.18*r),(xx+.36*r,yy+r*.48)]
            k = mix(c,rng.choice(((134,111,102),(172,136,93),(124,115,135))),.43)
            b.draw(p,tone(k,-16,-16,-12)); b.draw([p[0],p[1],p[2],p[3],(xx+.31*r,yy+.12*r)],tone(k,14,11,8))

    # Compact patches of raised clay. A broken ochre rim catches light on
    # the lit side; the split earth fits together like the pages of a book.
    for _ in range(w*h//4000):
        x,y,c,m=point()
        if m < .55:continue
        s=rng.uniform(.85,1.65)
        for ix,iy,path in [(0,0,[(-13,1),(-9,-3),(-4,-3),(0,-7),(7,-6),(8,-3),(2,0),(-3,1),(-6,3)]),
                           (11,-2,[(-8,3),(-7,0),(0,-3),(4,-7),(8,-6),(7,-1),(4,1),(0,2)]),
                           (1,6,[(-12,-1),(-5,-3),(0,-4),(5,-3),(3,-1),(0,1),(-6,2)])]:
            xx=x+ix*s; yy=y+iy*s
            p=[(xx+(a+rng.uniform(-1,1))*s,yy+v*s) for a,v in path]
            b.draw([(u,v+1.2*s) for u,v in p],tone(c,-20,-16,-11));b.draw(p,tone(c,9,7,4));b.draw(p[1:4],tone(c,19,15,8),1)

    # Fine branching fissures in patches of dry exposed soil, not all over it.
    for _ in range(w*h//6500):
        x,y,c,m=point()
        if m < .51: continue
        sign=rng.choice((-1,1)); pts=[(x,y)]
        for j in range(rng.randint(3,6)):
            xx,yy=pts[-1]; pts.append((xx+sign*rng.uniform(1,8), yy+rng.uniform(-4,3)))
        b.draw(pts,tone(c,-22,-18,-12),1)
        xx,yy=pts[2]; b.draw([(xx,yy),(xx-sign*2,yy+3),(xx-sign*7,yy+5)],tone(c,-15),1)

    # Banks of pillow moss: one scalloped mass, a cold undercut and a few
    # keyed sunlit planes. Keep the occupied areas small and irregular.
    for _ in range(w*h//6000):
        x,y,c,m=point()
        if m>.49: continue
        s=rng.uniform(.65,1.28)
        bank=mix(c,rng.choice(((117,139,61),(150,147,61),(96,130,64))),.77)
        shade=mix(bank,(53,83,57),.73); top=mix(bank,(177,162,70),.55)
        for j in range(rng.randint(3,7)):
            xx=x+j*5*s+rng.uniform(-5,5); yy=y+rng.uniform(-5,5); k=rng.uniform(.5,1.1)*s
            p=[(xx+a*k,yy+v*k) for a,v in ((-10,2),(-8,-3),(-5,-4),(-4,-6),(1,-7),(5,-6),(5,-4),(8,-4),(11,-1),(8,2),(2,3),(-3,2))]
            b.draw([(u+1,v+2*k) for u,v in p],shade);b.draw(p,bank)
            b.draw([p[n] for n in (1,2,3,4,5)]+[(xx+1*k,yy-3*k),(xx-5*k,yy-2*k)],top)

    # Rooted grass in clusters, with curved blades, alternating cold/ochre tips.
    for _ in range(w*h//2200):
        x,y,c,m=point()
        if rng.random() < m*.97: continue
        s=rng.uniform(.55,1.35); blades=rng.randint(4,7); lean=rng.uniform(-7,8)
        base=mix(c,(38,65,48),.72)
        mark(b,rng,x+3*s,y+1*s,17*s,5*s,base)
        for j in range(blades):
            a=-1+2*j/(blades-1); h1=rng.uniform(6,20)*s*(1.2-.42*abs(a)); xx=x+a*8*s; dx=(a*11+lean)*s
            tip=(xx+dx,y-h1); bend=(xx+dx*.24-2*s,y-h1*.64)
            foot=(xx-2.8*s,y); elbow=(xx+dx*.46+2*s,y-h1*.61)
            k=mix(c,rng.choice(((167,159,63),(149,150,62),(198,168,76))),.68)
            b.draw([foot,bend,tip,elbow,(xx+2.7*s,y-.5*s)],base)
            b.draw([foot,bend,tip,(xx+dx*.26,y-h1*.52)],k)

    # Sparse russet fallen leaf litter and small golden moss cushions.
    for _ in range(w*h//4500):
        x,y,c,m=point()
        if rng.random()<m*.84:continue
        for j in range(rng.randint(3,8)):
            xx=x+rng.gauss(0,10);yy=y+rng.gauss(0,4);r=rng.uniform(3.0,7.5)
            if j%6==0:
                k=mix(c,rng.choice(((168,103,57),(163,125,64))),.77)
                p=[(xx-r*1.4,yy+.3*r),(xx-r*.7,yy-.5*r),(xx,yy-.4*r),(xx+r*1.1,yy-.8*r),(xx+.8*r,yy+.15*r),(xx-.4*r,yy+.45*r)]
                b.draw(p,k);b.draw([p[0],(xx,yy)],tone(k,-14,-9,-4),1)
            else:
                k=mix(c,(150,145,66),rng.uniform(.28,.66));mark(b,rng,xx,yy,r,r*.72,tone(k,-8));mark(b,rng,xx-r*.24,yy-.64*r,r*.63,r*.42,tone(k,13,10,3))


def paving(im, mask, seed, repeat=False):
    w,h=im.size; nx=max(3,round(w/53)); ny=max(3,round(h/26)); sx,sy=w/nx,h/ny
    rng=Random(seed); b=Brush(im,repeat)
    # Broken courses that buckle together. Joints slide along each course;
    # very short chips abut long lintel-like slates (no Voronoi cells).
    joints={(i,j):rng.uniform(-.32,.32) for j in range(ny) for i in range(nx)}
    offset=[rng.random() for _ in range(ny)]
    def corner(i,j,side):
        u=i+joints[i%nx,j%ny]+offset[j%ny]
        v=j+side
        phase=2*pi*(u*max(1,round(nx/4))/nx+v/ny)
        return (u*sx+8*sin(2*pi*v*max(1,round(ny/6))/ny), v*sy+sy*(.24*sin(phase)+.12*sin(phase*2+1)))
    pixels=mask.load()
    # For the unwrapped world draw the boundary cells straddling the canvas too.
    for j in range(0 if repeat else -1,ny if repeat else ny+1):
        for i in range(0 if repeat else -1,nx if repeat else nx+1):
            corners=[corner(i,j,0),corner(i+1,j,0),corner(i+1,j,1),corner(i,j,1)]
            x=sum(a for a,_ in corners)/4; y=sum(c for _,c in corners)/4
            v=pixels[int(x)%w,int(y)%h]/255
            if v < .09 or rng.random() > min(1,v*1.23): continue
            poly=[((a-x)/sx,(c-y)/sy) for a,c in corners]
            # Knock the corners off. A hand-broken setback around irregular
            # flagstones is larger at the exposed shoulders and clay incursions.
            scale=(.59+.4*v)*rng.uniform(.88,.98); p=[]
            for k,(u,z) in enumerate(poly):
                l=poly[k-1]; r=poly[(k+1)%len(poly)]; s1=rng.uniform(.04,.20);s2=rng.uniform(.04,.21)
                for n,s in ((l,s1),(r,s2)):
                    p.append((x+(u+(n[0]-u)*s)*sx*scale,y+(z+(n[1]-z)*s)*sy*scale))
            soil=im.getpixel((int(x)%w,int(y)%h)); stone=rng.choice(((151,120,141),(160,128,146),(177,138,143),(156,123,143),(169,139,146),(145,120,146)))
            k=mix(soil,tone(stone,rng.uniform(-7,7)),.79+.18*v)
            # Silhouette wear, with a few missing corners and stepped spalls;
            # flagstones in the earth should not look like uniform cells.
            edge=[]
            for e,f in zip(p,p[1:]+p[:1]):
                edge.append(e);dx=f[0]-e[0];dy=f[1]-e[1];l=hypot(dx,dy)
                if l<9 or rng.random()<.33:continue
                t=rng.uniform(.22,.41); t2=rng.uniform(.49,.73); bite=min(9.5,l*.33)*rng.uniform(.58,1)
                edge.extend([(e[0]+dx*t,e[1]+dy*t),(e[0]+dx*(t+.05)-dy/l*bite,e[1]+dy*(t+.05)+dx/l*bite),
                             (e[0]+dx*t2-dy/l*bite*.58,e[1]+dy*t2+dx/l*bite*.58)])
            p=edge;depth=rng.uniform(2.1,6.7)*scale
            shadow=mix(soil,(71,54,65),.77);cold=mix(k,(77,48,88),.83);warm=mix(k,(220,173,155),.92)
            b.draw([(u+2,z+depth+1.4) for u,z in p],shadow)
            b.draw([(u,z+depth) for u,z in p],cold)
            for e,f in zip(p,p[1:]+p[:1]):
                if e[0]>f[0]:
                    v=rng.uniform(-8,9); b.draw([e,f,(f[0],f[1]+depth),(e[0],e[1]+depth)],tone(cold,v,v*.7,v*.65))
            b.draw(p,k)
            # A broad broken bevel, not a uniform line around every polygon.
            # The inner face is inset by a different amount on each side. A
            # few facets run well into the face where a slab has exfoliated.
            bevel=rng.uniform(.10,.34);inner=[]
            for u,z in p:
                t=bevel*rng.uniform(.80,1.2);inner.append((u+(x-u)*t,z+(y-z)*t))
            for n,(e,f) in enumerate(zip(p,p[1:]+p[:1])):
                dx,dy=f[0]-e[0],f[1]-e[1];l=max(1,hypot(dx,dy)); incidence=(dx*.95-dy*.68)/l
                if incidence>.21:
                    tint=mix(k,warm,min(1,.17+.65*incidence+rng.uniform(-.10,.14)))
                else:tint=tone(k,-13+4*incidence,-12+4*incidence,-8+3*incidence)
                g=inner[(n+1)%len(p)];h0=inner[n]
                b.draw([e,f,g,h0],tint)
                if incidence>.8 and l>9:
                    b.draw([(e[0]+.16*dx,e[1]+.16*dy),(e[0]+.63*dx,e[1]+.63*dy)],tone(tint,13,9,4),1)
            idx=rng.randrange(len(p));f=inner[idx];g=inner[(idx+max(2,len(p)//4))%len(p)]
            b.draw([inner[(idx+a)%len(p)] for a in range(max(2,len(p)//4)+1)]+[((x+g[0])*.5,(y+g[1])*.5),((x+f[0])*.5,(y+f[1])*.5)],tone(k,rng.uniform(6,13),6,3))
            for u,z in zip(p,p[1:]+p[:1]):
                dx,dy=z[0]-u[0],z[1]-u[1]; l=hypot(dx,dy)
                if l < 3:continue
                if dx-dy*.95 > 1.4:
                    t=rng.uniform(.12,.29); t2=rng.uniform(.76,.98)
                    e=(u[0]+dx*t,u[1]+dy*t);f=(u[0]+dx*t2,u[1]+dy*t2)
                    b.draw([e,f,(f[0]+(x-f[0])*.20,f[1]+(y-f[1])*.20)],tone(k,18,16,12))
                if l>12 and rng.random()<.38:
                    t=rng.uniform(.3,.8); e=(u[0]+dx*t,u[1]+dy*t)
                    f=(e[0]+(x-e[0])*.31,e[1]+(y-e[1])*.31);g=(f[0]+rng.uniform(-3,3),f[1]+rng.uniform(-2,2))
                    b.draw([e,(e[0]+2,e[1]),f,g],tone(k,-26,-22,-17),1)
            # Stone fracture: start at an edge, fork towards a second chipped
            # edge. Leave most faces intact. Lower edge has a tiny light catch.
            if rng.random()<.48:
                n=rng.randrange(len(p));u=p[n]; z=p[(n+len(p)//2)%len(p)]
                pts=[u]
                for t in (.17,.31,.54,.69,.81):
                    pts.append((u[0]+(z[0]-u[0])*t+rng.uniform(-2,2),u[1]+(z[1]-u[1])*t+rng.uniform(-1.8,1.8)))
                if rng.random()<.65: pts.append(z)
                b.draw([(xx+.3,yy+1.4) for xx,yy in pts[1:4]],tone(k,25,18,13),2);b.draw(pts,tone(k,-39,-31,-24),1)
                if rng.random()<.54:
                    a,c0=pts[0],pts[2];e=pts[1]; b.draw([a,(a[0]+2.8,a[1]+.4),c0,e],mix(cold,shadow,.6))
                e=pts[3]; g=p[(n+3)%len(p)]; b.draw([e,((e[0]+g[0])*.5+1,(e[1]+g[1])*.5),g],tone(k,-15),1)
            # Shale laminae / lichen blooms / fine tool scrape on the face.
            for n in range(rng.randint(2,7)):
                e=rng.choice(p); t=rng.uniform(.1,.73);xx=x+(e[0]-x)*t;yy=y+(e[1]-y)*t
                mark(b,rng,xx,yy,min(8,hypot(xx-e[0],yy-e[1])*.53),rng.uniform(.7,2.2),tone(k,rng.choice((-9,-5,6,10))))
            if rng.random()<.53:
                idx=rng.randrange(len(p)); A=p[idx]; B=p[(idx+1)%len(p)]; lichen=mix(k,(106,111,57),.80)
                for n in range(rng.randint(4,14)):
                    f=rng.random(); xx=A[0]+(B[0]-A[0])*f+rng.uniform(-2,2); yy=A[1]+(B[1]-A[1])*f+rng.uniform(-2,2)
                    r=rng.uniform(1.2,5.8);mark(b,rng,xx,yy+1,r,r*.82,tone(lichen,-21,-22,-12));mark(b,rng,xx,yy,r,r*.75,tone(lichen,rng.randint(-13,7)));mark(b,rng,xx-1,yy-1,r*.55,r*.32,tone(lichen,25,20,3))


def materials(size, mud, stone, seed, repeat=False):
    rng=Random(seed)
    turf=pigment(size,rng,[(62,88,67),(76,100,64),(95,112,59),(119,124,58),(145,133,63)])
    soil=pigment(size,rng,[(159,97,70),(175,111,72),(187,125,76),(199,140,80),(210,155,91)])
    # Dry olive bank between the turf and clay. Only the last few pixels
    # interpolate at either lip. In particular, never average red and green
    # into a grey shoulder across the width of a road.
    im=turf.copy()
    im.paste(ImageOps.colorize(turf.convert('L'),(99,78,47),(194,160,66)),(0,0),mud.point(lambda v:(v-70)*38))
    im.paste(soil,(0,0),mud.point(lambda v:(v-135)*36))
    soil_marks(im,rng,mud,repeat); paving(im,stone,seed+9,repeat)
    return im


def erode(mask, rng, spread):
    rough=Image.blend(wash(mask.size,rng,(50,30)),wash(mask.size,rng,(11,7)),.48)
    return ImageChops.add(mask.filter(ImageFilter.GaussianBlur(spread)),rough,scale=2).point(lambda n:(n-88)*3.2)


# Aprons are drawn individually; stepped pads on the chapel side of the route,
# a split procession near the altar, remnants of a terrace under the giant.
PADS=[(1885,1524,201,89),(2350,1745,175,79),(2650,1780,83,40),(3010,2310,190,80),
      (1190,1040,220,100),(3375,375,210,80),(2860,750,120,58),(1300,2420,180,72),
      (3230,2600,160,70),(3630,900,91,38),(821,1659,135,62),(4100,1680,138,67)]


def world_masks():
    rng=Random(124); clay=Image.new('L',SIZE); road=ImageDraw.Draw(clay); stone=Image.new('L',SIZE); flag=ImageDraw.Draw(stone)
    for j,(width,anchors) in enumerate(ROUTES):
        for i,(x,y) in enumerate(curve(anchors)):
            t=i*.031+j; r=width*(1.08+.25*sin(t)+.11*cos(t*2.3)); rr=r*.68
            road.ellipse((x-r,y-rr,x+r,y+rr),fill=255)
            wear=sin(t*1.51-.2)+.54*cos(t*.54)
            if wear>.03:
                q=width*(.22+min(1,wear)*.32); yy=y+rr*.2*sin(t*2)
                flag.ellipse((x-q,yy-q*.64,x+q,yy+q*.64),fill=235)
    for x,y,rx,ry in PADS:
        for d,r,m in ((road,1.5,255),(flag,1,248)):
            outline=[]
            for i in range(45):
                a=2*pi*i/45; k=1+.1*sin(3*a+x)+.09*sin(5*a-y)+rng.uniform(-.05,.05)
                outline.append((x+rx*r*k*cos(a),y+ry*r*k*sin(a)))
            d.polygon(outline,fill=m)
    # Irregular clearings rather than isolated ribbons on an unbroken lawn.
    for x,y,rx,ry in ((2315,1715,430,176),(2025,1570,255,99),(3450,700,260,121),(2710,1960,140,75),(2970,746,145,65)):
        road.polygon([(x+rx*(1+.15*sin(3*a+.7)+.07*cos(7*a))*cos(a), y+ry*(1+.18*cos(4*a))*sin(a)) for a in (2*pi*n/50 for n in range(50))], fill=240)
    for _ in range(180):
        x=rng.randrange(SIZE[0]);y=rng.randrange(SIZE[1]);r=rng.uniform(19,98)
        if clay.getpixel((x,y))<10:road.polygon([(x+u*r,y+v*r*.60) for u,v in rng.choice(MARKS)],fill=rng.randint(120,230))
    return erode(clay,rng,25),erode(stone,rng,13)


def sigil(im):
    # Exact sign from sheet 05 row 5 col 6 (file rows start at zero).
    # Cut pigment into the plate: dark incision + dusty red ochre. Lose parts
    # of the engraved stroke on chips and under light dusty scuffs.
    rng=Random(7004);size=(187,87);x,y=2293,1720
    mask=Image.open(ENV/'ground_overlays/ground_overlays_r04_c06.png').convert('RGBA').getchannel('A').resize(size,LANCZOS)
    grain=wash(size,rng,(8,5));mask=ImageChops.multiply(mask,grain.point(lambda v:min(255,115+v*.75)))
    d=ImageDraw.Draw(mask)
    for _ in range(85):
        xx=rng.randrange(size[0]); yy=rng.randrange(size[1]); d.line([(xx-2,yy+1),(xx+2,yy)],fill=0,width=1)
    patch=im.crop((x,y,x+size[0],y+size[1]));rgb=patch.split()
    # The lavender faces retain the deepest red; ochre-filled gaps retain
    # only traces. Pigment does not bridge a seam like a painted-on decal.
    rock=ImageChops.subtract(rgb[2],rgb[1],offset=128).point(lambda v:min(255,max(35,48+(v-95)*7)))
    mask=ImageChops.multiply(mask,rock)
    red=Image.merge('RGB',(rgb[0].point(lambda v:v*.61+48),rgb[1].point(lambda v:v*.50+8),rgb[2].point(lambda v:v*.50+10)))
    im.paste(patch.point(lambda v:v*.66),(x,y-1),mask);im.paste(red,(x,y),mask)


def draw_world():
    clay,stone=world_masks();land=materials(SIZE,clay,stone,62021)
    outside=Image.new('L',SIZE,255);ImageDraw.Draw(outside).polygon(WALL,fill=0)
    land=Image.composite(Image.blend(land,Image.new('RGB',SIZE,(48,51,70)),.29),land,outside.filter(ImageFilter.GaussianBlur(36)))
    sigil(land)
    for row in range(2):
        for col in range(2):
            w,h=SIZE[0]//2,SIZE[1]//2;x,y=col*w,row*h
            land.crop((x,y,x+w,y+h)).save(OUT/f'ground_{row}{col}.jpg',quality=95,subsampling=0,optimize=True)
    return land


def corner_mask(bits):
    # Raw corner index: clockwise from NW, with the LSB at NW.
    q=Image.new('L',(2,2));q.putdata([255*((bits>>n)&1) for n in (0,1,3,2)])
    # Sample across the entire cell, clamping the four corner values.
    return q.resize((256,256),Image.Resampling.BILINEAR,box=(.5,.5,1.5,1.5))


def draw_sheets():
    size=(256,256); flat=lambda n: Image.new('L',size,n)
    grass=materials(size,flat(0),flat(0),81001,True)
    dirt=materials(size,flat(255),flat(0),81002,True)
    stone=materials(size,flat(233),flat(255),81003,True)
    terrain=ENV/'terrain'
    for name,tile in zip(('grass','dirt','stone'),(grass,dirt,stone)):
        tile.save(terrain/f'{name}_256.png')
    rng=Random(9602)
    rough=Image.blend(wash(size,rng,(28,19)),wash(size,rng,(8,5)),.42)
    def border(mask):
        # Tear the mixed band only: preserve the labelled corners (and the
        # road sockets) rather than punching random holes in pure materials.
        return Image.blend(mask,rough,.35).point(lambda n:(n-124)*65)
    for name,a,b in (('grass_to_dirt',grass,dirt),('grass_to_stone',grass,stone),('dirt_to_stone',dirt,stone)):
        atlas=Image.new('RGB',(1024,1024))
        for n in range(16):
            mask=flat(0) if n==0 else flat(255) if n==15 else border(corner_mask(n))
            atlas.paste(Image.composite(b,a,mask),(n%4*256,n//4*256))
        atlas.save(terrain/f'{name}_atlas.png')
    links=['WE','NS','ES','WS','NE','NW','NWE','ESW','WNS','ENS','WNES','S','N','E','','W']
    for row in range(1,8):
        for col in range(1,9):
            dest=ENV/f'road_tiles_concept/road_tiles_r{row:02}_c{col:02}.png'
            with Image.open(dest) as old: dims=old.size
            if row==1:
                tile=ImageChops.offset((grass,dirt,stone)[0 if col<4 else 1 if col<7 else 2],col*79,col*43)
            else:
                mask=flat(0);d=ImageDraw.Draw(mask); paved=row in (4,5,7)
                if row<=5:
                    s=links[(row%2)*8+col-1];end={'W':(-64,128),'E':(320,128),'N':(128,-64),'S':(128,320)}
                    radius=60
                    for tag in s:d.line([(128,128),end[tag]],fill=255,width=2*radius)
                    if s:d.ellipse((128-radius,128-radius,128+radius,128+radius),fill=255)
                else:
                    # Four banks followed by four convex embankments.
                    polys=[[(0,118),(256,118),(256,256),(0,256)],[(0,0),(256,0),(256,138),(0,138)],[(119,0),(256,0),(256,256),(119,256)],[(0,0),(137,0),(137,256),(0,256)]]
                    if col<5:d.polygon(polys[col-1],fill=255)
                    else:
                        x,y=[(256,256),(0,256),(256,0),(0,0)][col-5];d.ellipse((x-236,y-236,x+236,y+236),fill=255)
                mask=border(mask.filter(ImageFilter.GaussianBlur(12)))
                tile=Image.composite(stone if paved else dirt,grass,mask)
            tile.resize(dims,LANCZOS).convert('RGBA').save(dest)
    return grass,dirt,stone


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--proof',type=Path,help='Existing proof directory outside Godot')
    args=parser.parse_args();land=draw_world();draw_sheets()
    if args.proof:
        for label,(x,y) in {'centre':(2390,1700),'edge':(3450,640)}.items():
            land.crop((x-640,y-360,x+640,y+360)).save(args.proof/f'churchyard_{label}.png')
        land.resize((1216,864),LANCZOS).save(args.proof/'churchyard_overview.jpg',quality=92)
