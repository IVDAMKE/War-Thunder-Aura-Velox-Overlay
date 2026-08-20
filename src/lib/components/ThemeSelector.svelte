<script lang="ts">
  import type { ThemeType } from '../types/telemetry';

  let currentTheme: ThemeType = $state('modern-bento');

  const themes: { id: ThemeType; label: string; icon: string }[] = [
    { id: 'modern-bento', label: 'Bento Glass', icon: '✨' },
    { id: 'dark-mode', label: 'OLED Dark', icon: '🌙' },
    { id: 'white-mode', label: 'Light', icon: '☀️' }
  ];

  $effect(() => {
    document.documentElement.setAttribute('data-theme', currentTheme);
  });

  function selectTheme(theme: ThemeType) {
    currentTheme = theme;
  }
</script>

<div class="theme-selector">
  {#each themes as theme}
    <button
      class="theme-btn"
      class:active={currentTheme === theme.id}
      onclick={() => selectTheme(theme.id)}
      title={theme.label}
    >
      <span class="icon">{theme.icon}</span>
      <span class="label">{theme.label}</span>
    </button>
  {/each}
</div>

<style>
  .theme-selector {
    display: flex;
    gap: 4px;
    background: rgba(0, 0, 0, 0.25);
    padding: 4px;
    border-radius: 12px;
    border: 1px solid var(--border-color);
  }

  .theme-btn {
    display: flex;
    align-items: center;
    gap: 6px;
    background: transparent;
    border: none;
    color: var(--text-secondary);
    padding: 6px 10px;
    border-radius: 8px;
    font-size: 0.75rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .theme-btn:hover {
    color: var(--text-primary);
    background: var(--bg-card-hover);
  }

  .theme-btn.active {
    background: var(--accent-color);
    color: #0f172a;
    font-weight: 700;
    box-shadow: var(--accent-glow);
  }

  .icon {
    font-size: 0.85rem;
  }

  @media (max-width: 640px) {
    .label {
      display: none;
    }
  }
</style>
