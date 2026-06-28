export interface Vector2 {
  x: number;
  y: number;
}

export type MachineType = "DT" | "FL";
export type BatteryType = "VPX" | "VPY";
export type MachineState =
  | "working"
  | "driving_to_queue"
  | "in_queue"
  | "driving_to_swap"
  | "at_swap"
  | "driving_away"
  | "driving_to_work"
  | "driving_from_work"
  | "driving_to_park"
  | "parked";
export type BatteryState = "in_machine" | "on_pad" | "held_by_crane";

export interface Machine {
  id: string;
  type: MachineType;
  state: MachineState;
  batteryId: string | null;
  pos: Vector2;
  lastPos: Vector2;
  rotation: number;
  heading: number;
  targetPos: Vector2 | null;
  path?: Vector2[];
  waitTime: number;
  swapBayId: string | null;
  assignedBatteryId: string | null;
  queueIndex?: number;
  workAreaId: number;
  workAreaMultiplier: number;
  parkingPos: Vector2;
  workSlotId: string | null;

  width: number;
  length: number;
  currentSpeed: number;
  maxSpeed: number;
  acceleration: number;
  deceleration: number;
  turnRate: number;
  isBraking: boolean;
  blockedBy: string | null;
  stopTimer: number;
}

export interface Battery {
  id: string;
  type: BatteryType;
  state: BatteryState;
  charge: number;
  pos: Vector2;
  machineId: string | null;
  padId: string | null;
  reservedBy: string | null;
}

export interface Pad {
  id: string;
  type: "charger" | "storage";
  pos: Vector2;
  batteryId: string | null;
  reserved: boolean;
}

export interface SwapBay {
  id: string;
  pos: Vector2;
  machineId: string | null;
  reservedBy: string | null;
}

export type CraneState =
  | "idle"
  | "moving_to_remove"
  | "removing"
  | "moving_to_store"
  | "storing"
  | "moving_to_fetch"
  | "fetching"
  | "moving_to_install"
  | "installing"
  | "moving_to_fetch_for_charge"
  | "fetching_for_charge"
  | "moving_to_charge"
  | "storing_for_charge";

export interface ConflictZone {
  id: string;
  pos: Vector2;
  radius: number;
  occupantId: string | null;
}

export interface StopSign {
  id: string;
  pos: Vector2;
  dir: Vector2;
}

export interface TrafficLight {
  id: string;
  pos: Vector2;
  swapBayId: string;
  state: "red" | "green";
}

export interface Crane {
  id: string;
  state: CraneState;
  pos: Vector2;
  targetPos: Vector2 | null;
  swapBayId: string | null;
  batteryId: string | null;
  targetPadId: string | null;
  timer: number;
  targetMachineId: string | null;
}

export interface SimConfig {
  speed: number;
  arrivalRateMult: number;
  swapTime: number; // seconds
  activeCranes: number;
  showLabels: boolean;
  showTrafficDebug: boolean;
  spareBatteries: number;
  shiftActive: boolean;
  workAreaSplits: [number, number, number, number];
  workAreaMultipliers: [number, number, number, number];
  dischargeTimeDT: number;
  dischargeTimeFL: number;
  chargeTimeVPX: number;
  chargeTimeVPY: number;
  speedDT: number;
  speedFL: number;
  deadTimeHours: number;
}

export interface SimKPIs {
  machinesWaiting: number;
  machinesServed: number;
  totalWaitTime: number;
  avgWaitingTime: number;
  chargedBatteriesReady: number;
  batteriesCharging: number;
  depletedWaiting: number;
  chargerUtilisation: number;
  craneUtilisation: number;
  totalTurnaroundTime: number;
  avgTurnaroundTime: number;
  bottleneck: string;
  simTimeHours: number;
}

export interface WorkSlot {
  id: string;
  areaId: number;
  pos: Vector2;
  machineId: string | null;
}

export interface SimState {
  time: number;
  machines: Machine[];
  batteries: Battery[];
  pads: Pad[];
  swapBays: SwapBay[];
  cranes: Crane[];
  workSlots: WorkSlot[];
  config: SimConfig;
  kpis: SimKPIs;
  conflictZones: ConflictZone[];
  stopSigns: StopSign[];
  trafficLights: TrafficLight[];
}
