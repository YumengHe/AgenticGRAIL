"""Import the real Meshy skin, bake slowed skeletal animation, stage and render QA."""
import bpy, math, json, pathlib, sys, datetime
from mathutils import Vector
R=pathlib.Path(__file__).resolve().parents[1]; OUT=R/'output'; OUT.mkdir(exist_ok=True)
def log(event,**kw):
    x={'time':datetime.datetime.now(datetime.timezone.utc).isoformat(),'stage':'06_blender','event':event,**kw}
    with (R/'logs/events.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(x,ensure_ascii=False)+'\n')
    print(json.dumps(x),flush=True)
def point(obj,target):obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()
def material(name,color,rough=.5,metal=0):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
    return m
def bounds(obj):
    e=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());return [e.matrix_world@v.co for v in e.data.vertices]
def area(name,loc,power,color,size,target=(0,0,.8),shape='DISK'):
    d=bpy.data.lights.new(name,'AREA');d.energy=power;d.color=color;d.shape=shape;d.size=size
    o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o);o.location=loc;point(o,target);return o

bpy.ops.wm.read_factory_settings(use_empty=True)
s=bpy.context.scene;s.render.fps=24
bpy.ops.import_scene.gltf(filepath=str(R/'assets/character_taichi.glb'))
arm=next(o for o in bpy.data.objects if o.type=='ARMATURE')
meshes=[o for o in bpy.data.objects if o.type=='MESH' and len(o.data.vertices)>1000]
for o in list(bpy.data.objects):
    if o.type=='MESH' and o not in meshes:bpy.data.objects.remove(o,do_unlink=True)
mesh=meshes[0]
for p in mesh.data.polygons:p.use_smooth=True
for tr in list(arm.animation_data.nla_tracks):arm.animation_data.nla_tracks.remove(tr)
source=max(bpy.data.actions,key=lambda a:a.frame_range[1]-a.frame_range[0]);arm.animation_data.action=source;arm.animation_data.action_slot=source.slots[0]
start,end=map(float,source.frame_range);frames=432
# glTF display lengths contain a centimeter/meter mismatch; shorten along the
# existing bone axis only, preserving rest orientations and all skin matrices.
bpy.context.view_layer.objects.active=arm;arm.select_set(True);bpy.ops.object.mode_set(mode='EDIT')
for b in arm.data.edit_bones:b.length=max(.1,b.length*.01)
bpy.ops.object.mode_set(mode='OBJECT');arm.show_in_front=True;arm.data.display_type='OCTAHEDRAL'
samples=[];foot_samples=[]
for f in range(1,frames+1):
    t=start+(end-start)*(f-1)/(frames-1);s.frame_set(math.floor(t),subframe=t%1);bpy.context.view_layer.update()
    poses={b.name:(b.location.copy(),b.rotation_quaternion.copy(),b.scale.copy()) for b in arm.pose.bones}
    samples.append(poses)
    if f%12==1:
        bb=bounds(mesh);foot_samples.append({'frame':f,'min_z':min(v.z for v in bb),'max_z':max(v.z for v in bb),'x_min':min(v.x for v in bb),'x_max':max(v.x for v in bb),'y_min':min(v.y for v in bb),'y_max':max(v.y for v in bb)})
arm.animation_data.action=None
for i,poses in enumerate(samples,1):
    for b in arm.pose.bones:
        b.rotation_mode='QUATERNION';b.location,b.rotation_quaternion,b.scale=poses[b.name]
        for prop in ['location','rotation_quaternion','scale']:b.keyframe_insert(prop,frame=i,group=b.name)
arm.animation_data.action.name='TAICHI_CloudHands_18s_Baked'
arm.data.pose_position='REST';bpy.context.view_layer.update()
rest_floor=min(v.z for v in bounds(mesh));arm.location.z=-rest_floor+.004
arm.data.pose_position='POSE';bpy.context.view_layer.update()
# Pin the ankle contact targets, and preserve the shoe's rest orientation.
# The upper body retains the generated motion, while two-bone leg IK solves
# the knees under the changing hip weight. These remain editable controls.
for side in ['Left','Right']:
    foot=arm.pose.bones[side+'Foot'];rest=arm.matrix_world@foot.bone.matrix_local
    target=bpy.data.objects.new('CTRL_'+side+'_Ankle',None);bpy.context.collection.objects.link(target)
    target.empty_display_type='SPHERE';target.empty_display_size=.055;target.matrix_world=rest
    ik=arm.pose.bones[side+'Leg'].constraints.new('IK');ik.name='Grounded ankle · 2 bone IK';ik.target=target;ik.chain_count=2;ik.use_stretch=False
    orient=foot.constraints.new('COPY_ROTATION');orient.name='Keep shoe planted';orient.target=target;orient.target_space='WORLD';orient.owner_space='WORLD'
    toe=arm.pose.bones[side+'ToeBase'];toe.rotation_quaternion=(1,0,0,0)
s.frame_start=1;s.frame_end=frames;s.frame_set(160)
log('motion_baked',status='IN_PROGRESS',progress=15,bones=len(arm.data.bones),frames=frames,source_frames=[start,end],duration=18,correction='Two ankle targets with 2-bone IK and world-space shoe orientation')
(OUT/'motion_quality.json').write_text(json.dumps({'foot_bounds_before_global_ground_alignment':foot_samples},indent=2),encoding='utf-8')
# Export a compact independent rig for the web viewer; downscale only this copy.
swaps=[]
for mat in bpy.data.materials:
    if mat.use_nodes:
        for node in mat.node_tree.nodes:
            if node.type=='TEX_IMAGE' and node.image and node.image.size[0]>2048:
                original=node.image;small=original.copy();small.scale(2048,2048);node.image=small;swaps.append((node,original,small))
