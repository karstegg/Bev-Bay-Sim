import { SimState } from "../sim/types";
import { COLORS } from "./colors";

export function drawBatteries(ctx: CanvasRenderingContext2D, state: SimState) {
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
}
