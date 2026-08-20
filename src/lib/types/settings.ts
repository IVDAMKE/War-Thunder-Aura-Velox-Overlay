// Layouts have been reverted to fixed CSS grid
export interface WidgetBounds {
  x: number;
  y: number;
  w: number;
  h: number;
}

export interface InterfaceSettings {
  playerUsername: string;
  showHeader: boolean;
  showTelemetryHud: boolean;
  showStatsWidget: boolean;
  showChatWidget: boolean;
  showMapWidget: boolean;
  showObjectivesWidget: boolean;
  showAiCopilotWidget: boolean;
  
  hudBounds: WidgetBounds;
  statsBounds: WidgetBounds;
  chatBounds: WidgetBounds;
  objectivesBounds: WidgetBounds;
  mapBounds: WidgetBounds;
  aiCopilotBounds: WidgetBounds;

  showSpeed: boolean;
  showAltitude: boolean;
  showGForce: boolean;
  showEngineRpm: boolean;
  showPitchRoll: boolean;
  showAutoTranslation: boolean;
  targetLanguage: string;
  ignoreSameLanguage: boolean;
  distanceUnit: 'km' | 'nm';
  mapWindowMode: 'draggable' | 'fullscreen';

  aiApiProvider: 'openai' | 'google' | 'custom';
  aiApiKey: string;
  aiModel: string;
  aiCustomEndpoint: string;
  aiTtsEnabled: boolean;
  aiTtsProvider: 'local' | 'openai' | 'google' | 'gemini';
  aiVoiceURI: string;
  aiOpenAiVoice: 'alloy' | 'echo' | 'fable' | 'onyx' | 'nova' | 'shimmer';
  aiGeminiVoice: 'Aoede' | 'Charon' | 'Fenrir' | 'Kore' | 'Puck';
  aiVoiceDistortion: boolean;
  aiVoiceAutoSend: boolean;
  
  idleFadeTime: number;
  idleFadeOpacity: number;
  
  compactMode: boolean;

  windowLaunchMode: 'fullscreen' | 'lastPosition';
  savedWindowPosition: { x: number; y: number } | null;
  savedWindowSize: { w: number; h: number } | null;

  shortcutToggleClickThrough: string;
  shortcutToggleSettings: string;

  // Custom Theme & Design Customizer
  overlayAccentColor: string;
  overlayBgColor: string;
  overlayOpacity: number;
  overlayCardRadius: number;
  overlayBackdropBlur: number;
  customCss: string;

  // Tactical Map Marker Templates
  mapTemplates: TacticalMapTemplate[];
  autoSelectMapTemplate: boolean;
}

export interface TacticalMapTemplate {
  id: string;
  mapId: string;
  name: string;
  createdAt: number;
  shapes: any[];
}

export const DEFAULT_SETTINGS: InterfaceSettings = {
  playerUsername: '',
  showHeader: true,
  showTelemetryHud: true,
  showStatsWidget: true,
  showChatWidget: true,
  showMapWidget: true,
  showObjectivesWidget: true,
  showAiCopilotWidget: false,

  hudBounds: { x: 20, y: 20, w: 500, h: 220 },
  statsBounds: { x: 540, y: 20, w: 400, h: 140 },
  chatBounds: { x: 20, y: 550, w: 400, h: 300 },
  objectivesBounds: { x: 20, y: 260, w: 250, h: 270 },
  mapBounds: { x: 540, y: 180, w: 400, h: 400 },
  aiCopilotBounds: { x: 20, y: 20, w: 400, h: 500 },

  showSpeed: true,
  showAltitude: true,
  showGForce: true,
  showEngineRpm: true,
  showPitchRoll: true,
  showAutoTranslation: true,
  targetLanguage: 'EN',
  ignoreSameLanguage: true,
  distanceUnit: 'km',
  mapWindowMode: 'draggable',
  aiApiProvider: 'openai',
  aiApiKey: '',
  aiModel: 'gpt-4o-mini',
  aiCustomEndpoint: 'http://localhost:11434/v1',
  aiTtsEnabled: true,
  aiTtsProvider: 'local',
  aiVoiceURI: '',
  aiOpenAiVoice: 'onyx',
  aiGeminiVoice: 'Puck',
  aiVoiceDistortion: true,
  aiVoiceAutoSend: true,
  idleFadeTime: 15,
  idleFadeOpacity: 0.33,
  compactMode: false,

  windowLaunchMode: 'fullscreen',
  savedWindowPosition: null,
  savedWindowSize: null,

  shortcutToggleClickThrough: 'Ctrl+Shift+X',
  shortcutToggleSettings: 'Ctrl+Shift+S',

  overlayAccentColor: '#38bdf8',
  overlayBgColor: '#121826',
  overlayOpacity: 0.72,
  overlayCardRadius: 16,
  overlayBackdropBlur: 14,
  customCss: '',

  mapTemplates: [],
  autoSelectMapTemplate: true
};

export const SUPPORTED_LANGUAGES = [
  { code: 'EN', name: 'English 🇬🇧' },
  { code: 'DE', name: 'German 🇩🇪' },
  { code: 'ES', name: 'Spanish 🇪🇸' },
  { code: 'FR', name: 'French 🇫🇷' },
  { code: 'PL', name: 'Polish 🇵🇱' },
  { code: 'PT', name: 'Portuguese 🇵🇹' },
  { code: 'RU', name: 'Russian 🇷🇺' },
  { code: 'ZH', name: 'Chinese 🇨🇳' }
];
