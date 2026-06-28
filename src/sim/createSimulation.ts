import {
  SimState,
  Pad,
  WorkSlot,
  Battery,
  Machine,
  SwapBay,
  Crane,
  SimConfig,
  ConflictZone,
  StopSign,
  TrafficLight,
} from "./types";
import { assignWorkArea } from "./layout";

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
          y: (areaId - 1) * 160 + 55 + Math.floor(s / 3) * 80,
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
      charge: 100,
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
      heading: 0,
      targetPos: null,
      waitTime: 0,
      swapBayId: null,
      assignedBatteryId: null,
      workAreaId: area.id,
      workAreaMultiplier: area.mult,
      parkingPos: { ...parkingPos },
      workSlotId: null,
      width: 24,
      length: 36,
      currentSpeed: 0,
      maxSpeed: config.speedDT,
      acceleration: 40,
      deceleration: 80,
      turnRate: 1.5,
      isBraking: false,
      blockedBy: null,
      stopTimer: 0,
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
      heading: 0,
      targetPos: null,
      waitTime: 0,
      swapBayId: null,
      assignedBatteryId: null,
      workAreaId: area.id,
      workAreaMultiplier: area.mult,
      parkingPos: { ...parkingPos },
      workSlotId: null,
      width: 20,
      length: 30,
      currentSpeed: 0,
      maxSpeed: config.speedFL,
      acceleration: 60,
      deceleration: 120,
      turnRate: 2.5,
      isBraking: false,
      blockedBy: null,
      stopTimer: 0,
    });
  }

  const swapBays: SwapBay[] = [
    { id: "SB1", pos: { x: 400, y: 200 }, machineId: null, reservedBy: null },
    { id: "SB2", pos: { x: 400, y: 500 }, machineId: null, reservedBy: null },
  ];

  const conflictZones: ConflictZone[] = [
    { id: "CZ_SB1_ENTRY", pos: { x: 230, y: 200 }, radius: 30, occupantId: null },
    { id: "CZ_SB2_ENTRY", pos: { x: 250, y: 500 }, radius: 30, occupantId: null },
    { id: "CZ_QUEUE_ENTRY", pos: { x: 200, y: 600 }, radius: 30, occupantId: null },
    { id: "CZ_WORK_EXIT_MERGE", pos: { x: 1280, y: 660 }, radius: 30, occupantId: null },
    { id: "CZ_PARK_MERGE", pos: { x: 20, y: 660 }, radius: 30, occupantId: null },
  ];

  const stopSigns: StopSign[] = [
    { id: "STOP_QUEUE", pos: { x: 200, y: 620 }, dir: { x: 0, y: -1 } },
    { id: "STOP_SB1", pos: { x: 200, y: 200 }, dir: { x: 1, y: 0 } },
    { id: "STOP_SB2", pos: { x: 230, y: 480 }, dir: { x: 0, y: 1 } },
    { id: "STOP_PARK", pos: { x: 20, y: 640 }, dir: { x: 0, y: 1 } },
  ];

  const trafficLights: TrafficLight[] = [
    { id: "TL_SB1", pos: { x: 220, y: 180 }, swapBayId: "SB1", state: "green" },
    { id: "TL_SB2", pos: { x: 250, y: 480 }, swapBayId: "SB2", state: "green" },
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
    conflictZones,
    stopSigns,
    trafficLights,
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
