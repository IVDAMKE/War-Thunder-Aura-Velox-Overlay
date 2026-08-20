<script lang="ts">
  import { untrack } from 'svelte';
  import type { TranslatedChatMessage, HudMsgPayload } from '../types/telemetry';
  import type { InterfaceSettings } from '../types/settings';

  let {
    lastChatMessage = null,
    lastHudMsg = null,
    settings = null
  }: {
    lastChatMessage?: TranslatedChatMessage | null;
    lastHudMsg?: HudMsgPayload | null;
    settings?: InterfaceSettings | null;
  } = $props();

  let kills = $state(0);
  let deaths = $state(0);
  let assists = $state(0);
  let elapsedTimeSec = $state(0);

  // Svelte 5 $derived runes for real-time statistical calculations
  let kdRatio = $derived(deaths === 0 ? kills.toFixed(2) : (kills / deaths).toFixed(2));
  let kdaRatio = $derived(deaths === 0 ? (kills + assists).toFixed(2) : ((kills + assists) / deaths).toFixed(2));
  let formattedTime = $derived(() => {
    const mins = Math.floor(elapsedTimeSec / 60).toString().padStart(2, '0');
    const secs = (elapsedTimeSec % 60).toString().padStart(2, '0');
    return `${mins}:${secs}`;
  });

  // Track match timer
  $effect(() => {
    const interval = setInterval(() => {
      elapsedTimeSec += 1;
    }, 1000);
    return () => clearInterval(interval);
  });

  let processedHudId = -1;

  // Process /hudmsg events correlated with playerUsername
  $effect(() => {
    if (!lastHudMsg || lastHudMsg.id === processedHudId) return;
    processedHudId = lastHudMsg.id;
    
    const username = settings?.playerUsername?.trim().toLowerCase();
    const msg = lastHudMsg.msg.toLowerCase();

    untrack(() => {
      if (username && username.length > 0) {
      if (msg.includes(username)) {
        // Kill / Death matching
        const killRegex = /(destroyed|shot down|sank|killed|сбил|уничтожил|потопил|убил)/;
        const crashRegex = /(crashed|разбился)/;

        if (killRegex.test(msg)) {
          const parts = msg.split(killRegex);
          // parts will be [attacker, match, victim]
          if (parts.length >= 3) {
            const attacker = parts[0];
            const victim = parts[parts.length - 1]; // Everything after the match
            
            if (attacker.includes(username)) {
              kills += 1;
            } else if (victim.includes(username)) {
              deaths += 1;
            }
          }
        } else if (crashRegex.test(msg)) {
          // If the message contains crash and the username is in the string, it's a death
          if (msg.includes(username)) {
            deaths += 1;
          }
        }

        // Assist matching
        if (msg.includes("assist") || msg.includes("помощь")) {
          assists += 1;
        }
      }
    } else {
      // Fallback if no username is set: Just count every global event
      const killRegex = /(destroyed|shot down|sank|killed|сбил|уничтожил|потопил|убил)/;
      if (killRegex.test(msg)) {
        kills += 1;
      }
      if (msg.includes("assist") || msg.includes("помощь")) {
        assists += 1;
      }
    }
    });
  });

  let processedChatId = -1;

  // Process system chat fallback (when /hudmsg is delayed or missing)
  $effect(() => {
    if (!lastChatMessage || lastChatMessage.id === processedChatId) return;
    processedChatId = lastChatMessage.id;

    const msg = lastChatMessage.original.toLowerCase();
    const username = settings?.playerUsername?.trim().toLowerCase();

    untrack(() => {
      if (username && username.length > 0 && msg.includes(username)) {
      const killRegex = /(destroyed|shot down|sank|killed|сбил|уничтожил|потопил|убил)/;
      const crashRegex = /(crashed|разбился)/;

      if (killRegex.test(msg)) {
        const parts = msg.split(killRegex);
        if (parts.length >= 3) {
          if (parts[0].includes(username)) kills += 1;
          else if (parts[parts.length - 1].includes(username)) deaths += 1;
        }
      } else if (crashRegex.test(msg)) {
        deaths += 1;
      }
      }
    });
  });

  function addKill() { kills += 1; }
  function removeKill() { if (kills > 0) kills -= 1; }
  function addDeath() { deaths += 1; }
  function removeDeath() { if (deaths > 0) deaths -= 1; }
  function addAssist() { assists += 1; }
  function removeAssist() { if (assists > 0) assists -= 1; }
  function resetStats() {
    kills = 0;
    deaths = 0;
    assists = 0;
    elapsedTimeSec = 0;
  }
</script>

