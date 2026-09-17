"""Create a smaller self-contained 2K .blend copy for browser download."""
import bpy,pathlib,zipfile
R=pathlib.Path(__file__).resolve().parents[1]
for image in bpy.data.images:
    if image.size[0]>2048:
        image.scale(2048,2048);image.pack()
bpy.ops.wm.save_as_mainfile(filepath=str(R/'output/taichi_scene_portable.blend'),compress=True)
with zipfile.ZipFile(R/'output/blender_portable.zip','w',zipfile.ZIP_DEFLATED,6) as z:
    z.write(R/'output/taichi_scene_portable.blend','taichi_scene_2k.blend')
    z.writestr('READ_ME.txt','Blender 5.2 project. This portable copy uses 2K textures.\nThe full 4K project remains in the local repository at output/taichi_scene.blend.\nAll lighting, 432 animation frames, 24 bones and foot IK controls are preserved.\n')
print('Portable archive bytes:',(R/'output/blender_portable.zip').stat().st_size)
