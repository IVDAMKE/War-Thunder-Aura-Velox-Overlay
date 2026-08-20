<script lang="ts">
  import type { InterfaceSettings, TacticalMapTemplate } from '$lib/types/settings';
  import type { TranslatedChatMessage } from '$lib/types/telemetry';

  let { 
    settings,
    chatLog = []
  }: { 
    settings: InterfaceSettings;
    chatLog?: TranslatedChatMessage[];
  } = $props();

  let canvas: HTMLCanvasElement;
  let ctx: CanvasRenderingContext2D;

  let mapImage = new Image();
  let mapLoaded = $state(false);
  
  let mapInfo: any = null;
  let mapObjects: any[] = [];
  
  let zoom = $state(1);
  let panX = $state(0);
  let panY = $state(0);

  // --- MAP TEMPLATES & AUTO REFRESH STATE ---
  function getMapIdentifier(info: any): string | null {
    if (!info) return null;
    if (info.map_name) return info.map_name;
    if (info.map_min && info.map_max && info.grid_zero) {
      return `${info.map_min[0]}_${info.map_min[1]}_${info.map_max[0]}_${info.map_max[1]}_${info.grid_zero[0]}_${info.grid_zero[1]}`;
    }
    return 'default_map';
  }

  let currentMapId = $state<string | null>(null);
  let activeTemplateId = $state<string>('none');
  let showSaveTemplateModal = $state(false);
  let newTemplateName = $state('');
  let showTemplateMenu = $state(false);

  let currentMapTemplates = $derived(
    settings.mapTemplates?.filter(t => t.mapId === (currentMapId || 'default_map')) || []
  );

  let currentMapName = $derived(
    mapInfo?.map_name || (currentMapId ? `Map (${currentMapId})` : 'Tactical Map')
  );

  let activeTemplateName = $derived(
    activeTemplateId === 'none' 
      ? 'No Template' 
      : (settings.mapTemplates?.find(t => t.id === activeTemplateId)?.name || 'No Template')
  );

  // Automatic Map Change & Refresh & Auto-Template Select Effect
  $effect(() => {
    if (mapInfo) {
      const newMapId = getMapIdentifier(mapInfo);
      if (newMapId && newMapId !== currentMapId) {
        currentMapId = newMapId;
        mapCacheBuster = Date.now();
        zoom = 1;
        panX = 0;
        panY = 0;

        // Auto-select template if enabled
        if (settings.autoSelectMapTemplate) {
          const available = settings.mapTemplates?.filter(t => t.mapId === currentMapId) || [];
          if (available.length > 0) {
            const firstTpl = available[0];
            activeTemplateId = firstTpl.id;
            shapes = JSON.parse(JSON.stringify(firstTpl.shapes));
          } else {
            activeTemplateId = 'none';
          }
        }
      }
    } else {
      currentMapId = null;
    }
  });

  function loadTemplate(tplId: string) {
    activeTemplateId = tplId;
    if (tplId === 'none') {
      shapes = [];
      return;
    }
    const tpl = settings.mapTemplates?.find(t => t.id === tplId);
    if (tpl) {
      shapes = JSON.parse(JSON.stringify(tpl.shapes));
    }
  }

  function handleSaveTemplate() {
    if (!newTemplateName.trim()) return;
    const mapKey = currentMapId || 'default_map';
    const newTpl: TacticalMapTemplate = {
      id: 'tpl_' + Date.now(),
      mapId: mapKey,
      name: newTemplateName.trim(),
      createdAt: Date.now(),
      shapes: JSON.parse(JSON.stringify(shapes))
    };

    settings.mapTemplates = [...(settings.mapTemplates || []), newTpl];
    activeTemplateId = newTpl.id;
    showSaveTemplateModal = false;
    newTemplateName = '';
  }

  function deleteCurrentTemplate() {
    if (activeTemplateId === 'none') return;
    settings.mapTemplates = (settings.mapTemplates || []).filter(t => t.id !== activeTemplateId);
    activeTemplateId = 'none';
    shapes = [];
  }

  // --- DRAWING TYPES & STATE ---
  type Point = { x: number; y: number };
  type ShapeBase = { color: string; weight: number };
  type LineShape = ShapeBase & { type: 'line', p1: Point, p2: Point };
  type CircleShape = ShapeBase & { type: 'circle', center: Point, edge: Point, radius: number };
  type PathShape = ShapeBase & { type: 'path', points: Point[] };
  type PoiShape = ShapeBase & { type: 'poi', pos: Point, index: number | string };
  type Shape = LineShape | CircleShape | PathShape | PoiShape;
  
  type Tool = 'pan' | 'line' | 'circle' | 'path' | 'poi' | 'eraser';

  let activeTool = $state<Tool>('pan');
  let selectedColor = $state('#FFFF00');
  let selectedWeight = $state(2);
  
  let shapes = $state<Shape[]>([]);
  let currentShape = $state<Shape | null>(null);
  let cursorMapPos = $state<Point | null>(null);

  function cycleColor() {
    const idx = COLORS.findIndex(c => c.id === selectedColor);
    selectedColor = COLORS[(idx + 1) % COLORS.length].id;
  }

  function cycleWeight() {
    const weights = [2, 5, 8];
    const idx = weights.indexOf(selectedWeight);
    selectedWeight = weights[(idx + 1) % weights.length];
  }

  const COLORS = [
    { id: '#FFFF00', label: 'Yellow' },
    { id: '#FF0000', label: 'Red' },
    { id: '#00AAFF', label: 'Blue' },
    { id: '#00FF00', label: 'Green' },
    { id: '#FFFFFF', label: 'White' },
    { id: '#000000', label: 'Black' }
  ];

  // Auto-commit paths when tool changes
  $effect(() => {
    if (activeTool !== 'path' && currentShape?.type === 'path') {
      commitPath();
    }
  });

  function commitPath() {
    if (currentShape?.type === 'path' && currentShape.points.length > 1) {
      shapes = [...shapes, currentShape];
    }
    currentShape = null;
  }

  // --- POLLING LOGIC ---
  let mapCacheBuster = $state(Date.now());
  let autoRefreshStage = 0;

  $effect(() => {
    let active = true;
    mapImage.src = `http://127.0.0.1:8111/map.img?t=${mapCacheBuster}`;
    mapImage.onload = () => { mapLoaded = true; };
    mapImage.onerror = () => { 
      console.warn('Failed to load map.img. Rendering empty background.');
      mapLoaded = true; 
    };

    const poll = async () => {
      try {
        const [infoRes, objRes] = await Promise.all([
          fetch('http://127.0.0.1:8111/map_info.json'),
          fetch('http://127.0.0.1:8111/map_obj.json')
        ]);
        if (infoRes.ok && objRes.ok) {
          mapInfo = await infoRes.json();
          mapObjects = await objRes.json();
          
          const isPlayer = (o: any) => o.type === 'player' || o.icon === 'Player' || o.color === '#ffff00' || o.color === '#feff00' || o.color === '#ffaa00';
          if (autoRefreshStage === 0 && mapObjects.some(isPlayer)) {
            autoRefreshStage = 1;
            mapCacheBuster = Date.now();
            setTimeout(() => { mapCacheBuster = Date.now(); }, 5000);
            setTimeout(() => { mapCacheBuster = Date.now(); }, 10000);
          }
        }
      } catch (e) {}
      if (active) setTimeout(poll, 200);
    };
    poll();
    return () => { active = false; };
  });

  // --- CHAT PINGS LOGIC ---
  let processedChats = new Set<number>();
  
  $effect(() => {
    if (chatLog.length === 0 || !mapInfo) return;
    const latest = chatLog[chatLog.length - 1];
    
    if (!processedChats.has(latest.id)) {
      processedChats.add(latest.id);
      
      const match = latest.original.match(/\[([A-Z])([1-9]|10).*?\]/i);
      if (match) {
        const letterStr = match[1].toUpperCase();
        const numStr = match[2];
        const row = letterStr.charCodeAt(0) - 65; // A=0 (Row/Y-axis)
        const col = parseInt(numStr) - 1; // 1=0 (Column/X-axis)
        
        let pctX, pctY;
        
        if (mapInfo.grid_steps && mapInfo.map_max && mapInfo.map_min && mapInfo.grid_zero && mapInfo.grid_size) {
           const mapWidth = mapInfo.map_max[0] - mapInfo.map_min[0];
           const mapHeight = mapInfo.map_max[1] - mapInfo.map_min[1];
           
           const metersX = mapInfo.grid_zero[0] + (col + 0.5) * mapInfo.grid_steps[0];
           const metersY = mapInfo.grid_zero[1] - (row + 0.5) * mapInfo.grid_steps[1];
           
           pctX = (metersX - mapInfo.map_min[0]) / mapWidth;
           pctY = (mapInfo.map_max[1] - metersY) / mapHeight;
        } else {
           pctX = (col + 0.5) / 10;
           pctY = (row + 0.5) / 10;
        }
        
        const canvasSize = 1024;
        const p = { x: pctX * canvasSize, y: pctY * canvasSize };
        
        const newShape: Shape = { 
          type: 'poi', 
          pos: p, 
          index: 'ALLY', 
          color: '#00e5ff', 
          weight: 1 
        };
        
        shapes = [...shapes, newShape];
        
        setTimeout(() => {
          shapes = shapes.filter(s => s !== newShape);
        }, 5000);
      }
    }
  });

  // --- RENDERING LOGIC ---
  function getMapDistanceMeters(p1: Point, p2: Point) {
    if (!mapInfo) return 0;
    const dx = p2.x - p1.x;
    const dy = p2.y - p1.y;
    const pixelDist = Math.sqrt(dx*dx + dy*dy);
    const mapWidthMeters = (mapInfo.map_max?.[0] || 32768) - (mapInfo.map_min?.[0] || -32768);
    const metersPerPixel = mapWidthMeters / 1024; // Canvas internal width is 1024
    return pixelDist * metersPerPixel;
  }
  
  function formatDistance(meters: number) {
    if (settings.distanceUnit === 'nm') {
      return (meters / 1852).toFixed(2) + ' nm';
    }
    return (meters / 1000).toFixed(2) + ' km';
  }

  function drawTextWithBackground(ctx: CanvasRenderingContext2D, text: string, x: number, y: number, color: string) {
    ctx.font = 'bold 16px sans-serif';
    const metrics = ctx.measureText(text);
    const width = metrics.width;
    const height = 16;
    
    // Reverse scale for text so it stays constant size regardless of zoom
    ctx.save();
    ctx.translate(x, y);
    ctx.scale(1/zoom, 1/zoom);
    
    ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
    ctx.beginPath();
    ctx.roundRect(-width/2 - 6, -height - 4, width + 12, height + 8, 4);
    ctx.fill();
    
    ctx.fillStyle = color;
    ctx.textAlign = 'center';
    ctx.fillText(text, 0, -2);
    
    ctx.restore();
  }

  function renderShape(ctx: CanvasRenderingContext2D, shape: Shape, inProgress = false) {
    ctx.strokeStyle = shape.color;
    ctx.fillStyle = shape.color;
    ctx.lineWidth = shape.weight / zoom;
    
    if (shape.type === 'line') {
      ctx.beginPath();
      ctx.moveTo(shape.p1.x, shape.p1.y);
      ctx.lineTo(shape.p2.x, shape.p2.y);
      ctx.stroke();
      
      const dist = getMapDistanceMeters(shape.p1, shape.p2);
      const midX = (shape.p1.x + shape.p2.x) / 2;
      const midY = (shape.p1.y + shape.p2.y) / 2;
      drawTextWithBackground(ctx, formatDistance(dist), midX, midY, shape.color);
      
    } else if (shape.type === 'circle') {
      ctx.beginPath();
      ctx.arc(shape.center.x, shape.center.y, shape.radius, 0, Math.PI * 2);
      ctx.stroke();
      
      // Draw crosshair at center
      const s = 5 / zoom;
      ctx.beginPath();
      ctx.moveTo(shape.center.x - s, shape.center.y);
      ctx.lineTo(shape.center.x + s, shape.center.y);
      ctx.moveTo(shape.center.x, shape.center.y - s);
      ctx.lineTo(shape.center.x, shape.center.y + s);
      ctx.stroke();
      
      const dist = getMapDistanceMeters(shape.center, shape.edge);
      drawTextWithBackground(ctx, formatDistance(dist), shape.edge.x, shape.edge.y, shape.color);
      
    } else if (shape.type === 'path') {
      if (shape.points.length === 0) return;
      
      ctx.beginPath();
      ctx.moveTo(shape.points[0].x, shape.points[0].y);
      let totalDist = 0;
      
      for (let i = 1; i < shape.points.length; i++) {
        ctx.lineTo(shape.points[i].x, shape.points[i].y);
        totalDist += getMapDistanceMeters(shape.points[i-1], shape.points[i]);
      }
      
      // Draw live segment to cursor if drawing
      if (inProgress && cursorMapPos) {
        ctx.lineTo(cursorMapPos.x, cursorMapPos.y);
        totalDist += getMapDistanceMeters(shape.points[shape.points.length - 1], cursorMapPos);
      }
      ctx.stroke();
      
      // Draw nodes
      for (const p of shape.points) {
        ctx.beginPath();
        ctx.arc(p.x, p.y, 4 / zoom, 0, Math.PI * 2);
        ctx.fill();
      }
      
      // Draw distance badge at the end
      const lastPoint = inProgress && cursorMapPos ? cursorMapPos : shape.points[shape.points.length - 1];
      drawTextWithBackground(ctx, formatDistance(totalDist), lastPoint.x, lastPoint.y, shape.color);
    } else if (shape.type === 'poi') {
      const radius = 12;
      
      // Shadow / glow
      ctx.beginPath();
      ctx.arc(shape.pos.x, shape.pos.y, (radius + 2) / zoom, 0, Math.PI * 2);
      ctx.fillStyle = 'rgba(0,0,0,0.5)';
      ctx.fill();

      // Draw pin circle
      ctx.beginPath();
      ctx.arc(shape.pos.x, shape.pos.y, radius / zoom, 0, Math.PI * 2);
      ctx.fillStyle = shape.color;
      ctx.fill();
      
      // Draw border
      ctx.lineWidth = 2 / zoom;
      ctx.strokeStyle = '#000000';
      ctx.stroke();

      // Draw text
      ctx.save();
      ctx.translate(shape.pos.x, shape.pos.y);
      ctx.scale(1/zoom, 1/zoom);
      
      // Calculate perceptive luminance to choose black or white text
      const hex = shape.color.replace('#', '');
      const r = parseInt(hex.substring(0, 2), 16) || 255;
      const g = parseInt(hex.substring(2, 4), 16) || 255;
      const b = parseInt(hex.substring(4, 6), 16) || 255;
      const luma = 0.2126 * r + 0.7152 * g + 0.0722 * b;
      
      ctx.fillStyle = luma < 128 ? '#FFFFFF' : '#000000';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.font = 'bold 15px sans-serif';
      ctx.fillText(shape.index.toString(), 0, 1);
      ctx.restore();
    }
  }

  $effect(() => {
    if (!canvas || !mapLoaded) return;
    ctx = canvas.getContext('2d')!;
    
    let animationFrameId: number;
    const render = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.save();
      ctx.translate(panX, panY);
      ctx.scale(zoom, zoom);
      
      try {
        if (mapImage.complete && mapImage.naturalWidth > 0) {
          ctx.drawImage(mapImage, 0, 0, canvas.width, canvas.height);
          
          if (mapInfo) {
            ctx.strokeStyle = 'rgba(255, 255, 255, 0.2)';
            ctx.lineWidth = 1 / zoom;
            ctx.fillStyle = 'rgba(255, 255, 255, 0.4)';
            ctx.font = `${14 / zoom}px sans-serif`;
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';

            if (mapInfo.grid_steps && mapInfo.map_max && mapInfo.map_min && mapInfo.grid_zero && mapInfo.grid_size) {
              const numGridsX = Math.round(mapInfo.grid_size[0] / mapInfo.grid_steps[0]);
              const numGridsY = Math.round(mapInfo.grid_size[1] / mapInfo.grid_steps[1]);
              
              const mapWidth = mapInfo.map_max[0] - mapInfo.map_min[0];
              const mapHeight = mapInfo.map_max[1] - mapInfo.map_min[1];
              
              const startX = ((mapInfo.grid_zero[0] - mapInfo.map_min[0]) / mapWidth) * canvas.width;
              const startY = ((mapInfo.map_max[1] - mapInfo.grid_zero[1]) / mapHeight) * canvas.height;
              
              const stepX = (mapInfo.grid_steps[0] / mapWidth) * canvas.width;
              const stepY = (mapInfo.grid_steps[1] / mapHeight) * canvas.height;
              
              for (let i = 0; i <= numGridsX; i++) {
                const x = startX + i * stepX;
                ctx.beginPath();
                ctx.moveTo(x, startY);
                ctx.lineTo(x, startY + numGridsY * stepY);
                ctx.stroke();
                
                if (i < numGridsX) {
                  ctx.fillText((i + 1).toString(), x + stepX / 2, startY + 20 / zoom);
                }
              }
              
              for (let i = 0; i <= numGridsY; i++) {
                const y = startY + i * stepY;
                ctx.beginPath();
                ctx.moveTo(startX, y);
                ctx.lineTo(startX + numGridsX * stepX, y);
                ctx.stroke();
                
                if (i < numGridsY) {
                  ctx.fillText(String.fromCharCode(65 + i), startX + 20 / zoom, y + stepY / 2);
                }
              }
            } else {
              const numGridsX = 10;
              const numGridsY = 10;
              const cellWidth = canvas.width / numGridsX;
              const cellHeight = canvas.height / numGridsY;
              
              for (let i = 1; i < numGridsX; i++) {
                ctx.beginPath();
                ctx.moveTo(i * cellWidth, 0);
                ctx.lineTo(i * cellWidth, canvas.height);
                ctx.stroke();
              }
              for (let i = 0; i < numGridsX; i++) {
                ctx.fillText((i + 1).toString(), (i + 0.5) * cellWidth, 20 / zoom);
              }
              for (let i = 1; i < numGridsY; i++) {
                ctx.beginPath();
                ctx.moveTo(0, i * cellHeight);
                ctx.lineTo(canvas.width, i * cellHeight);
                ctx.stroke();
              }
              for (let i = 0; i < numGridsY; i++) {
                ctx.fillText(String.fromCharCode(65 + i), 20 / zoom, (i + 0.5) * cellHeight);
              }
            }
          }
        }
      } catch (err) {}

      // Draw game objects
      for (const obj of mapObjects) {
         const px = obj.x * canvas.width;
         const py = obj.y * canvas.height;
         
          const isPlayer = obj.type === 'player' || obj.icon === 'Player' || obj.color === '#ffff00' || obj.color === '#feff00' || obj.color === '#ffaa00';
          if (isPlayer) {
           ctx.fillStyle = obj.color || '#ffff00';
           ctx.strokeStyle = '#000';
           ctx.lineWidth = 2 / zoom;
           
           let angle = -Math.PI / 2; // Default pointing UP
           if (obj.dx !== undefined && obj.dy !== undefined) {
             angle = Math.atan2(obj.dy, obj.dx);
           } else if (obj.dir && Array.isArray(obj.dir)) {
             angle = Math.atan2(obj.dir[1], obj.dir[0]);
           } else if (typeof obj.dir === 'number') {
             angle = obj.dir;
           }
           
           const size = 12 / zoom;
           
           ctx.beginPath();
           ctx.moveTo(px + Math.cos(angle) * size, py + Math.sin(angle) * size); // tip
           ctx.lineTo(px + Math.cos(angle + 2.6) * size, py + Math.sin(angle + 2.6) * size); // back left
           ctx.lineTo(px + Math.cos(angle - 2.6) * size, py + Math.sin(angle - 2.6) * size); // back right
           ctx.closePath();
           ctx.fill();
           ctx.stroke();
         } else {
           // Other objects (e.g. airfields, targets)
           ctx.fillStyle = obj.color || '#ff0000';
           ctx.beginPath();
           ctx.arc(px, py, 6 / zoom, 0, Math.PI * 2);
           ctx.fill();
         }
      }

      // Draw all committed shapes
      for (const shape of shapes) {
        renderShape(ctx, shape);
      }
      
      // Draw current in-progress shape
      if (currentShape) {
        renderShape(ctx, currentShape, true);
      }

      ctx.restore();
      animationFrameId = requestAnimationFrame(render);
    };
    render();
    return () => cancelAnimationFrame(animationFrameId);
  });

  // --- INTERACTION HANDLERS ---
  let isDragging = false;
  let lastX = 0;
  let lastY = 0;

  function getMapCoords(e: PointerEvent): Point {
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    const x = (e.clientX - rect.left) * scaleX;
    const y = (e.clientY - rect.top) * scaleY;
    return { x: (x - panX) / zoom, y: (y - panY) / zoom };
  }

  function handleWheel(e: WheelEvent) {
    e.preventDefault();
    const zoomFactor = 1.1;
    const oldZoom = zoom;
    if (e.deltaY < 0) zoom *= zoomFactor;
    else zoom /= zoomFactor;
    
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    const mouseX = (e.clientX - rect.left) * scaleX;
    const mouseY = (e.clientY - rect.top) * scaleY;
    
    panX = mouseX - (mouseX - panX) * (zoom / oldZoom);
    panY = mouseY - (mouseY - panY) * (zoom / oldZoom);
  }

  function hitTest(p: Point, shape: Shape): boolean {
    const threshold = 15 / zoom;
    if (shape.type === 'line') {
      // Distance from point to line segment
      const l2 = (shape.p1.x - shape.p2.x)**2 + (shape.p1.y - shape.p2.y)**2;
      if (l2 == 0) return Math.hypot(p.x - shape.p1.x, p.y - shape.p1.y) < threshold;
      let t = ((p.x - shape.p1.x) * (shape.p2.x - shape.p1.x) + (p.y - shape.p1.y) * (shape.p2.y - shape.p1.y)) / l2;
      t = Math.max(0, Math.min(1, t));
      const proj = { x: shape.p1.x + t * (shape.p2.x - shape.p1.x), y: shape.p1.y + t * (shape.p2.y - shape.p1.y) };
      return Math.hypot(p.x - proj.x, p.y - proj.y) < threshold;
    }
    if (shape.type === 'circle') {
      // Distance from center must be close to radius
      const d = Math.hypot(p.x - shape.center.x, p.y - shape.center.y);
      return Math.abs(d - shape.radius) < threshold;
    }
    if (shape.type === 'poi') {
      const d = Math.hypot(p.x - shape.pos.x, p.y - shape.pos.y);
      return d < (15 / zoom);
    }
    if (shape.type === 'path') {
      for (let i = 0; i < shape.points.length - 1; i++) {
        const p1 = shape.points[i];
        const p2 = shape.points[i+1];
        const l2 = (p1.x - p2.x)**2 + (p1.y - p2.y)**2;
        if (l2 == 0) continue;
        let t = ((p.x - p1.x) * (p2.x - p1.x) + (p.y - p1.y) * (p2.y - p1.y)) / l2;
        t = Math.max(0, Math.min(1, t));
        const proj = { x: p1.x + t * (p2.x - p1.x), y: p1.y + t * (p2.y - p1.y) };
        if (Math.hypot(p.x - proj.x, p.y - proj.y) < threshold) return true;
      }
    }
    return false;
  }

  function handlePointerDown(e: PointerEvent) {
    if (e.button === 1) { // Middle click for panning
      isDragging = true;
      lastX = e.clientX;
      lastY = e.clientY;
      canvas.setPointerCapture(e.pointerId);
      return;
    }

    if (e.button === 2) { // Right click
      if (activeTool === 'path' && currentShape?.type === 'path') {
        commitPath();
      } else {
        const p = getMapCoords(e);
        for (let i = shapes.length - 1; i >= 0; i--) {
          if (hitTest(p, shapes[i])) {
            const deletedType = shapes[i].type;
            shapes = shapes.filter((_, idx) => idx !== i);
            if (deletedType === 'poi') {
              let poiIndex = 1;
              shapes = shapes.map(s => s.type === 'poi' ? { ...s, index: poiIndex++ } : s);
            }
            break;
          }
        }
      }
      return;
    }
    
    if (e.button !== 0) return; // Only left click below
    const p = getMapCoords(e);
    
    if (activeTool === 'pan') {
      isDragging = true;
      lastX = e.clientX;
      lastY = e.clientY;
      canvas.setPointerCapture(e.pointerId);
    } else if (activeTool === 'eraser') {
      // Find closest shape and delete
      for (let i = shapes.length - 1; i >= 0; i--) {
        if (hitTest(p, shapes[i])) {
          const deletedType = shapes[i].type;
          shapes = shapes.filter((_, idx) => idx !== i);
          
          if (deletedType === 'poi') {
            let poiIndex = 1;
            shapes = shapes.map(s => s.type === 'poi' ? { ...s, index: poiIndex++ } : s);
          }
          break; // delete one at a time
        }
      }
    } else if (activeTool === 'line') {
      currentShape = { type: 'line', p1: p, p2: p, color: selectedColor, weight: selectedWeight };
      canvas.setPointerCapture(e.pointerId);
    } else if (activeTool === 'circle') {
      currentShape = { type: 'circle', center: p, edge: p, radius: 0, color: selectedColor, weight: selectedWeight };
      canvas.setPointerCapture(e.pointerId);
    } else if (activeTool === 'path') {
      if (!currentShape || currentShape.type !== 'path') {
        currentShape = { type: 'path', points: [p], color: selectedColor, weight: selectedWeight };
      } else {
        currentShape.points = [...currentShape.points, p];
      }
    } else if (activeTool === 'poi') {
      const poiCount = shapes.filter(s => s.type === 'poi').length;
      shapes = [...shapes, { type: 'poi', pos: p, index: poiCount + 1, color: selectedColor, weight: selectedWeight }];
    }
  }

  function handlePointerMove(e: PointerEvent) {
    const p = getMapCoords(e);
    cursorMapPos = p;
    
    if (isDragging) {
      const rect = canvas.getBoundingClientRect();
      const scaleX = canvas.width / rect.width;
      const scaleY = canvas.height / rect.height;
      panX += (e.clientX - lastX) * scaleX;
      panY += (e.clientY - lastY) * scaleY;
      lastX = e.clientX;
      lastY = e.clientY;
    } else if (currentShape && (activeTool === 'line' || activeTool === 'circle')) {
      if (currentShape.type === 'line') {
        currentShape.p2 = p;
      } else if (currentShape.type === 'circle') {
        currentShape.edge = p;
        currentShape.radius = Math.hypot(p.x - currentShape.center.x, p.y - currentShape.center.y);
      }
    }
  }

  function handlePointerUp(e: PointerEvent) {
    if (e.button === 1 || e.button === 2) {
      isDragging = false;
      canvas.releasePointerCapture(e.pointerId);
      return;
    }

    if (activeTool === 'line' || activeTool === 'circle') {
      if (currentShape) {
        shapes = [...shapes, currentShape];
        currentShape = null;
      }
    }
    isDragging = false;
    canvas.releasePointerCapture(e.pointerId);
  }
