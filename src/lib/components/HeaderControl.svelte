<script lang="ts">
  import { invoke } from '@tauri-apps/api/core';
  import { getCurrentWindow } from '@tauri-apps/api/window';
  import { onMount, onDestroy } from 'svelte';
  import type { GameStatus } from '../types/telemetry';
  import ThemeSelector from './ThemeSelector.svelte';

  let {
    status = null,
    isClickThrough = false,
    idleFadeTime = 15,
    idleFadeOpacity = 0.33,
    compactMode = false,
    shortcutClickThrough = 'Ctrl+Shift+X',
    shortcutSettings = 'Ctrl+Shift+S',
    onToggleClickThrough = () => {},
    onOpenSettings = () => {}
  }: {
    status?: GameStatus | null;
    isClickThrough?: boolean;
    idleFadeTime?: number;
    idleFadeOpacity?: number;
    compactMode?: boolean;
    shortcutClickThrough?: string;
    shortcutSettings?: string;
    onToggleClickThrough?: () => void;
    onOpenSettings?: () => void;
  } = $props();

  let isIdle = $state(false);
  let idleTimeout: ReturnType<typeof setTimeout>;

  function resetIdle() {
    isIdle = false;
    clearTimeout(idleTimeout);
    idleTimeout = setTimeout(() => {
      isIdle = true;
    }, idleFadeTime * 1000);
  }

  function handlePointerMove(e: PointerEvent) {
    if (e.clientY <= 70) {
      resetIdle();
    }
  }

  onMount(() => {
    resetIdle();
    window.addEventListener('pointermove', handlePointerMove);
  });

  onDestroy(() => {
    clearTimeout(idleTimeout);
    if (typeof window !== 'undefined') {
      window.removeEventListener('pointermove', handlePointerMove);
    }
  });

  async function handleHeaderMouseDown(e: MouseEvent) {
    if (e.button === 0 && !isClickThrough) {
      try {
        await getCurrentWindow().startDragging();
      } catch (err) {
        try {
          await invoke('start_drag');
        } catch (err2) {
          console.warn('Start drag failed:', err2);
        }
      }
    }
  }
</script>

<div
  class="header-control overlay-card {isIdle ? 'idle' : ''} {compactMode ? 'compact' : ''}"
  style="--idle-opacity: {idleFadeOpacity};"
  onpointerenter={resetIdle}
  onpointermove={resetIdle}
  role="presentation"
>
  <div
    class="brand"
    data-tauri-drag-region
    onmousedown={handleHeaderMouseDown}
    role="presentation"
  >
    <span class="material-symbols-outlined drag-handle" data-tauri-drag-region>drag_indicator</span>
    <span class="logo" data-tauri-drag-region><span class="material-symbols-outlined logo-icon" data-tauri-drag-region>bolt</span> WT AURA VELOX OVERLAY</span>
    <div class="status-indicator" data-tauri-drag-region>
      {#if status?.connected}
        <span class="dot online"></span>
        <span class="status-text text-online">LIVE TELEMETRY</span>
      {:else if status?.game_running}
        <span class="dot hangar"></span>
        <span class="status-text text-hangar">HANGAR / STANDBY</span>
      {:else}
        <span class="dot offline"></span>
        <span class="status-text text-offline">WAITING FOR ACES.EXE</span>
      {/if}
    </div>
  </div>

  <div class="actions" onmousedown={(e) => e.stopPropagation()}>
    <ThemeSelector />

    <button
      class="icon-btn settings-btn"
      onclick={(e) => { e.stopPropagation(); onOpenSettings(); }}
      title="Settings (Shortcut: {shortcutSettings})"
    >
      <span class="material-symbols-outlined">settings</span>
    </button>

    {#if !status?.game_running}
      <button
        class="icon-btn force-btn"
        onclick={(e) => { e.stopPropagation(); invoke('force_connect'); }}
        title="Force Connect (Bypass game detection)"
      >
        <span class="material-symbols-outlined">sync</span>
      </button>
    {/if}

    <button
      class="click-through-btn"
      class:active={isClickThrough}
      onclick={(e) => { e.stopPropagation(); onToggleClickThrough(); }}
      title={isClickThrough ? `Click-Through Mode Active (Shortcut: ${shortcutClickThrough})` : `Interactive Mode Active (Shortcut: ${shortcutClickThrough})`}
    >
      {#if isClickThrough}
        <span class="material-symbols-outlined">touch_app</span>
      {:else}
        <span class="material-symbols-outlined">mouse</span>
      {/if}
    </button>
  </div>
</div>

<style>
  .header-control {
    padding: 8px 16px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    transition: opacity 0.4s ease, filter 0.4s ease;
  }

  .header-control.idle {
    opacity: var(--idle-opacity, 0.33);
  }

  .header-control.compact {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    backdrop-filter: none !important;
    -webkit-backdrop-filter: none !important;
  }

  .header-control:hover,
  .header-control.idle:hover {
    opacity: 1;
  }

  .brand {
    display: flex;
    align-items: center;
    gap: 12px;
    cursor: move;
  }

  .drag-handle {
    font-size: 1rem;
    color: var(--text-muted);
    letter-spacing: -2px;
    cursor: move;
  }

  .logo {
    font-size: 0.85rem;
    font-weight: 900;
    letter-spacing: 0.08em;
    color: var(--accent-color);
    text-shadow: var(--accent-glow);
  }

  .status-indicator {
    display: flex;
    align-items: center;
    gap: 6px;
    background: rgba(0, 0, 0, 0.3);
    padding: 3px 10px;
    border-radius: 20px;
    border: 1px solid var(--border-color);
  }

  .dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
  }

  .dot.online {
    background: var(--success-color);
    box-shadow: 0 0 8px var(--success-color);
  }

  .dot.hangar {
    background: var(--warning-color);
    box-shadow: 0 0 8px var(--warning-color);
  }

  .dot.offline {
    background: var(--danger-color);
  }

  .status-text {
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.05em;
  }

  .text-online {
    color: var(--success-color);
  }

  .text-hangar {
    color: var(--warning-color);
  }

  .text-offline {
    color: var(--danger-color);
  }

  .actions {
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .settings-btn,
  .click-through-btn {
    background: rgba(0, 0, 0, 0.3);
    border: 1px solid var(--border-color);
    color: var(--text-primary);
    font-size: 0.72rem;
    font-weight: 700;
    padding: 6px 12px;
    border-radius: 8px;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 6px;
    transition: all 0.2s ease;
  }

  .settings-btn:hover,
  .click-through-btn:hover {
    border-color: var(--accent-color);
    background: var(--bg-card-hover);
  }

  .force-btn {
    background: rgba(255, 100, 100, 0.2);
    border: 1px solid rgba(255, 100, 100, 0.5);
    color: #ffcccc;
  }
  .force-btn:hover {
    background: rgba(255, 100, 100, 0.4);
  }

  .click-through-btn.active {
    background: rgba(245, 158, 11, 0.2);
    border-color: var(--warning-color);
    color: var(--warning-color);
  }

  .btn-icon {
    font-size: 0.85rem;
  }
</style>
