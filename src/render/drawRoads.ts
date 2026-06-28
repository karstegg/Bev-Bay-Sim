import { Vector2 } from "../sim/types";
import { COLORS } from "./colors";

export function drawHatchedPolygon(
  ctx: CanvasRenderingContext2D,
  points: Vector2[],
  spacing: number = 16,
  strokeColor: string = "rgba(255,255,255,0.06)",
  borderWidth: number = 2,
  borderColor: string = "rgba(255,255,255,0.15)",
) {
  if (points.length < 3) return;

  ctx.save();

  // 1. Draw border and fill with dark background
  ctx.beginPath();
  ctx.moveTo(points[0].x, points[0].y);
  for (let i = 1; i < points.length; i++) {
    ctx.lineTo(points[i].x, points[i].y);
  }
  ctx.closePath();
  ctx.fillStyle = "rgba(255, 255, 255, 0.012)";
  ctx.fill();

  // 2. Clip to polygon for hatching
  ctx.clip();

  // 3. Draw diagonal lines
  ctx.strokeStyle = strokeColor;
  ctx.lineWidth = 1.2;

  // Find bounding box to know line drawing range
  let minX = points[0].x,
    maxX = points[0].x;
  let minY = points[0].y,
    maxY = points[0].y;
  for (const p of points) {
    if (p.x < minX) minX = p.x;
    if (p.x > maxX) maxX = p.x;
    if (p.y < minY) minY = p.y;
    if (p.y > maxY) maxY = p.y;
  }

  const offset = spacing;
  for (let k = minX - (maxY - minY); k < maxX + (maxY - minY); k += offset) {
    ctx.beginPath();
    ctx.moveTo(k, minY);
    ctx.lineTo(k + (maxY - minY), maxY);
    ctx.stroke();
  }

  ctx.restore();

  // 4. Draw the border
  ctx.save();
  ctx.beginPath();
  ctx.moveTo(points[0].x, points[0].y);
  for (let i = 1; i < points.length; i++) {
    ctx.lineTo(points[i].x, points[i].y);
  }
  ctx.closePath();
  ctx.strokeStyle = borderColor;
  ctx.lineWidth = borderWidth;
  ctx.stroke();
  ctx.restore();
}

export function drawArrow(
  ctx: CanvasRenderingContext2D,
  from: Vector2,
  to: Vector2,
  color: string = "#F9A825",
) {
  ctx.save();
  ctx.strokeStyle = color;
  ctx.fillStyle = color;
  ctx.lineWidth = 1.5;

  const angle = Math.atan2(to.y - from.y, to.x - from.x);

  ctx.beginPath();
  ctx.moveTo(from.x, from.y);
  ctx.lineTo(to.x, to.y);
  ctx.stroke();

  ctx.beginPath();
  ctx.translate(to.x, to.y);
  ctx.rotate(angle);
  ctx.moveTo(0, 0);
  ctx.lineTo(-5, -3);
  ctx.lineTo(-5, 3);
  ctx.closePath();
  ctx.fill();

  ctx.restore();
}

export function drawCurvedArrow(
  ctx: CanvasRenderingContext2D,
  p1: Vector2,
  cp: Vector2,
  p2: Vector2,
  color: string = "#F9A825",
) {
  ctx.save();
  ctx.strokeStyle = color;
  ctx.fillStyle = color;
  ctx.lineWidth = 1.5;

  // Draw curve
  ctx.beginPath();
  ctx.moveTo(p1.x, p1.y);
  ctx.quadraticCurveTo(cp.x, cp.y, p2.x, p2.y);
  ctx.stroke();

  // Calculate derivative at end (t = 1) -> direction is p2 - cp
  const angle = Math.atan2(p2.y - cp.y, p2.x - cp.x);

  ctx.beginPath();
  ctx.translate(p2.x, p2.y);
  ctx.rotate(angle);
  ctx.moveTo(0, 0);
  ctx.lineTo(-5, -3);
  ctx.lineTo(-5, 3);
  ctx.closePath();
  ctx.fill();

  ctx.restore();
}