</script>

<div class="map-container {settings.mapWindowMode} {settings.compactMode ? 'compact' : ''}">
  <div class="map-toolbar">
    <div class="toolbar-top">
      {#if !settings.compactMode}
        <div class="toolbar-title">TACTICAL MAP</div>
      {/if}
      
      <button class="refresh-btn" onclick={() => mapCacheBuster = Date.now()} title="Force Reload Map Texture">
        <span class="material-symbols-outlined">refresh</span>
      </button>
      
      <div class="tool-group tools">
        <button class:active={activeTool === 'pan'} onclick={() => activeTool = 'pan'} title="Pan Map">
          <span class="material-symbols-outlined">pan_tool</span>
        </button>
        <button class:active={activeTool === 'line'} onclick={() => activeTool = 'line'} title="Draw Line">
          <span class="material-symbols-outlined">show_chart</span>
        </button>
        <button class:active={activeTool === 'circle'} onclick={() => activeTool = 'circle'} title="Draw Circle">
          <span class="material-symbols-outlined">radio_button_unchecked</span>
        </button>
        <button class:active={activeTool === 'path'} onclick={() => activeTool = 'path'} title="Draw Path">
          <span class="material-symbols-outlined">gesture</span>
        </button>
        <button class:active={activeTool === 'poi'} onclick={() => activeTool = 'poi'} title="Add Waypoint">
          <span class="material-symbols-outlined">location_on</span>
        </button>
        <button class:active={activeTool === 'eraser'} onclick={() => activeTool = 'eraser'} title="Eraser">
          <span class="material-symbols-outlined">ink_eraser</span>
        </button>
      </div>
      
      {#if activeTool === 'path' && currentShape?.type === 'path' && currentShape.points.length > 0}
        <button class="commit-btn" onclick={commitPath} title="Finish Path">
          <span class="material-symbols-outlined">check_circle</span>
        </button>
      {/if}
      
      <button class="danger-btn" onclick={() => { shapes = []; currentShape = null; }} title="Clear All Markers">
        <span class="material-symbols-outlined">delete_forever</span>
      </button>
    </div>
    
    <div class="toolbar-bottom">
      {#if settings.compactMode}
        <div class="tool-group compact-inline">
          <button onclick={cycleWeight} title="Cycle Thickness">
            {selectedWeight === 2 ? '1x' : selectedWeight === 5 ? '2x' : '3x'}
          </button>
          <button 
            class="color-btn active" 
            style="background: {selectedColor};" 
            onclick={cycleColor}
            title="Cycle Color"
          ></button>
        </div>
      {:else}
        <div class="tool-group weights">
          <button class:active={selectedWeight === 2} onclick={() => selectedWeight = 2}>1x</button>
          <button class:active={selectedWeight === 5} onclick={() => selectedWeight = 5}>2x</button>
          <button class:active={selectedWeight === 8} onclick={() => selectedWeight = 8}>3x</button>
        </div>
        <div class="tool-group colors">
          {#each COLORS as c}
            <button 
              class="color-btn" 
              class:active={selectedColor === c.id} 
              style="background: {c.id};" 
              onclick={() => selectedColor = c.id}
              title={c.label}
            ></button>
          {/each}
        </div>
      {/if}

      <!-- Unified Split Button for Map Marker Templates -->
      <div class="template-controls">
        <div class="split-template-btn" class:active={showTemplateMenu}>
          <button
            class="split-save-part"
            onclick={() => { showSaveTemplateModal = true; newTemplateName = ''; }}
            title="Save current markers as a new template for this map"
          >
            <span class="material-symbols-outlined">save</span>
          </button>

          <div class="split-divider"></div>

          <button
            class="split-arrow-part"
            onclick={() => showTemplateMenu = !showTemplateMenu}
            title={activeTemplateId !== 'none' ? `Active Template: ${activeTemplateName}` : 'Select Map Template'}
          >
            <span class="material-symbols-outlined">arrow_drop_down</span>
          </button>
        </div>

        {#if showTemplateMenu}
          <div class="template-menu-popup" onmouseleave={() => showTemplateMenu = false}>
            <div
              class="template-menu-item"
              class:selected={activeTemplateId === 'none'}
              onclick={() => { loadTemplate('none'); showTemplateMenu = false; }}
              role="presentation"
            >
              <span class="material-symbols-outlined item-icon">block</span>
              <span>No Template</span>
            </div>

            {#if currentMapTemplates.length > 0}
              <div class="menu-divider"></div>
              {#each currentMapTemplates as tpl}
                <div
                  class="template-menu-item"
                  class:selected={activeTemplateId === tpl.id}
                  onclick={() => { loadTemplate(tpl.id); showTemplateMenu = false; }}
                  role="presentation"
                >
                  <span class="material-symbols-outlined item-icon">location_on</span>
                  <span class="item-name">{tpl.name}</span>
                  {#if activeTemplateId === tpl.id}
                    <button
                      class="item-delete-btn"
                      onclick={(e) => { e.stopPropagation(); deleteCurrentTemplate(); showTemplateMenu = false; }}
                      title="Delete Template"
                    >
                      <span class="material-symbols-outlined">delete</span>
                    </button>
                  {/if}
                </div>
              {/each}
            {/if}
          </div>
        {/if}
      </div>
    </div>
  </div>

  {#if showSaveTemplateModal}
    <div class="template-modal-backdrop" onclick={() => showSaveTemplateModal = false} role="presentation">
      <div class="template-modal-card" onclick={(e) => e.stopPropagation()} role="presentation">
        <h4>💾 Save Map Marker Template</h4>
        <p class="desc">Save current tactical markers for map: <strong>{currentMapName}</strong></p>
        <input
          type="text"
          bind:value={newTemplateName}
          placeholder="Template Name (e.g. Airfields & Choke Points)"
          class="text-input tpl-name-input"
          onkeydown={(e) => { if (e.key === 'Enter') handleSaveTemplate(); }}
        />
        <div class="tpl-modal-actions">
          <button class="cancel-btn" onclick={() => showSaveTemplateModal = false}>Cancel</button>
          <button class="save-btn" onclick={handleSaveTemplate} disabled={!newTemplateName.trim()}>Save Template</button>
        </div>
      </div>
    </div>
  {/if}
  
  <canvas 
    bind:this={canvas} 
    width="1024" 
    height="1024"
    onwheel={handleWheel}
    onpointerdown={handlePointerDown}
    onpointermove={handlePointerMove}
    onpointerup={handlePointerUp}
    onpointerleave={() => cursorMapPos = null}
    oncontextmenu={(e) => e.preventDefault()}
  ></canvas>
</div>

<style>
  .map-container {
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
    background: transparent;
    border: 1px solid var(--border-color);
    border-radius: var(--card-radius, 8px);
    overflow: hidden;
    pointer-events: auto;
  }

  .map-toolbar {
    display: flex;
    flex-direction: column;
    gap: 8px;
    background: var(--bg-card, rgba(15, 23, 42, 0.9));
    padding: 8px;
    border-bottom: 1px solid var(--border-color);
    z-index: 10;
  }
  
  .toolbar-top, .toolbar-bottom {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .map-container.compact .map-toolbar {
    position: absolute;
    bottom: 10px;
    right: 10px;
    background: transparent;
    border: none;
    padding: 0;
    gap: 4px;
    flex-direction: column;
    align-items: flex-end;
  }

  .map-container.compact .toolbar-top,
  .map-container.compact .toolbar-bottom {
    flex-direction: column;
    gap: 4px;
  }

  .map-container.compact .tool-group {
    flex-direction: column;
    align-items: center;
    background: rgba(0, 0, 0, 0.6);
    backdrop-filter: blur(4px);
  }

  .map-container.compact .tool-group.compact-inline {
    flex-direction: row;
    align-items: center;
  }

  .toolbar-title {
    font-weight: 700;
    color: var(--accent-color);
    margin-right: auto;
  }

  .tool-group {
    display: flex;
    gap: 4px;
    background: rgba(0, 0, 0, 0.4);
    padding: 4px;
    border-radius: 6px;
  }

  button {
    background: transparent;
    border: 1px solid rgba(255, 255, 255, 0.1);
    color: var(--text-color);
    padding: 4px 8px;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.9rem;
    transition: all 0.2s ease;
  }

  button:hover {
    background: rgba(255, 255, 255, 0.1);
  }

  button.active {
    background: var(--accent-color);
    color: #000;
    font-weight: bold;
    border-color: var(--accent-color);
  }
  
  .color-btn {
    width: 20px;
    height: 20px;
    border-radius: 50%;
    padding: 0;
    border: 2px solid transparent;
  }
  
  .color-btn.active {
    border-color: white;
    transform: scale(1.2);
  }
  
  .commit-btn {
    background: rgba(0, 255, 100, 0.2);
    border-color: rgba(0, 255, 100, 0.5);
    color: #aaffcc;
  }
  
  .commit-btn:hover {
    background: rgba(0, 255, 100, 0.4);
  }

  button.danger-btn {
    border-color: rgba(239, 68, 68, 0.5);
    color: #ef4444;
  }

  button.refresh-btn {
    border-color: rgba(59, 130, 246, 0.5);
    background: rgba(59, 130, 246, 0.1);
  }
  button.refresh-btn:hover {
    background: rgba(59, 130, 246, 0.3);
  }

  .danger-btn:hover {
    background: rgba(255, 0, 0, 0.4);
  }

  canvas {
    flex: 1;
    width: 100%;
    height: 100%;
    cursor: crosshair;
    touch-action: none;
  }

  .template-controls {
    position: relative;
    display: flex;
    align-items: center;
    margin-left: auto;
  }

  .split-template-btn {
    display: flex;
    align-items: center;
    background: rgba(56, 189, 248, 0.15);
    border: 1px solid var(--accent-color);
    border-radius: 6px;
    overflow: hidden;
    transition: all 0.2s ease;
  }

  .split-template-btn:hover, .split-template-btn.active {
    box-shadow: 0 0 12px var(--accent-glow);
    background: rgba(56, 189, 248, 0.25);
  }

  .split-save-part, .split-arrow-part {
    background: transparent;
    border: none;
    color: var(--accent-color);
    padding: 4px 8px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: background 0.15s ease, color 0.15s ease;
  }

  .split-save-part:hover, .split-arrow-part:hover {
    background: var(--accent-color);
    color: #0f172a;
  }

  .split-divider {
    width: 1px;
    height: 18px;
    background: rgba(56, 189, 248, 0.35);
  }

  .template-menu-popup {
    position: absolute;
    bottom: 36px;
    right: 0;
    background: var(--bg-card, #121826);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 6px;
    min-width: 180px;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.6);
    backdrop-filter: blur(12px);
    z-index: 100;
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .template-menu-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 6px 10px;
    border-radius: 6px;
    font-size: 0.8rem;
    color: var(--text-secondary);
    cursor: pointer;
    transition: background 0.15s ease, color 0.15s ease;
  }

  .template-menu-item:hover {
    background: rgba(255, 255, 255, 0.08);
    color: var(--text-primary);
  }

  .template-menu-item.selected {
    background: rgba(56, 189, 248, 0.2);
    color: var(--accent-color);
    font-weight: 600;
  }

  .template-menu-item .item-icon {
    font-size: 16px;
  }

  .template-menu-item .item-name {
    flex: 1;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .template-menu-item .item-delete-btn {
    background: transparent;
    border: none;
    color: var(--danger-color);
    cursor: pointer;
    padding: 2px;
    display: flex;
    align-items: center;
    border-radius: 4px;
    opacity: 0.7;
  }

  .template-menu-item .item-delete-btn:hover {
    opacity: 1;
    background: rgba(239, 68, 68, 0.25);
  }

  .menu-divider {
    height: 1px;
    background: var(--border-color);
    margin: 4px 0;
  }

  .template-modal-backdrop {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.7);
    backdrop-filter: blur(6px);
    z-index: 1000;
    display: flex;
    justify-content: center;
    align-items: center;
  }

  .template-modal-card {
    background: var(--bg-card, #0f172a);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 16px 20px;
    width: 320px;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.7);
  }

  .template-modal-card h4 {
    margin: 0 0 6px 0;
    color: var(--accent-color);
    font-size: 0.95rem;
  }

  .template-modal-card .desc {
    margin: 0 0 12px 0;
    font-size: 0.78rem;
    color: var(--text-secondary);
  }

  .tpl-name-input {
    width: 100%;
    box-sizing: border-box;
    margin-bottom: 14px;
  }

  .tpl-modal-actions {
    display: flex;
    justify-content: flex-end;
    gap: 8px;
  }

  .cancel-btn {
    background: transparent;
    border: 1px solid var(--border-color);
    color: var(--text-muted);
    padding: 4px 12px;
    border-radius: 6px;
    font-size: 0.8rem;
    cursor: pointer;
  }

  .save-btn {
    background: var(--accent-color);
    color: #0f172a;
    border: none;
    font-weight: 700;
    padding: 4px 14px;
    border-radius: 6px;
    font-size: 0.8rem;
    cursor: pointer;
  }

  .save-btn:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }
</style>
