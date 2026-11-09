import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';
import { viewState,roomEye,engineeringGroups,overviewFrame } from './state.mjs';
import { daylightAt } from './daylight.mjs';

const $=id=>document.getElementById(id);
const container=$('viewport'),status=$('status');
let renderer,dirty=true;
try {
  renderer=new THREE.WebGLRenderer({antialias:true,preserveDrawingBuffer:true});
} catch(error) {
  status.classList.add('error');
  status.textContent='当前浏览器未能启用 WebGL 三维显示。请用支持 WebGL 的 Chrome / Edge 打开，或在浏览器设置中启用图形加速。上方仍可打开装修图纸。';
  document.querySelectorAll('aside button,aside input,aside select').forEach(e=>e.disabled=true);
  throw error;
}
renderer.setPixelRatio(Math.min(devicePixelRatio,2));
renderer.outputColorSpace=THREE.SRGBColorSpace;
renderer.toneMapping=THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure=1.15;
renderer.localClippingEnabled=true;
container.prepend(renderer.domElement);
renderer.domElement.tabIndex=0;
renderer.domElement.setAttribute('aria-label','三维视图：鼠标拖动旋转，滚轮缩放，右键平移');

const scene=new THREE.Scene();
scene.background=new THREE.Color('#e6ecdf');
const camera=new THREE.PerspectiveCamera(42,1,.03,220);
const controls=new OrbitControls(camera,renderer.domElement);
controls.addEventListener('change',()=>{dirty=true;});
controls.enableDamping=true;controls.dampingFactor=.09;
controls.minDistance=.15;controls.maxDistance=100;
controls.maxPolarAngle=Math.PI*.52;
controls.target.set(6,3,-12);
// Normal inspection stays unshadowed; daylight shadows are opt-in.
const skyLight=new THREE.HemisphereLight(0xeaf4ff,0xa5977a,2.2);scene.add(skyLight);
const sun=new THREE.DirectionalLight(0xfff2d8,3.1);
sun.position.set(12,28,16);sun.target.position.set(6,0,-12);
sun.shadow.mapSize.set(2048,2048);
Object.assign(sun.shadow.camera,{left:-26,right:26,top:26,bottom:-26,near:.5,far:110});
sun.shadow.bias=-.0005;sun.shadow.normalBias=.035;
renderer.shadowMap.type=THREE.PCFSoftShadowMap;renderer.shadowMap.autoUpdate=false;
scene.add(sun,sun.target);
const fill=new THREE.DirectionalLight(0xddeeff,1.5);fill.position.set(-10,12,-20);scene.add(fill);
const ground=new THREE.Mesh(new THREE.PlaneGeometry(130,130),new THREE.MeshStandardMaterial({color:0xdce2d1,roughness:1}));
ground.rotation.x=-Math.PI/2;ground.position.y=-.13;scene.add(ground);

const data=window.HOUSE_DESIGN;
const rooms=data?.room_specs||[];
const wardrobes=Object.values(data?.furniture||{}).flat().filter(item=>item.bedroom).map(item=>({...item,id:'wardrobe-'+item.bedroom}));
const groupNames={front:'前房一层',rear1:'后楼首层',rear2:'后楼二层'};
const engineeringNames={Structure:'梁柱结构',Electrical:'电气线路',Plumbing:'给排水管线',HVAC:'空调管路'};
const titles={whole:'整屋外观',ground:'首层布局',upper:'后楼二层',attic:'半层隔热阁楼'};
const layers={},meshes=[],labels=[],applianceLabels=[],openings=new Map();
let mode='whole',selectedRoom=null,indoor=false,ready=false;
let savedCamera;
let wardrobeDetail=null;
let dryingLift=null,dryingLowered=false;
const dryingCables=[];
const toWorld=(x,y,z)=>new THREE.Vector3(x,z,-y);
const engineeringSelection=()=>Object.fromEntries(engineeringGroups.map(group=>[group,$(group.toLowerCase())?.checked||false]));

const baseLighting={position:sun.position.clone(),target:sun.target.position.clone(),color:sun.color.clone(),background:scene.background.clone()};
const solarBounds=data.site_bounds||[0,0,...data.site],solarCenter=toWorld((solarBounds[0]+solarBounds[2])/2,(solarBounds[1]+solarBounds[3])/2,1);
const solarRadius=32,solarGroup=new THREE.Group();scene.add(solarGroup);solarGroup.visible=false;
const solarOrb=new THREE.Mesh(new THREE.SphereGeometry(1.3,16,12),new THREE.MeshBasicMaterial({color:0xffd27a,toneMapped:false,depthTest:false}));solarOrb.renderOrder=5;solarGroup.add(solarOrb);
const solarPoints=[];
for(let hour=6;hour<=18.001;hour+=.25)solarPoints.push(solarCenter.clone().add(new THREE.Vector3(...daylightAt(Math.min(hour,18)).direction).multiplyScalar(solarRadius)));
solarGroup.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(solarPoints),new THREE.LineDashedMaterial({color:0xc39b51,dashSize:.7,gapSize:.35,transparent:true,opacity:.65})).computeLineDistances());
const solarLabels=[];
for(const [hour,text] of [[6,'东 · 日出'],[12,'南 · 正午'],[18,'西 · 日落']]){
 const element=document.createElement('span');element.className='solar-label';element.textContent=text;element.hidden=true;container.append(element);
 solarLabels.push({element,point:solarCenter.clone().add(new THREE.Vector3(...daylightAt(hour).direction).multiplyScalar(solarRadius))});
}
const solarSky=new THREE.Color('#dce9f5'),solarHorizon=new THREE.Color('#e7d0b3'),solarWarm=new THREE.Color('#ffb47a'),solarWhite=new THREE.Color('#fff4dd');
let solarHour=9,solarPlaying=false,lastSolarTick=0,solarShadowState=false;
function requestSolarShadow(){
 if($('sun-enabled').checked&&!wardrobeDetail)renderer.shadowMap.needsUpdate=true;
 dirty=true;
}
function updateDaylight(){
 const enabled=$('sun-enabled').checked&&!wardrobeDetail,profile=daylightAt(solarHour),changed=solarShadowState!==enabled;
 solarShadowState=enabled;renderer.shadowMap.enabled=enabled;sun.castShadow=enabled;ground.receiveShadow=enabled;
 for(const mesh of meshes){
  const materials=Array.isArray(mesh.material)?mesh.material:[mesh.material];
  const engineering=engineeringGroups.includes(mesh.userData.floorGroup);
  mesh.castShadow=enabled&&!engineering&&!materials.some(mat=>mat.transparent);
  mesh.receiveShadow=enabled&&!engineering;
  for(const mat of materials){mat.clipShadows=true;mat.shadowSide=THREE.FrontSide;if(changed)mat.needsUpdate=true;}
 }
 if(changed)ground.material.needsUpdate=true;
 if(enabled){
  sun.position.copy(solarCenter).add(new THREE.Vector3(...profile.direction).multiplyScalar(solarRadius));sun.target.position.copy(solarCenter);
  sun.color.copy(solarWarm).lerp(solarWhite,profile.strength);sun.intensity=4*profile.strength;
  skyLight.intensity=.3+.7*profile.strength;fill.intensity=.12+.23*profile.strength;
  scene.background.copy(solarHorizon).lerp(solarSky,profile.strength);solarOrb.position.copy(sun.position);solarOrb.material.color.copy(sun.color);
 }else{
  sun.position.copy(baseLighting.position);sun.target.position.copy(baseLighting.target);sun.color.copy(baseLighting.color);sun.intensity=3.1;
  skyLight.intensity=2.2;fill.intensity=1.5;scene.background.copy(baseLighting.background);
 }
 solarGroup.visible=enabled&&mode==='whole'&&!indoor&&!wardrobeDetail;
 $('sun-time').value=String(solarHour);$('sun-time').setAttribute('aria-valuetext',profile.clock);$('sun-clock').value=profile.clock;
 $('sun-phase').textContent=$('sun-enabled').checked?profile.phase+' · 示意光影；房间内请使用“室内视角”。':'日照演示已关闭 · 当前为无投影查看。';
 $('sun-play').textContent=solarPlaying?'暂停播放':'播放日轨';$('sun-play').setAttribute('aria-pressed',String(solarPlaying));
 $('sun-badge').hidden=!$('sun-enabled').checked;$('sun-badge-time').textContent=profile.clock+' · 日照示意';$('sun-badge-play').textContent=solarPlaying?'暂停':'播放';
 requestSolarShadow();
}
function resetDaylight(){solarPlaying=false;solarHour=9;$('sun-enabled').checked=false;updateDaylight();}
$('sun-enabled').addEventListener('change',()=>{if(!$('sun-enabled').checked)solarPlaying=false;updateDaylight();});
$('sun-time').addEventListener('input',()=>{solarPlaying=false;solarHour=Number($('sun-time').value);$('sun-enabled').checked=true;updateDaylight();});
$('sun-time').addEventListener('change',()=>{if(innerWidth<=800)container.scrollIntoView({block:'start'});});
for(const button of document.querySelectorAll('[data-sun-hour]'))button.addEventListener('click',()=>{solarPlaying=false;solarHour=Number(button.dataset.sunHour);$('sun-enabled').checked=true;updateDaylight();if(innerWidth<=800)container.scrollIntoView({block:'start'});});
$('sun-play').addEventListener('click',()=>{const wasEnabled=$('sun-enabled').checked;solarPlaying=!solarPlaying;if(solarPlaying){if(!wasEnabled||solarHour>=18)solarHour=6;$('sun-enabled').checked=true;lastSolarTick=performance.now();}updateDaylight();if(solarPlaying&&innerWidth<=800)container.scrollIntoView({block:'start'});});
$('sun-badge-play').addEventListener('click',()=>$('sun-play').click());
$('sun-badge-off').addEventListener('click',()=>{$('sun-enabled').checked=false;solarPlaying=false;updateDaylight();});
$('sun-path').addEventListener('click',()=>{
 $('sun-enabled').checked=true;setMode('whole');$('labels').checked=false;updateVisibility();
 const target=solarCenter.clone().add(new THREE.Vector3(0,10,0)),fit=Math.max(1,1/camera.aspect);controls.maxDistance=120*fit;camera.far=220*fit;frame(target.clone().add(new THREE.Vector3(62,48,62).multiplyScalar(fit)),target);
 $('view-name').textContent='太阳东升西落 · 日轨示意';
 if(innerWidth<=800)container.scrollIntoView({block:'start'});
});

