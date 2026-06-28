import { SimState } from "../sim/types";
import { COLORS } from "./colors";

export function drawStations(ctx: CanvasRenderingContext2D, state: SimState) {
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
}
