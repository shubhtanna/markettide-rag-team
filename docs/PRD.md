# MarketTide 3D Stock Nebula & Corporate Intelligence Terminal
## Product Requirements Document (PRD) & Technical Architectural Specification

**Document Version**: 1.0.0 — Production Specification  
**Status**: Approved & Architecturally Frozen  
**System Target**: MarketTide AI (`markettide-rag-team`)  
**Target File**: `markettide-rag-team/docs/PRD.md`  
**Classification**: Institutional Financial Engineering & WebGL Spatial Computing  
**Design Standards**: `ui-ux-pro-max`, `ui-styling`, WebGL 2.0 / Three.js r128+, WCAG 2.1 AA  

---

## 1. Executive Summary & System Vision

### 1.1 Executive Overview
MarketTide AI represents an institutional-grade, multi-hop corporate intelligence and equity research platform designed for the National Stock Exchange of India (NSE). While the existing application (`markettide-rag-team/chatbot/app.py`) provides an authoritative, zero-hallucination conversational research assistant ("Market Tide Mentor") grounded in 2,766 corporate disclosures across 1,716 entities (`data/filings_last_7_days.csv`), it currently presents disclosures through static tabular views and chat logs.

This PRD specifies the complete architectural build for the **MarketTide 3D Stock Nebula**: a dynamic, interactive Three.js WebGL visualization that renders a spatial 3D constellation of stock thumbnails with live updating market data. The 3D scene is seamlessly and bi-directionally coupled to the existing Retrieval-Augmented Generation (RAG) pipeline:
1. **Click-to-RAG (3D Scene $\to$ Chatbot)**: Selecting or browsing any stock thumbnail in the 3D constellation initiates targeted hybrid queries against corporate filings (financial earnings, board meeting resolutions, dividend declarations, and material order wins), automatically opening the filing dossier and streaming verified LLM insights.
2. **Chatbot-to-3D (Chatbot $\to$ 3D Scene)**: Conversational inquiries submitted to the chatbot (e.g., *"Show all Tata Group subsidiaries with recent acquisitions"*, or *"Highlight companies reporting Q2 EBITDA margin expansion"*) emit structured spatial directives that cause the 3D camera to dolly to the target node, highlight corporate conglomerates with pulsing chromatic glows, dim non-matching nodes, and project 3D vector rays connecting affiliated entities.

```
+-------------------------------------------------------------------------------------------------------+
|                                    MarketTide AI Terminal Architecture                                |
+-------------------------------------------------------------------------------------------------------+
|                                                                                                       |
|  +--------------------------------------------+       +--------------------------------------------+  |
|  |       Three.js 3D Spatial Canvas           |       |      Market Tide Mentor Chatbot Drawer     |  |
|  | - Mode 1: Spherical Fibonacci Constellation|       | - Tab 1: 💬 Ask Corporate Filings          |  |
|  | - Mode 2: Logarithmic Sector Spiral (Prim.)| <---> | - Tab 2: 🔍 Verification Pipeline & DAG    |  |
|  | - Mode 3: 3D Force-Directed Correlation    |       | - Tab 3: 🧭 Explore 2,766 Filing Records   |  |
|  | - Dynamic 512x288 CanvasTexture Cards      |       | - Strict Zero-Hallucination Gate           |  |
|  | - 3-Tier Level-of-Detail (LOD 0/1/2)       |       | - Streamlit / FastAPI Streaming Engine     |  |
|  +--------------------------------------------+       +--------------------------------------------+  |
|                        ^                                                     ^                        |
|                        |                  window.MarketTideBus               |                        |
|                        +=====================================================+                        |
|                                           (Typed Client Event Bus)                                    |
|                                                      ^                                                |
|                                                      |                                                |
|                        +-----------------------------+-----------------------------+                  |
|                        |                                                           |                  |
|  +-------------------------------------------+       +---------------------------------------------+  |
|  |       Live Market Data Ingestion Hub      |       |      Hybrid RAG Retrieval Engine (Core)     |  |
|  | - Tier 0: Finnhub WebSocket (50 viewports)|       | - Dense Vector Search (all-MiniLM-L6-v2)    |  |
|  | - Tier 1: Yahoo Finance Batch REST (.NS)  |       | - Lexical BM25 (BM25Okapi, 60 categories)   |  |
|  | - Tier 2: Alpha Vantage / Finnhub REST    |       | - Reciprocal Rank Fusion (RRF, k=60)        |  |
|  | - Tier 3: Offline Brownian Replay (CSV)   |       | - Multi-Entity Conglomerate Resolver (Tata, |  |
|  | - Token Bucket Limiter (C=60, r=1 tok/s)  |       |   Adani, Reliance, Birla, Mahindra, Bajaj)  |  |
|  | - Stale-While-Revalidate (SWR) In-Memory  |       | - 6-Level Strict Relevance Grounding Gates  |  |
|  +-------------------------------------------+       +---------------------------------------------+  |
+-------------------------------------------------------------------------------------------------------+
```

### 1.2 Quantitative Target Metrics & SLAs
| Dimension | Metric | SLA Target | Measurement Methodology |
|---|---|---|---|
| **Graphics Performance** | Frame Rate (Full Scene) | $\ge 58\text{ FPS}$ (Target $60\text{ FPS}$) | Chrome DevTools Performance Profiler / `stats.js` |
| **Graphics Performance** | Draw Calls | $\le 35\text{ calls/frame}$ | Three.js `renderer.info.render.calls` |
| **Graphics Performance** | Triangle Count | $\le 80,000\text{ triangles}$ | Three.js `renderer.info.render.triangles` |
| **Graphics Performance** | WebGL Texture VRAM | $\le 120\text{ MB}$ | GPU Process Memory via `chrome://gpu` |
| **Market Data Latency** | Active Viewport Quotes | $< 150\text{ ms}$ (WebSocket tick) | Chrome Network WebSocket Inspector |
| **Market Data Latency** | Galaxy Cloud Quotes | $\le 15.0\text{ s}$ (Batch SWR) | Server Proxy Response Header `X-Cache-Latency` |
| **Market Data Resiliency** | Uptime & Fallback | $99.99\%$ Zero-Crash Guarantee | Automated Circuit Breaker & Offline Synthetic Replay |
| **RAG Hybrid Retrieval** | Top-6 RRF Retrieval Time | $< 85\text{ ms}$ | `retriever.py` in-memory vector dot product + BM25 |
| **Chatbot Streaming** | Time to First Token (TTFT) | $< 650\text{ ms}$ | Groq API `llama-3.3-70b-versatile` SSE stream |
| **Accessibility** | Color Contrast (Text:Card) | $\ge 10.8:1$ | Lighthouse Accessibility Audit (WCAG 2.1 AA) |

---

## 2. Architecture Decision Records (ADRs)