if(data?.engineering){
  const {members=[],routes=[],devices=[],circuits=[],notes=[]}=data.engineering;
  $('engineering-summary').textContent=`模型含 ${members.length} 项结构构件、${routes.length} 段线路、${devices.length} 个设备点位，${circuits.length} 个回路分组。`;
  for(const note of notes){const li=document.createElement('li');li.textContent=note;$('engineering-notes').append(li);}
}

for(const [group,name] of Object.entries(groupNames)) {
  const optgroup=document.createElement('optgroup');optgroup.label=name;
  for(const room of rooms.filter(r=>r.group===group)) {
    const option=document.createElement('option');option.value=room.id;option.textContent=room.name;optgroup.append(option);
    const label=document.createElement('button');label.className='room-label';label.textContent=room.name;label.hidden=true;
    label.addEventListener('click',()=>selectRoom(room.id));$('room-labels').append(label);
    labels.push({room,element:label});
  }
  $('room').append(optgroup);
}

function frame(position,target){dirty=true;camera.fov=indoor?68:42;camera.updateProjectionMatrix();camera.position.copy(position);controls.target.copy(target);controls.update();}
function overview(){
  indoor=false;controls.maxPolarAngle=Math.PI*.52;controls.maxDistance=100;camera.far=220;
  const framing=overviewFrame(mode,data?.site,data?.site_bounds),target=toWorld(...framing.target),distance=framing.distance;
  frame(target.clone().add(new THREE.Vector3(distance*.57,distance*.68,distance*.77)),target);
}

