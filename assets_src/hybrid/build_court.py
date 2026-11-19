"""Run in Blender background from the project root. No game-time generation."""
from pathlib import Path
from collections import deque
import math
import random
import bpy
import numpy as np

root = Path(__file__).resolve().parents[2]
raw = root / 'raw/FrogKnight_Enviroments'
out = root / 'assets/hybrid'
out.mkdir(exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.preferences.filepaths.save_version = 0
rng = random.Random(89)


def material(name, rgb=None, image=None):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    p.inputs['Roughness'].default_value = .94
    if image:
        t = m.node_tree.nodes.new('ShaderNodeTexImage')
        t.image = image
        m.node_tree.links.new(t.outputs['Color'], p.inputs['Base Color'])
    else:
        p.inputs['Base Color'].default_value = (*rgb, 1)
        m.diffuse_color = (*rgb, 1)
    return m


def mesh(name, vertices, faces, mat, uv=None):
    data = bpy.data.meshes.new(name)
    data.from_pydata(vertices, [], faces)
    data.update()
    o = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(o)
    data.materials.append(mat)
    if uv:
        layer = data.uv_layers.new()
        for loop in data.loops:
            layer.data[loop.index].uv = uv[loop.vertex_index]
    return o


def image(path):
    return bpy.data.images.load(str(raw / path), check_existing=True)


def relief(path, height, thickness):
    # Reconstruct two curved skins from the contiguous painted silhouette. A
    # distance field swells the middle; quads close the entire perimeter.
    im = image('individual_png/' + path + '.png')
    w,h = im.size
    pixels = np.empty(w*h*4, np.float32)
    im.pixels.foreach_get(pixels)
    stride = max(2, math.ceil(max(w,h)/86))
    mask = pixels.reshape(h,w,4)[stride//2::stride,stride//2::stride,3] > .78
    cells = set(zip(*np.where(mask)))
    biggest = set()
    dirs = [(0,1),(1,0),(0,-1),(-1,0)]
    while cells:
        q = [cells.pop()]; group = set(q)
        while q:
            y,x = q.pop()
            for dy,dx in dirs:
                k = (y+dy,x+dx)
                if k in cells:
                    cells.remove(k); group.add(k); q.append(k)
        if len(group)>len(biggest): biggest = group
    corners = {(y+dy,x+dx) for y,x in biggest for dy,dx in [(0,0),(0,1),(1,1),(1,0)]}
    rim = {k for k in corners if any((k[0]+dy,k[1]+dx) not in biggest for dy,dx in [(0,0),(-1,0),(0,-1),(-1,-1)])}
    dist = dict.fromkeys(rim,0); q = deque(rim)
    while q:
        y,x = q.popleft()
        for dy,dx in dirs:
            k=(y+dy,x+dx)
            if k in corners and k not in dist:
                dist[k]=dist[y,x]+1; q.append(k)
    ymin=min(y for y,x in corners); ymax=max(y for y,x in corners)
    xc=(min(x for y,x in corners)+max(x for y,x in corners))/2
    unit=height/(ymax-ymin); verts=[]; uv=[]; indices={}; faces=[]
    for side in [0,1]:
        for y,x in sorted(corners):
            z=(y-ymin)*unit
            bulge=1-math.exp(-dist[y,x]/4.5)
            depth=thickness*((.52+.28*bulge) if side else -(.12+.16*bulge))
            indices[side,y,x]=len(verts)
            verts.append(((x-xc)*unit,depth+.12*z,z))
            # Sample inside opaque pixels at the rim, never the empty gutter.
            cy,cx=next((y+a,x+b) for a,b in [(0,0),(-1,0),(0,-1),(-1,-1)] if (y+a,x+b) in biggest)
            uv.append((((cx+.5)*stride if (y,x) in rim else x*stride)/w,((cy+.5)*stride if (y,x) in rim else y*stride)/h))
    side_faces=[]
    for y,x in sorted(biggest):
        ring=[(y,x),(y,x+1),(y+1,x+1),(y+1,x)]
        f=[indices[0,*k] for k in ring]; b=[indices[1,*k] for k in ring]
        faces.extend([f,b[::-1]])
        for i,(dy,dx) in enumerate([(-1,0),(0,1),(1,0),(0,-1)]):
            if (y+dy,x+dx) not in biggest:
                j=(i+1)%4; side_faces.append(len(faces)); faces.append([f[j],f[i],b[i],b[j]])
    obj=mesh(Path(path).stem,verts,faces,material(Path(path).stem,image=im),uv)
    obj.data.materials.append(edge if 'brazier' not in path else iron)
    for idx in side_faces:
        obj.data.polygons[idx].material_index=1
    return obj


def scatter(path,h,d,places):
    original=relief(path,h,d)
    for i,(x,y,a,s) in enumerate(places):
        o=original if i==0 else original.copy()
        if i: bpy.context.collection.objects.link(o)
        o.location=(x,y,.025); o.rotation_euler.z=math.radians(a); o.scale=(s,s,s)


slate=material('Basalt / shadow',(.055,.064,.102)); edge=material('Amethyst shale',(.19,.135,.21)); gold=material('Old brass',(.52,.28,.095)); iron=material('Wrought iron',(.048,.035,.059)); stone=material('Lichen stone',(.26,.22,.29))


def slab(name,w,d,top,bottom,cut,m):
    x=w/2;y=d/2
    ring=[(-x+cut,-y),(x-cut,-y),(x,-y+cut),(x,y-cut),(x-cut,y),(-x+cut,y),(-x,y-cut),(-x,-y+cut)]
    return mesh(name,[(a,b,z) for z in [bottom,top] for a,b in ring],[[*range(7,-1,-1)],[*range(8,16)]]+[[i,(i+1)%8,(i+1)%8+8,i+8] for i in range(8)],m,[(a/3,b/3) for _ in range(2) for a,b in ring])


slab('Floating foundation',15,9.6,-.28,-.74,.70,slate)
slab('Brass reveal',15.04,9.64,-.235,-.28,.70,gold)
slab('Upper cornice',15.18,9.78,-.045,-.235,.72,edge)
slab('Moss court',15.0,9.6,0,-.045,.68,material('Wild grass',image=image('terrain/ground/grass_256.png')))

# A winding paved processional walk, widened at the chapel steps.
v=[]; uv=[]; f=[]
for i in range(31):
    y=-4.7+i*.3; center=.82*math.sin(.72*y)-.10*y; half=1.30+.42*(1+math.cos(.82*y))
    for x in [center-half+rng.uniform(-.11,.11),center+half+rng.uniform(-.11,.11)]:
        v.append((x,y,.012));uv.append((x/2.8,y/2.8))
    if i:f.append([2*i-2,2*i-1,2*i+1,2*i])
mesh('Pilgrim walk',v,f,material('Paving',image=image('terrain/ground/stone_256.png')),uv)

# Batch rail and finial solids by material to keep the imported draw count low.
batches={}
def prism(mat,x,y,z,rings,n=4,angle=math.pi/4):
    v,f=batches.setdefault(mat,([],[])); off=len(v)
    for zoff,rx,ry in rings:
        v.extend((x+rx*math.cos(angle+i*2*math.pi/n),y+ry*math.sin(angle+i*2*math.pi/n),z+zoff) for i in range(n))
    f.append(list(range(off+n-1,off-1,-1)))
    for j in range(len(rings)-1):
        for i in range(n):
            a=off+j*n+i;b=off+j*n+(i+1)%n;f.append([a,b,b+n,a+n])
    f.append(list(range(off+(len(rings)-1)*n,off+len(rings)*n)))


for i in range(4):
    ends=[(-6.9,-4.22),(6.9,-4.22),(6.9,4.22),(-6.9,4.22)]
    x,y=ends[i];x2,y2=ends[(i+1)%4];n=6 if i%2==0 else 4
    for j in range(n):
        px=x+(x2-x)*j/n;py=y+(y2-y)*j/n; dx=(x2-x)/n;dy=(y2-y)/n
        prism(stone,px,py,0,[(0,.23,.23),(.12,.23,.23),(.16,.17,.17),(.63,.17,.17),(.67,.22,.22),(.76,.20,.20),(.87,.06,.06)])
        for z in [.22,.49]:
            rx=max(abs(dx)/2,.032)*1.415;ry=max(abs(dy)/2,.032)*1.415
            prism(iron,px+dx/2,py+dy/2,z,[(0,rx,ry),(.045,rx,ry)])
        for k in range(1,7):
            t=k/7; h=.60+.07*(k%2)
            prism(iron,px+dx*t,py+dy*t,0,[(0,.025,.025),(h-.09,.025,.025),(h-.06,.057,.057),(h+.05,.005,.005)])
for m,(v,f) in batches.items():mesh(m.name+' perimeter',v,f,m)

scatter('wide_crypts/wide_skull_mausoleum',3.12,1.25,[(-.95,3.02,2,1)])
scatter('props/obelisk',2.18,.56,[(-4.97,1.42,12,1),(4.89,2.7,-7,.91)])
scatter('props/grave_cracked',1.35,.35,[(-3.9,-.75,12,1),(4.15,.70,-11,1),(-4.4,3.04,4,.8)])
scatter('props/grave_celtic',1.52,.42,[(3.65,2.8,-10,1),(-5.62,-2.3,12,.83),(5.48,-1.11,-7,.9)])
scatter('props/brazier',1.37,.42,[(-2.65,1.55,5,1),(1.02,1.62,-5,1)])
scatter('props/red_mushrooms',.52,.34,[(-3.45,-1.10,24,1),(5.25,-1.48,-18,.85),(2.78,2.55,12,.82),(-5.4,1.06,-16,.96)])
scatter('props/candle_cluster',.55,.26,[(-1.49,1.86,10,1),(4.25,.26,-12,.85),(-5.9,-2.46,8,.8)])

bpy.ops.file.pack_all()
for a in bpy.context.screen.areas:
    if a.type=='VIEW_3D':
        from mathutils import Euler
        a.spaces.active.region_3d.view_rotation=Euler((math.radians(57),0,0)).to_quaternion()
        a.spaces.active.region_3d.view_distance=19
        a.spaces.active.shading.color_type='TEXTURE'
bpy.ops.wm.save_as_mainfile(filepath=str(Path(__file__).with_name('vesper_court.blend')),compress=True)
bpy.ops.export_scene.gltf(filepath=str(out/'vesper_court.glb'),export_format='GLB',export_yup=True)
