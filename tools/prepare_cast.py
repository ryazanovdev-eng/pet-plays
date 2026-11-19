"""Rebuild M3 cast from the local raw delivery. Python 3 + Pillow, no resampling.

python tools/prepare_cast.py [--contacts PATH]
The optional review sheets are previews only; never put them in the game tree.
"""
from argparse import ArgumentParser
from bisect import bisect_right
from collections import defaultdict
from functools import lru_cache
import json
from pathlib import Path
import re
from shutil import copyfile

from PIL import Image, ImageChops, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'raw/FrogKnight_Animations'
OUT = ROOT / 'assets/cast'
ACTIONS = ('idle', 'walk', 'attack1', 'attack2', 'hurt', 'death')
# Registered native top-lefts on the undivided boss masters (not artwork bboxes).
BOSS_Y = {'boss_bone_king': (-65, 155, 387, 625, 873, 1181),
          'boss_rotten_giant': (-67, 172, 433, 661, 910, 1181)}
BOSS_X = (0, 264, 528, 791)
# Pixel positions of transparent valleys, used to assign *whole* islands rather
# than cutting on a rectangular grid. Includes detached magic and impact debris.
ROW_BREAKS = {'boss_bone_king': (247, 463, 699, 932, 1181),
              'boss_rotten_giant': (242, 486, 743, 981, 1227),
              'attack': (346, 685), 'walk': (357, 719), 'hurt': (368, 724)}
COLUMN_BREAKS = {'attack': (300, 586, 1127), 'walk': (341, 690, 1121),
                 'hurt': (367, 713, 1082)}
# Old on-screen scale is now exclusively a node transform. Baseline estimates
# use standing and walking soles, not the changing edges of weapon and FX.
# family: (native size, transparent margin left/top, source pivot, scale, speeds)
PROFILES = {
    'frog': ((627,627), (0,0), (313,539), 64/627, (4.5,8,10.5,7,5.5)),
    'skeleton': ((627,627), (0,0), (313,545), 88/627, (5,8,10,6.5,5)),
    'zombie': ((627,627), (0,0), (313,576), 88/627, (4.5,7,9,6.25,4.75)),
    'ghost': ((400,400), (120,16), (200,364), 88/400, (4.25,7.5,9.5,6.75,4.75)),
    'boss_bone_king': ((264,310), (56,16), (132,302), 180/264, (4.5,7,9,8.5,6.25,5.5)),
    'boss_rotten_giant': ((264,310), (56,16), (132,300), 180/264, (4.25,6.75,8.75,8,6,5.25)),
}


def islands(alpha):
    """8-connected runs on a binary image; no scipy dependency."""
    w,h = alpha.size
    data = alpha.tobytes()
    roots, runs, prev = [], [], []
    def root(i):
        while roots[i] != i:
            roots[i] = roots[roots[i]]
            i = roots[i]
        return i
    for y in range(h):
        row, start = [], 0
        for match in re.finditer(b'\xff+', data[y*w:(y+1)*w]):
            x,r = match.span(); i = len(roots)
            roots.append(i); runs.append((x,y,r)); row.append((x,r,i))
            while start < len(prev) and prev[start][1] < x:
                start += 1
            for k in range(start,len(prev)):
                if prev[k][0] > r:
                    break
                roots[root(prev[k][2])] = i
        prev = row
    groups = defaultdict(list)
    for i,run in enumerate(runs):
        groups[root(i)].append(run)
    return groups.values()