function updateVisibility(){
  dirty=true;
  ground.visible=!wardrobeDetail;
  const engineering=engineeringSelection(),view=viewState(mode,engineering);
  for(const [group,obj] of Object.entries(layers))obj.visible=view.groups.includes(group);
  if(layers.Roofs)layers.Roofs.visible=mode==='whole'&&$('roof').checked;
  if(layers.StairRoof)layers.StairRoof.visible=mode==='whole'&&$('roof').checked;
  if(layers.EntryRoof)layers.EntryRoof.visible=mode==='upper'||(mode==='whole'&&$('roof').checked);
  if(layers.BridgeCanopy)layers.BridgeCanopy.visible=mode==='whole'&&$('roof').checked;
  if(layers.OutbuildingRoof)layers.OutbuildingRoof.visible=mode==='whole'&&$('roof').checked;
  if(layers.PavilionRoof)layers.PavilionRoof.visible=['whole','upper'].includes(mode)&&$('roof').checked;
  if(layers.Pavilion)layers.Pavilion.visible=mode==='upper'||(mode==='whole'&&$('roof').checked);
  if(indoor&&selectedRoom?.kind==='stair'){
    for(const name of ['StairShell1','StairShell2','StairRoof'])if(layers[name])layers[name].visible=true;
  }
  if(indoor&&selectedRoom?.id==='rear2-8'&&layers.Attic)layers.Attic.visible=true;
  if(layers.Attic&&mode==='whole'&&!$('roof').checked)layers.Attic.visible=false;
  if(layers.Terrace&&mode==='whole'&&!$('roof').checked)layers.Terrace.visible=false;
  const cut=$('cut').checked;
  for(const mesh of meshes){
    if(wardrobeDetail){
      mesh.visible=$('furniture').checked&&mesh.userData.wardrobeId===wardrobeDetail;
      for(const mat of Array.isArray(mesh.material)?mesh.material:[mesh.material])mat.clippingPlanes=[];
      continue;
    }
    if(engineeringGroups.includes(mesh.userData.floorGroup)){
      mesh.visible=view.groups.includes(mesh.userData.floorGroup)&&view.engineeringFloors.includes(mesh.userData.engineeringFloor);
      continue;
    }
    mesh.visible=!mesh.userData.furnishing||$('furniture').checked;
    if(mesh.userData.interiorCeiling)mesh.visible=indoor&&!cut;
    if(mesh.userData.ceilingLight&&cut)mesh.visible=false;
    const height=['Rear2','StairShell2'].includes(mesh.userData.floorGroup)?4.75:mesh.userData.floorGroup==='Attic'?7.95:1.45;
    for(const mat of Array.isArray(mesh.material)?mesh.material:[mesh.material]) {
      mat.clippingPlanes=cut&&mesh.userData.sectionable?[new THREE.Plane(new THREE.Vector3(0,-1,0),height)]:[];
    }
  }
  updateDaylight();
  updateOpeningControls();
  updateWardrobeControls();
  const selectedEngineering=engineeringGroups.filter(group=>engineering[group]);
  const unavailable=selectedEngineering.filter(group=>!layers[group]);
  const messages=[];
  if(unavailable.length)messages.push(`${unavailable.map(group=>engineeringNames[group]).join('、')}未包含在当前模型中，请使用配套 I 版模型。`);
  if(mode==='attic'&&(engineering.Electrical||engineering.Plumbing))messages.push('阁楼仅显示上层承重示意，水电层暂不显示。');
  if(!messages.length)messages.push(selectedEngineering.length?'已按当前楼层筛选；管线可透过墙面查看。':'工程层默认关闭，勾选后按当前楼层显示。');
  $('engineering-status').textContent=messages.join(' ');
  $('engineering-legend').hidden=!selectedEngineering.length;
  document.querySelectorAll('[data-mode]').forEach(btn=>btn.setAttribute('aria-pressed',String(btn.dataset.mode===mode)));
  $('roof').disabled=!['whole','upper'].includes(mode);
  const detailWardrobe=wardrobes.find(item=>item.id===wardrobeDetail);
  const wardrobeSize=detailWardrobe&&[detailWardrobe.bounds[3]-detailWardrobe.bounds[1],detailWardrobe.bounds[2]-detailWardrobe.bounds[0],detailWardrobe.height].map(v=>Math.round(v*1000)).join(' × ');
  $('view-name').textContent=detailWardrobe?detailWardrobe.name+' · 收纳设计':selectedRoom?`${selectedRoom.name} · ${indoor?'室内视角':'布局'}`:titles[mode];
  $('view-name').nextElementSibling.textContent=detailWardrobe?`${wardrobeSize} mm（宽×深×高） · 挂衣杆 ${Math.round(detailWardrobe.rail_height*1000)} mm`:'精装方案 O · 衣柜／水电深化 · 米为模型单位';
  if(!selectedRoom){
    const descriptions={whole:'O版门窗支持单独及全部开关，东西院墙均封至连廊板底+3.42m；西廊下设三台洗烘设备和晾衣架，二楼亭子保留水池，洗衣机移至后楼过厅蓝框凹位，老人房床与梳妆台南北换位，两间卧室设梳妆台，厨房两个猛火灶分别标注。右前方杂物屋3.6×7.4m。沿用M版优化次卧830mm入口、独立衣柜与书桌、老人北区、主卧窗前柜体和餐叙灯。13张室内图为衣柜深化前O版；衣柜内部以当前3D为准。保留门前环境：补门前8米深空地和大门右前方3.6×7.4米一层杂物屋，均为暂定示意。主体位置不动。沿用K版：将两层东套卫移至梯间北侧，原湿区归入套房；堂屋旧北门封闭，北段圆桌兼用餐会客。前屋中西厨房取消餐位并补齐家电和独立排烟；厚重中式现代临街大门，后排一楼朝院横拉玻璃门。院墙接通，前屋屋顶西亭内电动晾衣、右侧旧架取消、中间活动；保留门厅、二层东雨廊、四房2.2／1.8米床及屋后5米。',ground:'后楼西起居、东老人房；北侧圆桌客厅，原堂屋到家务前室敞口封闭。西公卫经起居室北门到达，茶几缩窄保留通路。老人套卫外移楼梯北侧，原湿区并入私用休闲区。厨房只烹饪，洗碗机、微波炉、电饼铛和电饭煲均有位置，独立烟道沿东外墙上排。',upper:'封闭梯经侧主门、独立过道到公共过厅和家庭厅，不穿卧室。次卧套卫移至梯间北侧，原湿区归入书桌区。前屋露台西侧保留亭子和水池，洗衣机移到后楼过厅北墙凹位，亭内电动升降晾衣，右侧旧架取消、中部活动通行，双连廊入口保留。老人房和主卧2.2米、客房和次卧1.8米床沿用；施工及采光通风待核验。',attic:'后楼通风隔热阁楼沿用红色琉璃瓦，不作常住卧室。东侧套卫采用独立平屋顶，随整屋屋顶开关显示。'};
    $('room-info').replaceChildren();const title=document.createElement('strong');title.textContent=titles[mode];
    const p=document.createElement('p');p.textContent=descriptions[mode];$('room-info').append(title,p);
  }
}

function setMode(next){
  wardrobeDetail=null;
  viewState(next);mode=next;selectedRoom=null;$('room').value='';indoor=false;
  $('cut').checked=viewState(mode).cutWalls;$('roof').checked=mode==='whole';
  $('labels').checked=mode==='ground'||mode==='upper';
  updateVisibility();overview();
}

