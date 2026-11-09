// Illustrative 06:00–18:00 east–south–west arc; no site/date calibration.
export function daylightAt(hour) {
  if (!Number.isFinite(hour) || hour<6 || hour>18) throw new RangeError('Daylight hour must be 6–18');
  const angle=(hour-6)/12*Math.PI, height=Math.max(0,Math.sin(angle));
  const peak=55*Math.PI/180, minute=Math.round(hour*60);
  return {
    direction:[Math.cos(angle),height*Math.sin(peak),height*Math.cos(peak)],
    strength:Math.pow(height,.65),
    clock:`${String(Math.floor(minute/60)).padStart(2,'0')}:${String(minute%60).padStart(2,'0')}`,
    phase:hour<10?'晨光 · 太阳在东侧':hour<=14?'午间 · 太阳在南侧':'夕照 · 太阳在西侧',
  };
}
