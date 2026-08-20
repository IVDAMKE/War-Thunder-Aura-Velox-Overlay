export interface GameStateData {
  valid?: boolean;
  army?: string;
  type?: string;
  "H, m"?: number;
  "TAS, km/h"?: number;
  "IAS, km/h"?: number;
  M?: number;
  "AoA, deg"?: number;
  "AoS, deg"?: number;
  Ny?: number;
  "Vy, m/s"?: number;
  "Mfuel, kg"?: number;
  "Mfuel0, kg"?: number;
  "RPM 1"?: number;
  "throttle 1, %"?: number;
  "thrust 1, kgs"?: number;
  "oil temp 1, C"?: number;
}

export interface IndicatorsData {
  valid?: boolean;
  army?: string;
  type?: string;
  speed?: number;
  altitude_hour?: number;
  compass?: number;
  g_meter?: number;
  g_meter_max?: number;
  g_meter_min?: number;
  aoa?: number;
  aviahorizon_roll?: number;
  aviahorizon_pitch?: number;
  rpm?: number;
  throttle?: number;
}

export interface TelemetryPayload {
  state: GameStateData;
  indicators: IndicatorsData;
}

export interface TranslatedChatMessage {
  id: number;
  sender: string;
  original: string;
  translated: string;
  enemy: boolean;
  mode: string;
  time: number;
}

export interface GameStatus {
  game_running: boolean;
  connected: boolean;
  message: string;
}

export interface HudMsgPayload {
  id: number;
  msg: string;
  category: 'evt' | 'dmg';
}

export type ThemeType = 'modern-bento' | 'dark-mode' | 'white-mode';
