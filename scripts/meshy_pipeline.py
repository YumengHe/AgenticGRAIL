"""Resumable Meshy production pipeline. Credentials never enter artifacts or logs."""
import argparse, concurrent.futures, datetime, json, os, pathlib, re, time, urllib.request, urllib.error

ROOT = pathlib.Path(__file__).resolve().parents[1]
PRIVATE = ROOT / 'logs/private'
PRIVATE.mkdir(parents=True, exist_ok=True)
ASSETS = ROOT / 'assets'
ASSETS.mkdir(exist_ok=True)
BASE = 'https://api.meshy.ai'

def key():
    raw = (ROOT / '.env').read_text(encoding='utf-8-sig').strip()
    found = re.search(r'msy_[A-Za-z0-9_-]+', raw)
    if found: return found.group(0)
    for line in raw.splitlines():
        if '=' in line and not line.startswith('#'):
            return line.split('=', 1)[1].strip().strip('\"\'')
    return raw

def save(path, value):
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    temp.replace(path)

def log(stage, event, **extra):
    entry = {'time': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'stage': stage, 'event': event, **extra}
    with (ROOT / 'logs/events.jsonl').open('a', encoding='utf-8') as f: f.write(json.dumps(entry, ensure_ascii=False)+'\n')
    print(json.dumps(entry, ensure_ascii=True), flush=True)

def api(path, payload=None):
    req = urllib.request.Request(BASE + path, data=json.dumps(payload).encode() if payload is not None else None,
        headers={'Authorization': 'Bearer ' + key(), 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=90) as response: return json.load(response)
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors='replace').replace(key(), '[REDACTED]')
        raise RuntimeError(f'Meshy HTTP {e.code}: {body[:1500]}') from None

def task(stage, endpoint, payload):
    path = PRIVATE / (stage + '.json')
    if path.exists():
        record = json.loads(path.read_text(encoding='utf-8'))
    else:
        log(stage, 'submitted', endpoint=endpoint, parameters=payload)
        record = {'id': api(endpoint, payload)['result'], 'endpoint': endpoint, 'parameters': payload}
        save(path, record)
    last = None
    deadline = time.monotonic() + 3600
    while time.monotonic() < deadline:
        data = api(endpoint + '/' + record['id'])
        record['response'] = data
        save(path, record)
        status = (data.get('status'), data.get('progress'))
        if status != last:
            log(stage, 'progress', task_id=record['id'], status=status[0], progress=status[1], consumed_credits=data.get('consumed_credits'))
            last = status
        if status[0] == 'SUCCEEDED': return record['id'], data
        if status[0] in ('FAILED', 'CANCELED'): raise RuntimeError(f'{stage}: {data.get("task_error")}')
        time.sleep(15)
    raise TimeoutError(f'{stage}: still pending; resume the same task by rerunning')

def download(url, name):
    if not url: return
    dest = ASSETS / name
    if dest.exists() and dest.stat().st_size: return
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=180) as r, dest.with_suffix(dest.suffix+'.part').open('wb') as f:
        while block := r.read(1024*1024): f.write(block)
    dest.with_suffix(dest.suffix+'.part').replace(dest)
    log('download', 'saved', file='assets/'+name, bytes=dest.stat().st_size)

CHARACTER = ('Full-body stylized adult East Asian woman martial artist, elegant friendly animated film character, '
    'slightly cartoon proportions, expressive eyes and refined face. Black hair in a compact neat bun, silver hairpin. '
    'Black fitted traditional Tai Chi mandarin-collar jacket with silver frog buttons and thin silver piping, '
    'long sleeves ending at wrists, separate black loose tapered trousers, black flat kung fu shoes. '
    'Small silver earrings, silver wrist bracelets, silver waist clasp. Opaque modest clothing. '
    'Symmetric neutral A-pose, hands open separated fingers, arms away from body, legs shoulder width apart. '
    'Single complete humanoid, clear limbs for skeletal rigging, no props, no base, no scenery.')
TEXTURE = ('Stylized animated-film adult Chinese woman. Black hair, warm natural skin, dark brown eyes. '
    'Rich charcoal-black silk Tai Chi jacket and black trousers. Silver metallic frog closures, silver piping, '
    'silver bracelets, silver hairpin and silver small earrings. Black flat shoes. Clean elegant premium character, '
    'subtle fabric weave, no gold, no colorful accents, no painted shadows.')
MOTION = ('A woman slowly performs graceful Tai Chi cloud hands. Knees gently bent in a wide grounded stance, '
    'weight shifts smoothly left and right, torso turns softly. Both open hands trace large flowing circular arcs '
    'in front of the chest, one rising as the other lowers. Relaxed shoulders, controlled wrists, calm balanced continuous movement. '
    'No fighting, jumping or fast punches.')

def character():
    preview_id, p = task('01_geometry', '/openapi/v2/text-to-3d', {
        'mode':'preview','prompt':CHARACTER,'ai_model':'meshy-7','should_remesh':True,
        'target_polycount':45000,'topology':'triangle','pose_mode':'a-pose','target_formats':['glb']})
    download(p.get('thumbnail_url'), 'geometry_preview.png')
    download(p.get('model_urls',{}).get('glb'), 'character_geometry.glb')
    refined_id, r = task('02_texture', '/openapi/v2/text-to-3d', {
        'mode':'refine','preview_task_id':preview_id,'enable_pbr':True,'texture_resolution':'4k',
        'texture_prompt':TEXTURE,'target_formats':['glb']})
    download(r.get('thumbnail_url'), 'character_preview.png')
    download(r.get('model_urls',{}).get('glb'), 'character_textured.glb')
    rig_id, rig = task('03_rigging','/openapi/v1/rigging',{'input_task_id':refined_id,'height_meters':1.68})
    download(rig['result'].get('rigged_character_glb_url'), 'character_rigged.glb')
    download(rig['result'].get('rigged_character_fbx_url'), 'character_rigged.fbx')
    return rig_id

def motion():
    mid, m = task('04_motion','/openapi/v1/text-to-motion',{'prompt':MOTION,'mode':'prime','duration':10})
    download(m['result'].get('motion_url'), 'taichi_motion.'+m['result'].get('motion_format','fbx'))
    return mid

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--balance',action='store_true'); parser.add_argument('--library',action='store_true'); args=parser.parse_args()
    if args.library:
        print(json.dumps(api('/openapi/v1/animations/library?search=tai'),ensure_ascii=True)); return
    balance = api('/openapi/v1/balance'); log('account','balance',**balance)
    if args.balance: return
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        char_future=executor.submit(character); motion_future=executor.submit(motion)
        rig_id=char_future.result(); motion_id=motion_future.result()
    aid, a = task('05_retarget','/openapi/v1/animations',{'rig_task_id':rig_id,'motion_task_id':motion_id})
    download(a['result'].get('animation_glb_url'), 'character_taichi.glb')
    download(a['result'].get('animation_fbx_url'), 'character_taichi.fbx')
    log('pipeline','assets_ready',animation_task=aid)
    log('account','balance_after',**api('/openapi/v1/balance'))

if __name__=='__main__':
    try: main()
    except Exception as e:
        log('pipeline','error',message=str(e).replace(key(),'[REDACTED]'))
        raise SystemExit(1)
