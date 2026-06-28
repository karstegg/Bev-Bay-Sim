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
}

const COLORS = {
  bg: "#1A1C1E",
  grid: "#2C2F33",
  track: "#23272A",
  rail: "#3F444A",
  DT: "#37474F",
  FL: "#444444",
  batteryEmpty: "#F44336",
  batteryLow: "#F9A825",
  batteryMid: "#4CAF50",
  batteryFull: "#4CAF50",
  padCharger: "#2C2F33",
  padChargerBorder: "#3F444A",
  padStorage: "#23272A",
  padStorageBorder: "#3F444A",
  crane: "#F9A825",
  swapBay: "#F9A825",
};

export function createSimulation(config: SimConfig): SimState {
  const pads: Pad[] = [];
  const workSlots: WorkSlot[] = [];

  for (let areaId = 1; areaId <= 4; areaId++) {
    for (let s = 0; s < 6; s++) {
      workSlots.push({
        id: `WA${areaId}-${s}`,
        areaId,
        pos: {
          x: 1080 + (s % 3) * 70,
          y: (areaId - 1) * 160 + 70 + Math.floor(s / 3) * 50,
        },
        machineId: null,
      });
    }
  }
  // 8 Chargers (Top and Bottom rows)
  for (let i = 0; i < 4; i++)
    pads.push({
      id: `C${i}`,
      type: "charger",
      pos: { x: 650 + i * 90, y: 150 },
      batteryId: null,
      reserved: false,
    });
  for (let i = 0; i < 4; i++)
    pads.push({
      id: `C${i + 4}`,
      type: "charger",
      pos: { x: 650 + i * 90, y: 450 },
      batteryId: null,
      reserved: false,
    });

  // 8 Storage
  for (let i = 0; i < 4; i++)
    pads.push({
      id: `S${i}`,
      type: "storage",
      pos: { x: 650 + i * 90, y: 250 },
      batteryId: null,
      reserved: false,
    });
  for (let i = 0; i < 4; i++)
    pads.push({
      id: `S${i + 4}`,
      type: "storage",
      pos: { x: 650 + i * 90, y: 550 },
      batteryId: null,
      reserved: false,
    });

  const batteries: Battery[] = [];
  const machines: Machine[] = [];

  const spareCount = Math.min(16, Math.max(0, config.spareBatteries));
  const spareVPX = Math.ceil(spareCount / 2);
  const spareVPY = Math.floor(spareCount / 2);

  let bId = 0;

  // Create spare batteries
  for (let i = 0; i < spareVPX; i++)
    batteries.push({
      id: `VPX-${bId++}`,
      type: "VPX",
      state: "on_pad",
      charge: 100,
      pos: { x: 0, y: 0 },
      machineId: null,
      padId: null,
      reservedBy: null,
    });
  for (let i = 0; i < spareVPY; i++)
    batteries.push({
      id: `VPY-${bId++}`,
      type: "VPY",
      state: "on_pad",
      charge: 100,
      pos: { x: 0, y: 0 },
      machineId: null,
      padId: null,
      reservedBy: null,
    });

  // Assign spares to pads (chargers first)
  for (let i = 0; i < batteries.length; i++) {
    const b = batteries[i];
    const p = pads[i];
    b.padId = p.id;
    b.pos = { ...p.pos };
    p.batteryId = b.id;
  }

  // Machines
  for (let i = 0; i < 8; i++) {
    const b: Battery = {
      id: `VPX-${bId++}`,
      type: "VPX",
      state: "in_machine",
      charge: i === 0 ? 0 : 100,
      pos: { x: -100, y: -100 },
      machineId: `DT-${i}`,
      padId: null,
      reservedBy: null,
    };
    batteries.push(b);
    const area = assignWorkArea(config);
    const parkingPos = { x: 70, y: 55 + i * 40 };
    machines.push({
      id: `DT-${i}`,
      type: "DT",
      state: "parked",
      batteryId: b.id,
      pos: { ...parkingPos },
      lastPos: { ...parkingPos },
      rotation: 0,
      targetPos: null,
      waitTime: 0,
      swapBayId: null,
      assignedBatteryId: null,
      workAreaId: area.id,
      workAreaMultiplier: area.mult,
      parkingPos: { ...parkingPos },
      workSlotId: null,
    });
  }
  for (let i = 0; i < 6; i++) {
    const b: Battery = {
      id: `VPY-${bId++}`,
      type: "VPY",
      state: "in_machine",
      charge: 100,
      pos: { x: -100, y: -100 },
      machineId: `FL-${i}`,
      padId: null,
      reservedBy: null,
    };
    batteries.push(b);
    const area = assignWorkArea(config);
    const parkingPos = { x: 70, y: 55 + (8 + i) * 40 };
    machines.push({
      id: `FL-${i}`,
      type: "FL",
      state: "parked",
      batteryId: b.id,
      pos: { ...parkingPos },
      lastPos: { ...parkingPos },
      rotation: 0,
      targetPos: null,
      waitTime: 0,
      swapBayId: null,
      assignedBatteryId: null,
      workAreaId: area.id,
      workAreaMultiplier: area.mult,
      parkingPos: { ...parkingPos },
      workSlotId: null,
    });
  }

  const swapBays: SwapBay[] = [
    { id: "SB1", pos: { x: 400, y: 200 }, machineId: null, reservedBy: null },
    { id: "SB2", pos: { x: 400, y: 500 }, machineId: null, reservedBy: null },
  ];

  const cranes: Crane[] = [
    {
      id: "CR1",
      state: "idle",
      pos: { x: 500, y: 200 },
      targetPos: null,
      swapBayId: null,
      batteryId: null,
      targetPadId: null,
      timer: 0,
      targetMachineId: null,
    },
    {
      id: "CR2",
      state: "idle",
      pos: { x: 500, y: 500 },
      targetPos: null,
      swapBayId: null,
      batteryId: null,
      targetPadId: null,
      timer: 0,
      targetMachineId: null,
    },
  ];

  return {
    time: 0,
    machines,
    batteries,
    pads,
    swapBays,
    cranes,
    workSlots,
    config: { ...config },
    kpis: {
      machinesWaiting: 0,
      machinesServed: 0,
      totalWaitTime: 0,
      avgWaitingTime: 0,
      chargedBatteriesReady: 0,
      batteriesCharging: 0,
      depletedWaiting: 0,
      chargerUtilisation: 0,
      craneUtilisation: 0,
      totalTurnaroundTime: 0,
      avgTurnaroundTime: 0,
      bottleneck: "None",
      simTimeHours: 0,
    },
  };
}

function moveTowards(
  current: Vector2,
  target: Vector2 | null,
  speed: number,
  dt: number,
) {
  if (!target) return { ...current, reached: true };
  const dx = target.x - current.x;
  const dy = target.y - current.y;
  const dist = Math.sqrt(dx * dx + dy * dy);
  if (dist <= speed * dt) {
    return { x: target.x, y: target.y, reached: true };
  }
  return {
    x: current.x + (dx / dist) * speed * dt,
    y: current.y + (dy / dist) * speed * dt,
    reached: false,
  };
}

