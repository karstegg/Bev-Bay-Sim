import { SimConfig } from "./types";

export const DEFAULT_CONFIG: SimConfig = {
  speed: 1,
  arrivalRateMult: 1,
  swapTime: 5,
  activeCranes: 2,
  showLabels: true,
  showTrafficDebug: false,
  spareBatteries: 8,
  shiftActive: true,
  workAreaSplits: [25, 25, 20, 30],
  workAreaMultipliers: [0.8, 1.0, 1.5, 2.0],
  dischargeTimeDT: 150,
  dischargeTimeFL: 200,
  chargeTimeVPX: 12,
  chargeTimeVPY: 12,
  speedDT: 100,
  speedFL: 100,
  deadTimeHours: 3,
};
