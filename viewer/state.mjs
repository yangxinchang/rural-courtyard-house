const modes = {
  whole: {groups:['Site','Front','Rear1','Rear2','Attic','Roofs','Terrace','Stairs','StairShell1','StairShell2','StairRoof','EntryRoof','BridgeCanopy','Garden','Outbuilding','OutbuildingRoof','Pavilion','PavilionRoof'],floor:.3,cutWalls:false},
  ground: {groups:['Site','Front','Rear1','Stairs','StairShell1','Garden','Outbuilding'],floor:.3,cutWalls:true},
  upper: {groups:['Rear2','Terrace','Stairs','StairShell2','EntryRoof','Pavilion','PavilionRoof'],floor:3.6,cutWalls:true},
  attic: {groups:['Attic'],floor:6.9,cutWalls:true},
};

export const engineeringGroups = ['Structure','Electrical','Plumbing','HVAC'];

export function viewState(mode,engineering={}) {
  if (!Object.hasOwn(modes,mode)) throw new Error(`Unknown view: ${mode}`);
  const engineeringFloors=mode==='ground'?['front','rear1','site']:mode==='upper'?['rear2','site']:mode==='attic'?['rear2']:['front','rear1','rear2','site'];
  return {...modes[mode],engineeringFloors,groups:[...modes[mode].groups,...engineeringGroups.filter(group=>engineering[group]&&(mode!=='attic'||group==='Structure'))]};
}

export function overviewFrame(mode,site=[15.2,29.4],bounds=[0,0,...site]) {
  if(mode==='upper')return {target:[6,12,3.9],distance:30,topDistance:36};
  if(mode==='attic')return {target:[6,19,7.1],distance:21,topDistance:20};
  const [x1,y1,x2,y2]=bounds,span=Math.max(x2-x1,y2-y1);
  return {target:[(x1+x2)/2,(y1+y2)/2,2.3],distance:span*1.3,topDistance:span*1.55};
}

export function roomEye(room) {
  const [x1,y1,x2,y2]=room.bounds||room.inner;
  if(room.kind==='stair')return [room.floor>3?13.35:12.2,room.floor>3?17.25:17.5,room.floor+1.6];
  if(room.id==='front-0')return [8.95,2.4,room.floor+1.6];
  if(room.id==='front-2')return [3.65,4.10,room.floor+1.6];
  if(room.id==='rear1-1')return [2.32,21.6,room.floor+1.6];
  if(room.id==='rear1-0')return [2,16.4,room.floor+1.6];
  if(room.id==='rear1-3')return [6.7,20.1,room.floor+1.6];
  if(room.id==='rear1-2')return [3.2,21.8,room.floor+1.6];
  if(room.id==='rear1-5')return [9,16.4,room.floor+1.6];
  if(room.id==='rear1-6')return [10.5,21.55,room.floor+1.6];
  if(room.id==='rear1-7'||room.id==='rear2-7')return [12.4,22.02,room.floor+1.6];
  if(room.id==='rear1-8')return [12.4,15.15,room.floor+1.6];
  if(room.id==='rear2-6')return [10.8,21.55,room.floor+1.6];
  if(room.id==='rear2-3')return [6.7,17.4,room.floor+1.6];
  if(room.id==='rear2-5')return [8.3,18.75,room.floor+1.6];
  if(room.id==='rear2-8')return [6,15.3,room.floor+1.6];
  if(room.id==='rear2-9')return [10.55,16.55,room.floor+1.6];
  const kitchen=room.group==='front'&&room.index===0;
  const x=room.name==='衣帽'?x1+.35:kitchen?x1+.55:room.kind==='wet'?x2-.5:x2-.65;
  return [x,kitchen?y2-.9:y1+.8,room.floor+1.6];
}