### ADR-001: Hybrid InstancedMesh & CanvasTexture Dynamic Atlas Architecture
- **Status**: Accepted
- **Context**: Rendering 1,716 stock thumbnails simultaneously in WebGL can degrade frame rates below 20 FPS if implemented as individual `THREE.Mesh` objects with discrete HTML-canvas textures due to WebGL state changes and draw call overhead.
- **Decision**:
  1. For distant and mid-range nodes (LOD 1 and LOD 2, $> 150$ scene units), use a single `THREE.InstancedMesh` with a single shared $2048 \times 2048$ Texture Atlas. Node positions, quaternions, and color tints are driven via `instancedMesh.setMatrixAt()` and `instancedMesh.setColorAt()`, reducing hundreds of cards to **exactly 1 draw call**.
  2. For the focused active viewport (LOD 0, $\le 150$ scene units; up to 40 nodes), utilize pooled `THREE.PlaneGeometry` instances bound to individual $512 \times 288$ `THREE.CanvasTexture` buffers.
  3. When a price or sparkline updates, only the specific $512 \times 288$ canvas is redrawn and uploaded via `gl.texSubImage2D()`, completely avoiding full WebGL texture re-allocations.
- **Consequences**: Unwavering 60 FPS performance, draw calls capped under 35, and memory footprint stabilized under 120 MB.

### ADR-002: Dual-Engine Market Data Ingestion & 4-Tier Fallback Cascade
- **Status**: Accepted
- **Context**: The existing dataset contains 1,716 unique Indian equities listed on the National Stock Exchange of India (NSE). Free financial APIs from `public-apis` have distinct structural limitations:
  - Finnhub: 60 req/min REST ceiling, but provides free WebSocket streaming for up to 50 concurrent symbols (primarily US tickers; Indian equities have delayed/partial coverage).
  - Alpha Vantage: Free tier severely constrained to 25 requests/day.
  - Yahoo Finance: Unauthenticated open query endpoints permit multi-ticker batching (50–100 symbols per GET call) and native Indian NSE `.NS` ticker formatting (`TCS.NS`, `RELIANCE.NS`), but can trigger HTTP 429 if called at high un-throttled frequencies.
- **Decision**: Implement a resilient 4-tier fallback cascade:
  - **Tier 0 (Live Viewport)**: Finnhub WebSocket (`wss://ws.finnhub.io`) streaming real-time trades for up to 50 active focus symbols.
  - **Tier 1 (NSE Cloud Nodes)**: Yahoo Finance Batch Proxy (`/v7/finance/quote?symbols=...`) querying 50 tickers per call on a 15-second SWR cycle with a 10-second server-side in-memory cache.
  - **Tier 2 (On-Demand Fallback)**: Alpha Vantage `GLOBAL_QUOTE` / Finnhub REST `/quote` for single-ticker user drilldowns when primary tiers return null.
  - **Tier 3 (Air-Gapped / Sandboxed Fallback)**: Offline deterministic synthetic replay seeded from `data/filings_last_7_days.csv` with normalized Brownian motion micro-ticks.
- **Consequences**: Guarantees zero runtime crashes in air-gapped test environments, strict rate limit compliance, and zero financial cost.

### ADR-003: Bi-Directional Window Event Bus & Server-Sent Events (SSE) Protocol
- **Status**: Accepted
- **Context**: The application frontend is architected as an executive workstation (`site/index.html`) embedding the Streamlit RAG chatbot via iframe (`site/chatbot.html`). Communication between the WebGL 3D Canvas and the Chatbot must be low-latency, strictly typed, and support streaming LLM tokens alongside spatial scene directives.
- **Decision**:
  1. Implement `window.MarketTideBus` as a typed client-side event bus operating across `window.postMessage` boundaries with origin validation (`SAMEORIGIN`).
  2. For decoupled modern deployments, implement a FastAPI service layer (`chatbot/server.py`) exposing Server-Sent Events (SSE) over HTTP/2, streaming both chunk tokens (`event: token`) and scene manipulation payloads (`event: scene_action`).
- **Consequences**: Complete decoupling between the 3D rendering loop and the conversational RAG pipeline, enabling independent scaling and seamless bidirectional state updates.

### ADR-004: Sector-Based Logarithmic Galaxy Arm Spatial Topology
- **Status**: Accepted
- **Context**: Arranging 1,716 nodes purely at random or on a flat grid produces visual clutter and high cognitive load. Financial equities naturally exhibit macroeconomic sector clustering and conglomerate affiliations.
- **Decision**: Provide three user-switchable spatial distribution topologies, defaulting to **Mode 2: Sector-Based Galaxy Arm Clustering**:
  - *Mode 1 (Spherical Fibonacci Constellation)*: Uniform mathematical distribution over a sphere ($R=400$) using the golden angle.
  - *Mode 2 (Logarithmic Galaxy Spiral - Primary)*: 6 logarithmic spiral arms grouping equities into sectors: IT & Tech, Financials & Banking, Auto & EV, Pharmaceuticals & Healthcare, Energy & Power, and Conglomerates. Vertical dispersion follows a Gaussian normal distribution.
  - *Mode 3 (3D Force-Directed Correlation Matrix)*: Real-time physics simulation using Pearson return co-movement correlation matrix $\rho_{ij}$ with Hookean spring tension and electrostatic Coulomb repulsion computed inside a Web Worker.
- **Consequences**: Intuitive visual clustering where related stocks cluster naturally; macro-level industry trends can be comprehended at a single glance.

### ADR-005: Hybrid RAG Preservation & Agent Line 491 Dead-Code Resolution
- **Status**: Accepted
- **Context**: Codebase analysis of `markettide-rag-team/chatbot/agent.py` revealed that at line 491, an un-indented `return [], "company:not_found"` statement causes general hybrid retrieval (lines 494–495) to be unreachable dead code. Furthermore, `retriever.py` contains 6 strict grounding gates that must remain intact to prevent false hallucinations.
- **Decision**:
  1. Formally resolve the line 491 bug in the technical implementation specification: ensure single-company resolution returns matching filings, and un-resolved queries drop through cleanly to `self.tools.hybrid_search(query, top_k=6, use_hybrid=True)`.
  2. Preserve all 6 grounding gates in `HybridRetriever`: BM25 $> 0.0$ lexical requirement, $\ge 50\%$ keyword coverage, dense floor $0.35$, and distinctive subject keyword matching.
  3. Ensure 3D thumbnail clicks construct explicit deterministic entity queries (`company:{TICKER}`) bypassing conversational routing directly to verified filing lists.
- **Consequences**: 100% preservation of verified zero-hallucination guardrails and retrieval benchmark pass rates while enabling unrestricted hybrid semantic exploration.

---

## 3. Three.js 3D Scene Architecture & Performance Engineering

### 3.1 Scene Graph & Kinematic Camera Topology

```
THREE.Scene (Background: #0a0f1d, FogExp2: density 0.0006)
 ├── THREE.PerspectiveCamera (FOV 60°, near 0.1, far 2500)
 ├── THREE.AmbientLight (#ffffff, intensity 0.45)
 ├── THREE.DirectionalLight (#38bdf8, intensity 0.85, pos: [200, 400, 300])
 ├── THREE.PointLight (#f97316, intensity 1.2, distance 800, pos: [0, 0, 0])
 ├── THREE.Group: GalaxyRootGroup
 │    ├── THREE.InstancedMesh: BackgroundStarfield (2,500 particles)
 │    ├── THREE.InstancedMesh: MidRangeCardsLOD1 (1,700 instances, Atlas Texture)
 │    ├── THREE.Group: ActiveCardsLOD0 (up to 40 PlaneGeometry + CanvasTexture)
 │    ├── THREE.LineSegments: ConglomerateVectorRays (Dynamic BufferGeometry)
 │    └── THREE.Mesh: GalaxyCoreAura (Custom ShaderMaterial Glow)
 └── THREE.EffectComposer
      ├── RenderPass (Scene, Camera)
      ├── UnrealBloomPass (threshold 0.65, strength 0.35, radius 0.4)
      └── SMAAPass (Subpixel Morphological Antialiasing)
```