function roomInfo(room){
  const [x1,y1,x2,y2]=room.inner;
  const names=data.furniture[room.group].filter(f=>f.room===room.index&&!['chair','nightstand'].includes(f.kind)).map(f=>f.name);
  const decorations=(data.decorations?.[room.group]||[]).filter(item=>item.room===room.index);
  const materials={oak:'木色饰面',quartz:'浅色石英石',metal:'金属',accent:'暖灰背景板',fabric:'暖米色织物',light:'暖色灯光'};
  const title=document.createElement('strong');title.textContent=`${groupNames[room.group]} · ${room.name}`;
  const size=document.createElement('p');size.textContent=room.shape_note?`${room.shape_note} · ${room.finish}`:`参考净尺寸 ${(x2-x1).toFixed(2)} × ${(y2-y1).toFixed(2)} 米 · ${room.finish}`;
  const notes={
    'rear2-7':'二层东套卫位于梯间北侧，与首层老人套卫叠合，独立采光和排风；仅从次卧书桌区进入，原梯间北窗封闭。',
    'front-0':'厨房取消餐桌和卡座，东侧灶台／洗涤、洗碗机、北侧小家电台，西侧咖啡与烤箱、冰箱预留；东墙独立排烟立管示意出口+6.10m，静压、散热与回路按设备深化。',
    'front-1':'临街大门采用厚重木色双开门，深石门套、铜色拉手、线性金属细节与门灯意向；通堂内门与中央穿行保留。',
    'front-2':'由通堂西侧内门进入，木门向客房内开；原朝院门改窗。横床床头朝西，木纹饰面、米色床品、叠级灯槽与纱帘沿参考风格，保留衣柜和床尾使用空间。',
    'rear1-0':'西侧起居室，西侧沙发面向东侧电视；西窗下低背景，保留南窗和西窗；北门接家务前室。',
    'rear1-1':'西公卫由东侧家务前室800mm内开门进入；堂屋原直达敞口封闭，改经西起居室北门，不穿卧室。',
    'rear1-2':'北墙洗衣与窗下矮柜；南门接起居室，西门到公卫。堂屋北段西墙已封闭。',
    'rear1-3':'南侧双轨横拉玻璃门朝院；北段1.20m圆桌配六把软垫椅，中心木框暖灯，兼用餐会客，南侧活动与卧室门前通路保留。',
    'rear1-5':'东侧老人卧室，2.20m双人床移到北侧内区，床头朝东，低床头750mm；东墙南段设梳妆台、镜前灯和收纳凳；西侧床尾与北侧衣帽、套卫通路保留。保留南窗，东墙被梯间遮挡，实际采光通风待核验。',
    'rear1-6':'西墙五列2000mm平开衣柜，北窗侧移避柜，窗下单椅与矮边柜供穿衣、休息；新增阅读灯和软帘，中部通路到东侧套卫，不占门扇。',
    'rear1-7':'梯间北侧新老人套卫，参考净空约2.70×2.28m；只从西侧私用区进入，不与楼梯相通。淋浴、座凳、扶手、镜柜及独立排风意向。',
    'rear1-8':'西门接后楼有顶门廊，北门通原封闭楼梯，完成面连续平接；南、东侧采光窗，东窗下换鞋凳。顶盖覆盖原露天入口，屋面雨水独立收集；防水、结构及安装需深化。',
    'rear2-0':'主卧2.20m双人床，床头朝西，低床头750mm、背景720mm；西墙北段增梳妆台和台下凳；保留西窗、床尾及加深后的北侧通路；衣帽区五列2000mm衣柜，北窗侧向让位避免高柜遮窗。',
    'rear2-3':'西侧沙发对东侧电视背景，沙发前净距约500mm、茶几东侧面对电视柜段约1100mm；共用高柜移至东墙北端，北墙2.25m双人学习桌及双椅向西协调，南段入户和主卧门区保持通行。',
    'rear2-9':'东侧主门接封闭梯南端顶平台；由短过道向南至公共过厅，再到家庭厅，不穿卧室。北侧门进入1.8m双人床次卧。',
    'rear2-8':'东北接侧门入户过道；南侧左右各900 mm小门接双连廊。西段北墙设洗烘一体机凹位，朝南操作、前方约1000mm，接二楼DB2专用回路，独立给排水与西外墙污废水立管。主卧南窗略收窄，床与主卧入口保留。',
    'rear2-5':'原双床房改一张1.80m双人床，床头朝东；后楼加深1m，西侧床尾950mm、南侧830mm布置通路，独立入户过道保留。床北移200mm，北区新增独立衣柜、1500mm窗下书桌，北窗已加宽；实际床箱、门框和采光通风仍需核验。',
    'rear2-6':'西侧独立五列平开衣柜2000×550mm，1500mm书桌东移至北窗下；床尾转弯带710mm，椅前留通往东套卫的路线。加阅读灯和帘片，真实采光通风待核。',
  };
  const note=room.kind==='stair'?'墙体与顶盖围合；20级 × 165 mm，梯段1050 mm，中间平台1050 mm；南端顶平台接二层侧主门，首层入口朝南。':notes[room.id]||'';
  const detail=document.createElement('p');detail.textContent=[names.join('、'),note].filter(Boolean).join('。')||'保持通行。';
  const finish=document.createElement('p');finish.textContent=decorations.length?`装修细节 ${decorations.length} 项 · 主要材料：${[...new Set(decorations.map(item=>materials[item.material]||item.material))].slice(0,3).join('、')}。`:'无固定装修配件，保持通行。';
  $('room-info').replaceChildren(title,size,detail,finish);
  const wardrobe=wardrobes.find(item=>item.bedroom===room.id||`${room.group}-${item.room}`===room.id);
  if(wardrobe){
    const button=document.createElement('button');button.textContent='打开本卧室衣柜 · 查看内部';
    button.addEventListener('click',()=>{setWardrobe(wardrobe.id,'interior');focusWardrobe(wardrobe.id);});
    $('room-info').append(button);
  }
  const rendering=data.interior_renderings?.find(item=>item.room===room.id);
  if(rendering){const p=document.createElement('p'),link=document.createElement('a');link.href=rendering.path;link.textContent='查看本房间高清精装效果图';p.append(link);if(data.interior_rendering_note)p.append(document.createTextNode(' · '+data.interior_rendering_note));$('room-info').append(p);}
}

function selectRoom(id,eye=false){
  const room=rooms.find(r=>r.id===id);if(!room)return;
  wardrobeDetail=null;
  mode=room.group==='rear2'?'upper':'ground';selectedRoom=room;indoor=eye;$('room').value=id;
  $('roof').checked=false;$('cut').checked=!eye;$('labels').checked=!eye;
  updateVisibility();roomInfo(room);
  const [x1,y1,x2,y2]=room.bounds,cx=(x1+x2)/2,cy=(y1+y2)/2,z=room.floor;
  if(eye){
    const [eyeX,eyeY,eyeZ]=roomEye(room);
    const target=room.group==='front'&&room.index===0?toWorld(10.05,5.2,z+1.1):room.id==='front-2'?toWorld(1.8,2.3,z+1.1):room.kind==='stair'?toWorld(z>3?12.35:eyeX,eyeY+2.4,z>3?z+.15:z+1.25):room.id==='rear1-5'?toWorld(10.35,20.25,1.30):room.id==='rear2-5'?toWorld(10.0,20.25,z+1.25):room.id==='rear1-6'?toWorld(9.7,23.25,z+1.0):room.id==='rear2-6'?toWorld(9.45,23.25,z+1.3):room.id==='rear2-9'?toWorld(11.28,17.55,z+1.45):room.id==='rear2-8'?toWorld(x2-.7,eyeY,z+1.45):toWorld(cx,Math.min(y2-.3,eyeY+1.8),z+1.25);
    frame(toWorld(eyeX,eyeY,eyeZ),target);
  }else{
    const target=toWorld(cx,cy,z+.55),d=Math.max(x2-x1,y2-y1)*1.7;
    frame(target.clone().add(new THREE.Vector3(d*.5,d*.95,d*.8)),target);
  }
  if(innerWidth<=800)container.scrollIntoView({block:'start'});
}

function topView(){
  if(wardrobeDetail&&selectedRoom)roomInfo(selectedRoom);
  wardrobeDetail=null;
  indoor=false;let target,d;
  if(selectedRoom){const [x1,y1,x2,y2]=selectedRoom.bounds;target=toWorld((x1+x2)/2,(y1+y2)/2,selectedRoom.floor+.05);d=Math.max(x2-x1,y2-y1)*1.55;}
  else {const framing=overviewFrame(mode,data?.site,data?.site_bounds);target=toWorld(framing.target[0],framing.target[1],mode==='attic'?6.9:mode==='upper'?3.6:1);d=framing.topDistance;}
  $('cut').checked=true;if(mode==='whole'){mode='ground';$('roof').checked=false;}
  frame(target.clone().add(new THREE.Vector3(0,d,.025)),target);updateVisibility();
}

