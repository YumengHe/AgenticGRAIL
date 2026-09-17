"""Keep the local journal current; encode once the current render completes."""
import pathlib,time,json,subprocess,sys
R=pathlib.Path(__file__).resolve().parents[1];last=None;deadline=time.monotonic()+3600
while time.monotonic()<deadline:
    log=R/'logs/events.jsonl'
    stamp=log.stat().st_mtime
    if stamp!=last:
        subprocess.run([sys.executable,str(R/'scripts/sync_web.py')],check=True,cwd=R)
        last=stamp
    events=[json.loads(line) for line in log.read_text(encoding='utf-8').splitlines() if line]
    if any(e.get('event')=='render_progress' and e.get('status')=='SUCCEEDED' for e in events):
        subprocess.run([sys.executable,str(R/'scripts/encode_video.py')],check=True,cwd=R)
        subprocess.run([sys.executable,str(R/'scripts/sync_web.py')],check=True,cwd=R)
        print('ENCODE_AND_SYNC_COMPLETE',flush=True);break
    time.sleep(15)
else:raise SystemExit('Render not completed within one hour; PNGs retained for resumption.')