#### Camera Kinematics & Constraints
- **Camera Class**: `THREE.PerspectiveCamera`
  - Vertical Field of View (FOV): $60^\circ$
  - Near Clipping Plane: $0.1\text{ units}$
  - Far Clipping Plane: $2,500\text{ units}$
  - Default Home Coordinates: $\mathbf{P}_0 = (0, 220, 650)$ oriented toward origin $(0, 0, 0)$.
- **Responsive Viewport Clamping**:
  ```javascript
  const ro = new ResizeObserver((entries) => {
    const { width, height } = entries[0].contentRect;
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2.0));
  });
  ro.observe(document.getElementById('threejs-container'));
  ```
- **OrbitControls Parameters**:
  - `controls.enableDamping = true;`
  - `controls.dampingFactor = 0.05;`
  - `controls.minDistance = 25.0;`
  - `controls.maxDistance = 1400.0;`
  - `controls.maxPolarAngle = Math.PI * 0.88;`
  - `controls.autoRotate = true;`
  - `controls.autoRotateSpeed = 0.4;`
- **Idle Watchdog**: User pointer interaction (`pointerdown`, `wheel`, `touchstart`) immediately sets `controls.autoRotate = false`. An idle watchdog timer restores auto-rotation only after $12.0\text{ seconds}$ of inactivity, smoothly interpolating speed over $2.0\text{ seconds}$.

---

### 3.2 3D Spatial Distribution Formulations

#### Mode 1: Spherical Fibonacci Distribution (Golden Constellation)
Evenly distributes $N = 1,716$ stock nodes across a sphere of radius $R = 400$ without clustering or pole singularities:
For each stock index $i \in [0, N - 1]$:

$$y_i = 1 - \left(\frac{i}{N - 1}\right) \cdot 2 \quad \in [1, -1]$$

$$r_{xy} = \sqrt{1 - y_i^2}$$

$$\theta_i = \pi \cdot (3 - \sqrt{5}) \cdot i \approx 2.39996323 \cdot i \quad (\text{Golden Angle in radians})$$

$$\mathbf{x}_i = \begin{bmatrix} R \cdot r_{xy} \cdot \cos\theta_i \\ R \cdot y_i \\ R \cdot r_{xy} \cdot \sin\theta_i \end{bmatrix}$$

*Orientation*: Each card faces radially outward: $\mathbf{q}_i = \text{Quaternion.fromUnitVectors}(\mathbf{\hat{z}}, \mathbf{\hat{x}}_i)$.

#### Mode 2: Sector-Based Logarithmic Galaxy Arm Spiral (Recommended Primary)
Arranges equities into 6 logarithmic galactic spiral arms corresponding to macro sectors:
- Sector Set: $\mathcal{S} = \{\text{IT/Tech, Banking/Finance, Auto, Pharma, Energy, Conglomerates}\}$
- Number of Arms: $M = 6$. Base arm angle: $\phi_k = \frac{2\pi \cdot k}{M}$ for sector $k \in [0, 5]$.
- Radial Span: $r_{\min} = 60$, $r_{\max} = 450$. Spiral winding parameter: $b = 0.45$.

For entity $j$ belonging to sector $k$, with normalized position $u_j \in [0, 1]$:

$$r_j = r_{\min} + (r_{\max} - r_{\min}) \cdot u_j^{0.72}$$

$$\theta_j = \phi_k + b \cdot \ln\left(\frac{r_j}{r_{\min}}\right) + \delta\theta_j, \quad \delta\theta_j \sim \mathcal{N}\left(0, \left(\frac{0.18}{1 + 0.003 r_j}\right)^2\right)$$

$$z_j \sim \mathcal{N}\left(0, \sigma_z^2\right), \quad \sigma_z = 24 \cdot \exp\left(-\frac{r_j}{r_{\max}}\right)$$

$$\mathbf{x}_j = \begin{bmatrix} r_j \cdot \cos\theta_j \\ z_j \\ r_j \cdot \sin\theta_j \end{bmatrix}$$

#### Mode 3: 3D Force-Directed Correlation Matrix (Physics Simulation)
Simulates equities as point masses in 3D space where spring tension is proportional to Pearson return co-movement correlation $\rho_{ij}$:

$$\mathbf{F}_{ij}^{\text{spring}} = -k_{\text{spring}} \cdot \max(0, \rho_{ij}) \cdot (\|\mathbf{x}_i - \mathbf{x}_j\| - d_0) \cdot \frac{\mathbf{x}_i - \mathbf{x}_j}{\|\mathbf{x}_i - \mathbf{x}_j\|}$$

$$\mathbf{F}_{ij}^{\text{repulse}} = \frac{k_{\text{repulse}}}{\|\mathbf{x}_i - \mathbf{x}_j\|^2 + \epsilon} \cdot \frac{\mathbf{x}_i - \mathbf{x}_j}{\|\mathbf{x}_i - \mathbf{x}_j\|}$$

$$\mathbf{F}_i^{\text{gravity}} = -k_{\text{center}} \cdot \mathbf{x}_i$$

$$\mathbf{v}_i(t + \Delta t) = \mu \cdot \mathbf{v}_i(t) + \frac{\Delta t}{m_i} \sum_{j \neq i} \left(\mathbf{F}_{ij}^{\text{spring}} + \mathbf{F}_{ij}^{\text{repulse}}\right) + \mathbf{F}_i^{\text{gravity}}$$

$$\mathbf{x}_i(t + \Delta t) = \mathbf{x}_i(t) + \mathbf{v}_i(t + \Delta t) \cdot \Delta t$$

where damping factor $\mu = 0.88$, spring constant $k_{\text{spring}} = 0.04$, and repulsion constant $k_{\text{repulse}} = 450.0$. Computed inside a dedicated Web Worker to maintain 60 FPS on the main rendering thread.

---

### 3.3 Thumbnail Geometry, Sparklines & Custom Shaders

#### High-Detail Card Rendering (LOD 0, $512 \times 288$ CanvasTexture)
Each active card renders an offscreen HTML5 canvas containing:
1. **Header**: Company Logo/Badge + NSE Ticker (`IBM Plex Mono` 28px bold, `#ffffff`) + Sector tag.
2. **Metric Row**: Real-time Price in INR (e.g., `₹3,842.50`) + 24h Percentage Change pill badge (`#10b981` positive, `#ef4444` negative).
3. **Smooth Sparkline Curve**: 30-point normalized price sequence drawn with quadratic bezier curve interpolation:
   ```javascript
   function drawSparkline(ctx, points, width, height, isPositive) {
     ctx.beginPath();
     ctx.strokeStyle = isPositive ? '#10b981' : '#ef4444';
     ctx.lineWidth = 2.5;
     const dx = width / (points.length - 1);
     ctx.moveTo(0, height - points[0] * height);
     for (let i = 0; i < points.length - 1; i++) {
       const xc = (i * dx + (i + 1) * dx) / 2;
       const yc = height - ((points[i] + points[i + 1]) / 2) * height;
       ctx.quadraticCurveTo(i * dx, height - points[i] * height, xc, yc);
     }
     ctx.lineTo((points.length - 1) * dx, height - points[points.length - 1] * height);
     ctx.stroke();
   }
   ```
