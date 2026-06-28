import { Vector2, Machine, SimState } from "./types";

export function moveTowards(
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

function getDistance(a: Vector2, b: Vector2) {
  return Math.hypot(b.x - a.x, b.y - a.y);
}

function normalizeAngle(a: number) {
  while (a > Math.PI) a -= Math.PI * 2;
  while (a < -Math.PI) a += Math.PI * 2;
  return a;
}

export function moveMachineAlongPath(m: Machine, state: SimState, simDt: number): boolean {
  // Global release for conflict zones if we moved away
  for (const cz of state.conflictZones) {
    if (cz.occupantId === m.id) {
       const distToZone = getDistance(m.pos, cz.pos);
       if (distToZone > cz.radius + 20) {
          cz.occupantId = null;
       }
    }
  }

  if (!m.path || m.path.length === 0) {
    m.currentSpeed = Math.max(0, m.currentSpeed - m.deceleration * simDt);
    m.isBraking = m.currentSpeed > 0;
    return true;
  }

  const target = m.path[0];
  const distToTarget = getDistance(m.pos, target);
  
  let turnSlowdown = 1.0;
  if (m.path.length > 1) {
    const nextTarget = m.path[1];
    const angle1 = Math.atan2(target.y - m.pos.y, target.x - m.pos.x);
    const angle2 = Math.atan2(nextTarget.y - target.y, nextTarget.x - target.x);
    const angleDiff = Math.abs(normalizeAngle(angle2 - angle1));
    if (angleDiff > Math.PI / 4 && distToTarget < 60) {
      turnSlowdown = 0.3;
    }
  }
  
  // Early waypoint transition for smooth curves
  if (distToTarget < 25) {
    m.path.shift();
    if (m.path.length === 0) {
      m.pos = { ...target }; // Snap on final arrival
      m.currentSpeed = 0;
      m.isBraking = false;
      return true;
    }
  }

  const currentTarget = m.path[0] || target;
  const targetAngle = Math.atan2(currentTarget.y - m.pos.y, currentTarget.x - m.pos.x);
  
  const angleDiff = normalizeAngle(targetAngle - m.heading);
  const turnStep = m.turnRate * simDt;
  
  if (Math.abs(angleDiff) <= turnStep) {
    m.heading = targetAngle;
  } else {
    m.heading += Math.sign(angleDiff) * turnStep;
  }
  m.heading = normalizeAngle(m.heading);

  // Slow down if we are facing the wrong way (prevents orbital looping)
  if (Math.abs(angleDiff) > Math.PI / 4) {
    turnSlowdown = Math.min(turnSlowdown, 0.4);
  }

  let desiredSpeed = m.maxSpeed * turnSlowdown;
  m.blockedBy = null;
  m.isBraking = false;

  // 1. Follow distance
  const lookaheadDist = 80;
  for (const other of state.machines) {
    if (other.id === m.id) continue;
    if (other.state === "working" || other.state === "parked") continue; // Ignore vehicles parked off-road in slots
    const dist = getDistance(m.pos, other.pos);
    if (dist < lookaheadDist) {
      const angleToOther = Math.atan2(other.pos.y - m.pos.y, other.pos.x - m.pos.x);
      const relativeAngle = Math.abs(normalizeAngle(angleToOther - m.heading));
      if (relativeAngle < Math.PI / 3) {
        const lateralDist = dist * Math.sin(relativeAngle);
        if (lateralDist < m.width / 2 + other.width / 2 + 2) {
          desiredSpeed = Math.min(desiredSpeed, other.currentSpeed * 0.8);
          if (dist < m.length / 2 + other.length / 2 + 10) {
            desiredSpeed = 0;
            m.blockedBy = "Vehicle";
          }
        }
      }
    }
  }

  // 2. Traffic Lights
  for (const tl of state.trafficLights) {
    if (m.swapBayId === tl.swapBayId) {
      const distToLight = getDistance(m.pos, tl.pos);
      if (distToLight < 80) {
        const angleToLight = Math.atan2(tl.pos.y - m.pos.y, tl.pos.x - m.pos.x);
        const relativeAngle = Math.abs(normalizeAngle(angleToLight - m.heading));
        // Check if light is in front of the vehicle (within 90 degrees)
        if (relativeAngle <= Math.PI / 2 + 0.1) {
          if (tl.state === "red") {
            desiredSpeed = 0;
            m.blockedBy = "Traffic Light";
          }
        }
      }
    }
  }

  // 3. Conflict Zones
  for (const cz of state.conflictZones) {
    const distToZone = getDistance(m.pos, cz.pos);
    if (distToZone < cz.radius + 30) {
       const angleToZone = Math.atan2(cz.pos.y - m.pos.y, cz.pos.x - m.pos.x);
       if (Math.abs(normalizeAngle(angleToZone - m.heading)) < Math.PI / 3) {
         if (cz.occupantId && cz.occupantId !== m.id) {
            desiredSpeed = 0;
            m.blockedBy = "Conflict Zone";
         } else if (!cz.occupantId && distToZone < cz.radius + 15) {
            cz.occupantId = m.id;
         }
       }
    }
  }

  // 4. Stop Signs
  let nearStopSign = false;
  for (const sign of state.stopSigns) {
    const distToSign = getDistance(m.pos, sign.pos);
    if (distToSign < 40) {
      const angleToSign = Math.atan2(sign.pos.y - m.pos.y, sign.pos.x - m.pos.x);
      const signHeading = Math.atan2(sign.dir.y, sign.dir.x);
      if (
         Math.abs(normalizeAngle(angleToSign - m.heading)) < Math.PI / 3 &&
         Math.abs(normalizeAngle(signHeading - m.heading)) < Math.PI / 4
      ) {
        nearStopSign = true;
        if (m.stopTimer === 0) {
           desiredSpeed = 0;
           m.blockedBy = "Stop Sign";
           if (m.currentSpeed < 2) {
              m.stopTimer = 1.0; // Wait 1 second
           }
        }
      }
    }
  }

  if (m.stopTimer > 0) {
     m.stopTimer -= simDt;
     desiredSpeed = 0;
     m.blockedBy = "Yielding";
     if (m.stopTimer <= 0) {
        m.stopTimer = -1; // Done stopping, can proceed
     }
  }

  if (!nearStopSign && m.stopTimer < 0) {
     m.stopTimer = 0; // Reset once we've moved away
  }
  
  if (m.currentSpeed < desiredSpeed) {
    m.currentSpeed += m.acceleration * simDt;
    if (m.currentSpeed > desiredSpeed) m.currentSpeed = desiredSpeed;
  } else if (m.currentSpeed > desiredSpeed) {
    m.currentSpeed -= m.deceleration * simDt;
    m.isBraking = true;
    if (m.currentSpeed < desiredSpeed) m.currentSpeed = Math.max(0, desiredSpeed);
  }

  if (m.currentSpeed < 0) m.currentSpeed = 0;

  m.pos.x += Math.cos(m.heading) * m.currentSpeed * simDt;
  m.pos.y += Math.sin(m.heading) * m.currentSpeed * simDt;

  m.rotation = m.heading;

  return false;
}
