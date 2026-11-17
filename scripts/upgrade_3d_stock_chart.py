import re

css_addition = '''    /* Interactive 3D Chart Timeframe & Ticker Chips */
    .dock-chips-bar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      width: 100%;
      gap: 0.5rem;
      padding: 0 0.25rem;
    }
    .timeframe-group, .ticker-group {
      display: flex;
      gap: 0.35rem;
      align-items: center;
    }
    .tf-btn {
      background: rgba(15, 23, 42, 0.7);
      backdrop-filter: blur(16px);
      -webkit-backdrop-filter: blur(16px);
      border: 1px solid rgba(148, 163, 184, 0.18);
      color: var(--muted);
      font-family: var(--font-mono);
      font-size: 0.72rem;
      font-weight: 600;
      padding: 0.22rem 0.55rem;
      border-radius: 6px;
      cursor: pointer;
      transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .tf-btn:hover {
      color: #fff;
      border-color: rgba(0, 208, 156, 0.45);
      background: rgba(15, 23, 42, 0.9);
      transform: translateY(-1px);
    }
    .tf-btn.active {
      background: rgba(0, 208, 156, 0.16);
      border-color: #00d09c;
      color: #00d09c;
      box-shadow: 0 0 12px rgba(0, 208, 156, 0.25);
    }
    .ticker-btn {
      background: rgba(15, 23, 42, 0.7);
      backdrop-filter: blur(16px);
      -webkit-backdrop-filter: blur(16px);
      border: 1px solid rgba(148, 163, 184, 0.18);
      color: var(--muted);
      font-family: var(--font-mono);
      font-size: 0.72rem;
      font-weight: 600;
      padding: 0.22rem 0.65rem;
      border-radius: 6px;
      cursor: pointer;
      transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .ticker-btn:hover {
      color: #fff;
      border-color: rgba(6, 182, 212, 0.45);
      background: rgba(15, 23, 42, 0.9);
      transform: translateY(-1px);
    }
    .ticker-btn.active {
      background: rgba(6, 182, 212, 0.16);
      border-color: #06b6d4;
      color: #06b6d4;
      box-shadow: 0 0 12px rgba(6, 182, 212, 0.25);
    }
'''

html_chips = '''    <!-- Interactive Timeframe & Ticker Chips for 3D Three.js Graph -->
    <div class="dock-chips-bar" id="dock-chips-bar">
      <div class="timeframe-group">
        <button class="tf-btn active" onclick="switchTimeframe('1D', this)">1D</button>
        <button class="tf-btn" onclick="switchTimeframe('1W', this)">1W</button>
        <button class="tf-btn" onclick="switchTimeframe('1M', this)">1M</button>
        <button class="tf-btn" onclick="switchTimeframe('1Y', this)">1Y</button>
        <button class="tf-btn" onclick="switchTimeframe('ALL', this)">ALL</button>
      </div>
      <div class="ticker-group">
        <button class="ticker-btn active" onclick="switchTicker('PCJ', this)">PC JEWELLER ₹15.55</button>
        <button class="ticker-btn" onclick="switchTicker('NIFTY', this)">NIFTY 50 ₹24,367</button>
        <button class="ticker-btn" onclick="switchTicker('TATA', this)">TATA MOTORS ₹784</button>
      </div>
    </div>
'''