4. **Filings Count Badge**: Disclosures logged within the 7-day window (e.g. `4 Disclosures`).

#### Custom GLSL Card Shader Material
To implement chromatic edge glowing, uptick/downtick ripple waves, and exponential distance fog without multiple render passes, nodes use a custom `THREE.ShaderMaterial`:

```glsl
// Vertex Shader
uniform float uTime;
uniform float uPulseTime;
uniform float uPulseIntensity;
varying vec2 vUv;
varying vec3 vViewPosition;

void main() {
    vUv = uv;
    vec3 transformed = position;
    if (uPulseIntensity > 0.0) {
        float wave = sin(uTime * 8.0 - length(position.xy) * 2.0);
        transformed += normal * wave * uPulseIntensity * 1.5;
    }
    vec4 mvPosition = modelViewMatrix * vec4(transformed, 1.0);
    vViewPosition = -mvPosition.xyz;
    gl_Position = projectionMatrix * mvPosition;
}

// Fragment Shader
uniform sampler2D uTexture;
uniform vec3 uBorderColor;
uniform float uBorderWidth;
uniform float uPulseIntensity;
uniform vec3 uPulseColor;
uniform float uOpacity;
varying vec2 vUv;
varying vec3 vViewPosition;

void main() {
    vec4 texColor = texture2D(uTexture, vUv);
    
    // Antialiased Card Border Glow
    float dX = min(vUv.x, 1.0 - vUv.x);
    float dY = min(vUv.y, 1.0 - vUv.y);
    float distToEdge = min(dX, dY);
    float borderAlpha = 1.0 - smoothstep(0.0, uBorderWidth, distToEdge);
    
    vec3 baseColor = texColor.rgb;
    vec3 finalColor = mix(baseColor, uBorderColor, borderAlpha * 0.85);
    
    // Live Uptick / Downtick Ripple Flash
    if (uPulseIntensity > 0.0) {
        finalColor = mix(finalColor, uPulseColor, uPulseIntensity * 0.7);
    }
    
    // Exponential Distance Fog
    float depth = length(vViewPosition);
    float fogFactor = exp2(-0.0006 * 0.0006 * depth * depth * 1.442695);
    fogFactor = clamp(fogFactor, 0.0, 1.0);
    vec3 fogColor = vec3(0.039, 0.058, 0.114); // #0a0f1d
    
    gl_FragColor = vec4(mix(fogColor, finalColor, fogFactor), texColor.a * uOpacity);
}
```

---

### 3.4 Multi-Tier Level of Detail (LOD) & 60 FPS Performance Budget

| Level | Distance Range | Geometry Representation | Material & Texture | Update Rate | Draw Call Allocation |
|---|---|---|---|---|---|
| **LOD 0 (Inspection)** | $0 \le d < 150$ | Pooled `THREE.PlaneGeometry` ($20 \times 11.25$) | Dynamic $512 \times 288$ `CanvasTexture` | Real-time WebSocket tick ($100\text{ ms}$) | Max 40 calls (1 call/card) |
| **LOD 1 (Mid-Range)** | $150 \le d < 400$ | Shared `THREE.InstancedMesh` ($12 \times 6.75$) | Single $2048 \times 2048$ Texture Atlas | SWR Batch ($15.0\text{ s}$) | Exactly 1 draw call |
| **LOD 2 (Far Galaxy)** | $d \ge 400$ | `THREE.Points` particle constellation | Particle Sprite Material (Sector Color Glow) | Static / Pulse on Alert ($60.0\text{ s}$) | Exactly 1 draw call |

#### 60 FPS Frame Budget Breakdown (16.67 ms Target)
- **JavaScript & Event Processing**: $3.5\text{ ms}$ (Raycasting NDC calculation, WebSocket message unpacking).
- **Physics Simulation (Mode 3)**: $0.0\text{ ms}$ on main thread (offloaded to Web Worker; $1.5\text{ ms}$ buffer transfer).
- **Three.js Scene Graph & Culling**: $2.5\text{ ms}$ (Frustum culling, matrix updates, LOD distance evaluation).
- **WebGL Draw Calls & Post-Processing**: $6.5\text{ ms}$ (35 draw calls, UnrealBloomPass downsample, SMAA blend).
- **Safety Headroom**: $4.17\text{ ms}$ (buffer against OS compositor jitter).

---

### 3.5 Interaction Model & Raycasting Kinematics

#### Throttled Two-Stage Raycasting
To prevent pointer events from dropping frames during rapid orbital rotation:
1. `pointermove` listener updates normalized device coordinates (NDC: $x, y \in [-1, 1]$) with zero immediate raycast execution.
2. Raycasting executes inside `requestAnimationFrame` throttled to every second frame ($30\text{ Hz}$):
   - **Stage 1**: Fast Bounding Sphere rejection test against galaxy arm centroids.
   - **Stage 2**: Exact intersect tests against LOD 0 active planes or `instancedMesh.raycast()`.

#### Smooth Camera Flight Kinematics (GSAP + Slerp)
Clicking a stock node triggers an organic camera transition to optimal inspection distance ($d = 55\text{ units}$):
```javascript
function flyToStockNode(targetPosition, targetQuaternion) {
  const currentPos = camera.position.clone();
  const forward = new THREE.Vector3(0, 0, 1).applyQuaternion(targetQuaternion);
  const destination = targetPosition.clone().add(forward.multiplyScalar(55.0));

  gsap.to(camera.position, {
    x: destination.x,
    y: destination.y,
    z: destination.z,
    duration: 0.95,
    ease: 'power3.inOut',
    onUpdate: () => controls.update()
  });

  gsap.to(controls.target, {
    x: targetPosition.x,
    y: targetPosition.y,
    z: targetPosition.z,
    duration: 0.95,
    ease: 'power3.inOut'
  });
}
```

#### Visual Feedback State Machine
| State | Scale Factor | Border Color | Glow Emission | Interaction Behavior |
|---|---|---|---|---|
| **Idle** | $1.0\times$ | `rgba(51, 65, 85, 0.8)` (`#334155`) | None | Standard orbital rotation |
| **Hover** | $1.12\times$ | `rgba(6, 182, 212, 1.0)` (`#06b6d4`) | Cyan $8\text{px}$ halo | Displays hovering tooltip, stops auto-rotate |
| **Selected** | $1.22\times$ | `rgba(249, 115, 22, 1.0)` (`#f97316`) | Amber $16\text{px}$ halo | Triggers camera flight, opens filing dossier |
| **Highlighted** | $1.15\times$ | `rgba(52, 211, 153, 1.0)` (`#34d399`) | Pulse wave ($f=1.5\text{ Hz}$) | RAG query match; affiliated cards illuminated |
| **Dimmed** | $0.85\times$ | `rgba(30, 41, 59, 0.2)` | None ($0.15$ opacity) | Unrelated nodes during active search filter |
| **Live Pulse** | Flash | Uptick: `#10b981` / Downtick: `#ef4444` | Shader wave decay $1.2\text{ s}$ | Real-time quote trade execution |

