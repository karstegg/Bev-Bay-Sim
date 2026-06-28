import { SimState } from "./types";

export function updateBatteries(state: SimState, simDt: number) {
  const chargeTimeVPX = Math.max(1, state.config.chargeTimeVPX);
  const chargeTimeVPY = Math.max(1, state.config.chargeTimeVPY);

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
}
