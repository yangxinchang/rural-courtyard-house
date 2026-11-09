"""Blender: -b model/courtyard-house.blend --python render_interiors.py [-- preview 02]."""
import sys,json
from pathlib import Path
import bpy
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from design import room_specs,walls,furnishings,decoration
from interior_views import INTERIOR_VIEWS

scene=bpy.context.scene
assert 'Revision O' in scene['Design status'],'请先生成O版源模型'
rooms={room['id']:room for room in room_specs()}
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
preview=bool(args and args[0]=='preview')
full=bool(args and args[0]=='full')
assert preview or full or not args,'正式渲染请全量输出；单图检查请用 -- preview <机位ID>，补渲请用 -- full <机位ID>'
selected=set(args[1:] if (preview or full) else args)
views=[view for view in INTERIOR_VIEWS if not selected or view['id'] in selected]
assert views
output=ROOT/('tmp/revision-O/previews' if preview else '精装效果图')
output.mkdir(parents=True,exist_ok=True)
scene.render.engine='CYCLES'
scene.cycles.device='CPU'
try:
    devices=bpy.context.preferences.addons['cycles'].preferences
    devices.compute_device_type='OPTIX';devices.get_devices()
    if any(device.type=='OPTIX' for device in devices.devices):
        for device in devices.devices:device.use=device.type=='OPTIX'
        scene.cycles.device='GPU'
except RuntimeError as error:
    print('Cycles GPU unavailable, retaining CPU:',error,flush=True)
scene.cycles.samples=32 if preview else 160
scene.cycles.use_denoising=True
scene.cycles.use_adaptive_sampling=True
scene.cycles.adaptive_threshold=.06 if preview else .02
scene.cycles.adaptive_min_samples=12 if preview else 24
scene.render.resolution_x=960 if preview else 2560
scene.render.resolution_y=540 if preview else 1440
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.render.threads_mode='FIXED'
scene.render.threads=14
scene.view_settings.view_transform='AgX'
scene.view_settings.look='AgX - Medium High Contrast'
scene.view_settings.exposure=-1.42
scene.world.node_tree.nodes.get('Background').inputs['Strength'].default_value=.32
scene.world.node_tree.nodes.get('Background').inputs['Color'].default_value=(.72,.78,.86,1)
for key in ('Structure','Electrical','Plumbing','HVAC'):
    bpy.data.collections[key].hide_render=True
for obj in scene.objects:
    if obj.get('interiorCeiling') or obj.get('decorKind') in ('cove','lantern'):
        obj.hide_render=False
    if obj.get('decorKind')=='sheer':
        obj.hide_render=True
for obj in list(bpy.data.objects):
    if obj.type=='LIGHT':obj.hide_render=True
camera=bpy.data.objects.new('Interior effect camera',bpy.data.cameras.new('Interior effect camera'))
scene.collection.objects.link(camera)
camera.data.clip_start=.03
camera.data.clip_end=250
scene.camera=camera

def area_light(name,position,target,energy,size,color,shape='DISK',portal=False):
    light=bpy.data.lights.new(name,'AREA');light.energy=energy;light.shape=shape
    light.size=size;light.color=color
    if shape=='RECTANGLE':
        light.size_y=max(.4,size*.7)
    if portal:
        light.cycles.is_portal=True
        light.energy=0
    obj=bpy.data.objects.new(name,light);scene.collection.objects.link(obj);obj.location=position
    obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()
    return obj


def point_light(name,position,energy,radius,color):
    light=bpy.data.lights.new(name,'POINT');light.energy=energy;light.shadow_soft_size=radius
    light.color=color
    obj=bpy.data.objects.new(name,light);scene.collection.objects.link(obj);obj.location=position
    return obj

