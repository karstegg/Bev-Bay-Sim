import { SimState } from "./types";
import { moveTowards } from "./movement";

export function updateCranes(state: SimState, dt: number, simDt: number) {
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
