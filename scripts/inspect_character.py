import bpy, json, pathlib, sys
R=pathlib.Path(__file__).resolve().parents[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
source=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'character_taichi.glb'
if source.endswith('.fbx'): bpy.ops.import_scene.fbx(filepath=str(R/'assets'/source))
else: bpy.ops.import_scene.gltf(filepath=str(R/'assets'/source))
report={'objects':[], 'actions':[]}
for o in bpy.data.objects:
    d={'name':o.name,'type':o.type,'location':list(o.location),'scale':list(o.scale),'dimensions':list(o.dimensions)}
    if o.type=='ARMATURE':
        d['bones']=[{'name':b.name,'parent':b.parent.name if b.parent else None,'head':list(b.head_local),'tail':list(b.tail_local)} for b in o.data.bones]
    if o.type=='MESH': d['vertices']=len(o.data.vertices);d['faces']=len(o.data.polygons)
    report['objects'].append(d)
for a in bpy.data.actions:
    report['actions'].append({'name':a.name,'range':list(a.frame_range),'slots':[s.identifier for s in a.slots]})
(R/'output/inspect.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
