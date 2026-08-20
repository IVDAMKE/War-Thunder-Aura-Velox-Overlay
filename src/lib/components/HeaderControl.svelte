<script lang="ts">
  import { invoke } from '@tauri-apps/api/core';
  import type { GameStatus } from '../types/telemetry';
  import ThemeSelector from './ThemeSelector.svelte';

  let {
    status = null,
    isClickThrough = false,
    onToggleClickThrough = () => {},
    onOpenSettings = () => {}
  }: {
    status?: GameStatus | null;
    isClickThrough?: boolean;
    onToggleClickThrough?: () => void;
    onOpenSettings?: () => void;
  } = $props();

  async function handleHeaderMouseDown(e: MouseEvent) {
    if (e.button === 0 && !isClickThrough) {
      try {
        await invoke('start_drag');
      } catch (err) {
        console.warn('Start drag failed or running outside Tauri:', err);
      }
    }
  }
</script>

<div class="header-control overlay-card">
  <div
    class="brand"
    data-tauri-drag-region
    onmousedown={handleHeaderMouseDown}
    role="button"
    tabindex="0"
  >
    <span class="drag-handle" data-tauri-drag-region>⣿</span>
    <span class="logo" data-tauri-drag-region>⚡ WAR THUNDER ASSISTANT</span>
    <div class="status-indicator">
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

  <div class="actions">
    <ThemeSelector />

    <button
      class="icon-btn settings-btn"
      onclick={onOpenSettings}
      title="Configure interface layout settings (Shortcut: Ctrl+Shift+S)"
    >
      ⚙️ SETTINGS
    </button>

    {#if !status?.game_running}
      <button
        class="icon-btn force-btn"
        onclick={() => invoke('force_connect')}
        title="Bypass game detection"
      >
        ⚡ FORCE CONNECT
      </button>
    {/if}

    <button
      class="click-through-btn"
      class:active={isClickThrough}
      onclick={onToggleClickThrough}
      title="Toggle mouse pass-through mode (Shortcut: Ctrl+Shift+X)"
    >
      {#if isClickThrough}
        <span class="btn-icon">👻</span> CLICK-THROUGH ON
      {:else}
        <span class="btn-icon">🖱️</span> INTERACTIVE MODE
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
