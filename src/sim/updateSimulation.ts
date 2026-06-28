import { SimState } from "./types";
import { updateMachines } from "./machineLogic";
import { updateBatteries } from "./batteryLogic";
import { updateCranes } from "./craneLogic";

export function updateSimulation(state: SimState, dt: number) {
  const totalSimDt = dt * state.config.speed;
  if (totalSimDt <= 0) return;

  // Sub-step to prevent overshooting at high speeds
  // Max 0.1 sim seconds per step. At 50px/s, max movement is 5px per step.
  const MAX_STEP = 0.1;
  const steps = Math.ceil(totalSimDt / MAX_STEP);
  const stepSimDt = totalSimDt / steps;
  const stepDt = dt / steps;

  for (let i = 0; i < steps; i++) {
    state.time += stepSimDt;

    // 10 seconds of real time (at 1x) = 1 hour of sim time
    const simTimeHours = (state.time / 10) % 24;
    state.kpis.simTimeHours = simTimeHours;

    // Shift is active except for the last deadTimeHours
    state.config.shiftActive = simTimeHours < 24 - state.config.deadTimeHours;

    // Update Traffic Lights
    for (const tl of state.trafficLights) {
      const swapBay = state.swapBays.find((sb) => sb.id === tl.swapBayId);
      if (swapBay && (swapBay.machineId || swapBay.reservedBy)) {
         // Only green if reserved by a machine that is approaching (not yet in the bay)
         const resM = state.machines.find(m => m.id === swapBay.reservedBy);
         if (resM && resM.state === "driving_to_swap") {
            tl.state = "green";
         } else {
            tl.state = "red";
         }
      } else {
         tl.state = "green";
      }
    }

    updateMachines(state, stepDt, stepSimDt);
    updateBatteries(state, stepSimDt);
    updateCranes(state, stepDt, stepSimDt);
  }
}
