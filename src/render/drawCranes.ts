import { SimState } from "../sim/types";
import { COLORS } from "./colors";

export function drawCranes(ctx: CanvasRenderingContext2D, state: SimState) {
  for (let i = 0; i < state.cranes.length; i++) {
    const c = state.cranes[i];
    if (i >= state.config.activeCranes && c.state === "idle") continue; // Hide inactive cranes

    ctx.save();
    ctx.translate(c.pos.x, c.pos.y);

    // Draw bridge line
    ctx.strokeStyle = "#444";
    ctx.lineWidth = 8;
    ctx.beginPath();
    ctx.moveTo(0, -60);
    ctx.lineTo(0, 60);
    ctx.stroke();

    ctx.fillStyle = COLORS.crane;
    ctx.strokeStyle = "#000";
    ctx.lineWidth = 2;
    ctx.fillRect(-20, -15, 40, 30);
    ctx.strokeRect(-20, -15, 40, 30);

    ctx.shadowColor = "rgba(0,0,0,0.5)";
    ctx.shadowBlur = 10;
    ctx.shadowOffsetY = 4;
    ctx.fillRect(-20, -15, 40, 30);
    ctx.shadowBlur = 0;
    ctx.shadowOffsetY = 0;

    if (state.config.showLabels) {
      ctx.fillStyle = "#000";
      ctx.font = 'bold 10px "Helvetica Neue", sans-serif';
      ctx.textAlign = "center";
      ctx.fillText(c.id, 0, 4);
    }
    ctx.restore();
  }
}
