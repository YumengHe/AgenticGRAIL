"""Check distributable artifacts, GLB motion, archive portability and secret exclusion."""
import pathlib,json,struct,zipfile,re
R=pathlib.Path(__file__).resolve().parents[1]
data=(R/'output/character_web.glb').read_bytes();magic,version,total=struct.unpack_from('<4sII',data)
assert magic==b'glTF' and version==2 and total==len(data)
length,kind=struct.unpack_from('<II',data,12);g=json.loads(data[20:20+length])
assert len(g['skins'])==1 and len(g['skins'][0]['joints'])==24
assert len(g['animations'])==1
a=g['animations'][0];duration=max(g['accessors'][x['input']]['max'][0] for x in a['samplers'])
assert 17.9<duration<=18.1,duration
for channel in a['channels']:assert channel['target']['node']<len(g['nodes'])
with zipfile.ZipFile(R/'output/blender_portable.zip') as z:
    assert not z.testzip();assert 'taichi_scene_2k.blend' in z.namelist()
env=(R/'.env').read_text(encoding='utf-8-sig');match=re.search(r'msy_[A-Za-z0-9_-]+',env)
if match:secret=match.group(0).encode()
else:secret=env.strip().split('=',1)[-1].strip().strip('\"\'').encode()
files=list((R/'web/public').rglob('*'))
for f in files:
    if f.is_file():
        assert secret not in f.read_bytes(),f'Unexpected secret in {f.name}'
        assert f.stat().st_size<25*1024*1024,f'Over hosting asset size limit: {f.name}'
print(json.dumps({'glb_bones':24,'glb_clips':len(g['animations']),'glb_duration':duration,'glb_bytes':len(data),'portable_archive_bytes':(R/'output/blender_portable.zip').stat().st_size,'public_files_checked':sum(f.is_file() for f in files),'secret_scan':'passed'},indent=2))
