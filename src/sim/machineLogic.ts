import { SimState } from "./types";
import { moveMachineAlongPath } from "./movement";
import { getPathToPark, assignWorkArea } from "./layout";

export function updateMachines(state: SimState, dt: number, simDt: number) {
  const speedDT = state.config.speedDT;
  const speedFL = state.config.speedFL;
  const dischargeBaseDT = state.config.dischargeTimeDT;
  const dischargeBaseFL = state.config.dischargeTimeFL;

  const queuedMachines = state.machines
    .filter((m) => m.state === "driving_to_queue" || m.state === "in_queue")
    .sort((a, b) => b.waitTime - a.waitTime);

  queuedMachines.forEach((m, idx) => {
    m.queueIndex = idx;
  });

  for (const m of state.machines) {
    m.maxSpeed = m.type === "DT" ? speedDT : speedFL;

    const battery = state.batteries.find((b) => b.id === m.batteryId);

    // If battery SOC <= 20%, force it to go to swap or park
    if (battery && battery.charge <= 20) {
      const goingToSwapOrParkStates = [
        "driving_from_work",
        "driving_to_queue",
        "in_queue",
        "driving_to_swap",
        "at_swap",
        "driving_away",
      ];
      if (!state.config.shiftActive) {
        goingToSwapOrParkStates.push("driving_to_park", "parked");
      }

      if (!goingToSwapOrParkStates.includes(m.state)) {
        if (m.workSlotId) {
          const slot = state.workSlots.find((s) => s.id === m.workSlotId);
          if (slot) slot.machineId = null;
          m.workSlotId = null;
        }

        if (state.config.shiftActive) {
          m.state = "driving_from_work";

          if (m.pos.x <= 120) {
            // Left side / parking bay: drive straight down, then right along bottom road to queue
            m.path = [
              { x: 20, y: m.pos.y },
              { x: 20, y: 660 }, // Bottom of parking bay / bottom road
              { x: 200, y: 660 }, // Bottom lane to queue entry
              { x: 200, y: 580 }, // Enter queue upwards
            ];
          } else {
            // Anywhere else: go to distribution lane, down to bottom road, then to queue entry
            const slot = state.workSlots.find((s) => s.id === m.workSlotId);
            const areaAccessY = slot ? (slot.areaId - 1) * 160 + 95 : m.pos.y;
            m.path = [
              { x: m.pos.x, y: areaAccessY }, // Back out into access row
              { x: 1280, y: areaAccessY }, // Exit work slot to exit lane (1280)
              { x: 1280, y: 660 }, // Down the exit lane
              { x: 200, y: 660 }, // Across the bottom road
              { x: 200, y: 580 }, // Up into queue
            ];
          }
          m.targetPos = m.path[0];
        } else {
          m.state = "driving_to_park";
          m.path = getPathToPark(m);
          m.targetPos = m.path[0] || m.parkingPos;
        }
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
        }
      }
    } else if (m.state === "driving_from_work") {
      if (!state.config.shiftActive) {
        m.state = "driving_to_park";
        m.path = getPathToPark(m);
        m.targetPos = m.path[0] || m.parkingPos;
      } else {
        m.lastPos = { ...m.pos };
        const reached = moveMachineAlongPath(m, state, simDt);
        if (reached) {
          m.state = "driving_to_queue";
          m.pos = { x: 200, y: 580 }; // Enter from bottom lane
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
        const reached = moveMachineAlongPath(m, state, simDt);
        if (reached) {
          m.state = "working";
        }
      }
    } else if (m.state === "driving_to_park") {
      m.lastPos = { ...m.pos };
      if (!m.path || m.path.length === 0) {
        m.path = getPathToPark(m);
        m.targetPos = m.path[0] || m.parkingPos;
      }
      const reached = moveMachineAlongPath(m, state, simDt);
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
        let areaAccessY = (m.workAreaId - 1) * 160 + 95;
        if (emptySlot) {
          emptySlot.machineId = m.id;
          m.workSlotId = emptySlot.id;
          areaAccessY = (emptySlot.areaId - 1) * 160 + 95;
        }
        m.path = [
          { x: 20, y: m.pos.y }, // Drive to the access lane
          { x: 20, y: 20 }, // Drive up the parking bay access lane
          { x: 1020, y: 20 }, // Drive right along the top road
          { x: 1020, y: areaAccessY }, // Move down to access row
          { x: target.x, y: areaAccessY }, // Drive along access row
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
        const targetY = 250 + (m.queueIndex || 0) * 50;

        m.lastPos = { ...m.pos };

        // Ensure they just strictly follow queue up
        m.path = [{ x: 200, y: targetY }];
        const reached = moveMachineAlongPath(m, state, simDt);

        if (reached) {
          m.state = "in_queue";
        }

        // Allocate swap bay if at front
        if (m.state === "in_queue" && queuedMachines[0].id === m.id) {
          const reqBatType = m.type === "DT" ? "VPX" : "VPY";
          let emptySwapBay: typeof state.swapBays[0] | undefined;
          let chargedBattery: typeof state.batteries[0] | undefined;

          for (const sb of state.swapBays) {
            if (sb.reservedBy || sb.machineId) continue;
            const isTop = sb.id === "SB1";
            const b = state.batteries.find((b) => {
              if (
                b.type !== reqBatType ||
                b.charge < 99 ||
                b.reservedBy ||
                !b.padId
              )
                return false;
              const pad = state.pads.find((p) => p.id === b.padId);
              if (!pad) return false;
              return isTop ? pad.pos.y < 350 : pad.pos.y > 350;
            });
            if (b) {
              emptySwapBay = sb;
              chargedBattery = b;
              break;
            }
          }

          if (emptySwapBay && chargedBattery) {
            emptySwapBay.reservedBy = m.id;
            chargedBattery.reservedBy = m.id;
            m.swapBayId = emptySwapBay.id;
            m.assignedBatteryId = chargedBattery.id;
            m.state = "driving_to_swap";
            if (emptySwapBay.id === "SB2") {
              m.path = [
                { x: 200, y: 120 }, // Continue up queue lane to the turnoff
                { x: 230, y: 120 }, // Turn right into downward entry lane
                { x: 230, y: 500 }, // Drive down to Swap Station 2 y-level
                emptySwapBay.pos, // Enter Swap Station 2
              ];
            } else {
              m.path = [
                { x: 200, y: 200 }, // Drive to Swap Station 1 y-level
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
        const reached = moveMachineAlongPath(m, state, simDt);
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
      const reached = moveMachineAlongPath(m, state, simDt);
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
          let areaAccessY = (m.workAreaId - 1) * 160 + 95;
          if (emptySlot) {
            emptySlot.machineId = m.id;
            m.workSlotId = emptySlot.id;
            areaAccessY = (emptySlot.areaId - 1) * 160 + 95;
          }
          m.state = "driving_to_work";
          m.path = [
            { x: 450, y: m.pos.y }, // Drive right to the upward lane
            { x: 450, y: 20 }, // Drive up to the top road
            { x: 1020, y: 20 }, // Drive right along top road
            { x: 1020, y: areaAccessY }, // Move down to area access row
            { x: target.x, y: areaAccessY }, // Drive along access row
            target, // Enter work slot
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
}