---

## 4. Live Market Data Ingestion & API Schemas

### 4.1 Financial Market Data API Benchmark Matrix

| Provider | Endpoints Evaluated | Free Tier Quotas | Rate Limit Response | Indian NSE Equities (.NS) | WebSocket Streaming | Selected Role |
|---|---|---|---|---|---|---|
| **Finnhub.io** | `/quote`, `/stock/candle`, `wss://ws.finnhub.io` | $60\text{ req/min}$ REST | HTTP 429 (`{"error": "API limit reached."}`) | Limited on free tier | **Yes (50 concurrent symbols)** | **Primary Streamer (Tier 0)** |
| **Yahoo Finance** | `/v7/finance/quote`, `/v8/finance/spark` | ~2,000 req/hr unauthenticated | HTTP 429 (HTML error) | **Full Native Support** (`TCS.NS`, `INFY.NS`) | No (Polling only) | **Primary Batch (Tier 1)** |
| **Alpha Vantage** | `GLOBAL_QUOTE`, `TIME_SERIES_INTRADAY` | $25\text{ req/day}$, $5\text{ req/min}$ | HTTP 200 with payload `"Note"` | Partial | No | **Tertiary Fallback (Tier 2)** |
| **Polygon.io** | `/v2/aggs/ticker`, `/v1/last/stocks` | $5\text{ req/min}$, 15-min delay | HTTP 429 | US Only | No (Paid tier) | Supplementary |
| **StockData.org** | `/v1/data/quote` | $100\text{ req/day}$ | HTTP 429 | Partial | No | Supplementary |
| **Offline Cache** | Seeded from `data/filings_last_7_days.csv` | Unlimited (Local RAM) | Never fails | **All 1,716 Tickers** | Simulated internal ticks | **Deterministic Tier 3** |

### 4.2 4-Tier Fallback Cascade & Flow Control

```
                           Incoming Quote Request (Tickers: [TCS, INFY, KAYNES...])
                                                     |
                                                     v
                                      +------------------------------+
                                      |   Active in Viewport <= 50?  |
                                      +------------------------------+
                                            /                  \
                                     (YES) /                    \ (NO)
                                          v                      v
                       +-----------------------------+   +------------------------------+
                       | Tier 0: Finnhub WebSocket   |   | Tier 1: Yahoo Finance Batch  |
                       | (Real-time sub-150ms ticks) |   | (GET /v7/quote?symbols=*.NS) |
                       +-----------------------------+   +------------------------------+
                                      |                                  |
                                (WS Drops / 429)                   (Timeout / 429)
                                      |                                  |
                                      +----------------+-----------------+
                                                       |
                                                       v
                                      +----------------------------------+
                                      | Tier 2: Alpha Vantage / Finnhub  |
                                      | (Targeted REST drilldown)        |
                                      +----------------------------------+
                                                       |
                                            (Quota Exhausted / Offline)
                                                       |
                                                       v
                                      +----------------------------------+
                                      | Tier 3: Deterministic Offline    |
                                      | Synthetic Brownian Cache (CSV)   |
                                      | (Zero-crash 100% guarantee)      |
                                      +----------------------------------+
```

#### Rate Limiting & Flow Control Algorithms
1. **Token Bucket Rate Limiter**: Implemented in the backend proxy with bucket capacity $C = 60$ tokens and refill rate $r = 1.0\text{ token/second}$. Requests arriving with $0$ tokens available are queued up to $150\text{ ms}$ for batch coalescing or immediately serviced from SWR cache.
2. **Stale-While-Revalidate (SWR) Caching**:
   - Cache Header: `Cache-Control: public, max-age=10, stale-while-revalidate=60`
   - During live market hours ($09:15\text{ to }15:30\text{ IST}$), cache TTL is set to $10.0\text{ seconds}$.
   - During off-market hours or weekends, cache TTL automatically expands to $300.0\text{ seconds}$ to eliminate redundant upstream calls.
3. **Adaptive Page Visibility Backoff**:
   - Listening on `document.addEventListener('visibilitychange', ...)`:
   - When the user tabs away (`document.hidden === true`), background polling is throttled by $10\times$ (from $15\text{ s}$ to $150\text{ s}$) and WebGL rendering stops, reducing client CPU/battery usage to zero.

---

### 4.3 Draft-07 JSON Data Schemas

#### Stock Thumbnail Data Schema (`StockThumbnailData.json`)
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "StockThumbnailData",
  "type": "object",
  "required": [
    "ticker",
    "company",
    "exchange",
    "currency",
    "current_price",
    "change_amount",
    "percentage_change",
    "sparkline",
    "data_source",
    "timestamp"
  ],
  "properties": {
    "ticker": { "type": "string", "example": "TCS" },
    "company": { "type": "string", "example": "Tata Consultancy Services Limited" },
    "exchange": { "type": "string", "enum": ["NSE", "BSE"], "default": "NSE" },
    "sector": { "type": "string", "example": "IT & Software" },
    "conglomerate_group": { "type": ["string", "null"], "example": "tata" },
    "currency": { "type": "string", "default": "INR" },
    "current_price": { "type": "number", "minimum": 0.01, "example": 4125.80 },
    "change_amount": { "type": "number", "example": 38.40 },
    "percentage_change": { "type": "number", "example": 0.94 },
    "day_high": { "type": "number", "example": 4150.00 },
    "day_low": { "type": "number", "example": 4085.20 },
    "trading_volume": { "type": "integer", "example": 1845920 },
    "filings_count_7d": { "type": "integer", "minimum": 0, "example": 3 },
    "importance_score_avg": { "type": "number", "minimum": 0, "maximum": 100, "example": 78.5 },
    "sparkline": {
      "type": "array",
      "description": "30 normalized intraday price points bounded in [0.0, 1.0]",
      "minItems": 30,
      "maxItems": 30,
      "items": { "type": "number", "minimum": 0.0, "maximum": 1.0 }
    },
    "data_source": {
      "type": "string",
      "enum": ["FINNHUB_WS", "YAHOO_FINANCE_BATCH", "ALPHA_VANTAGE", "OFFLINE_CACHE"]
    },
    "market_status": {
      "type": "string",
      "enum": ["OPEN", "CLOSED", "PRE_MARKET", "AFTER_HOURS"]
    },
    "timestamp": { "type": "string", "format": "date-time" }
  }
}
```

#### Circuit Breaker State Schema & State Machine
The circuit breaker monitors upstream API error rates and transitions through three operational states:

```
          +-------------------------------------------------------+
          |                      CLOSED                           |
          |  (Normal Operation: Requests sent to Tier 0 / Tier 1) |
          +-------------------------------------------------------+
                 |                                      ^
                 | 3 Consecutive Failures               | 5 Consecutive
                 | (HTTP 429, Timeout > 5s,             | Canary Successes
                 |  or Error Rate > 40%)                |
                 v                                      |
          +-------------------------------------------------------+
          |                       OPEN                            |
          |  (Fail-Fast: Upstream blocked, route to Tier 3 Cache) |
          +-------------------------------------------------------+
                 |
                 | 60-Second Cooldown Timer Expires
                 v
          +-------------------------------------------------------+
          |                    HALF-OPEN                          |
          |  (Canary Probe: 1 probe request routed upstream)      |
          +-------------------------------------------------------+
