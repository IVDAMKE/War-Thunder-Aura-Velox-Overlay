// Dynamic Multi-Language Chat Translation Engine for War Thunder Desktop Assistant

const DICTIONARY: Record<string, Record<string, string>> = {
  // Common Russian words & combat calls
  "игра": { EN: "Game / Match", DE: "Spiel", ES: "Juego", FR: "Jeu", PL: "Gra", PT: "Jogo", RU: "Игра", ZH: "游戏" },
  "играть": { EN: "Play", DE: "Spielen", ES: "Jugar", FR: "Jouer", PL: "Grać", PT: "Jogar", RU: "Играть", ZH: "玩" },
  "бой": { EN: "Battle / Combat", DE: "Schlacht", ES: "Batalla", FR: "Bataille", PL: "Bitwa", PT: "Batalha", RU: "Бой", ZH: "战斗" },
  "враг": { EN: "Enemy", DE: "Feind", ES: "Enemigo", FR: "Ennemi", PL: "Wróg", PT: "Inimigo", RU: "Враг", ZH: "敌人" },
  "противник": { EN: "Enemy / Adversary", DE: "Feind", ES: "Enemigo", FR: "Ennemi", PL: "Przeciwnik", PT: "Inimigo", RU: "Противник", ZH: "对手" },
  "союзник": { EN: "Ally / Teammate", DE: "Verbündeter", ES: "Aliado", FR: "Allié", PL: "Sojusznik", PT: "Aliado", RU: "Союзник", ZH: "盟友" },
  "самолет": { EN: "Plane", DE: "Flugzeug", ES: "Avión", FR: "Avion", PL: "Samolot", PT: "Avião", RU: "Самолет", ZH: "飞机" },
  "вертолет": { EN: "Helicopter", DE: "Hubschrauber", ES: "Helicóptero", FR: "Hélicoptère", PL: "Helikopter", PT: "Helicóptero", RU: "Вертолет", ZH: "直升机" },
  "танк": { EN: "Tank", DE: "Panzer", ES: "Tanque", FR: "Char", PL: "Czołg", PT: "Tanque", RU: "Танк", ZH: "坦克" },
  "зенитка": { EN: "SPAA / Anti-Air", DE: "Flak", ES: "Antiaéreo", FR: "DCA", PL: "Plot / SPAA", PT: "Antiaérea", RU: "Зенитка", ZH: "防空炮" },
  "пво": { EN: "Anti-Air / Air Defense", DE: "Flugabwehr", ES: "Defensa Aérea", FR: "Défense Aérienne", PL: "Obrona Powietrzna", PT: "Defesa Aérea", RU: "ПВО", ZH: "防空" },
  "база": { EN: "Base", DE: "Basis", ES: "Base", FR: "Base", PL: "Baza", PT: "Base", RU: "База", ZH: "基地" },
  "точка": { EN: "Point / Cap", DE: "Punkt", ES: "Punto", FR: "Point", PL: "Punkt", PT: "Ponto", RU: "Точка", ZH: "据点" },
  "помощь": { EN: "Help", DE: "Hilfe", ES: "Ayuda", FR: "Aide", PL: "Pomoc", PT: "Ajuda", RU: "Помощь", ZH: "帮助" },
  "атака": { EN: "Attack", DE: "Angriff", ES: "Ataque", FR: "Attaque", PL: "Atak", PT: "Ataque", RU: "Атака", ZH: "攻击" },
  "защита": { EN: "Defense", DE: "Verteidigung", ES: "Defensa", FR: "Défense", PL: "Obrona", PT: "Defesa", RU: "Защита", ZH: "防御" },
  "внимание": { EN: "Attention", DE: "Achtung", ES: "Atención", FR: "Attention", PL: "Uwaga", PT: "Atenção", RU: "Внимание", ZH: "注意" },
  "карта": { EN: "Map", DE: "Karte", ES: "Mapa", FR: "Carte", PL: "Mapa", PT: "Mapa", RU: "Карта", ZH: "地图" },
  "квадрат": { EN: "Square / Grid", DE: "Planquadrat", ES: "Cuadrícula", FR: "Secteur", PL: "Kwadrat", PT: "Quadrado", RU: "Квадрат", ZH: "方格" },
  "да": { EN: "Yes", DE: "Ja", ES: "Sí", FR: "Oui", PL: "Tak", PT: "Sim", RU: "Да", ZH: "是" },
  "нет": { EN: "No", DE: "Nein", ES: "No", FR: "Non", PL: "Nie", PT: "Não", RU: "Нет", ZH: "不" },
  "хорошо": { EN: "Good / OK", DE: "Gut", ES: "Bien", FR: "Bien", PL: "Dobrze", PT: "Bem", RU: "Хорошо", ZH: "好" },
  "понял": { EN: "Roger / Copy", DE: "Verstanden", ES: "Copiado", FR: "Reçu", PL: "Zrozumiałem", PT: "Entendido", RU: "Понял", ZH: "收到" },
  "принял": { EN: "Copy that", DE: "Empfangen", ES: "Enterado", FR: "Bien reçu", PL: "Przyjąłem", PT: "Recebido", RU: "Принял", ZH: "明白" },
  "привет": { EN: "Hello", DE: "Hallo", ES: "Hola", FR: "Salut", PL: "Cześć", PT: "Olá", RU: "Привет", ZH: "你好" },
  "спасибо": { EN: "Thank you", DE: "Danke", ES: "Gracias", FR: "Merci", PL: "Dziękuję", PT: "Obrigado", RU: "Спасибо", ZH: "谢谢" },
  "извини": { EN: "Sorry", DE: "Entschuldigung", ES: "Perdón", FR: "Pardon", PL: "Przepraszam", PT: "Desculpe", RU: "Извини", ZH: "抱歉" },
  "внимание на карту!": { EN: "Attention to the map!", DE: "Achtung auf die Karte!", ES: "¡Atención al mapa!", FR: "Attention à la carte!", PL: "Uwaga na mapę!", PT: "Atenção ao mapa!", RU: "Внимание на карту!", ZH: "注意地图！" },
  "атакуйте точку": { EN: "Attack point", DE: "Greift den Punkt an", ES: "Atacad el punto", FR: "Attaquez le point", PL: "Atakować punkt", PT: "Ataquem o ponto", RU: "Атакуйте точку", ZH: "攻击目标点" },
  "защищайте точку": { EN: "Defend point", DE: "Verteidigt den Punkt", ES: "Defended el punto", FR: "Défendez le point", PL: "Bronić punktu", PT: "Defendam o ponto", RU: "Защищайте точку", ZH: "防守目标点" }
};

