<script lang="ts">
  import type { TelemetryPayload } from '../types/telemetry';
  import { DEFAULT_SETTINGS, type InterfaceSettings } from '../types/settings';

  let {
    telemetry = null,
    settings = DEFAULT_SETTINGS
  }: {
    telemetry?: TelemetryPayload | null;
    settings?: InterfaceSettings;
  } = $props();

  // Svelte 5 $derived runes for safe data extraction
  let altitude = $derived(
    telemetry?.state?.["H, m"] ?? telemetry?.indicators?.altitude_hour ?? 0
  );
  let iasSpeed = $derived(
    telemetry?.state?.["IAS, km/h"] ?? (telemetry?.indicators?.speed ? Math.round(telemetry.indicators.speed * 3.6) : 0)
  );
  let tasSpeed = $derived(telemetry?.state?.["TAS, km/h"] ?? 0);
  let mach = $derived(telemetry?.state?.M ?? 0);
  let gForce = $derived(
    telemetry?.state?.Ny ?? telemetry?.indicators?.g_meter ?? 1.0
  );
  let aoa = $derived(
    telemetry?.state?.["AoA, deg"] ?? telemetry?.indicators?.aoa ?? 0
  );
  let compass = $derived(
    Math.round(telemetry?.indicators?.compass ?? 0)
  );
  let rpm = $derived(
    telemetry?.state?.["RPM 1"] ?? telemetry?.indicators?.rpm ?? 0
  );
  let throttle = $derived(
    telemetry?.state?.["throttle 1, %"] ?? (telemetry?.indicators?.throttle ? Math.round(telemetry.indicators.throttle * 100) : 0)
  );
  let vehicleType = $derived(
    telemetry?.state?.type ?? telemetry?.indicators?.type ?? 'Aircraft'
  );

  let roll = $derived(telemetry?.indicators?.aviahorizon_roll ?? 0);
  let pitch = $derived(telemetry?.indicators?.aviahorizon_pitch ?? 0);

  // Warnings
  let isHighG = $derived(gForce > 6.0);
  let isStallWarning = $derived(iasSpeed < 180 && altitude > 200 && aoa > 14);

  function getCompassCardinal(deg: number): string {
    const directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'];
    return directions[Math.round(deg / 45) % 8];
  }
</script>