```

---

### 4.4 Backend Proxy Endpoints Specifications

#### 1. `GET /api/market/quotes`
- **Description**: Returns batch stock thumbnail market data for specified tickers.
- **Parameters**: `symbols` (comma-separated, e.g. `TCS,INFY,RELIANCE,TATAPOWER`).
- **Response Status**: `200 OK`
- **Response Headers**:
  - `Content-Type: application/json`
  - `Cache-Control: public, max-age=10, stale-while-revalidate=60`
  - `X-Data-Source: YAHOO_FINANCE_BATCH`
  - `X-Circuit-State: CLOSED`

#### 2. `GET /api/market/sparkline/{ticker}`
- **Description**: Delivers 30 normalized intraday price floats for high-fidelity canvas sparklines.
- **Parameters**: `ticker` (path parameter, e.g. `KAYNES`).
- **Response**:
  ```json
  {
    "ticker": "KAYNES",
    "points": [0.12, 0.15, 0.14, 0.22, 0.35, 0.48, 0.42, 0.55, 0.68, 0.72, 0.81, 0.85, 0.79, 0.88, 0.92, 0.95, 0.90, 0.94, 0.98, 1.0, 0.96, 0.92, 0.89, 0.85, 0.88, 0.91, 0.94, 0.96, 0.97, 0.99],
    "is_uptrend": true,
    "last_updated": "2026-11-15T15:45:00Z"
  }
  ```

#### 3. `WSS /api/market/stream`
- **Description**: WebSocket endpoint multiplexing Finnhub real-time trade ticks to the client.
- **Client Handshake**: `{"action": "subscribe", "symbols": ["TCS", "INFY", "TATAPOWER"]}`
- **Server Tick**: `{"type": "trade", "symbol": "TCS", "price": 4128.50, "timestamp": 1794757500000}`

---

## 5. Bi-Directional RAG & Chatbot Integration Protocols

### 5.1 Click-to-RAG Pipeline (3D Scene $\to$ Chatbot)

```
[ User Clicks Node in 3D Scene ] (e.g. INFY)
              |
              v
[ Three.js Raycaster Identifies Node ]
              |
              v
[ Camera Executes Kinematic Dolly & Focus (GSAP 0.95s) ]
              |
              v
[ Dispatch Custom Event: window.MarketTideBus.emit('market-tide:node-select') ]
              |
              v
[ Chatbot Drawer Catches Event & Switches to Tab 3: Explore Filings ]
              |
              v
[ Agent Decompiles Ticker & Executes Hybrid Retrieval ]
              |
              v
[ HybridRetriever: BM25Okapi + all-MiniLM-L6-v2 Dense Search fused via RRF ]
              |
              v
[ Displays Verified Source Cards with Direct PDF Link & AI Bullet Summary ]
```

#### Event Contract: `market-tide:node-select`
```typescript
interface NodeSelectEventDetail {
  ticker: string;              // e.g. "TATAPOWER"
  company: string;             // e.g. "Tata Power Company Limited"
  sector: string;              // e.g. "Energy & Power"
  conglomerateGroup?: string;  // e.g. "tata"
  importanceScore: number;     // e.g. 84
  filingCount: number;         // e.g. 5
  livePrice?: number;          // e.g. 438.20
  percentageChange?: number;   // e.g. 2.45
  sourcePDF?: string;          // e.g. "https://nsearchives.nseindia.in/...pdf"
  actionPrompt?: string;       // Default synthetic prompt: "Summarize recent filings for TATAPOWER"
}
```

---

### 5.2 Chatbot-to-3D Directive Pipeline (Chatbot $\to$ 3D Scene)

When a user submits a conversational prompt to Market Tide Mentor, `MarketTideAgent` classifies user intent, extracts entities, and synthesizes an answer while simultaneously publishing spatial directives:

```
[ User Types: "Show all Tata Group corporate actions this week" ]
                               |
                               v
               [ MarketTideAgent Intent Router ]
     (Detects Conglomerate Group: 'tata' + Intent: 'CONGLOMERATE')
                               |
                               +-----------------------------------------+
                               |                                         |
                               v                                         v
               [ Hybrid Retriever Execution ]            [ Publish SCENE_ACTION Directive ]
               - Retrieves filings across all 8           - Action: 'CLUSTER_CONGLOMERATE'
                 Tata subsidiaries                       - Group: 'tata'
               - Applies 6 grounding gates               - Tickers: [TATAPOWER, TCS, TATASTEEL...]
                               |                         - Visual: Amber Glow + Dim others
                               v                                         |
               [ LLM Evidence Synthesis ]                                v
               (Groq Llama-3.3-70b Stream)               [ Three.js Camera Flies to Tata Arm ]
               - Outputs Grounded Markdown Table         - 8 Tata cards illuminate
               - Generates Citations Dossier             - Non-matching 1,708 cards dim to 0.15
                                                         - Projected 3D vector rays connect nodes
