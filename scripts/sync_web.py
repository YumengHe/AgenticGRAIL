"""Copy only public artifacts and sanitized provenance into the viewer."""
import json, pathlib, shutil, datetime
R=pathlib.Path(__file__).resolve().parents[1]; P=R/'web/public'
for d in ['media','data','source']: (P/d).mkdir(parents=True,exist_ok=True)
events=[json.loads(l) for l in (R/'logs/events.jsonl').read_text(encoding='utf-8').splitlines() if l.strip()]
steps=[('01_geometry','角色重建','Meshy Text to 3D · A-pose · 45,000 面'),('02_texture','服装与材质','4K PBR · 黑衣 · 银饰'),('03_rigging','骨架绑定','Meshy 自动骨架 · 蒙皮权重'),('04_motion','太极动作','Text to Motion · 云手 · 10 秒原始动作'),('05_retarget','动作重定向','动作映射到角色骨架'),('06_blender','场景与渲染','Blender · 灯光、镜头与逐帧渲染'),('07_delivery','成片输出','H.264 MP4 · 网页归档')]
data={'updated':datetime.datetime.now(datetime.timezone.utc).isoformat(),'events':events,'steps':[],'files':[],'ready':False}
for sid,title,detail in steps:
    rows=[e for e in events if e['stage']==sid]; last=rows[-1] if rows else {}
    data['steps'].append({'id':sid,'title':title,'detail':detail,'status':last.get('status','PENDING'),'progress':last.get('progress',0),'taskId':last.get('task_id'),'credits':last.get('consumed_credits')})
for src,name,title in [('assets/character_preview.png','character_preview.png','角色预览'),('assets/geometry_preview.png','geometry_preview.png','几何预览'),('output/poster.jpg','poster.jpg','成片封面'),('output/taichi_final.mp4','taichi_final.mp4','1080p 成片'),('output/character_web.glb','character.glb','带动作的角色 GLB'),('output/skeleton_preview.mp4','skeleton_preview.mp4','骨架动作视频'),('output/contact_sheet.jpg','contact_sheet.jpg','动作检查图')]:
    f=R/src
    if f.exists():
        shutil.copy2(f,P/'media'/name);data['files'].append({'name':title,'url':'/media/'+name,'bytes':f.stat().st_size})
        if name=='taichi_final.mp4': data['ready']=True
portable=R/'output/blender_portable.zip'
if portable.exists():
    shutil.copy2(portable,P/'media/blender_portable.zip');data['files'].append({'name':'Blender 工程（2K）','url':'/media/blender_portable.zip','bytes':portable.stat().st_size})
for name in ['meshy_pipeline.py','build_scene.py','render_frames.py','encode_video.py','sync_web.py','verify_motion.py','package_blender.py']:
    if (R/'scripts'/name).exists(): shutil.copy2(R/'scripts'/name,P/'source'/name)
for name in ['scene_report.json','video_report.json','motion_quality.json']:
    if (R/'output'/name).exists():
        data[name.replace('.json','')]=json.loads((R/'output'/name).read_text(encoding='utf-8'));shutil.copy2(R/'output'/name,P/'data'/name)
if (R/'README.md').exists(): shutil.copy2(R/'README.md',P/'source/README.md')
for name,value in [('project',data),('events',events)]: (P/f'data/{name}.json').write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
print('Synced',len(events),'events and',len(data['files']),'artifacts')