new_three_code = '''    // ---------------------------------------------------------------------------
    // THREE.JS HIGH-FIDELITY 3D INTERACTIVE STOCK LINE SUITE (Groww / TradingView Style)
    // Thin glowing laser line, multi-line indicators, 3D perspective floor, raycast hover & drag-orbit
    // ---------------------------------------------------------------------------
    const canvasContainer = document.getElementById('canvas-container');
    const heroHud = document.getElementById('hero-hud');
    const searchOverlay = document.getElementById('search-results-overlay');
    const searchInput = document.getElementById('terminal-search-input');

    let width = window.innerWidth;
    let height = window.innerHeight;

    const scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0x070b14, 0.0006);

    // Dynamic 3D Camera at an appealing perspective angle
    const camera = new THREE.PerspectiveCamera(42, width / height, 1, 3000);
    camera.position.set(15, 30, 340);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'high-performance' });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    canvasContainer.appendChild(renderer.domElement);

    // Full Interactive Orbit & Pitch Controls
    const controls = new THREE.OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.autoRotate = false;
    controls.enableZoom = true;
    controls.maxDistance = 750;
    controls.minDistance = 160;
    controls.maxPolarAngle = Math.PI / 2 + 0.15; // Don't flip below ground

    // Ambient & Multi-Point Dynamic Lighting for 3D Sheen
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.95);
    scene.add(ambientLight);

    const pointLight = new THREE.PointLight(0x00d09c, 3.2, 900);
    pointLight.position.set(40, 90, 180);
    scene.add(pointLight);

    const cyanRimLight = new THREE.PointLight(0x06b6d4, 2.2, 800);
    cyanRimLight.position.set(-180, 50, -80);
    scene.add(cyanRimLight);

    // Root Group for 3D Spatial Tilt & Layout
    const chartGroup = new THREE.Group();
    // Default tilted perspective deck (gives genuine 3D depth)
    chartGroup.rotation.x = -0.16;
    chartGroup.rotation.y = 0.06;
    scene.add(chartGroup);

    // ---------------------------------------------------------------------------
    // 1. 3D HOLOGRAPHIC PERSPECTIVE FLOOR GRID & FINTECH AXES
    // ---------------------------------------------------------------------------
    const chartWidth = 440;
    const halfW = chartWidth / 2;
    const baselineY = 0; // Baseline at Y = 0
    const floorY = -75;

    // 3D Perspective Grid Floor (Trading Deck)
    const gridFloor = new THREE.GridHelper(520, 26, 0x06b6d4, 0x1e293b);
    gridFloor.position.set(0, floorY, 0);
    gridFloor.material.transparent = true;
    gridFloor.material.opacity = 0.12;
    chartGroup.add(gridFloor);

    // Dashed Previous Close Baseline Line at Y = 0
    const baselineGeo = new THREE.BufferGeometry().setFromPoints([
      new THREE.Vector3(-halfW - 25, baselineY, 0),
      new THREE.Vector3(halfW + 25, baselineY, 0)
    ]);
    const baselineMat = new THREE.LineDashedMaterial({
      color: 0x64748b,
      dashSize: 5,
      gapSize: 4,
      transparent: true,
      opacity: 0.5
    });
    const baselineLine = new THREE.Line(baselineGeo, baselineMat);
    baselineLine.computeLineDistances();
    chartGroup.add(baselineLine);

    // Subtle Horizontal Price Grid Lines
    const gridLevels = [-50, -25, 25, 50];
    gridLevels.forEach(gy => {
      const gGeo = new THREE.BufferGeometry().setFromPoints([
        new THREE.Vector3(-halfW - 15, gy, -1),
        new THREE.Vector3(halfW + 15, gy, -1)
      ]);
      const gMat = new THREE.LineBasicMaterial({
        color: 0x1e293b,
        transparent: true,
        opacity: 0.3
      });
      const gLine = new THREE.Line(gGeo, gMat);
      chartGroup.add(gLine);
    });

    // ---------------------------------------------------------------------------
    // 2. STOCK DATA MODEL & MULTI-TIMEFRAME GENERATOR
    // ---------------------------------------------------------------------------
    const NUM_POINTS = 160;
    const stockPoints = [];
    const stockY = [];
    const targetStockY = []; // for smooth morph transitions

    let currentTicker = 'PCJ';
    let currentTimeframe = '1D';
    let basePriceValue = 15.50;
    let priceScaleMultiplier = 0.02;

    function generatePriceTrajectory(ticker, tf, i, total) {
      const t = i / (total - 1);
      let base = 0;
      if (tf === '1D') {
        // Authentic Groww PC Jeweller intraday curve
        if (t < 0.12) base = Math.sin(t * Math.PI * 8) * 14 - (t * 220);
        else if (t < 0.45) base = -22 - Math.sin((t - 0.12) * 3.5) * 26 + Math.cos(t * 12) * 5;
        else if (t < 0.72) base = -42 + Math.sin((t - 0.45) * 8) * 22 + Math.sin(t * 18) * 4;
        else {
          const rt = (t - 0.72) / 0.28;
          base = -20 + rt * 45 + Math.sin(rt * Math.PI * 2) * 6;
        }
      } else if (tf === '1W') {
        // 1-Week Strong Bull Rally
        base = -35 + Math.pow(t, 0.8) * 68 + Math.sin(t * 14) * 8;
      } else if (tf === '1M') {
        // 1-Month Ascending Staircase
        base = -40 + Math.sin(t * 6) * 12 + t * 75 + Math.cos(t * 16) * 6;
      } else if (tf === '1Y') {
        // 1-Year Multi-Wave Consolidation & Breakout
        base = -25 + Math.sin(t * 10) * 24 + t * 65;
      } else {
        // ALL Timeframe Macro Ascending Triangle
        base = -45 + Math.sin(t * 8) * 18 + Math.pow(t, 1.4) * 85;
      }

      if (ticker === 'NIFTY') base *= 0.65; // NIFTY index has lower relative percentage swings
      else if (ticker === 'TATA') base = (base * 0.85) + Math.cos(t * 9) * 8;

      const microNoise = (Math.sin(i * 1.85) * 2.4 + Math.cos(i * 3.7) * 1.8 + ((i * 11) % 5 - 2) * 0.7);
      return base + microNoise;
    }

    for (let i = 0; i < NUM_POINTS; i++) {
      const x = -halfW + (i / (NUM_POINTS - 1)) * chartWidth;
      const y = generatePriceTrajectory('PCJ', '1D', i, NUM_POINTS);
      stockY.push(y);
      targetStockY.push(y);
      stockPoints.push(new THREE.Vector3(x, y, 0));
    }

    // ---------------------------------------------------------------------------
    // 3. THIN, CRISP GLOWING 3D LASER LINE & MULTI-LINE INDICATORS
    // ---------------------------------------------------------------------------
    const GROWW_GREEN = 0x00d09c;
    const GROWW_RED = 0xeb5b3c;
    const CYAN_INDICATOR = 0x06b6d4;
    const VIOLET_INDICATOR = 0x8b5cf6;

    // A) Thin, Crisp Glowing 3D Tube Ribbon (Radius 0.32 - NOT thick!)
    let curve = new THREE.CatmullRomCurve3(stockPoints, false, 'centripetal', 0.15);
    let tubeGeo = new THREE.TubeGeometry(curve, 200, 0.32, 8, false);
    const tubeMat = new THREE.MeshStandardMaterial({
      color: GROWW_GREEN,
      emissive: GROWW_GREEN,
      emissiveIntensity: 1.15,
      roughness: 0.15,
      metalness: 0.85
    });
    const tubeMesh = new THREE.Mesh(tubeGeo, tubeMat);
    chartGroup.add(tubeMesh);

    // B) Ultra-Sharp 1px Core Spine Line (Razor Edge Crispness)
    let coreLineGeo = new THREE.BufferGeometry().setFromPoints(curve.getPoints(240));
    const coreLineMat = new THREE.LineBasicMaterial({
      color: 0xffffff,
      transparent: true,
      opacity: 0.95
    });
    const coreLine = new THREE.Line(coreLineGeo, coreLineMat);
    chartGroup.add(coreLine);

    // C) Secondary Technical Indicator Line 1: 20-Period EMA (Thin Electric Cyan)
    const emaPoints = [];
    let prevEMA = stockY[0];
    const k = 2 / (20 + 1);
    for (let i = 0; i < NUM_POINTS; i++) {
      prevEMA = stockY[i] * k + prevEMA * (1 - k);
      emaPoints.push(new THREE.Vector3(stockPoints[i].x, prevEMA, -1.5));
    }
    const emaCurve = new THREE.CatmullRomCurve3(emaPoints, false, 'centripetal', 0.15);
    let emaGeo = new THREE.BufferGeometry().setFromPoints(emaCurve.getPoints(200));
    const emaMat = new THREE.LineBasicMaterial({
      color: CYAN_INDICATOR,
      transparent: true,
      opacity: 0.55
    });
    const emaLine = new THREE.Line(emaGeo, emaMat);
    chartGroup.add(emaLine);

    // D) Secondary Technical Indicator Line 2: Upper VWAP / Volatility Band (Thin Dashed Violet)
    const vwapPoints = [];
    for (let i = 0; i < NUM_POINTS; i++) {
      vwapPoints.push(new THREE.Vector3(stockPoints[i].x, stockPoints[i].y + 12 + Math.sin(i * 0.12) * 4, -2.5));
    }
    const vwapCurve = new THREE.CatmullRomCurve3(vwapPoints, false, 'centripetal', 0.15);
    let vwapGeo = new THREE.BufferGeometry().setFromPoints(vwapCurve.getPoints(200));
    const vwapMat = new THREE.LineDashedMaterial({
      color: VIOLET_INDICATOR,
      dashSize: 4,
      gapSize: 3,
      transparent: true,
      opacity: 0.42
    });
    const vwapLine = new THREE.Line(vwapGeo, vwapMat);
    vwapLine.computeLineDistances();
    chartGroup.add(vwapLine);

    // E) Translucent Gossamer Area Curtain (Fading downwards to floor at Y = -75)
    const areaGeo = new THREE.BufferGeometry();
    const areaPositions = new Float32Array(NUM_POINTS * 2 * 3);
    const areaColors = new Float32Array(NUM_POINTS * 2 * 3);
    const colorTop = new THREE.Color(GROWW_GREEN);
    const colorBottom = new THREE.Color(0x070b14);

    const areaIndices = [];
    for (let i = 0; i < NUM_POINTS - 1; i++) {
      const topA = i * 2;
      const botA = i * 2 + 1;
      const topB = (i + 1) * 2;
      const botB = (i + 1) * 2 + 1;
      areaIndices.push(topA, botA, topB);
      areaIndices.push(topB, botA, botB);
    }
    areaGeo.setIndex(areaIndices);

    function updateAreaMesh() {
      for (let i = 0; i < NUM_POINTS; i++) {
        const x = stockPoints[i].x;
        const y = stockPoints[i].y;
        const idx = i * 2 * 3;

        areaPositions[idx] = x;
        areaPositions[idx + 1] = y;
        areaPositions[idx + 2] = -0.5;

        areaPositions[idx + 3] = x;
        areaPositions[idx + 4] = floorY;
        areaPositions[idx + 5] = -0.5;

        areaColors[idx] = colorTop.r;
        areaColors[idx + 1] = colorTop.g;
        areaColors[idx + 2] = colorTop.b;

        areaColors[idx + 3] = colorBottom.r;
        areaColors[idx + 4] = colorBottom.g;
        areaColors[idx + 5] = colorBottom.b;
      }
      areaGeo.setAttribute('position', new THREE.BufferAttribute(areaPositions, 3));
      areaGeo.setAttribute('color', new THREE.BufferAttribute(areaColors, 3));
      areaGeo.attributes.position.needsUpdate = true;
      areaGeo.attributes.color.needsUpdate = true;
    }
    updateAreaMesh();

    const areaMat = new THREE.MeshBasicMaterial({
      vertexColors: true,
      transparent: true,
      opacity: 0.16,
      side: THREE.DoubleSide,
      depthWrite: false
    });
    const areaMesh = new THREE.Mesh(areaGeo, areaMat);
    chartGroup.add(areaMesh);

    // F) 3D Vertical Laser Drop-Filaments (Depth Anchors to Floor)
    const dropGroup = new THREE.Group();
    chartGroup.add(dropGroup);
    const dropLines = [];
    const DROP_INTERVAL = 8;
    for (let i = 0; i < NUM_POINTS; i += DROP_INTERVAL) {
      const dGeo = new THREE.BufferGeometry().setFromPoints([
        new THREE.Vector3(stockPoints[i].x, stockPoints[i].y, 0),
        new THREE.Vector3(stockPoints[i].x, floorY, 0)
      ]);
      const dMat = new THREE.LineBasicMaterial({
        color: 0x00d09c,
        transparent: true,
        opacity: 0.15
      });
      const dLine = new THREE.Line(dGeo, dMat);
      dropGroup.add(dLine);

      // Small glowing anchor dot on floor
      const anchorGeo = new THREE.SphereGeometry(1.2, 8, 8);
      const anchorMat = new THREE.MeshBasicMaterial({ color: 0x00d09c, transparent: true, opacity: 0.4 });
      const anchorMesh = new THREE.Mesh(anchorGeo, anchorMat);
      anchorMesh.position.set(stockPoints[i].x, floorY, 0);
      dropGroup.add(anchorMesh);

      dropLines.push({ line: dLine, anchor: anchorMesh, ptIndex: i });
    }

    // G) Traveling Data Photon Beads (Live Order Flow Pulses)
    const photons = [];
    const photonGeo = new THREE.SphereGeometry(1.5, 12, 12);
    const photonMat = new THREE.MeshBasicMaterial({ color: 0xffffff });
    for (let p = 0; p < 4; p++) {
      const pMesh = new THREE.Mesh(photonGeo, photonMat);
      chartGroup.add(pMesh);
      photons.push({
        mesh: pMesh,
        progress: (p * 0.25),
        speed: 0.0016 + p * 0.0004
      });
    }

    // ---------------------------------------------------------------------------
    // 4. LIVE BEACON & HYPER-INTERACTIVE RAYCASTING CROSSHAIR
    // ---------------------------------------------------------------------------
    // Vertical Crosshair Line (glides on hover or tracks live tip)
    const crosshairGeo = new THREE.BufferGeometry().setFromPoints([
      new THREE.Vector3(0, floorY, 0),
      new THREE.Vector3(0, 85, 0)
    ]);
    const crosshairMat = new THREE.LineDashedMaterial({
      color: 0x94a3b8,
      dashSize: 3,
      gapSize: 3,
      transparent: true,
      opacity: 0.65
    });
    const crosshairLine = new THREE.Line(crosshairGeo, crosshairMat);
    crosshairLine.computeLineDistances();
    chartGroup.add(crosshairLine);

    // Glowing Live Beacon Dot at Apex
    const beaconGeo = new THREE.SphereGeometry(2.4, 16, 16);
    const beaconMat = new THREE.MeshBasicMaterial({ color: 0xffffff });
    const beaconMesh = new THREE.Mesh(beaconGeo, beaconMat);
    chartGroup.add(beaconMesh);

    // Expanding Pulsing Ripple Halo Ring
    const haloGeo = new THREE.RingGeometry(1.5, 7.5, 32);
    const haloMat = new THREE.MeshBasicMaterial({
      color: GROWW_GREEN,
      transparent: true,
      opacity: 0.85,
      side: THREE.DoubleSide
    });
    const haloMesh = new THREE.Mesh(haloGeo, haloMat);
    chartGroup.add(haloMesh);

    // Interactive Hover Bead (Snaps to curve when user hovers mouse)
    const hoverBeadGeo = new THREE.SphereGeometry(2.8, 16, 16);
    const hoverBeadMat = new THREE.MeshBasicMaterial({ color: 0x06b6d4, transparent: true, opacity: 0 });
    const hoverBeadMesh = new THREE.Mesh(hoverBeadGeo, hoverBeadMat);
    chartGroup.add(hoverBeadMesh);

    // 3D Billboarded Live Tooltip Badge
    function createTooltipCanvas() {
      const c = document.createElement('canvas');
      c.width = 400;
      c.height = 110;
      return c;
    }
    const tooltipCanvas = createTooltipCanvas();
    const tooltipTexture = new THREE.CanvasTexture(tooltipCanvas);
    tooltipTexture.minFilter = THREE.LinearFilter;
    const tooltipSpriteMat = new THREE.SpriteMaterial({ map: tooltipTexture, transparent: true });
    const tooltipSprite = new THREE.Sprite(tooltipSpriteMat);
    tooltipSprite.scale.set(40, 11, 1);
    chartGroup.add(tooltipSprite);

    function updateTooltipBadge(priceVal, timeStr, isUp, isHovering = false) {
      const ctx = tooltipCanvas.getContext('2d');
      ctx.clearRect(0, 0, 400, 110);

      // Glassmorphic dark card
      ctx.fillStyle = 'rgba(7, 11, 20, 0.94)';
      ctx.strokeStyle = isHovering ? 'rgba(6, 182, 212, 0.8)' : (isUp ? 'rgba(0, 208, 156, 0.7)' : 'rgba(235, 91, 60, 0.7)');
      ctx.lineWidth = 2.5;

      const x = 5, y = 5, w = 390, h = 100, r = 16;
      ctx.beginPath();
      ctx.moveTo(x + r, y);
      ctx.lineTo(x + w - r, y);
      ctx.quadraticCurveTo(x + w, y, x + w, y + r);
      ctx.lineTo(x + w, y + h - r);
      ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
      ctx.lineTo(x + r, y + h);
      ctx.quadraticCurveTo(x, y + h, x, y + h - r);
      ctx.lineTo(x, y + r);
      ctx.quadraticCurveTo(x, y, x + r, y);
      ctx.closePath();
      ctx.fill();
      ctx.stroke();

      // Indicator dot
      ctx.fillStyle = isHovering ? '#06b6d4' : (isUp ? '#00d09c' : '#eb5b3c');
      ctx.beginPath();
      ctx.arc(32, 54, 7, 0, Math.PI * 2);
      ctx.fill();

      // Price text
      ctx.fillStyle = '#ffffff';
      ctx.font = 'bold 30px "IBM Plex Mono", monospace';
      ctx.fillText(currentTicker + ' ₹' + priceVal.toFixed(2), 52, 63);

      ctx.fillStyle = '#94a3b8';
      ctx.font = '500 22px "IBM Plex Mono", monospace';
      ctx.fillText('| ' + timeStr, 225, 62);

      tooltipTexture.needsUpdate = true;
    }

    // Baseline "PREV CLOSE" Badge
    function createBaselineSprite(text = 'PREV CLOSE ₹15.50') {
      const c = document.createElement('canvas');
      c.width = 340;
      c.height = 70;
      const ctx = c.getContext('2d');
      ctx.fillStyle = 'rgba(15, 23, 42, 0.85)';
      ctx.strokeStyle = 'rgba(100, 116, 139, 0.45)';
      ctx.lineWidth = 2;
      ctx.fillRect(4, 4, 332, 62);
      ctx.strokeRect(4, 4, 332, 62);

      ctx.fillStyle = '#94a3b8';
      ctx.font = '600 24px "IBM Plex Mono", monospace';
      ctx.fillText(text, 18, 42);

      const tex = new THREE.CanvasTexture(c);
      tex.minFilter = THREE.LinearFilter;
      const mat = new THREE.SpriteMaterial({ map: tex, transparent: true, opacity: 0.85 });
      const sp = new THREE.Sprite(mat);
      sp.scale.set(34, 7, 1);
      sp.position.set(-halfW - 14, baselineY - 10, 0);
      return sp;
    }
    let baselineSprite = createBaselineSprite('PREV CLOSE ₹15.50');
    chartGroup.add(baselineSprite);

    // ---------------------------------------------------------------------------
    // 5. MOUSE INTERACTION & RAYCASTING INSPECTION
    // ---------------------------------------------------------------------------
    let mouseX = 0, mouseY = 0;
    let targetMouseX = 0, targetMouseY = 0;
    let isUserHovering = false;
    let hoverNormalizedX = 1.0;
    let lastMouseMoveTime = 0;

    const raycaster = new THREE.Raycaster();
    const mouseVector = new THREE.Vector2();
    const planeGeo = new THREE.PlaneGeometry(chartWidth * 1.5, 300);
    const chartPlane = new THREE.Mesh(planeGeo, new THREE.MeshBasicMaterial({ visible: false }));
    chartGroup.add(chartPlane);

    window.addEventListener('mousemove', (e) => {
      targetMouseX = ((e.clientX / width) - 0.5) * 45;
      targetMouseY = ((e.clientY / height) - 0.5) * 30;

      // Calculate normalized mouse for raycasting
      mouseVector.x = (e.clientX / width) * 2 - 1;
      mouseVector.y = -(e.clientY / height) * 2 + 1;

      raycaster.setFromCamera(mouseVector, camera);
      const intersects = raycaster.intersectObject(chartPlane);

      if (intersects.length > 0) {
        const localPt = chartGroup.worldToLocal(intersects[0].point.clone());
        if (localPt.x >= -halfW && localPt.x <= halfW) {
          isUserHovering = true;
          hoverNormalizedX = (localPt.x + halfW) / chartWidth;
          lastMouseMoveTime = performance.now();
        }
      }
    });

    // Reset camera on double-click
    window.addEventListener('dblclick', () => {
      camera.position.set(15, 30, 340);
      controls.target.set(0, 0, 0);
      chartGroup.rotation.x = -0.16;
      chartGroup.rotation.y = 0.06;
    });

    // ---------------------------------------------------------------------------
    // 6. TIMEFRAME & TICKER SWITCHING WITH SMOOTH SPRING MORPH
    // ---------------------------------------------------------------------------
    let isMorphing = false;
    let morphProgress = 1.0;

    window.switchTimeframe = function(tf, btn) {
      if (currentTimeframe === tf) return;
      currentTimeframe = tf;

      document.querySelectorAll('.tf-btn').forEach(b => b.classList.remove('active'));
      if (btn) btn.classList.add('active');

      // Generate new target trajectory
      for (let i = 0; i < NUM_POINTS; i++) {
        targetStockY[i] = generatePriceTrajectory(currentTicker, currentTimeframe, i, NUM_POINTS);
      }
      isMorphing = true;
      morphProgress = 0.0;
    };

    window.switchTicker = function(tk, btn) {
      if (currentTicker === tk) return;
      currentTicker = tk;

      document.querySelectorAll('.ticker-btn').forEach(b => b.classList.remove('active'));
      if (btn) btn.classList.add('active');

      if (tk === 'PCJ') {
        basePriceValue = 15.50;
        priceScaleMultiplier = 0.02;
      } else if (tk === 'NIFTY') {
        basePriceValue = 24367.00;
        priceScaleMultiplier = 12.5;
      } else if (tk === 'TATA') {
        basePriceValue = 784.50;
        priceScaleMultiplier = 0.85;
      }

      // Update baseline label
      chartGroup.remove(baselineSprite);
      baselineSprite = createBaselineSprite(`PREV CLOSE ₹${basePriceValue.toFixed(2)}`);
      chartGroup.add(baselineSprite);

      // Generate new target trajectory
      for (let i = 0; i < NUM_POINTS; i++) {
        targetStockY[i] = generatePriceTrajectory(currentTicker, currentTimeframe, i, NUM_POINTS);
      }
      isMorphing = true;
      morphProgress = 0.0;
    };

    // ---------------------------------------------------------------------------
    // 7. REAL-TIME MARKET TICK ENGINE (Changing Live using Three.js)
    // ---------------------------------------------------------------------------
    let currentPriceTarget = stockY[NUM_POINTS - 1];
    let currentPrice = currentPriceTarget;
    let tickAccumulator = 0;
    let tickCounter = 0;

    function getFormattedTime(offsetMinutes = 0) {
      const d = new Date(Date.now() + offsetMinutes * 60000);
      let hours = d.getHours();
      const minutes = String(d.getMinutes()).padStart(2, '0');
      const seconds = String(d.getSeconds()).padStart(2, '0');
      const ampm = hours >= 12 ? 'PM' : 'AM';
      hours = hours % 12 || 12;
      return `${hours}:${minutes}:${seconds} ${ampm}`;
    }

    // ---------------------------------------------------------------------------
    // 8. RENDER LOOP AT SILKY 60 FPS
    // ---------------------------------------------------------------------------
    let clock = new THREE.Clock();

    function animate() {
      requestAnimationFrame(animate);
      const time = clock.getElapsedTime();

      // Smooth Morph Animation when user switches timeframe/ticker
      if (isMorphing) {
        morphProgress += 0.045;
        const ease = 0.5 - Math.cos(Math.min(1.0, morphProgress) * Math.PI) / 2;
        for (let i = 0; i < NUM_POINTS; i++) {
          stockY[i] += (targetStockY[i] - stockY[i]) * ease;
          stockPoints[i].y = stockY[i];
        }
        if (morphProgress >= 1.0) {
          isMorphing = false;
          currentPriceTarget = stockY[NUM_POINTS - 1];
        }
      }

      // Mouse Parallax Lerp when not dragging controls
      mouseX += (targetMouseX - mouseX) * 0.04;
      mouseY += (targetMouseY - mouseY) * 0.04;
      if (!controls.state || controls.state === -1) {
        chartGroup.rotation.y = 0.06 + mouseX * 0.002;
        chartGroup.rotation.x = -0.16 - mouseY * 0.0015;
      }
      controls.update();

      // Real-Time Micro-Tick Simulation
      tickAccumulator += 0.016;
      if (tickAccumulator > 0.065 && !isMorphing) {
        tickAccumulator = 0;
        tickCounter++;

        // Micro-price stochastic walk with slight mean reversion & momentum
        const deltaPrice = (Math.random() - 0.492) * 0.55 + (-currentPriceTarget * 0.012);
        currentPriceTarget = Math.max(-55, Math.min(48, currentPriceTarget + deltaPrice));

        // Advance line by streaming: Every ~36 ticks (~2.4s), commit a new point and shift left
        if (tickCounter % 36 === 0) {
          for (let i = 0; i < NUM_POINTS - 1; i++) {
            stockY[i] = stockY[i + 1];
            stockPoints[i].y = stockY[i];
          }
          stockY[NUM_POINTS - 1] = currentPriceTarget;
          stockPoints[NUM_POINTS - 1].y = currentPriceTarget;
        }
      }

      // Smooth lerp of current leading price point
      if (!isMorphing) {
        currentPrice += (currentPriceTarget - currentPrice) * 0.12;
        stockY[NUM_POINTS - 1] = currentPrice;
        stockPoints[NUM_POINTS - 1].y = currentPrice;
      }

      // Dynamic Color Shift based on baseline: Green above, Red below
      const isPositive = currentPrice >= baselineY;
      const targetColor = isPositive ? GROWW_GREEN : GROWW_RED;
      tubeMat.color.setHex(targetColor);
      tubeMat.emissive.setHex(targetColor);
      haloMat.color.setHex(targetColor);
      pointLight.color.setHex(targetColor);

      // Rebuild dynamic CatmullRom Curve through stock points
      curve = new THREE.CatmullRomCurve3(stockPoints, false, 'centripetal', 0.15);

      // Update Thin Tube Ribbon Geometry (Radius 0.32)
      tubeGeo.dispose();
      tubeGeo = new THREE.TubeGeometry(curve, 200, 0.32, 8, false);
      tubeMesh.geometry = tubeGeo;

      // Update Core Line
      coreLineGeo.dispose();
      coreLineGeo = new THREE.BufferGeometry().setFromPoints(curve.getPoints(240));
      coreLine.geometry = coreLineGeo;

      // Update Secondary Indicators (EMA and VWAP)
      prevEMA = stockY[0];
      for (let i = 0; i < NUM_POINTS; i++) {
        prevEMA = stockY[i] * k + prevEMA * (1 - k);
        emaPoints[i].y = prevEMA;
        vwapPoints[i].y = stockPoints[i].y + 12 + Math.sin(time * 0.8 + i * 0.12) * 3;
      }
      emaGeo.dispose();
      emaGeo = new THREE.BufferGeometry().setFromPoints(new THREE.CatmullRomCurve3(emaPoints, false, 'centripetal', 0.15).getPoints(200));
      emaLine.geometry = emaGeo;

      vwapGeo.dispose();
      vwapGeo = new THREE.BufferGeometry().setFromPoints(new THREE.CatmullRomCurve3(vwapPoints, false, 'centripetal', 0.15).getPoints(200));
      vwapLine.geometry = vwapGeo;
      vwapLine.computeLineDistances();

      // Update Translucent Area Gradient Mesh
      updateAreaMesh();

      // Update 3D Vertical Drop-Filaments to Floor
      dropLines.forEach(dl => {
        const pt = stockPoints[dl.ptIndex];
        dl.line.geometry.dispose();
        dl.line.geometry = new THREE.BufferGeometry().setFromPoints([
          new THREE.Vector3(pt.x, pt.y, 0),
          new THREE.Vector3(pt.x, floorY, 0)
        ]);
        dl.anchor.position.x = pt.x;
      });

      // Animate Traveling Data Photon Beads
      photons.forEach(p => {
        p.progress = (p.progress + p.speed) % 1.0;
        const pt = curve.getPointAt(p.progress);
        p.mesh.position.copy(pt);
      });

      // Hover Crosshair & Tooltip Logic
      if (isUserHovering && (performance.now() - lastMouseMoveTime > 2500)) {
        isUserHovering = false; // smooth return to live leading tick
      }

      let activeX, activeY, activePrice, activeTime, isHoverActive;
      const lastX = stockPoints[NUM_POINTS - 1].x;
      const lastY = stockPoints[NUM_POINTS - 1].y;

      if (isUserHovering) {
        const hoverIdx = Math.min(NUM_POINTS - 1, Math.max(0, Math.floor(hoverNormalizedX * (NUM_POINTS - 1))));
        activeX = stockPoints[hoverIdx].x;
        activeY = stockPoints[hoverIdx].y;
        activePrice = basePriceValue + activeY * priceScaleMultiplier;
        activeTime = getFormattedTime(-Math.round((1.0 - hoverNormalizedX) * 360));
        isHoverActive = true;

        hoverBeadMesh.position.set(activeX, activeY, 0.6);
        hoverBeadMat.opacity = 0.95;
      } else {
        activeX = lastX;
        activeY = lastY;
        activePrice = basePriceValue + currentPrice * priceScaleMultiplier;
        activeTime = getFormattedTime(0);
        isHoverActive = false;
        hoverBeadMat.opacity = 0;
      }

      // Update Crosshair Position
      crosshairLine.position.x = activeX;
      tooltipSprite.position.set(activeX - 22, activeY + 28, 1);
      updateTooltipBadge(activePrice, activeTime, activePrice >= basePriceValue, isHoverActive);

      // Position Live Beacon Dot and Pulsing Halo at Apex
      beaconMesh.position.set(lastX, lastY, 0.5);
      const pulseCycle = (time * 2.2) % 1.0;
      const haloScale = 1.0 + pulseCycle * 1.8;
      haloMesh.scale.set(haloScale, haloScale, 1);
      haloMat.opacity = Math.max(0, 0.85 * (1.0 - pulseCycle));
      haloMesh.position.set(lastX, lastY, 0.4);

      renderer.render(scene, camera);
    }
    requestAnimationFrame(animate);

    // Window Resize
    window.addEventListener('resize', () => {
      width = window.innerWidth;
      height = window.innerHeight;
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
      renderer.setSize(width, height);
    });
'''