for(const btn of document.querySelectorAll('[data-mode]'))btn.addEventListener('click',()=>setMode(btn.dataset.mode));
for(const id of ['roof','cut','labels','furniture','appliance-labels',...engineeringGroups.map(group=>group.toLowerCase())])$(id).addEventListener('change',updateVisibility);
$('room').addEventListener('change',()=>{$('room').value?selectRoom($('room').value):setMode(mode);});
$('room-top').addEventListener('click',()=>{if(!selectedRoom)selectRoom(mode==='upper'?'rear2-0':'front-0');topView();});
$('room-eye').addEventListener('click',()=>selectRoom(selectedRoom?.id||(mode==='upper'?'rear2-0':'front-0'),true));
$('entry-circulation').addEventListener('click',()=>selectRoom('rear2-9'));
$('rain-entry').addEventListener('click',()=>{
  setMode('whole');selectedRoom=rooms.find(room=>room.id==='rear1-8');$('room').value=selectedRoom.id;
  updateVisibility();roomInfo(selectedRoom);
  const target=toWorld(12.5,15.8,1.6);frame(target.clone().add(new THREE.Vector3(8,6,7)),target);
  $('view-name').textContent='避雨门厅 · 外观';
  if(innerWidth<=800)container.scrollIntoView({block:'start'});
});
$('east-canopy').addEventListener('click',()=>{
  setMode('whole');const target=toWorld(10.8,10.5,4.8);
  frame(target.clone().add(new THREE.Vector3(10,7,8)),target);
  $('view-name').textContent='二层东侧雨廊';
  const title=document.createElement('strong');title.textContent='二层东侧连廊 · 连续加顶';
  const note=document.createElement('p');note.textContent='浅色轻型顶棚覆盖前露台至后楼小门的整段连廊，向东收集雨水；细柱沿原栏杆线布置。二层布局隐藏高处顶棚便于看通路，整屋屋顶开关可控制显示。';
  $('room-info').replaceChildren(title,note);
  if(innerWidth<=800)container.scrollIntoView({block:'start'});
});
$('terrace-design').addEventListener('click',()=>{setMode('upper');const t=toWorld(6,3.8,3.9);frame(t.clone().add(new THREE.Vector3(8,10,9)),t);$('view-name').textContent='开放娱乐晾晒露台';const p=document.createElement('p');p.textContent='西侧亭内为电动升降晾衣、水池与收纳，右侧旧晾衣架取消；洗衣机移至后楼过厅，中部活动及两侧连廊通行；排烟立管在外侧。荷载、防水与固定需深化。';$('room-info').replaceChildren(p);});
$('forecourt-design').addEventListener('click',()=>{setMode('whole');const t=toWorld(7.5,-2,1);frame(t.clone().add(new THREE.Vector3(-13,13,17)),t);$('view-name').textContent='门前空地与右侧杂物屋';const p=document.createElement('p');p.textContent='门前空地暂按8米深，大门右前方一层杂物屋暂按3.6×7.4米；按最新标注移到东南侧，西门朝中部空地。中央直达入户，其余开敞。杂物屋已覆盖北段原空地，东西院墙上方缺口封闭。尺寸和地界需实测。';$('room-info').replaceChildren(p);});
$('decoration-design').addEventListener('click',()=>{$('furniture').checked=true;selectRoom('rear2-3');});
$('top').addEventListener('click',topView);
$('septic').addEventListener('click',()=>{
  setMode('whole');$('plumbing').checked=true;updateVisibility();
  const [x1,y1,x2,y2]=data?.engineering?.septic?.bounds||[8,25.9,11.6,28.3];
  const target=toWorld((x1+x2)/2,(y1+y2)/2,0);
  frame(target.clone().add(new THREE.Vector3(7,9,-7)),target);
  $('view-name').textContent='屋后排污与化粪池（示意）';
  if(innerWidth<=800)container.scrollIntoView({block:'start'});
});
$('reset').addEventListener('click',()=>{resetDaylight();setDrying(false);for(const opening of openings.values())opening.kind==='wardrobe'?setWardrobe(opening.id,'closed'):setOpening(opening,opening.defaultOpen);$('appliance-labels').checked=true;$('furniture').checked=true;for(const group of engineeringGroups)$(group.toLowerCase()).checked=false;setMode('whole');});
$('screenshot').addEventListener('click',()=>{renderer.render(scene,camera);const a=document.createElement('a');a.href=renderer.domElement.toDataURL('image/png');a.download=`院居-${selectedRoom?.name||titles[mode]}.png`;a.click();});
$('fullscreen').addEventListener('click',async()=>{try{document.fullscreenElement?await document.exitFullscreen():await container.requestFullscreen();}catch{$('render-status').textContent='浏览器未允许全屏，可最大化窗口查看。';}});
renderer.domElement.addEventListener('webglcontextlost',e=>{e.preventDefault();status.hidden=false;status.textContent='三维显示连接已中断，请刷新页面重新打开。';});
const resize=()=>{dirty=true;const {width,height}=container.getBoundingClientRect();renderer.setSize(width,height);camera.aspect=width/height;camera.updateProjectionMatrix();};
new ResizeObserver(resize).observe(container);resize();overview();

function updateOpeningControls(){
  const opening=openings.get($('opening').value);
  $('opening-toggle').disabled=!opening;$('opening-focus').disabled=!opening;
  $('opening-toggle').textContent=opening?(opening.open?'关闭这扇'+(opening.kind==='door'?'门':'窗'):'打开这扇'+(opening.kind==='door'?'门':'窗')):'打开 / 关闭';
  $('opening-toggle').setAttribute('aria-pressed',String(!!opening?.open));
  const buildingOpenings=[...openings.values()].filter(o=>o.kind!=='wardrobe'),count=buildingOpenings.filter(o=>o.open).length;
  $('opening-status').textContent=opening?`${opening.label} · ${opening.open?'已打开':'已关闭'} · 共 ${buildingOpenings.length} 处，${count} 处打开`:`共 ${buildingOpenings.length} 处门窗，${count} 处打开。窗为推拉示意。`;
}
function setOpening(opening,open){
  opening.open=open;
  for(const part of opening.parts){
    part.group.position.copy(part.closedPosition);
    if(part.meta.motion==='hinge')part.group.quaternion.setFromAxisAngle(new THREE.Vector3(0,1,0),open?part.meta.openAngle:part.meta.closedAngle);
    else if(open)part.group.position.add(new THREE.Vector3(part.meta.travel,0,0).applyQuaternion(part.group.quaternion));
  }
  requestSolarShadow();
}
function toggleOpening(id,doorIndex){
  const opening=openings.get(id);if(!opening)return;
  if(opening.kind==='wardrobe'){
    if(doorIndex===undefined)setWardrobe(id,opening.open?'closed':'open');
    else{
      const part=opening.parts.find(p=>p.meta.panelIndex===doorIndex);if(!part)return;
      part.open=!part.open;
      if(part.open)part.group.quaternion.setFromAxisAngle(new THREE.Vector3(0,1,0),part.meta.openAngle);
      else part.group.quaternion.copy(part.closedQuaternion);
      opening.open=opening.parts.some(p=>p.open);opening.view=opening.parts.every(p=>p.open)?'open':opening.open?'partial':'closed';
      $('wardrobe').value=id;requestSolarShadow();
    }
    updateWardrobeControls();return;
  }
  $('opening').value=id;setOpening(opening,!opening.open);updateOpeningControls();
}
$('opening').addEventListener('change',updateOpeningControls);
$('opening-toggle').addEventListener('click',()=>toggleOpening($('opening').value));
for(const [id,open] of [['open-all',true],['close-all',false]])$(id).addEventListener('click',()=>{for(const opening of openings.values())if(opening.kind!=='wardrobe')setOpening(opening,open);updateOpeningControls();});