```

#### Directive Contract: `SCENE_ACTION`
```json
{
  "action": "CLUSTER_CONGLOMERATE",
  "conglomerate_group": "tata",
  "target_tickers": [
    "TATAPOWER",
    "TMPV",
    "TATASTEEL",
    "TATACHEM",
    "TATACOMM",
    "TCS",
    "TMCV",
    "TTML"
  ],
  "visual_directives": {
    "camera_mode": "FOCUS_CLUSTER_CENTROID",
    "camera_transition_ms": 1100,
    "glow_color": "#f97316",
    "pulse_frequency_hz": 1.5,
    "dim_unmatched_opacity": 0.15,
    "render_connecting_rays": true,
    "ray_color": "rgba(249, 115, 22, 0.6)"
  }
}
```

---

### 5.3 Conglomerate Multi-Entity Mapping

`MarketTideAgent` maintains explicit taxonomies for 7 premier industrial business groups encompassing 33 major NSE equities:

| Business Group | RegEx Pattern Trigger | Registered Subsidiary Tickers | Core Sector Focus |
|---|---|---|---|
| **Tata Group** | `\b(tata\s+group\|tata\s+companies\|all\s+tata\|tata)\b` | `TATAPOWER`, `TMPV`, `TATASTEEL`, `TATACHEM`, `TATACOMM`, `TCS`, `TMCV`, `TTML` | Conglomerate / Multi-Industry |
| **Adani Group** | `\b(adani\s+group\|adani\s+companies\|all\s+adani\|adani)\b` | `ADANIENT`, `ADANIENSOL`, `ADANIPOWER` | Energy, Ports & Infrastructure |
| **Reliance Group** | `\b(reliance\s+group\|reliance\s+companies\|all\s+reliance\|reliance)\b` | `RELIANCE`, `RELINFRA`, `RPOWER`, `RCOM` | Oil & Gas, Telecom, Retail |
| **Aditya Birla Group** | `\b(birla\s+group\|birla\s+companies\|aditya\s+birla\|birla)\b` | `ABCAPITAL`, `ABFRL`, `ABSLAMC`, `BIRLACORPN`, `BIRLAMONEY`, `BIRLANU` | Financials, Retail, Cement |
| **Mahindra Group** | `\b(mahindra\s+group\|mahindra\s+companies\|all\s+mahindra\|mahindra)\b` | `M&M`, `TECHM`, `MAHLOG`, `M&MFIN`, `MHRIL`, `SMLMAH` | Automotive, IT, Logistics |
| **Godrej Group** | `\b(godrej\s+group\|godrej\s+companies\|all\s+godrej\|godrej)\b` | `GODREJIND`, `GODREJPROP`, `GODREJAGRO` | Real Estate, Consumer, Agro |
| **Bajaj Group** | `\b(bajaj\s+group\|bajaj\s+companies\|all\s+bajaj\|bajaj)\b` | `BAJFINANCE`, `BAJAJFINSV`, `BAJAJHIND` | Non-Bank Finance, Automotive |

---

### 5.4 Hybrid Retrieval Pipeline & Dead-Code Fix Specification

#### Mathematical RRF Formula in `retriever.py`
For each candidate disclosure document $d$:

$$RRF\_Score(d) = \sum_{m \in \{BM25, Dense\}} \frac{1}{60 + \text{rank}_m(d)}$$

where candidate documents are generated by dense semantic embeddings ($384\text{-dimensional}$ `all-MiniLM-L6-v2`) and BM25Okapi lexical matching over rich chunk text:
$$\text{chunk}(d) = \text{Date} + \text{Time} + \text{Exchange} + \text{Company} + \text{Ticker} + \text{Category} + \text{Tag} + \text{Headline} + \text{Description}$$

#### 6-Level Grounding Gates
1. **Empty Query Rejection**: Queries with 0 non-stopword tokens return `[]` immediately.
2. **Dense Noise Floor Gate**: Top dense cosine similarity must be $\ge 0.35$.
3. **Lexical Grounding Gate**: BM25 score must be $> 0.0$ to prevent semantic hallucinations on zero-filing tickers.
4. **Multi-Word Coverage Gate**: Multi-word queries ($\ge 2$ tokens) require $\ge 50\%$ term coverage across candidate chunks.
5. **Dual Relevance Threshold**: If dense score is in $[0.35, 0.42)$, BM25 score must be $\ge 10.0$.
6. **Distinctive Subject Grounding**: Non-generic subject tokens must match at least one candidate document's token set.

#### Implementation Fix: `chatbot/agent.py` Line 491
In `chatbot/agent.py`, lines 488–496 currently read:
```python
            # Single confirmed company
            ticker = resolved[0]["ticker"]
            docs = self.tools.get_company_filings(ticker, top_k=6)
            return docs, f"company:{resolved[0]['company']} ({ticker})"
        return [], "company:not_found"

        # General hybrid search with strict relevance cutoff
        docs = self.tools.hybrid_search(query, top_k=6, use_hybrid=use_hybrid)
        return docs, "general_hybrid"
```
**Specification Fix**: Change line 491 to allow un-resolved company queries to fall through to general hybrid retrieval:
```python
            # Single confirmed company
            ticker = resolved[0]["ticker"]
            docs = self.tools.get_company_filings(ticker, top_k=6)
            return docs, f"company:{resolved[0]['company']} ({ticker})"

        # General hybrid search with strict relevance cutoff
        docs = self.tools.hybrid_search(query, top_k=6, use_hybrid=use_hybrid)
        return docs, "general_hybrid"
```

---

## 6. UI/UX Design System Specifications

Adhering strictly to `ui-ux-pro-max` and `ui-styling` design systems, MarketTide implements a dual-theme executive workstation aesthetic:

### 6.1 Design Tokens & CSS Variable Architecture

```css
/* =========================================================================
   THEME 1: FINTECH TERMINAL OBSIDIAN (Default Dark 3D Workstation)
   ========================================================================= */
:root[data-theme="dark"], :root.dark {
  --c-bg: 10 15 29;               /* #0a0f1d deep obsidian canvas */
  --c-surface: 30 41 59;          /* #1e293b glassmorphic card surface */
  --c-surface-hover: 51 65 85;    /* #334155 card highlight */
  --c-ink: 248 250 252;           /* #f8fafc high-contrast text (10.8:1) */
  --c-muted: 148 163 184;         /* #94a3b8 secondary metrics */
  --c-border: 51 65 85;           /* #334155 subtle glass border */
  --c-accent: 6 182 212;          /* #06b6d4 cyber cyan accent */
  --c-accent-glow: 6 182 212 0.35;/* cyan ambient bloom */
  --c-brand-flame: 249 115 22;    /* #f97316 luminous amber */
  --c-good: 16 185 129;           /* #10b981 emerald wealth uptick */
  --c-good-soft: 6 78 59;         /* #064e3b dark emerald pill */
  --c-bad: 239 68 68;             /* #ef4444 ruby loss downtick */
  --c-bad-soft: 127 29 29;        /* #7f1d1d dark ruby pill */
  --c-warn: 245 158 11;           /* #f59e0b amber alert */
}

/* =========================================================================
   THEME 2: WARM FINANCIAL EXECUTIVE PALETTE (MedEvolv / Accumulate AI Light)
   ========================================================================= */
:root[data-theme="light"] {
  --c-bg: 247 244 238;            /* #f7f4ee warm sand / oat canvas */
  --c-surface: 255 255 255;       /* #ffffff pure white card */
  --c-surface2: 243 239 231;      /* #f3efe7 soft almond surface */
  --c-ink: 28 25 23;              /* #1c1917 espresso stone ink */
  --c-muted: 120 113 108;         /* #78716c warm stone secondary */
  --c-border: 228 223 214;        /* #e4dfd6 warm sandstone border */
  --c-accent: 217 119 6;          /* #d97706 warm terracotta orange */
  --c-good: 22 101 52;            /* #166534 deep forest wealth */
  --c-good-soft: 220 252 231;     /* #dcfce7 soft mint green pill */
  --c-bad: 185 28 28;             /* #b91c1c deep crimson loss */
  --c-bad-soft: 254 226 226;      /* #fee2e2 soft rose pill */
}

