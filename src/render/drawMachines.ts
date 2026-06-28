import { SimState } from "../sim/types";
import { COLORS } from "./colors";

export function drawMachines(ctx: CanvasRenderingContext2D, state: SimState) {
  for (const m of state.machines) {
    ctx.save();
    ctx.translate(m.pos.x, m.pos.y);
    ctx.rotate(m.rotation);

    if (m.type === "DT") {
      // Dump Truck Graphics
      ctx.fillStyle = COLORS.DT;
      ctx.strokeStyle = "#888";
      ctx.lineWidth = 1;

      // cab chassis
      ctx.fillRect(-15, -6, 12, 12);
      ctx.strokeRect(-15, -6, 12, 12);
      // rear chassis
      ctx.fillRect(-3, -4, 20, 8);

      // dump bed
      ctx.fillStyle = "#263238";
      ctx.fillRect(-2, -14, 22, 28);
      ctx.strokeRect(-2, -14, 22, 28);

      // cab top
      ctx.fillStyle = "#607D8B";
      ctx.fillRect(-12, -4, 6, 8);

      // wheels
      ctx.fillStyle = "#111";
      ctx.fillRect(-12, -16, 8, 4); // front left
      ctx.fillRect(-12, 12, 8, 4); // front right
      ctx.fillRect(8, -18, 12, 6); // rear left
      ctx.fillRect(8, 12, 12, 6); // rear right
    } else {
      // Loader (FL) Graphics
      // bucket
      ctx.fillStyle = "#455A64";
      ctx.strokeStyle = "#888";
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(-22, -14);
      ctx.lineTo(-14, -14);
      ctx.lineTo(-14, 14);
      ctx.lineTo(-22, 14);
      ctx.closePath();
      ctx.fill();
      ctx.stroke();

      // front arm/chassis
      ctx.fillStyle = COLORS.FL;
      ctx.fillRect(-14, -6, 12, 12);
      ctx.strokeRect(-14, -6, 12, 12);

      // rear chassis
      ctx.fillRect(0, -10, 18, 20);
      ctx.strokeRect(0, -10, 18, 20);

      // cab
      ctx.fillStyle = "#212121";
      ctx.fillRect(2, -6, 8, 12);

      // wheels
      ctx.fillStyle = "#111";
      ctx.fillRect(-10, -12, 8, 4); // front left
      ctx.fillRect(-10, 8, 8, 4); // front right
      ctx.fillRect(4, -14, 10, 4); // rear left
      ctx.fillRect(4, 10, 10, 4); // rear right
    }

    // Permanent label inside the vehicle graphic
    const num = parseInt(m.id.split("-")[1]) + 1;
    ctx.save();
    ctx.translate(0, 0); // center of body, not obscured by battery at rear
    ctx.rotate(-m.rotation);
    ctx.fillStyle = "#FFF";
    ctx.font = 'bold 16px "Helvetica Neue", sans-serif';
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(num.toString(), 0, 0);
    ctx.restore();

    // Brake lights
    if (m.isBraking || (m.currentSpeed === 0 && m.blockedBy)) {
      ctx.fillStyle = "#FF0000";
      ctx.shadowColor = "#FF0000";
      ctx.shadowBlur = 5;
      if (m.type === "DT") {
        ctx.fillRect(-16, -16, 2, 4);
        ctx.fillRect(-16, 12, 2, 4);
      } else {
        ctx.fillRect(4, -14, 2, 4); 
        ctx.fillRect(4, 10, 2, 4);
      }
      ctx.shadowBlur = 0;
    }

    ctx.restore();
  }
}