function setWardrobe(id,view){
  const opening=openings.get(id);if(!opening||opening.kind!=='wardrobe')return;
  $('wardrobe').value=id;opening.view=view;opening.open=view==='open';
  for(const part of opening.parts){
    part.group.visible=view!=='interior';part.group.position.copy(part.closedPosition);
    part.open=view==='open';
    if(part.open)part.group.quaternion.setFromAxisAngle(new THREE.Vector3(0,1,0),part.meta.openAngle);
    else part.group.quaternion.copy(part.closedQuaternion);
  }
  requestSolarShadow();
}
function updateWardrobeControls(){
  const wardrobe=wardrobes.find(item=>item.id===$('wardrobe').value),opening=openings.get(wardrobe?.id);
  const view=opening?.view||'closed';
  const names={closed:'五扇柜门已关闭',open:'五扇柜门已打开',partial:'部分柜门打开 · 可逐扇点击开关',interior:'五列内部展示 · 柜门暂时隐藏'};
  $('wardrobe-status').textContent=wardrobe?`${wardrobe.name} · ${names[view]}。${wardrobe.layout}。`:'请选择衣柜。';
  for(const button of document.querySelectorAll('[data-wardrobe-view]'))button.setAttribute('aria-pressed',String(button.dataset.wardrobeView===view));
}
function focusWardrobe(id){
  const wardrobe=wardrobes.find(item=>item.id===id);if(!wardrobe)return;
  selectRoom(wardrobe.bedroom);wardrobeDetail=id;$('wardrobe').value=id;
  $('furniture').checked=true;$('labels').checked=false;$('cut').checked=false;
  updateVisibility();
  const [a,b,c,d]=wardrobe.bounds,z=selectedRoom.floor,front=wardrobe.mirrored?c:a,sign=wardrobe.mirrored?1:-1;
  const target=toWorld((a+c)/2,(b+d)/2,z+wardrobe.height/2);
  frame(toWorld(front+sign*4.0,(b+d)/2-sign*.7,z+1.50),target);
  const title=document.createElement('strong');title.textContent=`${wardrobe.name} · ${Math.round((d-b)*1000)} × ${Math.round((c-a)*1000)} × ${Math.round(wardrobe.height*1000)} mm（宽×深×高）`;
  const note=document.createElement('p');note.textContent=`${wardrobe.layout}。挂衣杆高 ${Math.round(wardrobe.rail_height*1000)} mm，顶层板高 2080 mm；木色柜体与细金属拉手。`;
  const help=document.createElement('p');help.textContent='可拖动旋转查看；“打开五扇门”演示平开，也可点击单扇柜门开关。“查看全部内部”隐藏五扇门。平开门向外约400mm，开柜与通行分时使用。';
  $('room-info').replaceChildren(title,note,help);
}
$('wardrobe').addEventListener('change',()=>focusWardrobe($('wardrobe').value));
$('wardrobe-focus').addEventListener('click',()=>focusWardrobe($('wardrobe').value));
$('wardrobe-room').addEventListener('click',()=>{const wardrobe=wardrobes.find(item=>item.id===$('wardrobe').value);if(wardrobe)selectRoom(wardrobe.bedroom);});
for(const button of document.querySelectorAll('[data-wardrobe-view]'))button.addEventListener('click',()=>{
  setWardrobe($('wardrobe').value,button.dataset.wardrobeView);focusWardrobe($('wardrobe').value);
});
$('opening-focus').addEventListener('click',()=>{
  const opening=openings.get($('opening').value);if(!opening)return;
  setMode(['Rear2','StairShell2'].includes(opening.floorGroup)?'upper':'ground');
  $('cut').checked=false;$('labels').checked=false;updateVisibility();
  const normal=new THREE.Vector3(0,0,1).applyAxisAngle(new THREE.Vector3(0,1,0),opening.closedAngle);
  frame(opening.center.clone().addScaledVector(normal,3.4).add(new THREE.Vector3(0,1.1,0)),opening.center);
  $('view-name').textContent=opening.label;
  if(innerWidth<=800)container.scrollIntoView({block:'start'});
});
const picker=new THREE.Raycaster(),pointer=new THREE.Vector2(),activePointers=new Set();
let pointerStart=null;
renderer.domElement.addEventListener('pointerdown',event=>{
  activePointers.add(event.pointerId);
  pointerStart=activePointers.size===1&&event.button===0?{x:event.clientX,y:event.clientY,moved:false}:null;
});
renderer.domElement.addEventListener('pointermove',event=>{if(pointerStart&&Math.hypot(event.clientX-pointerStart.x,event.clientY-pointerStart.y)>6)pointerStart.moved=true;});
renderer.domElement.addEventListener('pointercancel',event=>{activePointers.delete(event.pointerId);pointerStart=null;});
renderer.domElement.addEventListener('pointerup',event=>{
  const start=pointerStart;activePointers.delete(event.pointerId);pointerStart=null;
  if(!start||start.moved||activePointers.size||event.button!==0||!ready)return;
  const rect=renderer.domElement.getBoundingClientRect();
  pointer.set((event.clientX-rect.left)/rect.width*2-1,-(event.clientY-rect.top)/rect.height*2+1);
  scene.updateMatrixWorld(true);camera.updateMatrixWorld(true);picker.setFromCamera(pointer,camera);
  for(const hit of picker.intersectObjects(meshes,false)){
    const mesh=hit.object;let visible=true;
    for(let node=mesh;node;node=node.parent)if(!node.visible){visible=false;break;}
    if(!visible)continue;
    const materials=Array.isArray(mesh.material)?mesh.material:[mesh.material];
    if(materials.some(mat=>mat.clippingPlanes?.some(plane=>plane.distanceToPoint(hit.point)<0)))continue;
    if(mesh.userData.openingId)toggleOpening(mesh.userData.openingId,mesh.userData.wardrobeDoorIndex);
    break;
  }
});
$('laundry-design').addEventListener('click',()=>{
  setMode('ground');$('cut').checked=false;updateVisibility();
  const target=toWorld(1.15,8.95,1.4);frame(toWorld(6.7,11.5,3.0),target);
  $('view-name').textContent='西连廊下 · 院内洗衣区';
  $('room-info').textContent='约2米洗衣区：主洗衣机＋叠放烘干机＋分区洗衣机，配洗衣池、台面和吊柜；前方约1.2米操作区。北侧两柱之间设可升降晾衣架，洗衣污废水与雨水分开。';
  if(innerWidth<=800)container.scrollIntoView({block:'start'});
});
$('pavilion-design').addEventListener('click',()=>{setMode('upper');$('roof').checked=true;$('cut').checked=false;$('labels').checked=false;updateVisibility();const target=toWorld(3.1,3.5,4.6);frame(toWorld(9,-2,8),target);$('view-name').textContent='二楼亭子 · 电动升降晾衣';$('room-info').textContent='亭内改为电动升降晾衣区，北侧水池和收纳保留；桌椅及东侧旧晾衣架取消。洗衣机已移到后楼二层过厅。使用升起／降下按钮查看状态，显示屋顶可切换亭顶。';if(innerWidth<=800)container.scrollIntoView({block:'start'});});
$('upper-laundry').addEventListener('click',()=>{
  selectRoom('rear2-8');indoor=true;$('cut').checked=false;$('labels').checked=false;updateVisibility();
  frame(toWorld(3.68,14.84,4.80),toWorld(3.68,16.10,4.40));
  $('view-name').textContent='二楼过厅 · 洗烘一体机';
  $('room-info').textContent='按蓝框移到主卧前过厅北侧凹位，机身向北后退，前方约1000mm通行/操作空间；保留主卧入口与床位。专用DB2-W1回路，插座和水阀分置上方两侧，独立排水立管沿西外墙接污废水井。勾选电气、给排水可查看连接；机器前开门与走人分时使用，最终按机型核尺寸。';
  if(innerWidth<=800)container.scrollIntoView({block:'start'});
});
$('kitchen-appliances').addEventListener('click',()=>{$('appliance-labels').checked=true;selectRoom('front-0');});
const kitchenKinds=new Set(['hob','sink','fridge','dishwasher','microwave','griddle','ricecooker','oven','coffee']);
function setDrying(lowered){
  dryingLowered=lowered;if(!dryingLift)return;
  const travel=lowered?dryingLift.meta.liftTravel:0;
  dryingLift.group.position.copy(dryingLift.closedPosition).add(new THREE.Vector3(0,-travel,0));
  for(const part of dryingCables)part.group.scale.y=part.closedScale.y*(1+travel/part.meta.cableLength);
  $('drying-status').textContent=lowered?'已降下 · 晾衣杆距地约1250mm，挂衣时下方保持净空。':'已升起 · 晾衣杆距地约2250mm；实际长衣下摆高度按衣物核对。';
  if(data.terrace_drying?.verification)$('drying-status').textContent+=' 承重、锚固和室外机型尚未核定。';
  $('drying-up').setAttribute('aria-pressed',String(!lowered));$('drying-down').setAttribute('aria-pressed',String(lowered));requestSolarShadow();
}
$('drying-up').addEventListener('click',()=>setDrying(false));
$('drying-down').addEventListener('click',()=>setDrying(true));
$('drying-focus').addEventListener('click',()=>{
  setMode('upper');$('roof').checked=false;$('cut').checked=false;$('labels').checked=false;updateVisibility();
  frame(toWorld(7.6,-.5,7.8),toWorld(3.15,3.2,5.1));$('view-name').textContent='亭内电动升降晾衣区';
  $('room-info').textContent='按蓝框将亭内改为电动升降晾衣区，原桌椅和东侧落地架已取消。北侧水池与收纳保留，台前名义约700mm；升起约2250mm、降下约1250mm，中央东侧通路留空。独立DB0-D1回路、带停止墙控，设备安装支架跨接亭梁；载荷、锚固及防雨等级按机型深化。';
  if(innerWidth<=800)container.scrollIntoView({block:'start'});
});
for(const item of data.furniture.front.filter(f=>f.room===0&&kitchenKinds.has(f.kind))){
  const element=document.createElement('span');element.className='appliance-label';element.hidden=true;
  element.textContent=item.name.replace(/（示意）|预留600|预留|操作位| \/ 咖啡台/g,'');container.append(element);
  const [a,b,c,d]=item.bounds;
  applianceLabels.push({element,point:toWorld((a+c)/2,(b+d)/2,.3+(item.z||0)+item.height+.13)});
}

