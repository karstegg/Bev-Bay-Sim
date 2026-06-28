import { SimState } from "./types";

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
