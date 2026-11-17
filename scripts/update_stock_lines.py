import os

new_code = '''    // ---------------------------------------------------------------------------
    // THREE.JS PURE REAL-TIME DYNAMIC STOCK LINE CHART (Groww / TradingView Style)
    // ---------------------------------------------------------------------------
    const canvasContainer = document.getElementById('canvas-container');
    const heroHud = document.getElementById('hero-hud');
    const searchOverlay = document.getElementById('search-results-overlay');
    const searchInput = document.getElementById('terminal-search-input');

    let width = window.innerWidth;
    let height = window.innerHeight;

    const scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0x070b14, 0.0008);

    const camera = new THREE.PerspectiveCamera(45, width / height, 1, 3000);
    camera.position.set(0, 0, 360);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'high-performance' });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    canvasContainer.appendChild(renderer.domElement);

    const controls = new THREE.OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.autoRotate = false;
    controls.enableZoom = true;
    controls.maxDistance = 700;
    controls.minDistance = 180;

    // Ambient & Point Lighting for 3D Sheen
    const ambientLight = new THREE.AmbientLight(0xffffff, 1.2);
    scene.add(ambientLight);

    const pointLight = new THREE.PointLight(0x00d09c, 3.0, 800);
    pointLight.position.set(0, 80, 160);
    scene.add(pointLight);

    // Root Group for 3D Mouse Parallax & Tilting
    const chartGroup = new THREE.Group();
    scene.add(chartGroup);

    // ---------------------------------------------------------------------------
    // 1. FINTECH AXES & DASHED PREVIOUS CLOSE BASELINE
    // ---------------------------------------------------------------------------
    const chartWidth = 440;
    const halfW = chartWidth / 2;
    const baselineY = 0; // Previous close at Y = 0

    // Dashed Previous Close Baseline Line (Matching Groww's gray dashed baseline)
    const baselineGeo = new THREE.BufferGeometry().setFromPoints([
      new THREE.Vector3(-halfW - 20, baselineY, 0),
      new THREE.Vector3(halfW + 20, baselineY, 0)
    ]);
    const baselineMat = new THREE.LineDashedMaterial({
      color: 0x64748b,
      dashSize: 5,
      gapSize: 4,
      transparent: true,
      opacity: 0.55
    });
    const baselineLine = new THREE.Line(baselineGeo, baselineMat);
    baselineLine.computeLineDistances();
    chartGroup.add(baselineLine);

    // Subtle Horizontal Price Grid Lines
    const gridLevels = [-60, -30, 30, 60];
    gridLevels.forEach(gy => {
      const gGeo = new THREE.BufferGeometry().setFromPoints([
        new THREE.Vector3(-halfW - 10, gy, -2),
        new THREE.Vector3(halfW + 10, gy, -2)
      ]);
      const gMat = new THREE.LineBasicMaterial({
        color: 0x1e293b,
        transparent: true,
        opacity: 0.35
      });
      const gLine = new THREE.Line(gGeo, gMat);
      chartGroup.add(gLine);
    });

    // ---------------------------------------------------------------------------
    // 2. STOCK DATA MODEL (Jagged Intraday Path with Micro-Volatility)
    // ---------------------------------------------------------------------------
    const NUM_POINTS = 160;
    const stockPoints = [];
    const stockY = [];

    // Authentic Intraday Price Walk mirroring Groww reference (PC Jeweller ₹15.50)
    // Starts near baseline, dips to morning low, double bottom, rallies back up
    function generateBasePrice(i, total) {
      const t = i / (total - 1);
      let base = 0;
      if (t < 0.1) {
        // Morning gap & drop
        base = Math.sin(t * Math.PI * 10) * 16 - (t * 220);
      } else if (t < 0.45) {
        // Morning consolidation & selloff to trough
        base = -22 - Math.sin((t - 0.1) * 3.5) * 26 + Math.cos(t * 12) * 5;
      } else if (t < 0.7) {
        // Double bottom bounce & test
        base = -42 + Math.sin((t - 0.45) * 8) * 22 + Math.sin(t * 18) * 4;
      } else {
        // Afternoon rally & breakout above baseline
        const rt = (t - 0.7) / 0.3;
        base = -20 + rt * 45 + Math.sin(rt * Math.PI * 2) * 6;
      }
      // Micro-jag volatility (authentic high-frequency market ticks)
      const microNoise = (Math.sin(i * 1.85) * 2.8 + Math.cos(i * 3.7) * 2.2 + ((i * 13) % 7 - 3) * 0.9);
      return base + microNoise;
    }

    for (let i = 0; i < NUM_POINTS; i++) {
      const x = -halfW + (i / (NUM_POINTS - 1)) * chartWidth;
      const y = generateBasePrice(i, NUM_POINTS);
      stockY.push(y);
      stockPoints.push(new THREE.Vector3(x, y, 0));
    }

    // ---------------------------------------------------------------------------
    // 3. THREE.JS STOCK LINE MESH & TRANSLUCENT AREA GRADIENT FILL
    // ---------------------------------------------------------------------------
    const GROWW_GREEN = 0x00d09c;
    const GROWW_RED = 0xeb5b3c;

    // A) Glowing 3D Tube Ribbon (Volumetric Line with Specular Sheen)
    let curve = new THREE.CatmullRomCurve3(stockPoints, false, 'centripetal', 0.15);
    let tubeGeo = new THREE.TubeGeometry(curve, 180, 1.4, 8, false);
    const tubeMat = new THREE.MeshStandardMaterial({
      color: GROWW_GREEN,
      emissive: GROWW_GREEN,
      emissiveIntensity: 0.85,
      roughness: 0.2,
      metalness: 0.7
    });
    const tubeMesh = new THREE.Mesh(tubeGeo, tubeMat);
    chartGroup.add(tubeMesh);

    // B) Sharp High-Precision Core Spine Line (Razor Edge Contrast)
    let coreLineGeo = new THREE.BufferGeometry().setFromPoints(curve.getPoints(240));
    const coreLineMat = new THREE.LineBasicMaterial({
      color: 0xffffff,
      transparent: true,
      opacity: 0.9,
      linewidth: 2
    });
    const coreLine = new THREE.Line(coreLineGeo, coreLineMat);
    chartGroup.add(coreLine);

    // C) Translucent Area Gradient Fill Mesh (Fading towards floor)
    const floorY = -75;
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

        // Top vertex (stock line position)
        areaPositions[idx] = x;
        areaPositions[idx + 1] = y;
        areaPositions[idx + 2] = -0.5;

        // Bottom vertex (floor)
        areaPositions[idx + 3] = x;
        areaPositions[idx + 4] = floorY;
        areaPositions[idx + 5] = -0.5;

        // Top color (Emerald Green)
        areaColors[idx] = colorTop.r;
        areaColors[idx + 1] = colorTop.g;
        areaColors[idx + 2] = colorTop.b;

        // Bottom color (Dark Slate Alpha Fade)
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
      opacity: 0.22,
      side: THREE.DoubleSide,
      depthWrite: false
    });
    const areaMesh = new THREE.Mesh(areaGeo, areaMat);
    chartGroup.add(areaMesh);

    // ---------------------------------------------------------------------------
    // 4. LIVE BEACON & VERTICAL CROSSHAIR AT LATEST TICK (Groww Reference)
    // ---------------------------------------------------------------------------
    // Vertical Crosshair Line tracking latest point
    const crosshairGeo = new THREE.BufferGeometry().setFromPoints([
      new THREE.Vector3(0, floorY, 0),
      new THREE.Vector3(0, 85, 0)
    ]);
    const crosshairMat = new THREE.LineDashedMaterial({
      color: 0x94a3b8,
      dashSize: 3,
      gapSize: 3,
      transparent: true,
      opacity: 0.6
    });
    const crosshairLine = new THREE.Line(crosshairGeo, crosshairMat);
    crosshairLine.computeLineDistances();
    chartGroup.add(crosshairLine);

    // Glowing Live Beacon Sphere
    const beaconGeo = new THREE.SphereGeometry(2.6, 16, 16);
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

    // 3D Billboarded Live Tooltip Badge (e.g. "₹15.55 | 2:43 PM")
    function createTooltipCanvas() {
      const c = document.createElement('canvas');
      c.width = 380;
      c.height = 110;
      return c;
    }
    const tooltipCanvas = createTooltipCanvas();
    const tooltipTexture = new THREE.CanvasTexture(tooltipCanvas);
    tooltipTexture.minFilter = THREE.LinearFilter;
    const tooltipSpriteMat = new THREE.SpriteMaterial({ map: tooltipTexture, transparent: true });
    const tooltipSprite = new THREE.Sprite(tooltipSpriteMat);
    tooltipSprite.scale.set(38, 11, 1);
    chartGroup.add(tooltipSprite);

    function updateTooltipBadge(priceVal, timeStr, isUp) {
      const ctx = tooltipCanvas.getContext('2d');
      ctx.clearRect(0, 0, 380, 110);

      // Glassmorphic dark card
      ctx.fillStyle = 'rgba(7, 11, 20, 0.92)';
      ctx.strokeStyle = isUp ? 'rgba(0, 208, 156, 0.7)' : 'rgba(235, 91, 60, 0.7)';
      ctx.lineWidth = 2.5;

      // Rounded rectangle
      const x = 5, y = 5, w = 370, h = 100, r = 16;
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

      // Live green/red indicator dot
      ctx.fillStyle = isUp ? '#00d09c' : '#eb5b3c';
      ctx.beginPath();
      ctx.arc(32, 54, 7, 0, Math.PI * 2);
      ctx.fill();

      // Price text: e.g. ₹15.55 | 2:43 PM
      ctx.fillStyle = '#ffffff';
      ctx.font = 'bold 30px "IBM Plex Mono", monospace';
      ctx.fillText('₹' + priceVal.toFixed(2), 52, 63);

      ctx.fillStyle = '#94a3b8';
      ctx.font = '500 24px "IBM Plex Mono", monospace';
      ctx.fillText('| ' + timeStr, 188, 62);

      tooltipTexture.needsUpdate = true;
    }

    // Baseline "PREV CLOSE ₹15.50" Label Sprite
    function createBaselineSprite() {
      const c = document.createElement('canvas');
      c.width = 320;
      c.height = 70;
      const ctx = c.getContext('2d');
      ctx.fillStyle = 'rgba(15, 23, 42, 0.8)';
      ctx.strokeStyle = 'rgba(100, 116, 139, 0.4)';
      ctx.lineWidth = 2;
      ctx.fillRect(4, 4, 312, 62);
      ctx.strokeRect(4, 4, 312, 62);

      ctx.fillStyle = '#94a3b8';
      ctx.font = '600 24px "IBM Plex Mono", monospace';
      ctx.fillText('PREV CLOSE ₹15.50', 20, 42);

      const tex = new THREE.CanvasTexture(c);
      tex.minFilter = THREE.LinearFilter;
      const mat = new THREE.SpriteMaterial({ map: tex, transparent: true, opacity: 0.85 });
      const sp = new THREE.Sprite(mat);
      sp.scale.set(32, 7, 1);
      sp.position.set(-halfW + 30, baselineY - 8, 0);
      return sp;
    }
    chartGroup.add(createBaselineSprite());

    // ---------------------------------------------------------------------------
    // 5. REAL-TIME MARKET TICK ENGINE (Changing Live using Three.js)
    // ---------------------------------------------------------------------------
    let currentPriceTarget = stockY[NUM_POINTS - 1];
    let currentPrice = currentPriceTarget;
    let tickAccumulator = 0;
    let tickCounter = 0;

    function getFormattedTime() {
      const now = new Date();
      let hours = now.getHours();
      const minutes = String(now.getMinutes()).padStart(2, '0');
      const seconds = String(now.getSeconds()).padStart(2, '0');
      const ampm = hours >= 12 ? 'PM' : 'AM';
      hours = hours % 12 || 12;
      return hours + ':' + minutes + ':' + seconds + ' ' + ampm;
    }

    // Initial tooltip render
    updateTooltipBadge(15.50 + currentPrice * 0.02, getFormattedTime(), currentPrice >= 0);

    // ---------------------------------------------------------------------------
    // 6. MOUSE PARALLAX WITH SILKY INERTIA
    // ---------------------------------------------------------------------------
    let mouseX = 0, mouseY = 0;
    let targetMouseX = 0, targetMouseY = 0;
    window.addEventListener('mousemove', (e) => {
      targetMouseX = ((e.clientX / width) - 0.5) * 50;
      targetMouseY = ((e.clientY / height) - 0.5) * 35;
    });

    // ---------------------------------------------------------------------------
    // 7. RENDER LOOP AT SILKY 60 FPS
    // ---------------------------------------------------------------------------
    let clock = new THREE.Clock();

    function animate() {
      requestAnimationFrame(animate);
      const time = clock.getElapsedTime();

      // Mouse Parallax Lerp
      mouseX += (targetMouseX - mouseX) * 0.04;
      mouseY += (targetMouseY - mouseY) * 0.04;

      // Subtle 3D Chart Tilt
      chartGroup.rotation.y = mouseX * 0.003;
      chartGroup.rotation.x = -mouseY * 0.002;

      // Real-Time Micro-Tick Simulation
      tickAccumulator += 0.016;
      if (tickAccumulator > 0.065) {
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

        // Update tooltip display
        const displayPrice = 15.50 + currentPriceTarget * 0.02;
        updateTooltipBadge(displayPrice, getFormattedTime(), currentPriceTarget >= baselineY);
      }

      // Smooth lerp of current leading price point
      currentPrice += (currentPriceTarget - currentPrice) * 0.12;
      stockY[NUM_POINTS - 1] = currentPrice;
      stockPoints[NUM_POINTS - 1].y = currentPrice;

      // Dynamic Color Shift based on baseline: Green above, Red below
      const isPositive = currentPrice >= baselineY;
      const targetColor = isPositive ? GROWW_GREEN : GROWW_RED;
      tubeMat.color.setHex(targetColor);
      tubeMat.emissive.setHex(targetColor);
      haloMat.color.setHex(targetColor);
      pointLight.color.setHex(targetColor);

      // Rebuild dynamic CatmullRom Curve through stock points
      curve = new THREE.CatmullRomCurve3(stockPoints, false, 'centripetal', 0.15);

      // Update Tube Ribbon Geometry
      tubeGeo.dispose();
      tubeGeo = new THREE.TubeGeometry(curve, 180, 1.4, 8, false);
      tubeMesh.geometry = tubeGeo;

      // Update Core Line
      coreLineGeo.dispose();
      coreLineGeo = new THREE.BufferGeometry().setFromPoints(curve.getPoints(240));
      coreLine.geometry = coreLineGeo;

      // Update Translucent Area Gradient Mesh
      updateAreaMesh();

      // Position Live Beacon and Crosshair at Tip (Leading Edge)
      const lastX = stockPoints[NUM_POINTS - 1].x;
      const lastY = stockPoints[NUM_POINTS - 1].y;

      beaconMesh.position.set(lastX, lastY, 0.5);

      // Animate Pulsing Ripple Halo
      const pulseCycle = (time * 2.2) % 1.0;
      const haloScale = 1.0 + pulseCycle * 1.8;
      haloMesh.scale.set(haloScale, haloScale, 1);
      haloMat.opacity = Math.max(0, 0.85 * (1.0 - pulseCycle));
      haloMesh.position.set(lastX, lastY, 0.4);

      // Update Crosshair Position
      crosshairLine.position.x = lastX;
      tooltipSprite.position.set(lastX - 22, lastY + 28, 1);

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
    });'''

target_path = 'markettide-rag-team/site/index.html'
with open(target_path, 'r', encoding='utf-8') as f:
    content = f.read()

start_marker = '// ---------------------------------------------------------------------------\n    // THREE.JS 3D CINEMATIC FINANCIAL TERRAIN & HOLOGRAPHIC WAVE\n    // ---------------------------------------------------------------------------'
end_marker = "    // Window Resize\n    window.addEventListener('resize', () => {\n      width = window.innerWidth;\n      height = window.innerHeight;\n      camera.aspect = width / height;\n      camera.updateProjectionMatrix();\n      renderer.setSize(width, height);\n    });"

start_idx = content.find(start_marker)
end_idx = content.find(end_marker)

if start_idx == -1 or end_idx == -1:
    print('FAILED: Markers not found!')
else:
    end_idx += len(end_marker)
    updated = content[:start_idx] + new_code + content[end_idx:]
    with open(target_path, 'w', encoding='utf-8') as f:
        f.write(updated)
    print('SUCCESS: site/index.html updated successfully with pure dynamic Three.js stock lines graph!')
