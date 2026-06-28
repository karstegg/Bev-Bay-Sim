import { useEffect, useRef, useState } from "react";
import {
  createSimulation,
} from "./sim/createSimulation";
import {
  updateSimulation,
} from "./sim/updateSimulation";
import {
  updateKPIs,
} from "./sim/kpiLogic";
import {
  drawSimulation,
} from "./render/drawSimulation";
import {
  SimState,
  SimConfig,
  SimKPIs,
} from "./sim/types";
import { DEFAULT_CONFIG } from "./sim/config";
import { Play, Pause, RotateCcw, Settings, Activity } from "lucide-react";

export default function App() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const simRef = useRef<SimState | null>(null);
  const reqRef = useRef<number>(0);
  const lastTimeRef = useRef<number>(0);

  const [running, setRunning] = useState(false);
  const [config, setConfig] = useState<SimConfig>(DEFAULT_CONFIG);
  const [kpis, setKpis] = useState<SimKPIs | null>(null);
  const [needsReset, setNeedsReset] = useState(false);
  const [showLegend, setShowLegend] = useState(false);
  const [selectedBevId, setSelectedBevId] = useState("DT-0");

  const handleDrainBattery = () => {
    if (simRef.current) {
      const bev = simRef.current.machines.find((m) => m.id === selectedBevId);
      if (bev) {
        const bat = simRef.current.batteries.find(
          (b) => b.id === bev.batteryId,
        );
        if (bat) {
          bat.charge = 0;
          const ctx = canvasRef.current?.getContext("2d");
          if (ctx) drawSimulation(ctx, simRef.current);
        }
      }
    }
  };

  useEffect(() => {
    if (!simRef.current) {
      simRef.current = createSimulation(config);
      setKpis(simRef.current.kpis);
    }

    // Update config in sim state without full reset (except for spareBatteries)
    if (simRef.current) {
      simRef.current.config = { ...config };
      if (simRef.current.config.spareBatteries !== config.spareBatteries) {
        setNeedsReset(true);
      }
    }
  }, [config]);

  const initSim = () => {
    simRef.current = createSimulation(config);
    setKpis(simRef.current.kpis);
    setNeedsReset(false);
    if (canvasRef.current) {
      drawSimulation(canvasRef.current.getContext("2d")!, simRef.current);
    }
  };

  const handleReset = () => {
    setRunning(false);
    initSim();
  };

  useEffect(() => {
    const ctx = canvasRef.current?.getContext("2d");
    if (!ctx) return;

    const tick = (time: number) => {
      if (!lastTimeRef.current) lastTimeRef.current = time;
      const dt = (time - lastTimeRef.current) / 1000;
      lastTimeRef.current = time;

      if (simRef.current) {
        if (running) {
          // Cap dt to prevent huge jumps if tab is backgrounded
          updateSimulation(simRef.current, Math.min(dt, 0.1));
          updateKPIs(simRef.current);
          // We only want to set React state occasionally to avoid too many re-renders
          // But for KPIs, every frame is okay if we want live updates, or we could throttle.
          // React 18 batches this well enough.
          setKpis({ ...simRef.current.kpis });
        }
        drawSimulation(ctx, simRef.current);
      }
      reqRef.current = requestAnimationFrame(tick);
    };

    reqRef.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(reqRef.current);
  }, [running]);

  return (
    <div className="flex h-screen w-screen bg-[#1A1C1E] text-[#E0E0E0] overflow-hidden font-[Helvetica_Neue,Arial,sans-serif] selection:bg-[#F9A825]/30">
      {/* Sidebar */}
      <div className="w-80 flex-shrink-0 bg-[#23272A] border-r-2 border-[#3F444A] flex flex-col z-10 overflow-y-auto">
        <div className="p-5 border-b-2 border-[#3F444A]">
          <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
            <Activity className="w-5 h-5 text-[#F9A825]" />
            BEV Battery Bay
          </h1>
          <p className="text-[10px] text-[#F9A825] mt-1 uppercase tracking-wider font-bold">
            Underground Mine Simulation
          </p>
        </div>

        {/* Controls */}
        <div className="p-5 border-b-2 border-[#3F444A] space-y-5">
          <div className="flex items-center gap-2 mb-2">
            <button
              onClick={() => setRunning(!running)}
              className={`flex-1 flex justify-center items-center gap-2 py-2 px-4 rounded font-bold transition-colors ${running ? "bg-[#3F444A] text-white hover:bg-[#4a4f55]" : "bg-[#F9A825] text-black hover:bg-[#e59820]"}`}
            >
              {running ? (
                <>
                  <Pause className="w-4 h-4" /> PAUSE SIMULATION
                </>
              ) : (
                <>
                  <Play className="w-4 h-4" /> START SIMULATION
                </>
              )}
            </button>
            <button
              onClick={handleReset}
              className="p-2 bg-[#3F444A] hover:bg-[#4a4f55] rounded text-white transition-colors"
              title="Reset Simulation"
            >
              <RotateCcw className="w-5 h-5" />
            </button>
          </div>

          <div className="space-y-3 text-sm">
            <div className="flex items-center justify-between">
              <div className="flex w-full bg-[#2C2F33] rounded p-1 border border-[#3F444A] gap-1">
                {[1, 2, 5].map((s) => (
                  <button
                    key={s}
                    onClick={() => setConfig({ ...config, speed: s })}
                    className={`flex-1 px-3 py-1.5 rounded text-xs font-bold transition-colors ${config.speed === s ? "bg-[#F9A825] text-black" : "bg-[#3F444A] text-white hover:bg-[#4a4f55]"}`}
                  >
                    {s}x
                  </button>
                ))}
              </div>
            </div>

            <SliderControl
              label="Arrival Rate (Mult)"
              value={config.arrivalRateMult}
              min={0.5}
              max={5}
              step={0.5}
              onChange={(v: number) =>
                setConfig({ ...config, arrivalRateMult: v })
              }
              displayValue={`${config.arrivalRateMult}x`}
            />

            <SliderControl
              label="Charge Time VPX (DT)"
              value={config.chargeTimeVPX}
              min={5}
              max={120}
              step={1}
              onChange={(v: number) =>
                setConfig({ ...config, chargeTimeVPX: v })
              }
              displayValue={`${config.chargeTimeVPX}s`}
            />

            <SliderControl
              label="Charge Time VPY (FL)"
              value={config.chargeTimeVPY}
              min={5}
              max={120}
              step={1}
              onChange={(v: number) =>
                setConfig({ ...config, chargeTimeVPY: v })
              }
              displayValue={`${config.chargeTimeVPY}s`}
            />

            <SliderControl
              label="Discharge Rate DT (lower=faster)"
              value={config.dischargeTimeDT}
              min={10}
              max={3600}
              step={10}
              onChange={(v: number) =>
                setConfig({ ...config, dischargeTimeDT: v })
              }
              displayValue={`${config.dischargeTimeDT}s`}
            />

            <SliderControl
              label="Discharge Rate FL (lower=faster)"
              value={config.dischargeTimeFL}
              min={10}
              max={3600}
              step={10}
              onChange={(v: number) =>
                setConfig({ ...config, dischargeTimeFL: v })
              }
              displayValue={`${config.dischargeTimeFL}s`}
            />

            <SliderControl
              label="Speed DT"
              value={config.speedDT}
              min={50}
              max={300}
              step={10}
              onChange={(v: number) => setConfig({ ...config, speedDT: v })}
              displayValue={`${config.speedDT}`}
            />

            <SliderControl
              label="Speed FL"
              value={config.speedFL}
              min={50}
              max={300}
              step={10}
              onChange={(v: number) => setConfig({ ...config, speedFL: v })}
              displayValue={`${config.speedFL}`}
            />

            <SliderControl
              label="Dead Time (Hours)"
              value={config.deadTimeHours}
              min={0}
              max={12}
              step={1}
              onChange={(v: number) =>
                setConfig({ ...config, deadTimeHours: v })
              }
              displayValue={`${config.deadTimeHours}h`}
            />

            <div className="pt-2 border-t border-[#3F444A]">
              <div className="text-xs font-bold text-[#E0E0E0] mb-2 uppercase tracking-wider">
                Work Area Splits %
              </div>
              <div className="flex gap-1 mb-2">
                {[0, 1, 2, 3].map((i) => (
                  <div key={i} className="flex-1">
                    <input
                      type="number"
                      min="0"
                      max="100"
                      className="w-full bg-[#1A1C1E] border border-[#3F444A] rounded p-1 text-xs text-center"
                      value={config.workAreaSplits[i]}
                      onChange={(e) => {
                        const splits = [...config.workAreaSplits] as [
                          number,
                          number,
                          number,
                          number,
                        ];
                        splits[i] = parseInt(e.target.value) || 0;
                        setConfig({ ...config, workAreaSplits: splits });
                      }}
                    />
                  </div>
                ))}
              </div>
            </div>

            <div className="pt-2 border-t border-[#3F444A]">
              <div className="text-xs font-bold text-[#E0E0E0] mb-2 uppercase tracking-wider">
                Work Area Depletion Mult
              </div>
              <div className="flex gap-1">
                {[0, 1, 2, 3].map((i) => (
                  <div key={i} className="flex-1">
                    <input
                      type="number"
                      min="0.1"
                      max="10"
                      step="0.1"
                      className="w-full bg-[#1A1C1E] border border-[#3F444A] rounded p-1 text-xs text-center"
                      value={config.workAreaMultipliers[i]}
                      onChange={(e) => {
                        const mults = [...config.workAreaMultipliers] as [
                          number,
                          number,
                          number,
                          number,
                        ];
                        mults[i] = parseFloat(e.target.value) || 1;
                        setConfig({ ...config, workAreaMultipliers: mults });
                      }}
                    />
                  </div>
                ))}
              </div>
            </div>

            <SliderControl
              label="Swap Time"
              value={config.swapTime}
              min={2}
              max={20}
              step={1}
              onChange={(v: number) => setConfig({ ...config, swapTime: v })}
              displayValue={`${config.swapTime}s`}
            />

            <SliderControl
              label="Active Cranes"
              value={config.activeCranes}
              min={1}
              max={2}
              step={1}
              onChange={(v: number) =>
                setConfig({ ...config, activeCranes: v })
              }
              displayValue={config.activeCranes}
            />

            <SliderControl
              label="Spare Batteries (Req Reset)"
              value={config.spareBatteries}
              min={0}
              max={16}
              step={1}
              onChange={(v: number) =>
                setConfig({ ...config, spareBatteries: v })
              }
              displayValue={config.spareBatteries}
            />

            {needsReset && (
              <div className="text-xs text-[#F9A825] bg-[#F9A825]/10 p-2 rounded border border-[#F9A825]/20 font-bold uppercase tracking-wider">
                Reset required to apply battery count.
              </div>
            )}

            <label className="flex items-center gap-2 cursor-pointer pt-3 border-t border-[#3F444A] mt-4">
              <input
                type="checkbox"
                checked={config.showLabels}
                onChange={(e) =>
                  setConfig({ ...config, showLabels: e.target.checked })
                }
                className="rounded border-[#3F444A] bg-[#2C2F33] text-[#F9A825] focus:ring-[#F9A825]/20"
              />
              <span className="text-[11px] font-bold uppercase tracking-wider text-[#F9A825]">
                Show Object Labels
              </span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer pt-1 mt-1">
              <input
                type="checkbox"
                checked={config.showTrafficDebug}
                onChange={(e) =>
                  setConfig({ ...config, showTrafficDebug: e.target.checked })
                }
                className="rounded border-[#3F444A] bg-[#2C2F33] text-[#F9A825] focus:ring-[#F9A825]/20"
              />
              <span className="text-[11px] font-bold uppercase tracking-wider text-[#F9A825]">
                Show Traffic Debug
              </span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer pt-1 mt-1">
              <input
                type="checkbox"
                checked={showLegend}
                onChange={(e) => setShowLegend(e.target.checked)}
                className="rounded border-[#3F444A] bg-[#2C2F33] text-[#F9A825] focus:ring-[#F9A825]/20"
              />
              <span className="text-[11px] font-bold uppercase tracking-wider text-[#F9A825]">
                Show Legend
              </span>
            </label>
          </div>
        </div>

        {/* Battery Test Tool */}
        <div className="p-5 border-b-2 border-[#3F444A] space-y-3 shrink-0">
          <h2 className="text-[11px] font-bold text-[#F9A825] uppercase tracking-wider">
            Test Battery Swap (0% SOC)
          </h2>
          <p className="text-[10px] text-gray-400">
            Select any BEV to instantly drain its battery to 0% and verify its
            auto-routing straight to the swap station.
          </p>
          <div className="flex gap-2">
            <select
              value={selectedBevId}
              onChange={(e) => setSelectedBevId(e.target.value)}
              className="flex-1 bg-[#2C2F33] border border-[#3F444A] rounded p-1 text-xs text-white outline-none focus:border-[#F9A825]"
            >
              {(simRef.current
                ? simRef.current.machines.map((m) => m.id)
                : [
                    "DT-0",
                    "DT-1",
                    "DT-2",
                    "DT-3",
                    "DT-4",
                    "DT-5",
                    "DT-6",
                    "DT-7",
                    "FL-0",
                    "FL-1",
                    "FL-2",
                    "FL-3",
                    "FL-4",
                    "FL-5",
                  ]
              ).map((id) => (
                <option key={id} value={id}>
                  {id}
                </option>
              ))}
            </select>
            <button
              onClick={handleDrainBattery}
              className="px-3 py-1.5 bg-[#F44336] hover:bg-[#d32f2f] text-white font-bold rounded text-xs transition-colors flex items-center gap-1 shrink-0"
            >
              Drain to 0%
            </button>
          </div>
        </div>

        {/* Dashboard */}
        <div className="p-5 flex-1 flex flex-col gap-3">
          <h2 className="text-[11px] font-bold text-[#F9A825] uppercase tracking-wider mb-1">
            Live KPIs
          </h2>

          {kpis && (
            <div className="grid grid-cols-2 gap-3 text-sm">
              <MetricBox
                label="Waiting"
                value={kpis.machinesWaiting}
                color="text-[#F9A825]"
              />
              <MetricBox
                label="Served"
                value={kpis.machinesServed}
                color="text-[#E0E0E0]"
              />
              <MetricBox
                label="Avg Wait"
                value={`${kpis.avgWaitingTime.toFixed(1)}s`}
                color="text-[#E0E0E0]"
              />
              <MetricBox
                label="Avg Turnaround"
                value={`${kpis.avgTurnaroundTime.toFixed(1)}s`}
                color="text-[#E0E0E0]"
              />

              <div className="col-span-2 h-px bg-[#3F444A] my-1" />

              <MetricBox
                label="Charged Ready"
                value={kpis.chargedBatteriesReady}
                color="text-[#4CAF50]"
              />
              <MetricBox
                label="Charging"
                value={kpis.batteriesCharging}
                color="text-[#F9A825]"
              />
              <MetricBox
                label="Depleted Wait"
                value={kpis.depletedWaiting}
                color="text-[#F44336]"
              />
              <MetricBox
                label="Charger Util"
                value={`${kpis.chargerUtilisation.toFixed(0)}%`}
                color="text-[#E0E0E0]"
              />

              <div
                className={`col-span-2 mt-2 p-3 rounded border flex items-center gap-3 font-bold ${kpis.bottleneck === "None" ? "bg-[#2C2F33] border-[#3F444A] text-[#E0E0E0]" : "bg-[rgba(244,67,54,0.9)] border-white text-white"}`}
              >
                {kpis.bottleneck !== "None" && (
                  <Activity className="w-5 h-5 shrink-0" />
                )}
                <div>
                  <div className="text-[10px] uppercase opacity-80 mb-0.5 tracking-wider">
                    System Bottleneck
                  </div>
                  <div className="text-sm">{kpis.bottleneck.toUpperCase()}</div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Canvas Area */}
      <div
        className="flex-1 flex flex-col items-center justify-center bg-[#1A1C1E] p-4 relative"
        style={{
          backgroundImage: "radial-gradient(#2c2f33 1px, transparent 1px)",
          backgroundSize: "40px 40px",
        }}
      >
        {/* Timeline */}
        <div className="w-full max-w-[1300px] mb-4 bg-[#2C2F33] border border-[#3F444A] rounded-lg p-3 shrink-0">
          <div className="flex justify-between text-[10px] text-[#E0E0E0] font-bold opacity-60 mb-2 px-1">
            {[0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24].map((h) => (
              <span key={h}>{h}h</span>
            ))}
          </div>
          <div className="w-full h-4 relative">
            <input
              type="range"
              min="0"
              max="24"
              step="0.1"
              className="w-full h-2 bg-[#1A1C1E] rounded-full appearance-none outline-none cursor-pointer border border-[#3F444A] [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-4 [&::-webkit-slider-thumb]:h-4 [&::-webkit-slider-thumb]:bg-[#F9A825] [&::-webkit-slider-thumb]:rounded-full absolute top-1"
              value={kpis ? kpis.simTimeHours : 0}
              onChange={(e) => {
                if (simRef.current) {
                  simRef.current.time = parseFloat(e.target.value) * 10;
                }
              }}
            />
            <div
              className="absolute top-1 left-0 h-2 bg-[#F9A825] rounded-l-full pointer-events-none"
              style={{ width: `${kpis ? (kpis.simTimeHours / 24) * 100 : 0}%` }}
            />
            <div
              className="absolute top-1 right-0 h-2 bg-[#F44336]/50 rounded-r-full pointer-events-none"
              style={{ width: `${(config.deadTimeHours / 24) * 100}%` }}
              title="Dead Time (Parking)"
            />
          </div>
        </div>

        {/* Maintain aspect ratio wrapper */}
        <div className="relative w-full max-w-[1300px] aspect-[1300/700] overflow-hidden shadow-[0_10px_30px_rgba(0,0,0,0.8)] border border-[#3F444A] bg-[#1A1C1E]">
          <canvas
            ref={canvasRef}
            width={1300}
            height={700}
            className="w-full h-full block"
          />
        </div>

        {/* Legend overlay */}
        {showLegend && (
          <div className="absolute top-8 right-8 bg-[#2C2F33]/90 backdrop-blur border border-[#3F444A] p-4 rounded text-xs flex gap-6 pointer-events-none shadow-[0_4px_10px_rgba(0,0,0,0.5)]">
            <div className="space-y-3">
              <LegendItem color="#37474F" label="Dump Truck (DT)" />
              <LegendItem color="#444444" label="Loader (FL)" />
              <LegendItem color="#F9A825" label="Overhead Crane" isBorder />
            </div>
            <div className="space-y-3">
              <LegendItem color="#4CAF50" label="Charged Batt." />
              <LegendItem color="#F9A825" label="Charging Batt." />
              <LegendItem color="#F44336" label="Depleted Batt." />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function SliderControl({
  label,
  value,
  min,
  max,
  step,
  onChange,
  displayValue,
}: any) {
  return (
    <div className="bg-[#2C2F33] p-3 rounded border border-[#3F444A]">
      <div className="flex justify-between mb-2">
        <label className="text-[#F9A825] text-[11px] uppercase font-bold tracking-wider">
          {label}
        </label>
        <span className="text-[#E0E0E0] font-mono text-[11px]">
          {displayValue}
        </span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        className="w-full h-1 bg-[#3F444A] rounded-full appearance-none cursor-pointer accent-[#F9A825]"
      />
    </div>
  );
}

function MetricBox({
  label,
  value,
  color = "text-[#F9A825]",
}: {
  label: string;
  value: string | number;
  color?: string;
}) {
  return (
    <div className="bg-[#2C2F33] border border-[#3F444A] rounded p-3 flex flex-col items-center justify-center text-center">
      <span className="text-[10px] text-[#E0E0E0] opacity-60 uppercase tracking-[1px] mb-1">
        {label}
      </span>
      <span className={`font-mono text-2xl font-bold ${color}`}>{value}</span>
    </div>
  );
}

function LegendItem({
  color,
  label,
  isBorder,
}: {
  color: string;
  label: string;
  isBorder?: boolean;
}) {
  return (
    <div className="flex items-center gap-2">
      <div
        className={`w-4 h-4 rounded-sm ${isBorder ? "border-2 bg-transparent" : ""}`}
        style={{
          backgroundColor: isBorder ? "transparent" : color,
          borderColor: color,
        }}
      />
      <span className="text-[#E0E0E0] font-bold text-[11px] uppercase tracking-wider">
        {label}
      </span>
    </div>
  );
}
