"""Build one voxel pet (headless Blender, the lihfolk-stud-voxel box rig) at its in-game size.

    python tools/pets/build_pet.py SnowBunny            # one creature
    python tools/pets/build_pet.py all                  # every file in tools/pets/creatures/
    python tools/pets/build_pet.py SnowBunny --quick    # export only (no renders)

Each creature file (tools/pets/creatures/<Id>.py) is a studlib creature (NAME = the CreatureConfig id,
plus RARITY). Two passes:
  1. export at 5 studs per metre and measure the model,
  2. rebuild with STUDS set so the model's biggest dimension (height or length) is the doc's pet size:
     3 studs, 20% bigger (3.6) for Legendary and Mythic.
Outputs: store-assets/creatures/<Id>/ (renders, sheet.png, loop.gif, the .blend, json) and the game's
build data src/replicated/Pets/Models/<Id>Data.luau + <Id>Clips.luau (built in game by PetBuild).
"""
import os, re, shutil, subprocess, sys, glob

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HERE = os.path.join(ROOT, 'tools', 'pets')
STUDLIB = os.path.join(HERE, 'voxel', 'studlib.py')
POST = os.path.join(HERE, 'voxel', 'post.py')
OUT = os.path.join(ROOT, 'store-assets', 'creatures')
GAME = os.path.join(ROOT, 'src', 'replicated', 'Pets', 'Models')
TMP = os.path.join(ROOT, 'tmp', 'pets')
SIZE = {'Common': 3.0, 'Uncommon': 3.0, 'Rare': 3.0, 'Epic': 3.0, 'Legendary': 3.6, 'Mythic': 3.6}


def blender():
    exe = os.environ.get('BLENDER_EXE')
    if exe:
        return exe
    found = sorted(glob.glob(r'C:\Program Files\Blender Foundation\*\blender.exe'))
    return found[-1]


def run(src, mode, out, studs, variants=False):
    env = dict(os.environ, PET_STUDS=str(studs))
    if variants:
        env['PET_VARIANTS'] = '1'
    r = subprocess.run([blender(), '-b', '--factory-startup', '--python', STUDLIB, '--', src, mode, out],
                       capture_output=True, text=True, env=env, encoding='utf8', errors='replace')
    text = r.stdout + r.stderr
    problems = [l for l in text.splitlines() if re.search(r'Traceback|Error|WARNING', l) and 'Color management' not in l]
    size = re.search(r'PET_SIZE_M ([\d.]+) ([\d.]+) ([\d.]+)', text)
    result = re.search(r'STUD_RESULT .*', text)
    if not size or not result:
        print(text[-3000:])
        raise SystemExit('build failed: ' + src)
    return [float(size.group(i)) for i in (1, 2, 3)], result.group(0), problems


def build(cid, quick=False):
    src = os.path.join(HERE, 'creatures', cid + '.py')
    rarity = re.search(r"^RARITY\s*=\s*'(\w+)'", open(src, encoding='utf8').read(), re.M).group(1)
    target = SIZE[rarity]
    (h, w, d), _, _ = run(src, 'export', os.path.join(TMP, cid), 5.0)
    studs = target / max(h, d)
    out = os.path.join(OUT, cid)
    if not quick and os.path.isdir(os.path.join(out, 'render')):
        shutil.rmtree(os.path.join(out, 'render'))
    (h, w, d), result, problems = run(src, 'export' if quick else 'all', out, studs, variants=True)
    if not quick:
        subprocess.run([sys.executable, POST, out], check=True, capture_output=True)
    os.makedirs(GAME, exist_ok=True)
    for suffix in ('Data.luau', 'Clips.luau'):
        shutil.copy(os.path.join(out, cid + suffix), os.path.join(GAME, cid + suffix))
    print('%s %s: %.2f studs tall, %.2f wide, %.2f long (%.3f studs/m). %s' % (cid, rarity, h * studs, w * studs, d * studs, studs, result))
    for p in problems:
        print('   ', p)


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    quick = '--quick' in sys.argv
    ids = args
    if ids == ['all']:
        ids = sorted(os.path.splitext(f)[0] for f in os.listdir(os.path.join(HERE, 'creatures')) if f.endswith('.py'))
    jobs = next((int(a.split('=')[1]) for a in sys.argv if a.startswith('--jobs=')), 1)
    if jobs > 1:
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(jobs) as pool:
            list(pool.map(lambda cid: build(cid, quick), ids))
    else:
        for cid in ids:
            build(cid, quick)