// In-Memory async translation cache
const translationCache: Record<string, string> = {};
const pendingRequests: Set<string> = new Set();
let updateCallback: (() => void) | null = null;

export function setTranslationUpdateCallback(cb: () => void) {
  updateCallback = cb;
}

export function isSameLanguage(originalText: string, targetLang: string = 'EN', translation: string = ''): boolean {
  if (!originalText || !originalText.trim()) return true;

  const lang = (targetLang || 'EN').toUpperCase();
  const trimmed = originalText.trim();
  const lower = trimmed.toLowerCase();

  // If translation matches original text (case-insensitive)
  if (translation && translation.toLowerCase().trim() === lower) {
    return true;
  }

  // Language script detection
  const isCyrillic = /[\u0400-\u04FF]/.test(trimmed);
  const isChinese = /[\u4E00-\u9FFF]/.test(trimmed);
  const isLatin = /^[a-z0-9\s!.,?'-]+$/i.test(trimmed);

  // Target is Russian & text is Cyrillic
  if (lang === 'RU' && isCyrillic) return true;

  // Target is Chinese & text is Chinese
  if (lang === 'ZH' && isChinese) return true;

  // Target is English & text is plain Latin without Cyrillic/Chinese
  if (lang === 'EN' && isLatin && !isCyrillic && !isChinese) return true;

  // Fallback match check
  if (translation === `[${lang}]: ${trimmed}`) return true;

  return false;
}

export function getTranslation(originalText: string, targetLang: string = 'EN'): string {
  if (!originalText || !originalText.trim()) return '';

  const lang = targetLang || 'EN';
  const trimmed = originalText.trim();
  const cacheKey = `${lang}:${trimmed}`;

  // Check async online translation cache first
  if (translationCache[cacheKey]) {
    return translationCache[cacheKey];
  }

  const lower = trimmed.toLowerCase();

  // 1. Check exact phrase dictionary match
  if (DICTIONARY[lower] && DICTIONARY[lower][lang]) {
    return DICTIONARY[lower][lang];
  }

  // 2. Word-by-word token replacement
  const words = trimmed.split(/(\s+)/);
  let hasTranslation = false;
  let translatedWords = words.map(word => {
    const clean = word.toLowerCase().replace(/[^a-zа-я0-9]/gi, '');
    if (DICTIONARY[clean] && DICTIONARY[clean][lang]) {
      hasTranslation = true;
      const match = DICTIONARY[clean][lang];
      if (word.length > 0 && word[0] === word[0].toUpperCase()) {
        return match.charAt(0).toUpperCase() + match.slice(1);
      }
      return match;
    }
    return word;
  });

  if (hasTranslation) {
    return translatedWords.join('');
  }

  // 3. Trigger background online translation fetch (MyMemory API) if not already pending
  fetchOnlineTranslation(trimmed, lang);

  // Return best immediate fallback while online API fetches
  return `[${lang}]: ${trimmed}`;
}

async function fetchOnlineTranslation(text: string, targetLang: string) {
  const cacheKey = `${targetLang}:${text}`;
  if (pendingRequests.has(cacheKey)) return;
  pendingRequests.add(cacheKey);

  try {
    const url = `https://api.mymemory.translated.net/get?q=${encodeURIComponent(text)}&langpair=autodetect|${targetLang.toLowerCase()}`;
    const res = await fetch(url);
    if (res.ok) {
      const data = await res.json();
      if (data?.responseData?.translatedText) {
        let result = data.responseData.translatedText;
        result = result.replace(/&#39;/g, "'").replace(/&quot;/g, '"');
        translationCache[cacheKey] = result;
        if (updateCallback) {
          updateCallback();
        }
      }
    }
  } catch (err) {
    console.warn('Online translation API fetch failed:', err);
  } finally {
    pendingRequests.delete(cacheKey);
  }
}