<div class="overlay-card stats-widget {settings?.compactMode ? 'compact' : ''}">
  {#if !settings?.compactMode}
    <div class="stats-header">
      <span class="title">
        COMBAT STATS
        {#if settings?.playerUsername}
          <span class="user-badge" title="Tracking {settings.playerUsername}">({settings.playerUsername})</span>
        {/if}
      </span>
      <span class="match-time">⏱️ {formattedTime()}</span>
    </div>
  {/if}

  <div class="stats-grid">
    <div class="stat-box">
      <span class="label">KILLS</span>
      <div class="value-row">
        <button class="mini-btn" onclick={removeKill}>-</button>
        <span class="value text-success">{kills}</span>
        <button class="mini-btn" onclick={addKill}>+</button>
      </div>
    </div>

    <div class="stat-box">
      <span class="label">DEATHS</span>
      <div class="value-row">
        <button class="mini-btn" onclick={removeDeath}>-</button>
        <span class="value text-danger">{deaths}</span>
        <button class="mini-btn" onclick={addDeath}>+</button>
      </div>
    </div>

    <div class="stat-box">
      <span class="label">ASSISTS</span>
      <div class="value-row">
        <button class="mini-btn" onclick={removeAssist}>-</button>
        <span class="value text-warning">{assists}</span>
        <button class="mini-btn" onclick={addAssist}>+</button>
      </div>
    </div>

    <div class="stat-box highlight">
      <span class="label">K/D RATIO</span>
      <span class="value accent">{kdRatio}</span>
    </div>
  </div>

  <div class="footer-row">
    <span class="kda">KDA: {kdaRatio}</span>
    {#if !settings?.compactMode}
      <button class="reset-btn" onclick={resetStats}>Reset</button>
    {/if}
  </div>
</div>

<style>
  .stats-widget {
    padding: 10px 12px;
    display: flex;
    flex-direction: column;
    gap: 8px;
    overflow: hidden;
    box-sizing: border-box;
    width: 100%;
  }

  .stats-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid var(--border-color);
    padding-bottom: 4px;
    flex-wrap: wrap;
    gap: 4px;
  }

  .title {
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.06em;
    color: var(--text-secondary);
    white-space: nowrap;
    display: flex;
    align-items: center;
    gap: 4px;
  }

  .user-badge {
    font-size: 0.65rem;
    color: var(--accent-color);
    font-weight: 600;
    max-width: 90px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .match-time {
    font-size: 0.75rem;
    font-family: monospace;
    color: var(--accent-color);
  }

  .stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(65px, 1fr));
    gap: 6px;
    width: 100%;
  }

  .stat-box {
    background: rgba(0, 0, 0, 0.25);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 6px 4px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-width: 0;
    overflow: hidden;
  }

  .stat-box.highlight {
    background: rgba(56, 189, 248, 0.08);
    border-color: var(--border-glow);
  }

  .label {
    font-size: 0.58rem;
    font-weight: 700;
    color: var(--text-muted);
    letter-spacing: 0.03em;
    white-space: nowrap;
    text-overflow: ellipsis;
    overflow: hidden;
    max-width: 100%;
  }

  .value-row {
    display: flex;
    align-items: center;
    gap: 4px;
    margin-top: 2px;
    max-width: 100%;
  }

  .value {
    font-size: 1.1rem;
    font-weight: 800;
    line-height: 1;
  }

  .text-success { color: var(--success-color); }
  .text-danger { color: var(--danger-color); }
  .text-warning { color: var(--warning-color); }
  .accent { color: var(--accent-color); }

  .mini-btn {
    background: rgba(255, 255, 255, 0.1);
    border: none;
    color: var(--text-secondary);
    border-radius: 4px;
    width: 16px;
    height: 16px;
    font-size: 0.7rem;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }

  .mini-btn:hover {
    background: var(--accent-color);
    color: #000;
  }

  .footer-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.72rem;
    flex-wrap: wrap;
    gap: 4px;
  }

  .kda {
    color: var(--text-secondary);
    font-weight: 600;
  }

  .reset-btn {
    background: transparent;
    border: 1px solid var(--border-color);
    color: var(--text-muted);
    padding: 2px 8px;
    border-radius: 6px;
    font-size: 0.68rem;
    cursor: pointer;
  }

  .reset-btn:hover {
    color: var(--danger-color);
    border-color: var(--danger-color);
  }

  /* Compact Mode Styles */
  .stats-widget.compact {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    backdrop-filter: none !important;
    padding: 0;
  }

  .stats-widget.compact .stat-box {
    background: transparent;
    border: none;
    padding: 2px;
  }

  .stats-widget.compact .label,
  .stats-widget.compact .value,
  .stats-widget.compact .kda {
    text-shadow: 1px 1px 2px #000, -1px -1px 2px #000, 1px -1px 2px #000, -1px 1px 2px #000, 0px 4px 6px rgba(0,0,0,0.8);
  }

  .stats-widget.compact .mini-btn {
    opacity: 0.2;
  }

  .stats-widget.compact:hover .mini-btn {
    opacity: 1;
  }
</style>