function groupOf(mesh){let node=mesh;while(node){if(node.userData.floorGroup)return node.userData.floorGroup;node=node.parent;}return 'Site';}

async function load(){
  if((!window.HOUSE_MODEL&&!window.HOUSE_MODEL_URL)||!data)throw new Error('模型文件未完整加载，请保留 model 与 viewer 文件夹在页面旁边。');
  const loader=new GLTFLoader();
  const gltf=window.HOUSE_MODEL_URL?await loader.loadAsync(window.HOUSE_MODEL_URL):
    await loader.parseAsync(Uint8Array.from(atob(window.HOUSE_MODEL),c=>c.charCodeAt(0)).buffer,'');
  const root=gltf.scene;root.updateMatrixWorld(true);
  const buckets=new Map(),moving=new Map();
  root.traverse(obj=>{
    const meta=obj.userData;if((!meta.motion||!meta.openingId)&&!meta.motorizedDryingId&&!meta.motorizedCable)return;
    const group=new THREE.Group();obj.matrixWorld.decompose(group.position,group.quaternion,group.scale);
    const part={group,meta,closedPosition:group.position.clone(),closedQuaternion:group.quaternion.clone()};
    if(meta.motion==='slide'&&meta.defaultOpen)part.closedPosition.sub(new THREE.Vector3(meta.travel,0,0).applyQuaternion(group.quaternion));
    moving.set(obj,part);
    if(meta.motorizedDryingId||meta.motorizedCable){
      if(meta.motorizedDryingId)dryingLift=part;
      else{part.closedScale=group.scale.clone();dryingCables.push(part);}
      if(!layers[meta.floorGroup]){layers[meta.floorGroup]=new THREE.Group();scene.add(layers[meta.floorGroup]);}
      layers[meta.floorGroup].add(group);return;
    }
    if(!openings.has(meta.openingId))openings.set(meta.openingId,{id:meta.openingId,label:meta.openingLabel,kind:meta.openingKind,motion:meta.motion,floorGroup:meta.floorGroup,defaultOpen:meta.defaultOpen,open:meta.defaultOpen,closedAngle:meta.closedAngle??new THREE.Euler().setFromQuaternion(group.quaternion).y,parts:[]});
    openings.get(meta.openingId).parts.push(part);
    if(!layers[meta.floorGroup]){layers[meta.floorGroup]=new THREE.Group();scene.add(layers[meta.floorGroup]);}
    layers[meta.floorGroup].add(group);
  });
  root.traverse(obj=>{
    if(!obj.isMesh)return;
    const group=groupOf(obj),meta={...obj.userData,floorGroup:group};
    let pivot=obj.parent;while(pivot&&!moving.has(pivot))pivot=pivot.parent;
    const part=moving.get(pivot);
    meta.ceilingLight=obj.name.startsWith('Ceiling_light');
    meta.furnishing=!!meta.fixtureId||/^(Timber_table|Table_leg|Chair_|Storage_(north_shelf|east_shelf|shelf_upright|covered_box))/.test(obj.name);
    const attributes=Object.entries(obj.geometry.attributes).sort().map(([name,attr])=>`${name}:${attr.itemSize}:${attr.array.constructor.name}:${attr.normalized}`).join(',');
    const key=[group,pivot?.uuid||'',meta.openingId||'',meta.engineeringFloor||'',obj.material.uuid,!!meta.sectionable,meta.fixtureId||'',!!meta.ceilingLight,!!meta.interiorCeiling,!!meta.furnishing,!!obj.geometry.index,attributes].join('|');
    if(!buckets.has(key))buckets.set(key,{material:obj.material,meta,part,geometries:[]});
    const geom=obj.geometry.clone();geom.applyMatrix4(part?new THREE.Matrix4().copy(pivot.matrixWorld).invert().multiply(obj.matrixWorld):obj.matrixWorld);buckets.get(key).geometries.push(geom);
  });
  for(const {material,meta,part,geometries} of buckets.values()){
    const merged=mergeGeometries(geometries,false);
    if(!merged)throw new Error('无法组合模型几何，请重新导出三维模型。');
    const mat=material.clone();mat.side=THREE.DoubleSide;
    if(mat.transparent){mat.opacity=.25;mat.depthWrite=false;}
    const mesh=new THREE.Mesh(merged,mat);mesh.userData=meta;
    if(['Electrical','Plumbing','HVAC'].includes(meta.floorGroup)){
      mat.depthTest=false;mat.depthWrite=false;mesh.renderOrder=3;mesh.castShadow=false;mesh.receiveShadow=false;
    }
    if(!layers[meta.floorGroup]){layers[meta.floorGroup]=new THREE.Group();scene.add(layers[meta.floorGroup]);}
    (part?part.group:layers[meta.floorGroup]).add(mesh);meshes.push(mesh);
    geometries.forEach(g=>g.dispose());
  }
  scene.updateMatrixWorld(true);
  $('opening').replaceChildren(new Option('选择门窗',''));
  for(const opening of openings.values()){
    const box=new THREE.Box3();
    for(const mesh of meshes)if(mesh.userData.openingId===opening.id)box.expandByObject(mesh);
    opening.center=box.getCenter(new THREE.Vector3());
    if(opening.kind!=='wardrobe')$('opening').append(new Option(opening.label,opening.id));
  }
  $('wardrobe').replaceChildren(...wardrobes.filter(item=>openings.has(item.id)).map(item=>new Option(item.name,item.id)));
  $('wardrobe-controls').disabled=!$('wardrobe').options.length;
  $('drying-controls').disabled=!dryingLift;setDrying(false);
  $('sun-controls').disabled=false;
  $('opening-controls').disabled=false;
  window.HOUSE_MODEL=null;
  ready=true;status.hidden=true;$('render-status').textContent='模型已打开 · 可旋转查看';
  updateVisibility();
  window.houseViewer={
    getState:()=>({ready,mode,room:selectedRoom?.id||null,indoor,cut:$('cut').checked,roof:$('roof').checked,
      engineering:engineeringSelection(),engineeringVisible:Object.fromEntries(engineeringGroups.map(group=>[group,meshes.filter(mesh=>mesh.userData.floorGroup===group&&mesh.visible&&layers[group]?.visible).length])),
      groups:Object.fromEntries(Object.entries(layers).map(([name,g])=>[name,g.visible])),meshes:meshes.length,
      decorVisible:new Set(meshes.filter(mesh=>mesh.userData.fixtureId?.startsWith('decor-')&&mesh.visible&&layers[mesh.userData.floorGroup]?.visible).map(mesh=>mesh.userData.fixtureId)).size,
      ceilingsVisible:meshes.filter(mesh=>mesh.userData.interiorCeiling&&mesh.visible&&layers[mesh.userData.floorGroup]?.visible).length,
      sunlight:{enabled:$('sun-enabled').checked,hour:solarHour,playing:solarPlaying,position:sun.position.toArray(),shadows:renderer.shadowMap.enabled,clock:daylightAt(solarHour).clock},
      drying:{ready:!!dryingLift,lowered:dryingLowered,position:dryingLift?.group.position.toArray(),cableScales:dryingCables.map(p=>p.group.scale.y)},
      wardrobeDetail,wardrobes:[...openings.values()].filter(o=>o.kind==='wardrobe').map(o=>({id:o.id,view:o.view||'closed',parts:o.parts.map(p=>({index:p.meta.panelIndex,open:!!p.open,position:p.group.position.toArray(),quaternion:p.group.quaternion.toArray(),visible:p.group.visible})),visibleMeshes:meshes.filter(m=>m.userData.wardrobeId===o.id&&m.visible&&layers[m.userData.floorGroup]?.visible).length})),
      openings:[...openings.values()].filter(o=>o.kind!=='wardrobe').map(o=>({id:o.id,label:o.label,kind:o.kind,motion:o.motion,open:o.open,defaultOpen:o.defaultOpen,parts:o.parts.map(p=>({position:p.group.position.toArray(),quaternion:p.group.quaternion.toArray()}))})),
      camera:camera.position.toArray(),target:controls.target.toArray(),rendererCalls:renderer.info.render.calls}),
  };
}
load().catch(error=>{status.hidden=false;status.classList.add('error');status.textContent=`三维模型打开失败：${error.message}`;console.error(error);});