bpy.ops.object.select_all(action='DESELECT');arm.select_set(True)
for o in meshes:o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(OUT/'character_web.glb'),export_format='GLB',use_selection=True,export_animations=True,export_animation_mode='ACTIVE_ACTIONS',export_frame_range=True,export_force_sampling=True,export_image_format='JPEG',export_jpeg_quality=88)
for node,original,small in swaps:node.image=original;bpy.data.images.remove(small)

stone=material('Pearl limestone',(.30,.36,.37),.7)
floor=material('Cool silver studio',(.37,.43,.45),.68)
silver=material('Brushed silver',(.53,.61,.64),.32,.75)
dark=material('Graphite inset',(.025,.040,.045),.48,.25)
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.085));bpy.context.object.name='Infinite studio floor';bpy.context.object.data.materials.append(floor)
bpy.ops.mesh.primitive_cylinder_add(vertices=192,radius=1.30,depth=.075,location=(0,0,-.042));pod=bpy.context.object;pod.name='Practice platform';pod.data.materials.append(stone)
bevel=pod.modifiers.new('Soft stone edge','BEVEL');bevel.width=.018;bevel.segments=3;pod.modifiers.new('Weighted normals','WEIGHTED_NORMAL')
for radius,z,minor,mat in [(1.27,-.006,.004,silver),(1.12,-.002,.0028,silver),(1.3,-.048,.006,dark)]:
    bpy.ops.mesh.primitive_torus_add(major_radius=radius,minor_radius=minor,major_segments=160,minor_segments=12,location=(0,0,z));bpy.context.object.data.materials.append(mat)
# A circular architectural relief frames the silhouette without clutter.
bpy.ops.mesh.primitive_cylinder_add(vertices=192,radius=1.42,depth=.07,location=(0,1.20,1.24),rotation=(math.pi/2,0,0));disc=bpy.context.object;disc.name='Silver moon backdrop';disc.data.materials.append(material('Moon satin',(.43,.52,.53),.55,.15))
bev=disc.modifiers.new('Rounded edge','BEVEL');bev.width=.04;bev.segments=5;disc.modifiers.new('Weighted normals','WEIGHTED_NORMAL')
bpy.ops.mesh.primitive_torus_add(major_radius=1.43,minor_radius=.012,major_segments=192,minor_segments=12,location=(0,1.23,1.24),rotation=(math.pi/2,0,0));bpy.context.object.data.materials.append(silver)
# Large softboxes give black fabric readable folds and a narrow silver rim.
area('Warm key',(-3,-4,5),650,(1,.89,.78),4)
area('Cool fill',(3,-2,3),400,(.72,.85,1),3)
area('Rim',(-1,2.2,3.7),900,(.70,.89,1),2.5)
area('Front eye light',(0,-4,2.2),70,(1,1,1),2)
world=bpy.data.worlds.new('Studio atmosphere');s.world=world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.17,.21,.25,1);world.node_tree.nodes['Background'].inputs[1].default_value=.35
bpy.ops.object.camera_add(location=(2.0,-5.0,2.0));cam=bpy.context.object;cam.name='Portrait motion camera';s.camera=cam;cam.data.lens=50;point(cam,(0,0,.86))
# A gentle camera drift is separate from all skeletal motion.
for frame,loc,target in [(1,(1.5,-5.1,1.9),(0,0,.86)),(432,(1.9,-5.0,2.03),(0,0,.86))]:
    cam.location=loc;point(cam,target);cam.keyframe_insert('location',frame=frame);cam.keyframe_insert('rotation_euler',frame=frame)
s.render.engine='CYCLES';s.cycles.samples=48;s.cycles.use_denoising=True;s.cycles.adaptive_threshold=.04
prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
for d in prefs.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.max_bounces=6;s.cycles.diffuse_bounces=3;s.cycles.glossy_bounces=4
s.render.resolution_x=1920;s.render.resolution_y=1080;s.render.resolution_percentage=100
s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB';s.render.image_settings.compression=15
s.view_settings.view_transform='AgX'
s.render.film_transparent=False
s.render.use_file_extension=True
bpy.ops.object.select_all(action='DESELECT');arm.select_set(True);bpy.context.view_layer.objects.active=arm
s.frame_set(160);bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'taichi_scene.blend'))
report={'bones':len(arm.data.bones),'vertices':len(mesh.data.vertices),'faces':len(mesh.data.polygons),'frames':frames,'fps':24,'duration':18,'engine':'Cycles / OptiX','samples':48,'resolution':[1920,1080],'source':'Meshy generated and retargeted skeletal motion','action':arm.animation_data.action.name}
(OUT/'scene_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');log('scene_saved',status='IN_PROGRESS',progress=25,**report)
if '--preview' in sys.argv:
    s.render.resolution_percentage=50;s.cycles.samples=24
    for f in [1,86,172,258,344,432]:
        s.frame_set(f);s.render.filepath=str(OUT/f'qa_{f:04}.png');bpy.ops.render.render(write_still=True)
    log('preview_frames_rendered',status='IN_PROGRESS',progress=30)