@lru_cache(maxsize=5)
def extract_master(key):
    boss = key in BOSS_Y
    path = RAW/'reference_sources'/(f'{key}_approved_sheet_4x6.png' if boss
                                    else f'ghost_{key}_approved_reference.png')
    master = Image.open(path).convert('RGBA')
    # For segmentation only. Actual output is the original straight RGBA,
    # including its partially transparent edge, not a binary alpha image.
    strong = master.getchannel('A').point(lambda a: 255 if a >= 24 else 0)
    ownership = defaultdict(list)
    for runs in islands(strong):
        if sum(r-x for x,y,r in runs) < 3:
            continue
        x = (min(x for x,y,r in runs)+max(r for x,y,r in runs))/2
        y = (runs[0][1]+runs[-1][1])/2
        row = bisect_right(ROW_BREAKS[key], y)
        # The giant's third stomp sprays across the left and right cell lines.
        cuts = ((260,495,798) if key=='boss_rotten_giant' and row==2
                else (250,497,782) if key=='boss_bone_king' and row==3
                else COLUMN_BREAKS.get(key,(264,528,791)))
        col = bisect_right(cuts,x)
        ownership[row,col].extend(runs)
    result = {}
    for rc,runs in ownership.items():
        x0 = min(x for x,y,r in runs)-5; x1 = max(r for x,y,r in runs)+5
        y0 = min(y for x,y,r in runs)-5; y1 = max(y for x,y,r in runs)+6
        box = (x0,y0,x1,y1)
        tile = master.crop(box)
        mask = Image.new('L',tile.size)
        pen = ImageDraw.Draw(mask)
        for x,y,r in runs:
            pen.line((x-x0,y-y0,r-1-x0,y-y0),fill=255)
        # Retain the soft fringe surrounding our islands, never borrow solid
        # pixels from another island. Neither filter is applied to the artwork.
        margin = mask.filter(ImageFilter.MaxFilter(9))
        margin = ImageChops.subtract(margin,ImageChops.subtract(strong.crop(box),mask))
        tile.putalpha(ImageChops.multiply(tile.getchannel('A'),margin))
        box2 = tile.getbbox(); tile = tile.crop(box2)
        result[rc] = (tile, (x0+box2[0],y0+box2[1]),path)
    return result


def put_checked(canvas,tile,pos):
    b = tile.getbbox(); x,y = pos
    if not (0<=b[0]+x and 0<=b[1]+y and b[2]+x<=canvas.width and b[3]+y<=canvas.height):
        raise ValueError(f'Artwork outside canvas: {b} + {pos} in {canvas.size}')
    canvas.paste(tile,pos)  # no blend: preserve straight RGBA including translucent pixels


def resource(cid, animations, scale, pivot):
    deps, clips = [], []
    for name,clip in animations.items():
        frames = []
        for i,frame in enumerate(clip['frames'],1):
            key = f'{name}_{i:02d}'
            deps.append(f'[ext_resource type="Texture2D" path="{frame["path"]}" id="{key}"]')
            frames.append('{"duration": 1.0, "texture": ExtResource("'+key+'")}')
        clips.append('{\n"frames": ['+',\n'.join(frames)+'],\n"loop": '+
                     str(clip['loop']).lower()+f',\n"name": &"{name}",\n"speed": {float(clip["fps"])}\n'+'}')
    (OUT/f'{cid}.tres').write_text('[gd_resource type="SpriteFrames" format=3]\n\n'+
                                   '\n'.join(deps)+'\n\n[resource]\nanimations = ['+', '.join(clips)+']\n',encoding='utf-8')
    (ROOT/f'game/cast/{cid}.tscn').write_text(f'''[gd_scene format=3]

[ext_resource type="SpriteFrames" path="res://assets/cast/{cid}.tres" id="frames"]

[node name="{cid}" type="AnimatedSprite2D"]
scale = Vector2({scale:.10f}, {scale:.10f})
texture_filter = 2
sprite_frames = ExtResource("frames")
animation = &"idle"
autoplay = "idle"
centered = false
offset = Vector2({-pivot[0]}, {-pivot[1]})
''',encoding='utf-8')