function animate(now=performance.now()){
  requestAnimationFrame(animate);controls.update();
  if(solarPlaying&&now-lastSolarTick>=50){
   solarHour=Math.min(18,solarHour+Math.min((now-lastSolarTick)/1000,.25)*.4);lastSolarTick=now;
   if(solarHour>=18)solarPlaying=false;
   updateDaylight();
  }
  if(!dirty)return;
  dirty=false;
  for(const {room,element} of labels){
    const visible=ready&&$('labels').checked&&!indoor&&viewState(mode).groups.includes({front:'Front',rear1:'Rear1',rear2:'Rear2'}[room.group]);
    if(!visible){element.hidden=true;continue;}
    const [x1,y1,x2,y2]=room.bounds;const point=toWorld((x1+x2)/2,(y1+y2)/2,room.floor+.5).project(camera);
    element.hidden=point.z>1||point.z<0||Math.abs(point.x)>1||Math.abs(point.y)>1;
    element.style.left=`${(point.x+1)*.5*container.clientWidth}px`;element.style.top=`${(1-point.y)*.5*container.clientHeight}px`;
  }
  for(const label of solarLabels){
    const point=label.point.clone().project(camera);label.element.hidden=!solarGroup.visible||point.z<0||point.z>1||Math.abs(point.x)>1||Math.abs(point.y)>1;
    if(!label.element.hidden){label.element.style.left=(point.x+1)*.5*container.clientWidth+'px';label.element.style.top=((1-point.y)*.5*container.clientHeight-24)+'px';}
  }
  const occupied=[];
  for(const label of applianceLabels){
    const point=label.point.clone().project(camera);
    const visible=ready&&$('appliance-labels').checked&&$('furniture').checked&&selectedRoom?.id==='front-0'&&point.z>0&&point.z<1&&Math.abs(point.x)<1&&Math.abs(point.y)<1;
    label.element.hidden=!visible;if(!visible)continue;
    const w=label.element.offsetWidth,h=label.element.offsetHeight;
    let x=Math.max(w/2+8,Math.min(container.clientWidth-w/2-8,(point.x+1)*.5*container.clientWidth));
    let y=(1-point.y)*.5*container.clientHeight;
    for(let i=0;i<applianceLabels.length;i++){
      if(!occupied.some(b=>Math.abs(x-b.x)<(w+b.w)/2+4&&Math.abs(y-b.y)<(h+b.h)/2+3))break;
      y-=h+4;
    }
    y=Math.max(h/2+8,y);occupied.push({x,y,w,h});label.element.style.left=x+'px';label.element.style.top=y+'px';
  }
  const dir=new THREE.Vector3();camera.getWorldDirection(dir);
  $('compass').style.transform=`rotate(${Math.atan2(dir.x,-dir.z)}rad)`;
  renderer.render(scene,camera);
}
animate();