export function drawRoads(ctx: CanvasRenderingContext2D) {
  // Background
  ctx.fillStyle = COLORS.bg;
  ctx.fillRect(0, 0, 1300, 700);

  // 1. DRAW THREE LARGE HATCHED ISLANDS ("NO-GO" ZONES / SAFETY AREAS)
  // Left Top Island (Above Roadway 1, left of new upward lane)
  drawHatchedPolygon(ctx, [
    { x: 250, y: 40 },
    { x: 250, y: 150 },
    { x: 270, y: 170 },
    { x: 430, y: 170 },
    { x: 430, y: 40 },
  ]);

  // Right Top Island (Above Roadway 1, right of new upward lane)
  drawHatchedPolygon(ctx, [
    { x: 470, y: 40 },
    { x: 470, y: 170 },
    { x: 1040, y: 170 },
    { x: 1040, y: 40 },
  ]);

  // Middle Island (Between Roadway 1 & 2)
  drawHatchedPolygon(ctx, [
    { x: 250, y: 250 },
    { x: 270, y: 230 },
    { x: 1040, y: 230 },
    { x: 1040, y: 470 },
    { x: 270, y: 470 },
    { x: 250, y: 450 },
  ]);

  // Bottom Island (Below Roadway 2) - Shifted up to y = 640 to make space for bottom road
  drawHatchedPolygon(ctx, [
    { x: 250, y: 550 },
    { x: 270, y: 530 },
    { x: 1040, y: 530 },
    { x: 1040, y: 640 },
    { x: 250, y: 640 },
  ]);

  // Bottom-Left Island (Below Parking Bay)
  drawHatchedPolygon(ctx, [
    { x: 35, y: 610 },
    { x: 120, y: 610 },
    { x: 120, y: 640 },
    { x: 35, y: 640 },
  ]);

  // 2. PARKING BAY
  ctx.fillStyle = "rgba(255,255,255,0.01)";
  ctx.fillRect(20, 20, 100, 580);
  ctx.strokeStyle = "#3F444A";
  ctx.lineWidth = 1.5;
  ctx.strokeRect(20, 20, 100, 580);
  ctx.fillStyle = "#F9A825";
  ctx.font = 'bold 10px "Helvetica Neue", sans-serif';
  ctx.fillText("PARKING BAY", 25, 35);

  // Draw parking spots
  for (let i = 0; i < 14; i++) {
    ctx.strokeStyle = "rgba(255,255,255,0.08)";
    ctx.strokeRect(30, 55 + i * 40 - 15, 80, 30);
  }

  // 3. DRAW TRAVELING WAYS (ROADS, LANE DIVIDERS, CENTERLINES)
  ctx.strokeStyle = "rgba(255,255,255,0.12)";
  ctx.lineWidth = 1;

  // Outer solid boundaries
  ctx.beginPath();
  ctx.moveTo(120, 20);
  ctx.lineTo(120, 650);
  ctx.moveTo(210, 20);
  ctx.lineTo(210, 650);
  ctx.stroke();

  // Lane dividers for the central median (x = 150 to x = 180)
  ctx.beginPath();
  ctx.moveTo(150, 20);
  ctx.lineTo(150, 610);
  ctx.moveTo(180, 20);
  ctx.lineTo(180, 610);
  ctx.stroke();

  // Draw vertical hatched divider
  ctx.save();
  ctx.beginPath();
  ctx.rect(150, 20, 30, 590);
  ctx.clip();
  ctx.fillStyle = "rgba(249, 168, 37, 0.15)";
  for (let i = 0; i < 700; i += 15) {
    ctx.beginPath();
    ctx.moveTo(140, 10 + i);
    ctx.lineTo(190, 60 + i);
    ctx.lineTo(190, 70 + i);
    ctx.lineTo(140, 20 + i);
    ctx.fill();
  }
  ctx.restore();

  // Bottom connecting loop lanes
  ctx.beginPath();
  ctx.moveTo(120, 650);
  ctx.lineTo(210, 650);
  ctx.stroke();

  // SB2 Entry Lane boundary (x = 210 to x = 250)
  ctx.beginPath();
  ctx.moveTo(250, 120);
  ctx.lineTo(250, 530);
  ctx.stroke();

  // Dashed Centerlines
  ctx.save();
  ctx.strokeStyle = "rgba(255,255,255,0.08)";
  ctx.setLineDash([4, 6]);

  // Top Road centerline (y = 20)
  ctx.beginPath();
  ctx.moveTo(20, 20);
  ctx.lineTo(1280, 20);
  ctx.stroke();

  // New Upward Lane to Top Road (x = 450)
  ctx.beginPath();
  ctx.moveTo(450, 200);
  ctx.lineTo(450, 20);
  ctx.stroke();

  // Bottom Road centerline (y = 660)
  ctx.beginPath();
  ctx.moveTo(20, 660);
  ctx.lineTo(1280, 660);
  ctx.stroke();

  // Downward Lane (x = 135)
  ctx.beginPath();
  ctx.moveTo(135, 20);
  ctx.lineTo(135, 650);
  ctx.stroke();

  // Entry vertical lane centerline (x = 1020)
  ctx.beginPath();
  ctx.moveTo(1020, 20);
  ctx.lineTo(1020, 660);
  ctx.stroke();

  // Exit vertical lane centerline (x = 1280)
  ctx.beginPath();
  ctx.moveTo(1280, 20);
  ctx.lineTo(1280, 660);
  ctx.stroke();

  // Upward Lane (x = 195)
  ctx.beginPath();
  ctx.moveTo(195, 20);
  ctx.lineTo(195, 650);
  ctx.stroke();

  // SB2 Entry Lane (x = 230)
  ctx.beginPath();
  ctx.moveTo(230, 120);
  ctx.lineTo(230, 500);
  ctx.stroke();

  // Roadway 1 centerline (y = 200)
  ctx.beginPath();
  ctx.moveTo(250, 200);
  ctx.lineTo(1040, 200);
  ctx.stroke();

  // Roadway 2 centerline (y = 500)
  ctx.beginPath();
  ctx.moveTo(250, 500);
  ctx.lineTo(1040, 500);
  ctx.stroke();

  ctx.restore();

  // 4. DRAW DIRECTIONAL MARKINGS (FLOW ARROWS)
  // Top road arrows (pointing right)
  drawArrow(ctx, { x: 380, y: 20 }, { x: 410, y: 20 });
  drawArrow(ctx, { x: 630, y: 20 }, { x: 660, y: 20 });
  drawArrow(ctx, { x: 880, y: 20 }, { x: 910, y: 20 });
  drawArrow(ctx, { x: 1130, y: 20 }, { x: 1160, y: 20 });

  // Bottom road arrows (pointing left)
  drawArrow(ctx, { x: 1160, y: 660 }, { x: 1130, y: 660 });
  drawArrow(ctx, { x: 880, y: 660 }, { x: 850, y: 660 });
  drawArrow(ctx, { x: 630, y: 660 }, { x: 600, y: 660 });
  drawArrow(ctx, { x: 380, y: 660 }, { x: 350, y: 660 });

  // New Upward Lane arrows
  drawArrow(ctx, { x: 450, y: 150 }, { x: 450, y: 120 });
  drawArrow(ctx, { x: 450, y: 70 }, { x: 450, y: 40 });

  // Downward lane arrows
  drawArrow(ctx, { x: 135, y: 80 }, { x: 135, y: 110 });
  drawArrow(ctx, { x: 135, y: 280 }, { x: 135, y: 310 });
  drawArrow(ctx, { x: 135, y: 480 }, { x: 135, y: 510 });

  // Right vertical lane arrows (entry lane x=1020, exit lane x=1280)
  drawArrow(ctx, { x: 1020, y: 80 }, { x: 1020, y: 110 });
  drawArrow(ctx, { x: 1020, y: 280 }, { x: 1020, y: 310 });
  drawArrow(ctx, { x: 1020, y: 480 }, { x: 1020, y: 510 });

  drawArrow(ctx, { x: 1280, y: 80 }, { x: 1280, y: 110 });
  drawArrow(ctx, { x: 1280, y: 280 }, { x: 1280, y: 310 });
  drawArrow(ctx, { x: 1280, y: 480 }, { x: 1280, y: 510 });

  for (let areaId = 1; areaId <= 4; areaId++) {
     const accessY = (areaId - 1) * 160 + 95;
     drawArrow(ctx, { x: 1050, y: accessY }, { x: 1080, y: accessY });
     drawArrow(ctx, { x: 1200, y: accessY }, { x: 1230, y: accessY });
  }

  // Bottom connecting loop arrows
  drawCurvedArrow(
    ctx,
    { x: 135, y: 640 },
    { x: 135, y: 675 },
    { x: 165, y: 675 },
  );
  drawCurvedArrow(
    ctx,
    { x: 165, y: 675 },
    { x: 195, y: 675 },
    { x: 195, y: 640 },
  );

  // Upward lane arrows
  drawArrow(ctx, { x: 195, y: 560 }, { x: 195, y: 530 });
  drawArrow(ctx, { x: 195, y: 360 }, { x: 195, y: 330 });
  drawArrow(ctx, { x: 195, y: 160 }, { x: 195, y: 130 });

  // Turn off into Swap Station 1 (SB1)
  drawCurvedArrow(
    ctx,
    { x: 195, y: 220 },
    { x: 195, y: 200 },
    { x: 225, y: 200 },
  );
  drawArrow(ctx, { x: 225, y: 200 }, { x: 255, y: 200 });

  // SB2 Entry Lane downward arrows
  drawArrow(ctx, { x: 230, y: 220 }, { x: 230, y: 250 });
  drawArrow(ctx, { x: 230, y: 380 }, { x: 230, y: 410 });

  // Turn into Swap Station 2 (SB2)
  drawCurvedArrow(
    ctx,
    { x: 230, y: 480 },
    { x: 230, y: 500 },
    { x: 255, y: 500 },
  );
  drawArrow(ctx, { x: 255, y: 500 }, { x: 285, y: 500 });

  // Roadway 1 Exit arrows (Horizontal towards working areas)
  drawArrow(ctx, { x: 490, y: 200 }, { x: 520, y: 200 });
  drawArrow(ctx, { x: 710, y: 200 }, { x: 740, y: 200 });
  drawArrow(ctx, { x: 910, y: 200 }, { x: 940, y: 200 });

  // Roadway 2 Exit arrows (Horizontal towards working areas)
  drawArrow(ctx, { x: 490, y: 500 }, { x: 520, y: 500 });
  drawArrow(ctx, { x: 710, y: 500 }, { x: 740, y: 500 });
  drawArrow(ctx, { x: 910, y: 500 }, { x: 940, y: 500 });
}