def contact(cid,char,dest):
    # Thumbnail only the review image, never the individual production PNGs.
    actions = char['animations']; scale = char['game_scale']; ox,oy = char['pivot_px']
    tile_w = 240; tile_h = 235 if cid in BOSS_Y else 160
    sheet = Image.new('RGB',(4*tile_w,len(actions)*tile_h),(57,68,72)); d=ImageDraw.Draw(sheet)
    for row,(action,clip) in enumerate(actions.items()):
        for col,frame in enumerate(clip['frames']):
            im=Image.open(ROOT/frame['path'][6:]); x=col*tile_w; y=row*tile_h
            factor = scale if cid in BOSS_Y else scale*1.45
            sprite=im.resize((round(im.width*factor),round(im.height*factor)),Image.Resampling.LANCZOS)
            foot=(x+tile_w//2,y+tile_h-32)
            d.line((x,foot[1],x+tile_w-2,foot[1]),fill=(92,103,107))
            sheet.paste(sprite,(foot[0]-round(ox*factor),foot[1]-round(oy*factor)),sprite)
            d.text((x+7,y+tile_h-18),f'{action}/{col+1:02d}    {clip["fps"]} fps',fill='white')
    sheet.save(dest/f'{cid}.png')


def main(dest):
    data=json.loads((RAW/'manifest.json').read_text(encoding='utf-8'))
    manifest={'schema_version':2,'source':'res://raw/FrogKnight_Animations/manifest.json',
              'format':'native straight-alpha RGBA PNG; no filtering or resampling of artwork',
              'bbox_convention':'xyxy, exclusive maximum', 'characters':{}}
    if dest: dest.mkdir(parents=True,exist_ok=True)
    for cid,record in data['character_data'].items():
        family = cid if cid in BOSS_Y else cid.split('_')[0]
        native,pad,anchor,scale,rates=PROFILES[family]
        source=RAW/'characters'/record['type']/cid
        pivot=[a+b for a,b in zip(anchor,pad)]
        size=tuple(a+2*b for a,b in zip(native,pad))
        char={'sprite_frames':f'res://assets/cast/{cid}.tres','scene':f'res://game/cast/{cid}.tscn',
              'source_directory':source.relative_to(ROOT).as_posix(),'source_frame_size_px':native,
              'frame_size_px':size,'source_padding_xy':pad,'pivot_px':pivot,'game_scale':scale,'animations':{}}
        manifest['characters'][cid]=char
        actions = ACTIONS if cid in BOSS_Y else ('idle','walk','attack','hurt','death')
        assert set(actions)==set(record['animations'])
        for action,rate in zip(actions,rates,strict=True):
            rawclip=record['animations'][action]; assert tuple(rawclip['cell_size_px'])==native
            clip={'fps':rate,'loop':rawclip['loop'],'frames':[]}; char['animations'][action]=clip
            folder=OUT/cid/action; folder.mkdir(parents=True,exist_ok=True)
            for col,ref in enumerate(rawclip['frames']):
                p=source/ref['file']; raw=Image.open(p); assert raw.mode=='RGBA' and raw.size==native
                out=folder/p.name; frame={'path':'res://'+out.relative_to(ROOT).as_posix()}
                if cid in BOSS_Y or (family=='ghost' and (action in ('walk','attack') or (action=='hurt' and col==1))):
                    key=cid if cid in BOSS_Y else action
                    row=ACTIONS.index(action) if cid in BOSS_Y else ('ghost_blue','ghost_purple','ghost_green').index(cid)
                    tile,corner,master=extract_master(key)[row,col]
                    mx,my=(BOSS_X[col],BOSS_Y[cid][row]) if cid in BOSS_Y else (362*col-19,362*row-19)
                    im=Image.new('RGBA',size); put_checked(im,tile,(corner[0]-mx+pad[0],corner[1]-my+pad[1]))
                    im.save(out); frame.update(master=master.relative_to(ROOT).as_posix(),
                        canvas_origin_on_master_xy=[mx-pad[0],my-pad[1]],export_repair='whole native pose and associated FX isolated from approved master')
                elif any(pad):
                    im=Image.new('RGBA',size); put_checked(im,raw,pad); im.save(out)
                else:
                    copyfile(p,out); im=raw
                alpha=im.getchannel('A'); frame.update(alpha_bbox_xyxy=alpha.getbbox(),alpha_max=alpha.getextrema()[1]); clip['frames'].append(frame)
        resource(cid,char['animations'],scale,pivot)
        if dest: contact(cid,char,dest)
    chars=manifest['characters']; animations=[a for c in chars.values() for a in c['animations'].values()]
    manifest.update(characters_total=len(chars),animations_total=len(animations),frames_total=sum(len(a['frames']) for a in animations))
    (OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':
    args=ArgumentParser(description=__doc__); args.add_argument('--contacts',type=Path)
    main(args.parse_args().contacts)