rendered=[]
for view in views:
    room=rooms[view['room']]
    x1,y1,x2,y2=room['inner'];cx,cy=(x1+x2)/2,(y1+y2)/2;floor=room['floor']
    eye=view['eye'];target=view['target']
    assert any(a<eye[0]<c and b<eye[1]<d for a,b,c,d in room.get('floor_parts',[room['inner']])),view
    for item in furnishings()[room['group']]:
        a,b,c,d=item['bounds']
        assert not (a<eye[0]<c and b<eye[1]<d),('室内相机落在家具占地内',view['name'],item['name'])
    camera.location=eye;camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler()
    camera.data.lens=view['lens'];camera.data.sensor_width=36
    area=max(9,(x2-x1)*(y2-y1))
    lights=[area_light('Interior warm ambient',(cx,cy,floor+2.86),(cx,cy,floor),
                       area*4.2,min(2.6,max(1.0,(x2-x1)*.55)),(1,.885,.745))]
    lights.append(area_light('Interior soft bounce',(cx,cy,floor+1.55),(cx,cy+.01,floor+1.5),
                             area*.55,min(3.2,max(1.4,(x2-x1)*.7)),(.98,.93,.86)))
    for fixture in decoration()[room['group']]:
        if fixture['room']!=room['index'] or fixture['kind']!='lantern':continue
        a,b,c,d=fixture['bounds'];lx,ly=(a+c)/2,(b+d)/2
        lights.append(area_light('Lantern downward light',(lx,ly,floor+fixture['z']-.02),
                                 (lx,ly,floor+.75),34,.55,(1,.82,.62)))
    for wall in walls(room['group']):
        a,b=wall['a'],wall['b'];horizontal=a[1]==b[1]
        for opening in wall['openings']:
            if opening['kind']!='window':continue
            x=a[0]+opening['offset']+opening['width']/2 if horizontal else a[0]
            y=a[1] if horizontal else a[1]+opening['offset']+opening['width']/2
            if not (x1-.25<=x<=x2+.25 and y1-.25<=y<=y2+.25):continue
            z=floor+opening['sill']+opening['height']/2
            direction=Vector((cx-x,cy-y,0)).normalized()
            lights.append(area_light('Window daylight fill',
                                     (x+direction.x*.16,y+direction.y*.16,z),(cx,cy,floor+1.15),
                                     75,min(1.15,max(.7,opening['width']*.85)),(.90,.95,1)))
            lights.append(area_light('Window light portal',
                                     (x+direction.x*.02,y+direction.y*.02,z),(cx,cy,floor+1.15),
                                     0,min(1.3,opening['width']), (1,1,1),shape='RECTANGLE',portal=True))
    for obj in bpy.data.objects:
        ox,oy,oz=obj.location
        if not (x1-.25<=ox<=x2+.25 and y1-.25<=oy<=y2+.25):continue
        if obj.get('downlightWatt') and oz>floor+2.8:
            lights.append(area_light('Downlight pool',(ox,oy,oz-.09),(ox,oy,floor),
                                     obj['downlightWatt']*1.3,.12,(1,.80,.58)))
        if obj.get('lampWatt') and floor+.3<oz<floor+2.2:
            lights.append(point_light('Practical lamp',(ox,oy,oz-.10),
                                      obj['lampWatt']*1.1,.05,(1,.74,.50)))
    filename=f"{view['id']}-{view['name']}.png"
    scene.render.filepath=str(output/filename)
    print('INTERIOR START',filename,flush=True)
    bpy.ops.render.render(write_still=True)
    print('INTERIOR DONE',filename,flush=True)
    rendered.append(dict(view,file=filename,resolution=[scene.render.resolution_x,scene.render.resolution_y]))
    for light in lights:bpy.data.objects.remove(light,do_unlink=True)
if not preview and len(views)==len(INTERIOR_VIEWS):
    (output/'manifest.json').write_text(json.dumps({'version':'O','source':'courtyard-house.blend','views':rendered},ensure_ascii=False,indent=2))
print('INTERIOR EFFECTS COMPLETE',len(rendered),flush=True)
