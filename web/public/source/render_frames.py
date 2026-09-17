"""Resume-safe Cycles rendering. Invoke with Blender -b scene.blend --python ..."""
import bpy, pathlib, datetime, json, time, sys
R=pathlib.Path(__file__).resolve().parents[1];s=bpy.context.scene;folder=R/'output/frames';folder.mkdir(exist_ok=True)
prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
for d in prefs.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.render.use_persistent_data=True
begin=time.monotonic()
for frame in range(s.frame_start,s.frame_end+1):
    dest=folder/f'{frame:04}.png'
    if dest.exists() and dest.stat().st_size>50000:continue
    s.frame_set(frame);s.render.filepath=str(dest);bpy.ops.render.render(write_still=True)
    if frame%24==0 or frame==s.frame_end:
        row={'time':datetime.datetime.now(datetime.timezone.utc).isoformat(),'stage':'06_blender','event':'render_progress','status':'SUCCEEDED' if frame==s.frame_end else 'IN_PROGRESS','progress':round(30+frame/s.frame_end*70),'frame':frame,'total_frames':s.frame_end,'elapsed_seconds':round(time.monotonic()-begin,2)}
        with (R/'logs/events.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(row)+'\n')
        print(json.dumps(row),flush=True)