# 1. Update site/index.html
target_path = 'markettide-rag-team/site/index.html'
with open(target_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Add CSS if not present
if '.dock-chips-bar' not in content:
    css_anchor = '    .bottom-search-dock {'
    idx = content.find(css_anchor)
    if idx != -1:
        content = content[:idx] + css_addition + '\n' + content[idx:]

# Add HTML chips if not present
if 'id="dock-chips-bar"' not in content:
    html_anchor = '    <div class="dock-glass-card">'
    idx = content.find(html_anchor)
    if idx != -1:
        content = content[:idx] + html_chips + content[idx:]

# Replace Three.js script block
start_marker = '// ---------------------------------------------------------------------------\n    // THREE.JS PURE REAL-TIME DYNAMIC STOCK LINE CHART (Groww / TradingView Style)'
end_marker = "    // Window Resize\n    window.addEventListener('resize', () => {\n      width = window.innerWidth;\n      height = window.innerHeight;\n      camera.aspect = width / height;\n      camera.updateProjectionMatrix();\n      renderer.setSize(width, height);\n    });"

start_idx = content.find(start_marker)
end_idx = content.find(end_marker)

if start_idx == -1:
    # Try alternative start marker
    start_marker = '// ---------------------------------------------------------------------------\n    // THREE.JS HIGH-FIDELITY 3D INTERACTIVE STOCK LINE SUITE'
    start_idx = content.find(start_marker)

if start_idx != -1 and end_idx != -1:
    end_idx += len(end_marker)
    content = content[:start_idx] + new_three_code.strip() + content[end_idx:]
    with open(target_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print('SUCCESS: site/index.html updated with thin, appealing 3D interactive stock lines!')
else:
    print(f'ERROR: start_idx={start_idx}, end_idx={end_idx}')