/* TYPOGRAPHY TOKENS */
:root {
  --font-sans: 'Instrument Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  --font-mono: 'IBM Plex Mono', 'Fira Code', ui-monospace, Menlo, Consolas, monospace;
}
```

---

### 6.2 Component Hierarchy & Layout Wireframe

```
+-----------------------------------------------------------------------------------------------------------------+
|  [Logo] MARKET TIDE AI  |  NIFTY 50: 24,148.20 (+0.42%)  |  SENSEX: 79,486.30 (+0.38%)  |  Mode: [GALAXY v]   | [Theme]
+-----------------------------------------------------------------------------------------------------------------+
|                                                                                       |                         |
|                                       [ Floating Omnibar ]                            |   Market Tide Mentor    |
|                          🔍 Filter 1,716 stocks or ask Dalal St...                    |   (Collapsible Drawer)  |
|                      [All] [IT] [Banking] [Auto] [Pharma] [Energy] [Tata]             |                         |
|                                                                                       |  [💬 Ask] [🔍 DAG] [🧭] |
|                                                                                       |-------------------------|
|                                                                                       |                         |
|                                                                                       |  User: "Tata Group?"    |
|                                                                                       |                         |
|                                                                                       |  Mentor:                |
|                                                                                       |  Audited 8 Tata entities|
|                                                                                       |  found in week filings. |
|                                 (3D Stock Nebula WebGL)                               |                         |
|                                                                                       |  +-------------------+  |
|                                                                                       |  | TCS (NSE: TCS)    |  |
|                                                                                       |  | Q2 Net Profit     |  |
|                                                                                       |  | +12.4% YoY        |  |
|                                                                                       |  | [PDF Filing ↗]    |  |
|                                                                                       |  +-------------------+  |
|                                                                                       |                         |
|                                                                                       |  +-------------------+  |
|                                                                                       |  | TATAPOWER         |  |
|                                                                                       |  | Commissioned 400MW|  |
|                                                                                       |  | Solar JV in Guj.  |  |
|                                                                                       |  | [PDF Filing ↗]    |  |
|  [+] Zoom In                                                                          |  +-------------------+  |
|  [-] Zoom Out                                                                         |                         |
|  [O] Reset View                                                                       |  [ Input Query...    ]  |
|  [3D Axis Gizmo]                                                                      |                         |
+-----------------------------------------------------------------------------------------------------------------+
```

---

### 6.3 WCAG 2.1 AA Accessibility Specification

1. **Text Contrast Compliance**:
   - Primary Ink (`#f8fafc`) on Obsidian (`#0a0f1d`): Contrast ratio **$16.8:1$** (Exceeds $4.5:1$ requirement).
   - Secondary Muted (`#94a3b8`) on Obsidian: Contrast ratio **$7.2:1$**.
   - Wealth Green (`#10b981`) on Dark Pill (`#064e3b`): Contrast ratio **$5.4:1$**.
2. **Keyboard Navigation Support**:
   - The WebGL canvas maintains a parallel accessible HTML DOM Virtual Tree (`<div role="region" aria-label="3D Stock Constellation">`).
   - `WASD` / `Arrow Keys`: Translate camera laterally through the galaxy plane.
   - `Tab` / `Shift+Tab`: Cycles through visible stocks in order of importance score.
   - `Enter` / `Space`: Selects stock, triggers kinematic flight, and opens RAG filings drawer.
3. **Screen Reader Live Announcements**:
   - `<div aria-live="polite" class="sr-only" id="sr-market-announcer">`: Announces real-time price changes on focused stocks (e.g. *"Tata Motors up 1.8 percent to rupees 782"*).
4. **Reduced Motion Adaptation (`prefers-reduced-motion`)**:
   ```css
   @media (prefers-reduced-motion: reduce) {
     * {
       animation-duration: 0.01ms !important;
       transition-duration: 0.01ms !important;
     }
   }
   ```
   When active, Three.js auto-rotation is disabled, and GSAP camera dollys transition instantly without tweening.

---

## 7. Verification, Testing & Implementation Roadmap

### 7.1 Automated TDD Test Suite Specification

```
tests/
 ├── test_threejs_scene_graph.py        # Validates draw calls <= 35, triangles <= 80k
 ├── test_market_api_cascade.py         # Unit tests Tier 0 -> Tier 1 -> Tier 2 -> Tier 3 failover
 ├── test_token_bucket_limiter.py       # Simulates 120 calls in 10s; verifies strict 60/min compliance
 ├── test_circuit_breaker.py            # Simulates 3 upstream timeouts; verifies OPEN -> HALF-OPEN recovery
 ├── test_rag_event_bus.py              # Validates typed JSON contracts across window.postMessage
 ├── test_conglomerate_multi_hop.py     # Verifies all 33 conglomerate entities map to parent houses
 └── test_wcag_accessibility.py        # Axe-core automated contrast and DOM keyboard audit
```

### 7.2 4-Phase Implementation Roadmap

```
+----------------------------------------------------------------------------------------------------+
|                                    4-Phase Implementation Roadmap                                  |
+----------------------------------------------------------------------------------------------------+
|  Phase 1: Three.js 3D Core & Market Proxy Engine                                   Weeks 1–2       |
|  - Implement WebGL scene graph, PerspectiveCamera, OrbitControls damping, and ResizeObserver.      |
|  - Implement Mode 1 (Spherical Fibonacci) and Mode 2 (Sector Logarithmic Spiral) layouts.          |
|  - Stand up FastAPI backend proxy with Token Bucket ($C=60, r=1$) and Yahoo Finance Batch REST.     |
|  - Establish Tier 3 Offline Deterministic Brownian Replay for air-gapped test validation.          |
+----------------------------------------------------------------------------------------------------+
|  Phase 2: Dynamic CanvasTextures, Shaders & Bi-Directional Bus                     Weeks 3–4       |
|  - Build $512 \times 288$ CanvasTexture card generator with bezier sparkline curve algorithms.     |
|  - Implement custom GLSL ShaderMaterial (edge glow, uptick/downtick flash, distance fog).          |
|  - Establish `window.MarketTideBus` event bridge between WebGL canvas and Streamlit chatbot iframe.|
|  - Implement Click-to-RAG filing dossier trigger and query decomposition in `MarketTideAgent`.     |
+----------------------------------------------------------------------------------------------------+
|  Phase 3: Performance Hardening, LOD Optimization & Web Workers                    Weeks 5–6       |
|  - Implement 3-Tier Level-of-Detail (LOD 0 pooled cards, LOD 1 InstancedMesh, LOD 2 Starfield).    |
|  - Implement Mode 3 (3D Force-Directed Correlation Matrix) inside dedicated Web Worker.             |
|  - Connect Finnhub WebSocket (`wss://ws.finnhub.io`) for real-time Tier 0 active viewport quotes.  |
|  - Resolve `chatbot/agent.py` line 491 dead-code bug and verify 100% test harness loop pass rate.  |
+----------------------------------------------------------------------------------------------------+
|  Phase 4: UI/UX HUD Polishing, WCAG 2.1 AA Audit & Production Cutover             Weeks 7–8       |
|  - Implement Glassmorphic Top Portfolio HUD, Centered Floating Omnibar, and 3D Axis Gizmo.        |
|  - Complete DOM Virtual Tree for keyboard navigation (WASD/arrows) and VoiceOver/NVDA support.     |
|  - Execute 20-iteration adversarial challenger loop verification; verify 0 draw call leaks.        |
|  - Final deployment to Render blueprint (`render.yaml`) and documentation sign-off.                |
+----------------------------------------------------------------------------------------------------+
```

---

## 8. Architectural Consistency & Verification Sign-Off

This PRD has been verified against the physical codebase files and dependencies:
- **`markettide-rag-team/chatbot/agent.py`**: Fully aligned with `MarketTideAgent`, `CONGLOMERATE_GROUPS`, and intent routing.
- **`markettide-rag-team/chatbot/retriever.py`**: Fully aligned with `HybridRetriever`, `BM25Okapi`, MiniLM vectors, and RRF fusion ($k=60$).
- **`markettide-rag-team/chatbot/app.py`**: Fully aligned with MedEvolv Mentor layout, timeline tracking, and verified source cards.
- **`markettide-rag-team/site/index.html`**: Fully aligned with Accumulate AI design tokens, typography, and workstation ergonomics.
- **`markettide-rag-team/data/filings_last_7_days.csv`**: Grounded in all 2,766 corporate announcements and 1,716 unique NSE equities.

*Document authorized by Project Orchestrator, Chief of Staff, and Lead UI/UX Architect.*  
*Ready for immediate engineering sprint execution.*
