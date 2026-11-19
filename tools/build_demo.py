"""Bake the offline art showcase from imported Godot scenes and SpriteFrames."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

from PIL import Image, ImageChops, ImageOps

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'demo' / 'media'
GODOT = (os.environ.get('GODOT_CONSOLE') or os.environ.get('GODOT_BIN') or
         shutil.which('godot') or r'D:\godot\Godot_v4.7.2-stable_win64_console.exe')


def godot(*args):
    run = subprocess.run([GODOT, '--path', str(ROOT), *map(str, args)], cwd=ROOT,
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    log = run.stdout.decode('utf-8', 'replace')
    print(log, flush=True)
    if run.returncode or 'ERROR:' in log:
        raise SystemExit(f'Godot failed: {args}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('items', nargs='*', help='cast, arena, arena_edge, arena_wave, level_up, shop, gallery, inventory or one sheet')
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    for obsolete in ('hybrid.webp', 'hybrid-motion.webp'):
        (OUT / obsolete).unlink(missing_ok=True)
    for item in args.items or ('cast', 'arena', 'arena_edge', 'arena_wave', 'level_up', 'shop', 'gallery', 'inventory'):
        if item == 'cast':
            godot('--headless', '--script', 'res://tools/demo_frames.gd')
            # The static design portraits are distinct from the animated Godot poses.
            for png in (ROOT / 'assets' / 'portraits').glob('*.png'):
                with Image.open(png) as image:
                    ImageOps.contain(image, (264, 216)).save(OUT / (png.stem + '-portrait.webp'), lossless=True)
                (OUT / (png.stem + '.webp')).unlink(missing_ok=True)  # old reduced atlas
            continue
        catalog = {p.stem: p for p in (ROOT / 'game' / 'arena_inventory').glob('*.tscn')}
        stills = {key: ROOT / 'game' / (key + '.tscn') for key in ('level_up', 'shop')}
        if item == 'inventory' or item in catalog or item in stills:
            selected = sorted(catalog.values()) if item == 'inventory' else [(stills | catalog)[item]]
            for scene in selected:
                with tempfile.TemporaryDirectory() as temp:
                    count = 10 if item in stills else 2
                    godot('--resolution', '1280x720', '--fixed-fps', '12', '--write-movie',
                          Path(temp) / 'frame.png', '--quit-after', str(count), 'res://' + scene.relative_to(ROOT).as_posix())
                    captures = sorted(Path(temp).glob('*.png'))
                    if len(captures) != count:
                        raise SystemExit(f'{scene.stem}: incomplete capture')
                    with Image.open(captures[1]) as sample:
                        still = sample.convert('RGB')
                    if item in stills:
                        # A modal is a paused moment, not just an animation exported as a still.
                        for path in captures[2:]:
                            with Image.open(path) as later:
                                if ImageChops.difference(still, later.convert('RGB')).getbbox():
                                    raise SystemExit(f'{item}: movement behind the modal at {path.name}')
                    still.save(OUT / (scene.stem + '.webp'), lossless=True)
            continue
        if item not in ('arena', 'arena_edge', 'arena_wave', 'gallery'):
            parser.error('Unknown scene: ' + item)
        with tempfile.TemporaryDirectory() as temp:
            godot('--resolution', '1280x720', '--fixed-fps', '24', '--write-movie',
                  Path(temp) / 'frame.png', '--quit-after', '49', f'res://game/{item}.tscn')
            paths = sorted(Path(temp).glob('*.png'))[1:]
            if len(paths) != 48:
                raise SystemExit(f'{item}: expected 48 rendered frames, got {len(paths)}')
            frames = []
            for path in paths:
                with Image.open(path) as sample:
                    frames.append(sample.convert('RGB'))
            frames[0].save(OUT / f'{item}.webp', lossless=True)
            frames[0].save(OUT / f'{item}-motion.webp', save_all=True, append_images=frames[1:],
                           duration=[42,41,42]*16, loop=0, lossless=True, method=3)