function moveMachineAlongPath(m: Machine, speed: number, dt: number): boolean {
  if (m.path && m.path.length > 0) {
    m.targetPos = m.path[0];
  }

  if (!m.targetPos) return true;

  const res = moveTowards(m.pos, m.targetPos, speed, dt);
  m.pos = { x: res.x, y: res.y };

  if (res.reached) {
    if (m.path && m.path.length > 0) {
      m.path.shift();
      if (m.path.length > 0) {
        m.targetPos = m.path[0];
        return false;
      }
    }
    return true; // Reached final destination
  }
  return false;
}

function getPathToPark(m: Machine): Vector2[] {
  const path: Vector2[] = [];

  if (m.pos.x >= 1000) {
    // 1. In working areas: drive down to bottom lane, then go to parking entry from below
    path.push({ x: 1020, y: 660 });
    path.push({ x: 70, y: 660 });
    path.push({ x: 70, y: m.parkingPos.y });
  } else if (m.pos.x >= 250) {
    // 2. In swap stations: drive right to clear the station first, then go to parking entry from below
    path.push({ x: 1020, y: m.pos.y });
    path.push({ x: 1020, y: 660 });
    path.push({ x: 70, y: 660 });
    path.push({ x: 70, y: m.parkingPos.y });
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
      path.push({ x: 70, y: 660 });
      path.push({ x: 70, y: m.parkingPos.y });
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

export function updateSimulation(state: SimState, dt: number) {
  const simDt = dt * state.config.speed;
  state.time += simDt;

  // 10 seconds of real time (at 1x) = 1 hour of sim time
  const simTimeHours = (state.time / 10) % 24;
  state.kpis.simTimeHours = simTimeHours;

  // Shift is active except for the last deadTimeHours
  state.config.shiftActive = simTimeHours < 24 - state.config.deadTimeHours;

  const chargeTimeVPX = Math.max(1, state.config.chargeTimeVPX);
  const chargeTimeVPY = Math.max(1, state.config.chargeTimeVPY);
  const dischargeBaseDT = state.config.dischargeTimeDT;
  const dischargeBaseFL = state.config.dischargeTimeFL;
  const speedDT = state.config.speedDT;
  const speedFL = state.config.speedFL;

  // --- MACHINES ---
  const queuedMachines = state.machines
    .filter((m) => m.state === "driving_to_queue" || m.state === "in_queue")
    .sort((a, b) => b.waitTime - a.waitTime);

  queuedMachines.forEach((m, idx) => {
    m.queueIndex = idx;
  });

  for (const m of state.machines) {
    const battery = state.batteries.find((b) => b.id === m.batteryId);

    // If battery SOC is 0, force it to go straight to battery swap if shift is active!
    if (state.config.shiftActive && battery && battery.charge <= 0.1) {
      const goingToSwapStates = [
        "driving_from_work",
        "driving_to_queue",
        "in_queue",
        "driving_to_swap",
        "at_swap",
        "driving_away",
      ];
      if (!goingToSwapStates.includes(m.state)) {
        if (m.workSlotId) {
          const slot = state.workSlots.find((s) => s.id === m.workSlotId);
          if (slot) slot.machineId = null;
          m.workSlotId = null;
        }

        m.state = "driving_from_work";

        if (m.pos.x <= 120) {
          // Left side / parking bay: drive straight down, then right along bottom road to queue
          m.path = [
            { x: 70, y: 660 }, // Bottom of parking bay / bottom road
            { x: 195, y: 660 }, // Bottom lane to queue entry
            { x: 195, y: 600 }, // Enter queue upwards
          ];
        } else {
          // Anywhere else: go to distribution lane, down to bottom road, then to queue entry
          m.path = [
            { x: 1020, y: m.pos.y },
            { x: 1020, y: 660 },
            { x: 195, y: 660 },
            { x: 195, y: 600 },
          ];
        }
        m.targetPos = m.path[0];
      }
    }

    if (m.state === "working") {
      if (!state.config.shiftActive) {
        if (m.workSlotId) {
          const slot = state.workSlots.find((s) => s.id === m.workSlotId);
          if (slot) slot.machineId = null;
          m.workSlotId = null;
        }
        m.state = "driving_to_park";
        m.path = getPathToPark(m);
        m.targetPos = m.path[0] || m.parkingPos;
      } else {
        const battery = state.batteries.find((b) => b.id === m.batteryId);
        if (battery) {
          const dischargeRate =
            m.type === "DT" ? dischargeBaseDT : dischargeBaseFL;
          const rateMult = state.config.arrivalRateMult * m.workAreaMultiplier;
          battery.charge -= (100 / (dischargeRate / rateMult)) * simDt;
          if (battery.charge <= 20) {
            m.state = "driving_from_work";
            m.path = [
              { x: 1020, y: m.pos.y }, // Exit work area to the distribution lane
              { x: 1020, y: 660 }, // Drive down the distribution lane
              { x: 195, y: 660 }, // Drive left along bottom lane
              { x: 195, y: 600 }, // Enter queue upward
            ];
            m.targetPos = m.path[0];
            if (m.workSlotId) {
              const slot = state.workSlots.find((s) => s.id === m.workSlotId);
              if (slot) slot.machineId = null;
              m.workSlotId = null;
            }
          }
        }
      }
    } else if (m.state === "driving_from_work") {
      if (!state.config.shiftActive) {
        m.state = "driving_to_park";
        m.path = getPathToPark(m);
        m.targetPos = m.path[0] || m.parkingPos;
      } else {
        m.lastPos = { ...m.pos };
        const mSpeed =
          (m.type === "DT" ? speedDT : speedFL) * state.config.speed;
        const reached = moveMachineAlongPath(m, mSpeed, dt);
        if (reached) {
          m.state = "driving_to_queue";
          m.pos = { x: 195, y: 650 }; // Enter from bottom lane
          m.path = [];
          m.waitTime = 0;
        }
      }
    } else if (m.state === "driving_to_work") {
      if (!state.config.shiftActive) {
        if (m.workSlotId) {
          const slot = state.workSlots.find((s) => s.id === m.workSlotId);
          if (slot) slot.machineId = null;
          m.workSlotId = null;
        }
        m.state = "driving_to_park";
        m.path = getPathToPark(m);
        m.targetPos = m.path[0] || m.parkingPos;
      } else {
        m.lastPos = { ...m.pos };
        const mSpeed =
          (m.type === "DT" ? speedDT : speedFL) * state.config.speed;
        const reached = moveMachineAlongPath(m, mSpeed, dt);
        if (reached) {
          m.state = "working";
        }
      }
    } else if (m.state === "driving_to_park") {
      m.lastPos = { ...m.pos };
      const mSpeed = (m.type === "DT" ? speedDT : speedFL) * state.config.speed;
      if (!m.path || m.path.length === 0) {
        m.path = getPathToPark(m);
        m.targetPos = m.path[0] || m.parkingPos;
      }
      const reached = moveMachineAlongPath(m, mSpeed, dt);
      if (reached) {
        m.state = "parked";
      }
    } else if (m.state === "parked") {
      m.rotation = 0; // face right while parked
      if (state.config.shiftActive) {
        const area = assignWorkArea(state.config);
        m.workAreaId = area.id;
        m.workAreaMultiplier = area.mult;
        const emptySlot = state.workSlots.find(
          (s) => s.areaId === m.workAreaId && !s.machineId,
        );
        let target = emptySlot
          ? emptySlot.pos
          : { x: 1100, y: (m.workAreaId - 1) * 160 + 80 };
        if (emptySlot) {
          emptySlot.machineId = m.id;
          m.workSlotId = emptySlot.id;
        }
        m.path = [
          { x: 70, y: 20 }, // Drive up the parking bay
          { x: 1020, y: 20 }, // Drive right along the top road
          { x: 1020, y: target.y }, // Move down to the row of the working area
          target, // Enter work area
        ];
        m.targetPos = m.path[0];
        m.state = "driving_to_work";
      }
    } else if (m.state === "driving_to_queue" || m.state === "in_queue") {
      if (!state.config.shiftActive) {
        m.state = "driving_to_park";
        m.path = getPathToPark(m);
        m.targetPos = m.path[0] || m.parkingPos;
        m.waitTime = 0;
      } else {
        m.waitTime += simDt;
        const targetY = 100 + (m.queueIndex || 0) * 50;

        m.lastPos = { ...m.pos };
        const mSpeed =
          (m.type === "DT" ? speedDT : speedFL) * state.config.speed;

        // Ensure they just strictly follow queue up
        m.path = [{ x: 200, y: targetY }];
        const reached = moveMachineAlongPath(m, mSpeed, dt);

        if (reached) {
          m.state = "in_queue";
        }

        // Allocate swap bay if at front
        if (m.state === "in_queue" && queuedMachines[0].id === m.id) {
          const emptySwapBay = state.swapBays.find((sb) => !sb.reservedBy);
          const reqBatType = m.type === "DT" ? "VPX" : "VPY";
          const chargedBattery = state.batteries.find(
            (b) =>
              b.type === reqBatType &&
              b.charge >= 99 &&
              !b.reservedBy &&
              b.padId,
          );

          if (emptySwapBay && chargedBattery) {
            emptySwapBay.reservedBy = m.id;
            chargedBattery.reservedBy = m.id;
            m.swapBayId = emptySwapBay.id;
            m.assignedBatteryId = chargedBattery.id;
            m.state = "driving_to_swap";
            if (emptySwapBay.id === "SB2") {
              m.path = [
                { x: 195, y: 120 }, // Continue up queue lane to the turnoff
                { x: 230, y: 120 }, // Turn right into downward entry lane
                { x: 230, y: 500 }, // Drive down to Swap Station 2 y-level
                emptySwapBay.pos, // Enter Swap Station 2
              ];
            } else {
              m.path = [
                { x: 195, y: 200 }, // Drive to Swap Station 1 y-level
                emptySwapBay.pos, // Enter Swap Station 1
              ];
            }
            m.targetPos = m.path[0];
          }
        }
      }
    } else if (m.state === "driving_to_swap") {
      if (!state.config.shiftActive) {
        const sb = state.swapBays.find((sb) => sb.id === m.swapBayId);
        if (sb) sb.reservedBy = null;
        const b = state.batteries.find((b) => b.id === m.assignedBatteryId);
        if (b) b.reservedBy = null;
        m.swapBayId = null;
        m.assignedBatteryId = null;
        m.state = "driving_to_park";
        m.path = getPathToPark(m);
        m.targetPos = m.path[0] || m.parkingPos;
      } else {
        m.lastPos = { ...m.pos };
        const mSpeed =
          (m.type === "DT" ? speedDT : speedFL) * state.config.speed;
        const reached = moveMachineAlongPath(m, mSpeed, dt);
        if (reached) {
          m.state = "at_swap";
          const sb = state.swapBays.find((sb) => sb.id === m.swapBayId);
          if (sb) sb.machineId = m.id;
        }
      }
    } else if (m.state === "driving_away") {
      if (!m.path || m.path.length === 0) {
        m.path = [{ x: 450, y: m.pos.y }];
        m.targetPos = m.path[0];
      }
      m.lastPos = { ...m.pos };
      const mSpeed = (m.type === "DT" ? speedDT : speedFL) * state.config.speed;
      const reached = moveMachineAlongPath(m, mSpeed, dt);
      if (reached) {
        const sb = state.swapBays.find((sb) => sb.id === m.swapBayId);
        if (sb) {
          sb.machineId = null;
          sb.reservedBy = null;
        }
        m.swapBayId = null;
        state.kpis.machinesServed++;
        state.kpis.totalTurnaroundTime += m.waitTime;
        m.waitTime = 0;

        if (!state.config.shiftActive) {
          m.state = "driving_to_park";
          m.path = getPathToPark(m);
          m.targetPos = m.path[0] || m.parkingPos;
        } else {
          const area = assignWorkArea(state.config);
          m.workAreaId = area.id;
          m.workAreaMultiplier = area.mult;
          const emptySlot = state.workSlots.find(
            (s) => s.areaId === m.workAreaId && !s.machineId,
          );
          let target = emptySlot
            ? emptySlot.pos
            : { x: 1100, y: (m.workAreaId - 1) * 160 + 80 };
          if (emptySlot) {
            emptySlot.machineId = m.id;
            m.workSlotId = emptySlot.id;
          }
          m.state = "driving_to_work";
          m.path = [
            { x: 450, y: m.pos.y }, // Drive right to the upward lane
            { x: 450, y: 20 }, // Drive up to the top road
            { x: 1020, y: 20 }, // Drive right along top road
            { x: 1020, y: target.y }, // Move down to target row
            target, // Enter work area
          ];
          m.targetPos = m.path[0];
        }
      }
    }

    // Calculate rotation based on velocity
    const dx = m.pos.x - m.lastPos.x;
    const dy = m.pos.y - m.lastPos.y;
    if (Math.abs(dx) > 0.1 || Math.abs(dy) > 0.1) {
      m.rotation = Math.atan2(dy, dx);
    }
  }

  // --- BATTERIES ---
  for (const b of state.batteries) {
    if (b.state === "in_machine") {
      const m = state.machines.find((m) => m.id === b.machineId);
      if (m) b.pos = { ...m.pos };
    } else if (b.state === "held_by_crane") {
      const c = state.cranes.find((c) => c.batteryId === b.id);
      if (c) b.pos = { ...c.pos };
    } else if (b.state === "on_pad") {
      const p = state.pads.find((p) => p.id === b.padId);
      if (p) {
        b.pos = { ...p.pos };
        if (p.type === "charger" && b.charge < 100) {
          const cTime = b.type === "VPX" ? chargeTimeVPX : chargeTimeVPY;
          b.charge += (100 / cTime) * simDt;
          if (b.charge > 100) b.charge = 100;
        }
      }
    }
  }

  // --- CRANES ---
  const craneSpeed = 150 * state.config.speed;
  for (let i = 0; i < state.cranes.length; i++) {
    const crane = state.cranes[i];

    if (crane.state === "idle" && i < state.config.activeCranes) {
      // Priority 1: Swap Bays
      const sbNeedingService = state.swapBays.find((sb) => {
        if (!sb.machineId) return false;
        const m = state.machines.find((m) => m.id === sb.machineId);
        // Needs service if it has old battery and no crane is currently targeting it
        return (
          m &&
          m.state === "at_swap" &&
          m.batteryId &&
          !state.cranes.some((c) => c.targetMachineId === m.id)
        );
      });

      if (sbNeedingService) {
        const m = state.machines.find(
          (m) => m.id === sbNeedingService.machineId,
        );
        if (m) {
          crane.targetMachineId = m.id;
          crane.swapBayId = sbNeedingService.id;
          crane.targetPos = sbNeedingService.pos;
          crane.state = "moving_to_remove";
        }
      } else {
        // Priority 2: Maintenance (move from storage to empty charger)
        const batteryOnStorage = state.batteries.find((b) => {
          const p = state.pads.find((p) => p.id === b.padId);
          return (
            p &&
            p.type === "storage" &&
            b.charge < 100 &&
            !b.reservedBy &&
            !state.cranes.some((c) => c.batteryId === b.id)
          );
        });
        const emptyCharger = state.pads.find(
          (p) => p.type === "charger" && !p.batteryId && !p.reserved,
        );

        if (batteryOnStorage && emptyCharger) {
          emptyCharger.reserved = true;
          batteryOnStorage.reservedBy = crane.id; // borrow reservedBy to prevent duplicate picking
          crane.targetPadId = emptyCharger.id;
          crane.batteryId = batteryOnStorage.id;
          crane.targetPos = batteryOnStorage.pos;
          crane.state = "moving_to_fetch_for_charge";
        }
      }
    } else if (crane.state === "moving_to_remove") {
      const res = moveTowards(crane.pos, crane.targetPos, craneSpeed, dt);
      crane.pos = res;
      if (res.reached) {
        crane.state = "removing";
        crane.timer = state.config.swapTime / 2;
      }
    } else if (crane.state === "removing") {
      crane.timer -= simDt;
      if (crane.timer <= 0) {
        const m = state.machines.find((m) => m.id === crane.targetMachineId);
        if (m) {
          const b = state.batteries.find((b) => b.id === m.batteryId);
          if (b) {
            crane.batteryId = b.id;
            m.batteryId = null;
            b.state = "held_by_crane";
            b.machineId = null;

            const emptyPad =
              state.pads.find(
                (p) => p.type === "charger" && !p.batteryId && !p.reserved,
              ) ||
              state.pads.find(
                (p) => p.type === "storage" && !p.batteryId && !p.reserved,
              );
            if (emptyPad) {
              emptyPad.reserved = true;
              crane.targetPadId = emptyPad.id;
              crane.targetPos = emptyPad.pos;
              crane.state = "moving_to_store";
            }
          }
        }
      }
    } else if (crane.state === "moving_to_store") {
      const res = moveTowards(crane.pos, crane.targetPos, craneSpeed, dt);
      crane.pos = res;
      if (res.reached) {
        crane.state = "storing";
        crane.timer = 0.5;
      }
    } else if (crane.state === "storing") {
      crane.timer -= simDt;
      if (crane.timer <= 0) {
        const b = state.batteries.find((b) => b.id === crane.batteryId);
        const p = state.pads.find((p) => p.id === crane.targetPadId);
        if (b && p) {
          b.padId = p.id;
          b.state = "on_pad";
          p.batteryId = b.id;
          p.reserved = false;
          crane.batteryId = null;

          // Fetch charged battery
          const m = state.machines.find((m) => m.id === crane.targetMachineId);
          if (m) {
            const chargedB = state.batteries.find(
              (b) => b.id === m.assignedBatteryId,
            );
            if (chargedB) {
              crane.targetPos = chargedB.pos;
              crane.state = "moving_to_fetch";
            }
          }
        }
      }
    } else if (crane.state === "moving_to_fetch") {
      const res = moveTowards(crane.pos, crane.targetPos, craneSpeed, dt);
      crane.pos = res;
      if (res.reached) {
        crane.state = "fetching";
        crane.timer = 0.5;
      }
    } else if (crane.state === "fetching") {
      crane.timer -= simDt;
      if (crane.timer <= 0) {
        const m = state.machines.find((m) => m.id === crane.targetMachineId);
        if (m) {
          const b = state.batteries.find((b) => b.id === m.assignedBatteryId);
          if (b) {
            const p = state.pads.find((p) => p.id === b.padId);
            crane.batteryId = b.id;
            b.state = "held_by_crane";
            b.padId = null;
            if (p) p.batteryId = null;

            crane.targetPos = state.swapBays.find(
              (sb) => sb.id === crane.swapBayId,
            )?.pos || { x: 0, y: 0 };
            crane.state = "moving_to_install";
          }
        }
      }
    } else if (crane.state === "moving_to_install") {
      const res = moveTowards(crane.pos, crane.targetPos, craneSpeed, dt);
      crane.pos = res;
      if (res.reached) {
        crane.state = "installing";
        crane.timer = state.config.swapTime / 2;
      }
    } else if (crane.state === "installing") {
      crane.timer -= simDt;
      if (crane.timer <= 0) {
        const m = state.machines.find((m) => m.id === crane.targetMachineId);
        const b = state.batteries.find((b) => b.id === crane.batteryId);
        if (m && b) {
          m.batteryId = b.id;
          b.state = "in_machine";
          b.machineId = m.id;
          b.reservedBy = null;
          m.assignedBatteryId = null;
          m.state = "driving_away";

          crane.batteryId = null;
          crane.targetMachineId = null;
          crane.swapBayId = null;
          crane.state = "idle";
        }
      }
    }

    // Maintenance
    else if (crane.state === "moving_to_fetch_for_charge") {
      const res = moveTowards(crane.pos, crane.targetPos, craneSpeed, dt);
      crane.pos = res;
      if (res.reached) {
        crane.state = "fetching_for_charge";
        crane.timer = 0.5;
      }
    } else if (crane.state === "fetching_for_charge") {
      crane.timer -= simDt;
      if (crane.timer <= 0) {
        const b = state.batteries.find((b) => b.id === crane.batteryId);
        if (b) {
          const p = state.pads.find((p) => p.id === b.padId);
          if (p) p.batteryId = null;
          b.state = "held_by_crane";
          b.padId = null;

          const targetPad = state.pads.find((p) => p.id === crane.targetPadId);
          if (targetPad) {
            crane.targetPos = targetPad.pos;
            crane.state = "moving_to_charge";
          }
        }
      }
    } else if (crane.state === "moving_to_charge") {
      const res = moveTowards(crane.pos, crane.targetPos, craneSpeed, dt);
      crane.pos = res;
      if (res.reached) {
        crane.state = "storing_for_charge";
        crane.timer = 0.5;
      }
    } else if (crane.state === "storing_for_charge") {
      crane.timer -= simDt;
      if (crane.timer <= 0) {
        const b = state.batteries.find((b) => b.id === crane.batteryId);
        const p = state.pads.find((p) => p.id === crane.targetPadId);
        if (b && p) {
          b.padId = p.id;
          b.state = "on_pad";
          b.reservedBy = null;
          p.batteryId = b.id;
          p.reserved = false;

          crane.batteryId = null;
          crane.targetPadId = null;
          crane.state = "idle";
        }
      }
    }
  }
}

export function updateKPIs(state: SimState) {
  const kpi = state.kpis;
  kpi.machinesWaiting = state.machines.filter(
    (m) => m.state === "driving_to_queue" || m.state === "in_queue",
  ).length;
  kpi.chargedBatteriesReady = state.batteries.filter(
    (b) => b.charge >= 99 && b.state === "on_pad",
  ).length;

  let chgCount = 0;
  let stgWaitCount = 0;

  for (const b of state.batteries) {
    if (b.charge < 99 && b.state === "on_pad") {
      const p = state.pads.find((pad) => pad.id === b.padId);
      if (p?.type === "charger") chgCount++;
      else if (p?.type === "storage") stgWaitCount++;
    }
  }
  kpi.batteriesCharging = chgCount;
  kpi.depletedWaiting = stgWaitCount;

  kpi.chargerUtilisation = (chgCount / 8) * 100;

  const activeC = Math.min(state.config.activeCranes, state.cranes.length);
  const busyC = state.cranes.filter(
    (c, i) => i < activeC && c.state !== "idle",
  ).length;
  kpi.craneUtilisation = activeC > 0 ? (busyC / activeC) * 100 : 0;

  kpi.avgTurnaroundTime =
    kpi.machinesServed > 0 ? kpi.totalTurnaroundTime / kpi.machinesServed : 0;
  const queuedMachines = state.machines.filter(
    (m) => m.state === "driving_to_queue" || m.state === "in_queue",
  );
  const totWait = queuedMachines.reduce((sum, m) => sum + m.waitTime, 0);
  kpi.avgWaitingTime =
    queuedMachines.length > 0 ? totWait / queuedMachines.length : 0;

  // Bottlenecks
  const emptyPads = state.pads.filter((p) => !p.batteryId).length;

  if (kpi.machinesWaiting > 3) {
    if (kpi.chargedBatteriesReady === 0)
      kpi.bottleneck = "No charged batteries ready";
    else if (kpi.craneUtilisation > 95) kpi.bottleneck = "Crane congestion";
    else kpi.bottleneck = "Swap bay congestion";
  } else if (kpi.depletedWaiting > 0 && kpi.chargerUtilisation > 95) {
    kpi.bottleneck = "Chargers saturated";
  } else if (emptyPads === 0) {
    kpi.bottleneck = "No empty pads available";
  } else {
    kpi.bottleneck = "None";
  }
}

function drawHatchedPolygon(
  ctx: CanvasRenderingContext2D,
  points: Vector2[],
  spacing: number = 16,
  strokeColor: string = "rgba(255,255,255,0.06)",
  borderWidth: number = 2,
  borderColor: string = "rgba(255,255,255,0.15)",
) {
  if (points.length < 3) return;

  ctx.save();

  // 1. Draw border and fill with dark background
  ctx.beginPath();
  ctx.moveTo(points[0].x, points[0].y);
  for (let i = 1; i < points.length; i++) {
    ctx.lineTo(points[i].x, points[i].y);
  }
  ctx.closePath();
  ctx.fillStyle = "rgba(255, 255, 255, 0.012)";
  ctx.fill();

  // 2. Clip to polygon for hatching
  ctx.clip();

  // 3. Draw diagonal lines
  ctx.strokeStyle = strokeColor;
  ctx.lineWidth = 1.2;

  // Find bounding box to know line drawing range
  let minX = points[0].x,
    maxX = points[0].x;
  let minY = points[0].y,
    maxY = points[0].y;
  for (const p of points) {
    if (p.x < minX) minX = p.x;
    if (p.x > maxX) maxX = p.x;
    if (p.y < minY) minY = p.y;
    if (p.y > maxY) maxY = p.y;
  }

  const offset = spacing;
  for (let k = minX - (maxY - minY); k < maxX + (maxY - minY); k += offset) {
    ctx.beginPath();
    ctx.moveTo(k, minY);
    ctx.lineTo(k + (maxY - minY), maxY);
    ctx.stroke();
  }

  ctx.restore();

  // 4. Draw the border
  ctx.save();
  ctx.beginPath();
  ctx.moveTo(points[0].x, points[0].y);
  for (let i = 1; i < points.length; i++) {
    ctx.lineTo(points[i].x, points[i].y);
  }
  ctx.closePath();
  ctx.strokeStyle = borderColor;
  ctx.lineWidth = borderWidth;
  ctx.stroke();
  ctx.restore();
}

function drawArrow(
  ctx: CanvasRenderingContext2D,
  from: Vector2,
  to: Vector2,
  color: string = "#F9A825",
) {
  ctx.save();
  ctx.strokeStyle = color;
  ctx.fillStyle = color;
  ctx.lineWidth = 1.5;

  const angle = Math.atan2(to.y - from.y, to.x - from.x);

  ctx.beginPath();
  ctx.moveTo(from.x, from.y);
  ctx.lineTo(to.x, to.y);
  ctx.stroke();

  ctx.beginPath();
  ctx.translate(to.x, to.y);
  ctx.rotate(angle);
  ctx.moveTo(0, 0);
  ctx.lineTo(-5, -3);
  ctx.lineTo(-5, 3);
  ctx.closePath();
  ctx.fill();

  ctx.restore();
}

function drawCurvedArrow(
  ctx: CanvasRenderingContext2D,
  p1: Vector2,
  cp: Vector2,
  p2: Vector2,
  color: string = "#F9A825",
) {
  ctx.save();
  ctx.strokeStyle = color;
  ctx.fillStyle = color;
  ctx.lineWidth = 1.5;

  // Draw curve
  ctx.beginPath();
  ctx.moveTo(p1.x, p1.y);
  ctx.quadraticCurveTo(cp.x, cp.y, p2.x, p2.y);
  ctx.stroke();

  // Calculate derivative at end (t = 1) -> direction is p2 - cp
  const angle = Math.atan2(p2.y - cp.y, p2.x - cp.x);

  ctx.beginPath();
  ctx.translate(p2.x, p2.y);
  ctx.rotate(angle);
  ctx.moveTo(0, 0);
  ctx.lineTo(-5, -3);
  ctx.lineTo(-5, 3);
  ctx.closePath();
  ctx.fill();

  ctx.restore();
}

export function drawSimulation(ctx: CanvasRenderingContext2D, state: SimState) {
  ctx.clearRect(0, 0, 1300, 700);

  // Background
  ctx.fillStyle = COLORS.bg;
  ctx.fillRect(0, 0, 1300, 700);

  // 1. DRAW THREE LARGE HATCHED ISLANDS ("NO-GO" ZONES / SAFETY AREAS)
  // Left Top Island (Above Roadway 1, left of new upward lane)
  drawHatchedPolygon(ctx, [
    { x: 250, y: 40 },
    { x: 250, y: 150 },
    { x: 270, y: 170 },
    { x: 430, y: 170 },
    { x: 430, y: 40 },
  ]);

  // Right Top Island (Above Roadway 1, right of new upward lane)
  drawHatchedPolygon(ctx, [
    { x: 470, y: 40 },
    { x: 470, y: 170 },
    { x: 1040, y: 170 },
    { x: 1040, y: 40 },
  ]);

  // Middle Island (Between Roadway 1 & 2)
  drawHatchedPolygon(ctx, [
    { x: 250, y: 250 },
    { x: 270, y: 230 },
    { x: 1040, y: 230 },
    { x: 1040, y: 470 },
    { x: 270, y: 470 },
    { x: 250, y: 450 },
  ]);

  // Bottom Island (Below Roadway 2) - Shifted up to y = 640 to make space for bottom road
  drawHatchedPolygon(ctx, [
    { x: 250, y: 550 },
    { x: 270, y: 530 },
    { x: 1040, y: 530 },
    { x: 1040, y: 640 },
    { x: 250, y: 640 },
  ]);

  // Bottom-Left Island (Below Parking Bay) - Split into two sections to leave a 30px entrance centered at x = 70
  // Left Side
  drawHatchedPolygon(ctx, [
    { x: 20, y: 610 },
    { x: 55, y: 610 },
    { x: 55, y: 640 },
    { x: 20, y: 640 },
  ]);
  // Right Side
  drawHatchedPolygon(ctx, [
    { x: 85, y: 610 },
    { x: 120, y: 610 },
    { x: 120, y: 640 },
    { x: 85, y: 640 },
  ]);

  // 2. PARKING BAY
  ctx.fillStyle = "rgba(255,255,255,0.01)";
  ctx.fillRect(20, 20, 100, 580);
  ctx.strokeStyle = "#3F444A";
  ctx.lineWidth = 1.5;
  ctx.strokeRect(20, 20, 100, 580);
  ctx.fillStyle = "#F9A825";
  ctx.font = 'bold 10px "Helvetica Neue", sans-serif';
  ctx.fillText("PARKING BAY", 25, 35);

  // Draw parking spots
  for (let i = 0; i < 14; i++) {
    ctx.strokeStyle = "rgba(255,255,255,0.08)";
    ctx.strokeRect(30, 55 + i * 40 - 15, 80, 30);
  }

  // 3. DRAW TRAVELING WAYS (ROADS, LANE DIVIDERS, CENTERLINES)
  ctx.strokeStyle = "rgba(255,255,255,0.12)";
  ctx.lineWidth = 1;

  // Outer solid boundaries
  ctx.beginPath();
  ctx.moveTo(120, 20);
  ctx.lineTo(120, 650);
  ctx.moveTo(210, 20);
  ctx.lineTo(210, 650);
  ctx.stroke();

  // Lane dividers for the central median (x = 150 to x = 180)
  ctx.beginPath();
  ctx.moveTo(150, 20);
  ctx.lineTo(150, 610);
  ctx.moveTo(180, 20);
  ctx.lineTo(180, 610);
  ctx.stroke();

  // Draw vertical hatched divider
  ctx.save();
  ctx.beginPath();
  ctx.rect(150, 20, 30, 590);
  ctx.clip();
  ctx.fillStyle = "rgba(249, 168, 37, 0.15)";
  for (let i = 0; i < 700; i += 15) {
    ctx.beginPath();
    ctx.moveTo(140, 10 + i);
    ctx.lineTo(190, 60 + i);
    ctx.lineTo(190, 70 + i);
    ctx.lineTo(140, 20 + i);
    ctx.fill();
  }
  ctx.restore();

  // Bottom connecting loop lanes
  ctx.beginPath();
  ctx.moveTo(120, 650);
  ctx.lineTo(210, 650);
  ctx.stroke();

  // SB2 Entry Lane boundary (x = 210 to x = 250)
  ctx.beginPath();
  ctx.moveTo(250, 120);
  ctx.lineTo(250, 530);
  ctx.stroke();

  // Dashed Centerlines
  ctx.save();
  ctx.strokeStyle = "rgba(255,255,255,0.08)";
  ctx.setLineDash([4, 6]);

  // Top Road centerline (y = 20)
  ctx.beginPath();
  ctx.moveTo(70, 20);
  ctx.lineTo(1040, 20);
  ctx.stroke();

  // New Upward Lane to Top Road (x = 450)
  ctx.beginPath();
  ctx.moveTo(450, 200);
  ctx.lineTo(450, 20);
  ctx.stroke();

  // Bottom Road centerline (y = 660)
  ctx.beginPath();
  ctx.moveTo(70, 660);
  ctx.lineTo(1040, 660);
  ctx.stroke();

  // Downward Lane (x = 135)
  ctx.beginPath();
  ctx.moveTo(135, 20);
  ctx.lineTo(135, 650);
  ctx.stroke();

  // Upward Lane (x = 195)
  ctx.beginPath();
  ctx.moveTo(195, 20);
  ctx.lineTo(195, 650);
  ctx.stroke();

  // SB2 Entry Lane (x = 230)
  ctx.beginPath();
  ctx.moveTo(230, 120);
  ctx.lineTo(230, 500);
  ctx.stroke();

  // Roadway 1 centerline (y = 200)
  ctx.beginPath();
  ctx.moveTo(250, 200);
  ctx.lineTo(1040, 200);
  ctx.stroke();

  // Roadway 2 centerline (y = 500)
  ctx.beginPath();
  ctx.moveTo(250, 500);
  ctx.lineTo(1040, 500);
  ctx.stroke();

  ctx.restore();

  // 4. DRAW DIRECTIONAL MARKINGS (FLOW ARROWS)
  // Top road arrows (pointing right)
  drawArrow(ctx, { x: 380, y: 20 }, { x: 410, y: 20 });
  drawArrow(ctx, { x: 630, y: 20 }, { x: 660, y: 20 });
  drawArrow(ctx, { x: 880, y: 20 }, { x: 910, y: 20 });

  // Bottom road arrows (pointing left)
  drawArrow(ctx, { x: 880, y: 660 }, { x: 850, y: 660 });
  drawArrow(ctx, { x: 630, y: 660 }, { x: 600, y: 660 });
  drawArrow(ctx, { x: 380, y: 660 }, { x: 350, y: 660 });

  // New Upward Lane arrows
  drawArrow(ctx, { x: 450, y: 150 }, { x: 450, y: 120 });
  drawArrow(ctx, { x: 450, y: 70 }, { x: 450, y: 40 });

  // Downward lane arrows
  drawArrow(ctx, { x: 135, y: 80 }, { x: 135, y: 110 });
  drawArrow(ctx, { x: 135, y: 280 }, { x: 135, y: 310 });
  drawArrow(ctx, { x: 135, y: 480 }, { x: 135, y: 510 });

  // Bottom connecting loop arrows
  drawCurvedArrow(
    ctx,
    { x: 135, y: 640 },
    { x: 135, y: 675 },
    { x: 165, y: 675 },
  );
  drawCurvedArrow(
    ctx,
    { x: 165, y: 675 },
    { x: 195, y: 675 },
    { x: 195, y: 640 },
  );

  // Upward lane arrows
  drawArrow(ctx, { x: 195, y: 560 }, { x: 195, y: 530 });
  drawArrow(ctx, { x: 195, y: 360 }, { x: 195, y: 330 });
  drawArrow(ctx, { x: 195, y: 160 }, { x: 195, y: 130 });

  // Turn off into Swap Station 1 (SB1)
  drawCurvedArrow(
    ctx,
    { x: 195, y: 220 },
    { x: 195, y: 200 },
    { x: 225, y: 200 },
  );
  drawArrow(ctx, { x: 225, y: 200 }, { x: 255, y: 200 });

  // SB2 Entry Lane downward arrows
  drawArrow(ctx, { x: 230, y: 220 }, { x: 230, y: 250 });
  drawArrow(ctx, { x: 230, y: 380 }, { x: 230, y: 410 });

  // Turn into Swap Station 2 (SB2)
  drawCurvedArrow(
    ctx,
    { x: 230, y: 480 },
    { x: 230, y: 500 },
    { x: 255, y: 500 },
  );
  drawArrow(ctx, { x: 255, y: 500 }, { x: 285, y: 500 });

  // Roadway 1 Exit arrows (Horizontal towards working areas)
  drawArrow(ctx, { x: 490, y: 200 }, { x: 520, y: 200 });
  drawArrow(ctx, { x: 710, y: 200 }, { x: 740, y: 200 });
  drawArrow(ctx, { x: 910, y: 200 }, { x: 940, y: 200 });

  // Roadway 2 Exit arrows (Horizontal towards working areas)
  drawArrow(ctx, { x: 490, y: 500 }, { x: 520, y: 500 });
  drawArrow(ctx, { x: 710, y: 500 }, { x: 740, y: 500 });
  drawArrow(ctx, { x: 910, y: 500 }, { x: 940, y: 500 });

  // 5. SWAP STATIONS (SB1 & SB2 BAYS)
  for (const sb of state.swapBays) {
    ctx.strokeStyle = "#444";
    ctx.lineWidth = 2;
    ctx.strokeRect(sb.pos.x - 40, sb.pos.y - 30, 80, 60);

    ctx.fillStyle = "rgba(255,255,255,0.015)";
    ctx.fillRect(sb.pos.x - 40, sb.pos.y - 30, 80, 60);

    if (state.config.showLabels) {
      ctx.fillStyle = COLORS.bg;
      ctx.fillRect(sb.pos.x - 38, sb.pos.y - 42, 110, 14);
      ctx.fillStyle = COLORS.swapBay;
      ctx.font = 'bold 10px "Helvetica Neue", sans-serif';
      ctx.fillText(
        `SWAP STATION ${sb.id.replace("SB", "")}`,
        sb.pos.x - 35,
        sb.pos.y - 32,
      );
    }
  }

  // Crane Rails
  ctx.strokeStyle = COLORS.rail;
  ctx.lineWidth = 1.5;
  ctx.beginPath();
  ctx.moveTo(400, 150);
  ctx.lineTo(1040, 150);
  ctx.stroke();
  ctx.beginPath();
  ctx.moveTo(400, 250);
  ctx.lineTo(1040, 250);
  ctx.stroke();

  ctx.beginPath();
  ctx.moveTo(400, 450);
  ctx.lineTo(1040, 450);
  ctx.stroke();
  ctx.beginPath();
  ctx.moveTo(400, 550);
  ctx.lineTo(1040, 550);
  ctx.stroke();

  // Pads
  ctx.fillStyle = "rgba(0,0,0,0.2)";
  ctx.strokeStyle = "#333";
  ctx.lineWidth = 1;
  ctx.fillRect(640, 140, 180, 110);
  ctx.strokeRect(640, 140, 180, 110);
  ctx.fillRect(820, 140, 180, 110);
  ctx.strokeRect(820, 140, 180, 110);
  ctx.fillRect(640, 440, 180, 110);
  ctx.strokeRect(640, 440, 180, 110);
  ctx.fillRect(820, 440, 180, 110);
  ctx.strokeRect(820, 440, 180, 110);

  // Draw Working Areas
  const AREA_COLORS = [
    "#8BC34A", // Area 1: 0.8x
    "#FFC107", // Area 2: 1.0x
    "#FF9800", // Area 3: 1.5x
    "#F44336", // Area 4: 2.0x
  ];

  for (let areaId = 1; areaId <= 4; areaId++) {
    const yOffset = (areaId - 1) * 160 + 30;
    ctx.strokeStyle = AREA_COLORS[areaId - 1];
    ctx.lineWidth = 2;
    ctx.strokeRect(1040, yOffset, 230, 130);

    ctx.fillStyle = AREA_COLORS[areaId - 1] + "11"; // light transparent fill
    ctx.fillRect(1040, yOffset, 230, 130);

    ctx.fillStyle = AREA_COLORS[areaId - 1];
    ctx.font = 'bold 12px "Helvetica Neue", sans-serif';
    ctx.fillText(`WORKING AREA ${areaId}`, 1050, yOffset + 20);

    // Draw slot outlines
    const slotsInArea = state.workSlots.filter((s) => s.areaId === areaId);
    ctx.strokeStyle = "rgba(255,255,255,0.1)";
    ctx.lineWidth = 1;
    for (const s of slotsInArea) {
      ctx.strokeRect(s.pos.x - 22, s.pos.y - 18, 44, 36);
    }
  }

  for (const p of state.pads) {
    ctx.lineWidth = 1;
    ctx.strokeStyle =
      p.type === "charger" ? COLORS.padChargerBorder : COLORS.padStorageBorder;
    ctx.fillStyle =
      p.type === "charger" ? COLORS.padCharger : COLORS.padStorage;

    ctx.strokeRect(p.pos.x - 20, p.pos.y - 20, 40, 40);
    ctx.fillRect(p.pos.x - 20, p.pos.y - 20, 40, 40);

    if (p.type === "charger") {
      // Draw charger post
      ctx.fillStyle = "#666";
      ctx.fillRect(p.pos.x + 10, p.pos.y - 15, 4, 15);

      // Connection line
      const b = state.batteries.find((b) => b.id === p.batteryId);
      if (b && b.charge < 100) {
        ctx.beginPath();
        ctx.moveTo(p.pos.x + 5, p.pos.y - 7);
        ctx.lineTo(p.pos.x + 10, p.pos.y - 7);
        ctx.strokeStyle = "#999";
        ctx.lineWidth = 1;
        ctx.stroke();
      }
    }

    if (state.config.showLabels) {
      ctx.fillStyle = "#94a3b8";
      ctx.font = "9px monospace";
      ctx.fillText(p.id, p.pos.x - 18, p.pos.y - 22);
    }
  }

  // Machines
  for (const m of state.machines) {
    ctx.save();
    ctx.translate(m.pos.x, m.pos.y);
    ctx.rotate(m.rotation);

    if (m.type === "DT") {
      // Dump Truck Graphics
      ctx.fillStyle = COLORS.DT;
      ctx.strokeStyle = "#888";
      ctx.lineWidth = 1;

      // cab chassis
      ctx.fillRect(-15, -6, 12, 12);
      ctx.strokeRect(-15, -6, 12, 12);
      // rear chassis
      ctx.fillRect(-3, -4, 20, 8);

      // dump bed
      ctx.fillStyle = "#263238";
      ctx.fillRect(-2, -14, 22, 28);
      ctx.strokeRect(-2, -14, 22, 28);

      // cab top
      ctx.fillStyle = "#607D8B";
      ctx.fillRect(-12, -4, 6, 8);

      // wheels
      ctx.fillStyle = "#111";
      ctx.fillRect(-12, -16, 8, 4); // front left
      ctx.fillRect(-12, 12, 8, 4); // front right
      ctx.fillRect(8, -18, 12, 6); // rear left
      ctx.fillRect(8, 12, 12, 6); // rear right
    } else {
      // Loader (FL) Graphics
      // bucket
      ctx.fillStyle = "#455A64";
      ctx.strokeStyle = "#888";
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(-22, -14);
      ctx.lineTo(-14, -14);
      ctx.lineTo(-14, 14);
      ctx.lineTo(-22, 14);
      ctx.closePath();
      ctx.fill();
      ctx.stroke();

      // front arm/chassis
      ctx.fillStyle = COLORS.FL;
      ctx.fillRect(-14, -6, 12, 12);
      ctx.strokeRect(-14, -6, 12, 12);

      // rear chassis
      ctx.fillRect(0, -10, 18, 20);
      ctx.strokeRect(0, -10, 18, 20);

      // cab
      ctx.fillStyle = "#212121";
      ctx.fillRect(2, -6, 8, 12);

      // wheels
      ctx.fillStyle = "#111";
      ctx.fillRect(-10, -12, 8, 4); // front left
      ctx.fillRect(-10, 8, 8, 4); // front right
      ctx.fillRect(4, -14, 10, 4); // rear left
      ctx.fillRect(4, 10, 10, 4); // rear right
    }

    // Permanent label inside the vehicle graphic
    const num = parseInt(m.id.split("-")[1]) + 1;
    ctx.save();
    ctx.translate(0, 0); // center of body, not obscured by battery at rear
    ctx.rotate(-m.rotation);
    ctx.fillStyle = "#FFF";
    ctx.font = 'bold 16px "Helvetica Neue", sans-serif';
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(num.toString(), 0, 0);
    ctx.restore();

    ctx.restore();
  }

  // Batteries
  for (const b of state.batteries) {
    ctx.save();

    let bw = 20,
      bh = 24;
    if (b.type === "VPX") {
      bw = 24;
      bh = 28;
    } else {
      bw = 16;
      bh = 20;
    }

    let bRot = 0;
    if (b.state === "in_machine") {
      const m = state.machines.find((m) => m.id === b.machineId);
      if (m) {
        ctx.translate(m.pos.x, m.pos.y);
        ctx.rotate(m.rotation);
        bRot = m.rotation;
        ctx.translate(16, 0);
      } else {
        ctx.translate(b.pos.x, b.pos.y);
      }
    } else {
      ctx.translate(b.pos.x, b.pos.y);
    }

    let color = COLORS.batteryEmpty;
    if (b.charge > 20) color = COLORS.batteryLow;
    if (b.charge > 80) color = COLORS.batteryMid;
    if (b.charge >= 99) color = COLORS.batteryFull;

    ctx.fillStyle = color;
    ctx.fillRect(-bw / 2, -bh / 2, bw, bh);

    if (b.charge >= 99) {
      ctx.shadowColor = "rgba(76,175,80,0.4)";
      ctx.shadowBlur = 10;
      ctx.fillRect(-bw / 2, -bh / 2, bw, bh);
      ctx.shadowBlur = 0;
    }

    ctx.strokeStyle = "rgba(0,0,0,0.3)";
    ctx.lineWidth = 1;
    ctx.strokeRect(-bw / 2, -bh / 2, bw, bh);

    // SOC bar inside battery if not full
    if (b.charge < 99) {
      ctx.fillStyle = "#222";
      ctx.fillRect(-bw / 2 + 2, -4, bw - 4, 4);
      ctx.fillStyle = COLORS.batteryEmpty;
      ctx.fillRect(-bw / 2 + 2, -4, (bw - 4) * (b.charge / 100), 4);
    }

    if (state.config.showLabels) {
      ctx.save();
      ctx.rotate(-bRot);
      ctx.fillStyle = "#fff";
      ctx.font = "bold 8px monospace";
      ctx.textAlign = "center";
      ctx.fillText(b.type, 0, -bh / 2 - 2);
      ctx.restore();
    }

    ctx.restore();
  }

  // Cranes
  for (let i = 0; i < state.cranes.length; i++) {
    const c = state.cranes[i];
    if (i >= state.config.activeCranes && c.state === "idle") continue; // Hide inactive cranes

    ctx.save();
    ctx.translate(c.pos.x, c.pos.y);

    // Draw bridge line
    ctx.strokeStyle = "#444";
    ctx.lineWidth = 8;
    ctx.beginPath();
    ctx.moveTo(0, -60);
    ctx.lineTo(0, 60);
    ctx.stroke();

    ctx.fillStyle = COLORS.crane;
    ctx.strokeStyle = "#000";
    ctx.lineWidth = 2;
    ctx.fillRect(-20, -15, 40, 30);
    ctx.strokeRect(-20, -15, 40, 30);

    ctx.shadowColor = "rgba(0,0,0,0.5)";
    ctx.shadowBlur = 10;
    ctx.shadowOffsetY = 4;
    ctx.fillRect(-20, -15, 40, 30);
    ctx.shadowBlur = 0;
    ctx.shadowOffsetY = 0;

    if (state.config.showLabels) {
      ctx.fillStyle = "#000";
      ctx.font = 'bold 10px "Helvetica Neue", sans-serif';
      ctx.textAlign = "center";
      ctx.fillText(c.id, 0, 4);
    }
    ctx.restore();
  }
}