<div class="overlay-card telemetry-hud {settings.compactMode ? 'compact' : ''}">
  <div class="hud-header">
    <div class="vehicle-info">
      <span class="type-badge">{vehicleType.toUpperCase()}</span>
      <span class="heading-badge">🧭 {compass}° {getCompassCardinal(compass)}</span>
    </div>
    {#if settings.showGForce && isHighG}
      <span class="warning-badge g-warn">⚠️ HIGH G ({gForce}G)</span>
    {:else if isStallWarning}
      <span class="warning-badge stall-warn">⚠️ STALL WARNING</span>
    {/if}
  </div>

  <div class="hud-main-grid">
    <!-- Speed Section -->
    {#if settings.showSpeed}
      <div class="hud-block">
        <div class="gauge-row">
          <div class="metric">
            <span class="label">IAS SPEED</span>
            <span class="value big">{iasSpeed} <span class="unit">km/h</span></span>
          </div>
          <div class="metric">
            <span class="label">TAS SPEED</span>
            <span class="value">{tasSpeed} <span class="unit">km/h</span></span>
          </div>
          <div class="metric">
            <span class="label">MACH</span>
            <span class="value">{mach.toFixed(2)} M</span>
          </div>
        </div>
      </div>
    {/if}

    <!-- Altitude & Climb Section -->
    {#if settings.showAltitude}
      <div class="hud-block">
        <div class="gauge-row">
          <div class="metric">
            <span class="label">ALTITUDE</span>
            <span class="value big">{Math.round(altitude)} <span class="unit">m</span></span>
          </div>
          {#if settings.showGForce}
            <div class="metric">
              <span class="label">G-FORCE</span>
              <span class="value" class:text-danger={gForce > 6}>{gForce.toFixed(1)} G</span>
            </div>
          {/if}
          <div class="metric">
            <span class="label">AoA</span>
            <span class="value">{aoa.toFixed(1)}°</span>
          </div>
        </div>
      </div>
    {/if}

    <!-- Engine & Systems -->
    {#if settings.showEngineRpm}
      <div class="hud-block">
        <div class="gauge-row">
          <div class="metric">
            <span class="label">THROTTLE</span>
            <span class="value">{throttle}%</span>
          </div>
          <div class="metric">
            <span class="label">ENGINE RPM</span>
            <span class="value">{Math.round(rpm)}</span>
          </div>
          {#if settings.showPitchRoll}
            <div class="metric">
              <span class="label">PITCH / ROLL</span>
              <span class="value">{pitch.toFixed(0)}° / {roll.toFixed(0)}°</span>
            </div>
          {/if}
        </div>
      </div>
    {/if}
  </div>
</div>

<style>
  .telemetry-hud {
    padding: 14px 18px;
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .hud-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .vehicle-info {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .type-badge {
    background: var(--accent-color);
    color: #0f172a;
    font-size: 0.7rem;
    font-weight: 800;
    padding: 2px 8px;
    border-radius: 6px;
    letter-spacing: 0.05em;
  }

  .heading-badge {
    font-size: 0.8rem;
    font-weight: 700;
    font-family: monospace;
    color: var(--text-primary);
  }

  .warning-badge {
    font-size: 0.7rem;
    font-weight: 800;
    padding: 2px 8px;
    border-radius: 6px;
    animation: pulse 1s infinite alternate;
  }

  .g-warn {
    background: rgba(239, 68, 68, 0.25);
    color: var(--danger-color);
    border: 1px solid var(--danger-color);
  }

  .stall-warn {
    background: rgba(245, 158, 11, 0.25);
    color: var(--warning-color);
    border: 1px solid var(--warning-color);
  }

  @keyframes pulse {
    from { opacity: 0.6; }
    to { opacity: 1; }
  }

  .hud-main-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 10px;
  }

  .hud-block {
    background: rgba(0, 0, 0, 0.2);
    border: 1px solid var(--border-color);
    border-radius: 10px;
    padding: 10px;
  }

  .gauge-row {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    justify-content: space-between;
    align-items: baseline;
  }

  .metric {
    display: flex;
    flex-direction: column;
    min-width: 60px;
    flex: 1;
  }

  .label {
    font-size: 0.62rem;
    font-weight: 600;
    color: var(--text-muted);
    letter-spacing: 0.05em;
  }

  .value {
    font-size: 1rem;
    font-weight: 700;
    font-family: 'JetBrains Mono', monospace;
    color: var(--text-primary);
  }

  .value.big {
    font-size: 1.35rem;
    color: var(--accent-color);
  }

  .unit {
    font-size: 0.7rem;
    color: var(--text-secondary);
    font-weight: 400;
  }

  .text-danger {
    color: var(--danger-color);
  }

  @media (max-width: 768px) {
    .hud-main-grid {
      grid-template-columns: 1fr;
    }
  }

  /* Compact Mode Styles */
  .telemetry-hud.compact {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    backdrop-filter: none !important;
    padding: 0;
  }

  .telemetry-hud.compact .hud-block {
    background: transparent;
    border: none;
    padding: 4px;
  }

  .telemetry-hud.compact .label,
  .telemetry-hud.compact .value,
  .telemetry-hud.compact .unit,
  .telemetry-hud.compact .heading-badge {
    text-shadow: 1px 1px 2px #000, -1px -1px 2px #000, 1px -1px 2px #000, -1px 1px 2px #000, 0px 4px 6px rgba(0,0,0,0.8);
  }
</style>
