import { SimState } from "../sim/types";
import { drawRoads } from "./drawRoads";
import { drawStations } from "./drawStations";
import { drawMachines } from "./drawMachines";
import { drawBatteries } from "./drawBatteries";
import { drawCranes } from "./drawCranes";

export function drawSimulation(ctx: CanvasRenderingContext2D, state: SimState) {
  ctx.clearRect(0, 0, 1300, 700);

  drawRoads(ctx);

  // Draw stop signs and traffic lights on top of roads
  for (const sign of state.stopSigns) {
    ctx.save();
    ctx.translate(sign.pos.x, sign.pos.y);
    const angle = Math.atan2(sign.dir.y, sign.dir.x);
    ctx.rotate(angle);
    ctx.fillStyle = "#E53935";
    ctx.strokeStyle = "#FFF";
    ctx.lineWidth = 1;
    // Octagon
    ctx.beginPath();
    for (let i = 0; i < 8; i++) {
      const a = (i * Math.PI) / 4 + Math.PI / 8;
      const x = Math.cos(a) * 8;
      const y = Math.sin(a) * 8;
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.closePath();
    ctx.fill();
    ctx.stroke();
    ctx.restore();
  }

  drawStations(ctx, state);

  for (const tl of state.trafficLights) {
    ctx.save();
    ctx.translate(tl.pos.x, tl.pos.y);
    ctx.fillStyle = "#222";
    ctx.fillRect(-6, -10, 12, 20);
    ctx.fillStyle = tl.state === "red" ? "#F44336" : "#4CAF50";
    ctx.shadowColor = tl.state === "red" ? "rgba(244,67,54,0.8)" : "rgba(76,175,80,0.8)";
    ctx.shadowBlur = 8;
    ctx.beginPath();
    ctx.arc(0, tl.state === "red" ? -4 : 4, 3, 0, Math.PI * 2);
    ctx.fill();
    ctx.shadowBlur = 0;
    if (state.config.showLabels) {
      ctx.fillStyle = "#fff";
      ctx.font = "8px monospace";
      ctx.fillText(tl.id, 8, 4);
    }
    ctx.restore();
  }

  drawMachines(ctx, state);

  // Draw traffic debug
  if (state.config.showTrafficDebug) {
    ctx.save();
    ctx.lineWidth = 1;
    
    // Conflict zones
    for (const cz of state.conflictZones) {
       ctx.strokeStyle = cz.occupantId ? "#F44336" : "#4CAF50";
       ctx.fillStyle = cz.occupantId ? "rgba(244,67,54,0.2)" : "rgba(76,175,80,0.2)";
       ctx.beginPath();
       ctx.arc(cz.pos.x, cz.pos.y, cz.radius, 0, Math.PI * 2);
       ctx.fill();
       ctx.stroke();
       ctx.fillStyle = "#fff";
       ctx.font = "10px monospace";
       ctx.fillText(cz.id, cz.pos.x, cz.pos.y);
       if (cz.occupantId) {
         ctx.fillText(`Claimed: ${cz.occupantId}`, cz.pos.x, cz.pos.y + 12);
       }
    }

    // Machine debug
    for (const m of state.machines) {
       ctx.strokeStyle = m.isBraking ? "#F44336" : "#2196F3";
       ctx.beginPath();
       ctx.moveTo(m.pos.x, m.pos.y);
       ctx.lineTo(m.pos.x + Math.cos(m.heading) * 30, m.pos.y + Math.sin(m.heading) * 30);
       ctx.stroke();

       if (m.blockedBy) {
          ctx.fillStyle = "#F44336";
          ctx.font = "bold 10px monospace";
          ctx.fillText(`Wait: ${m.blockedBy}`, m.pos.x + 15, m.pos.y - 15);
       }
    }

    ctx.restore();
  }

  drawBatteries(ctx, state);
  drawCranes(ctx, state);
}
