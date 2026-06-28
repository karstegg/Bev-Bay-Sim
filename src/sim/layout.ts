import { Machine, Vector2, SimConfig } from "./types";

export function getPathToPark(m: Machine): Vector2[] {
  const path: Vector2[] = [];

  if (m.pos.x >= 1040) {
    // 1. In working areas: drive to access row, exit lane, down to bottom lane, then go to parking entry from below
    // We assume if they are >= 1040 they are in a work area. We need to compute areaAccessY.
    // If we don't have workSlotId here, we can guess based on y.
    const areaId = Math.floor(m.pos.y / 160) + 1;
    const areaAccessY = (areaId - 1) * 160 + 95;
    path.push({ x: m.pos.x, y: areaAccessY });
    path.push({ x: 1280, y: areaAccessY });
    path.push({ x: 1280, y: 660 });
    path.push({ x: 20, y: 660 });
    path.push({ x: 20, y: m.parkingPos.y });
  } else if (m.pos.x >= 250) {
    // 2. In swap stations: drive right to clear the station first, down entry lane (1020) then parking entry
    path.push({ x: 1020, y: m.pos.y });
    path.push({ x: 1020, y: 660 });
    path.push({ x: 20, y: 660 });
    path.push({ x: 20, y: m.parkingPos.y });
  } else {
    // 3. Already in the vertical lanes
    if (m.pos.x > 150) {
      // Upward lane (going up)
      path.push({ x: 195, y: 40 });
      path.push({ x: 135, y: 40 });
      path.push({ x: 135, y: m.parkingPos.y });
    } else {
      // Downward lane (going down)
      path.push({ x: 135, y: 660 });
      path.push({ x: 20, y: 660 });
      path.push({ x: 20, y: m.parkingPos.y });
    }
  }

  path.push(m.parkingPos);
  return path;
}

export function assignWorkArea(config: SimConfig) {
  const r = Math.random() * 100;
  let sum = 0;
  for (let i = 0; i < 4; i++) {
    sum += config.workAreaSplits[i];
    if (r <= sum) return { id: i + 1, mult: config.workAreaMultipliers[i] };
  }
  return { id: 4, mult: config.workAreaMultipliers[3] };
}
