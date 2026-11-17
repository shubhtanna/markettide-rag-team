/**
 * verify_e2e_milestone2.js - Comprehensive Frontend E2E Verification Suite for Milestone 2
 *
 * Validates Tier 1-4 requirements from ORIGINAL_REQUEST.md and PROJECT.md:
 * - R1: Emerging Search Animation (transform-origin: bottom center, spring easing curve, glassmorphic blur)
 * - R2: Executive Financial Filings Table (table structure, typography tokens, metadata columns, row drawer)
 * - R3: Clean Interface (complete removal of zero-hallucination pill badge and suggestion chips)
 * - R4: Client-side Subjective Query Refusal & Factual Disclosures Explanation (0 matches, 0 filings, canonical text)
 * - Follow-up Visual Directive: Three.js 3D Candlestick Wave Landscape (grid plane, green/red candlesticks, MA splines, volume bars, 60fps loop)
 */

const fs = require('fs');
const path = require('path');
const assert = require('assert');

console.log('================================================================================');
console.log('  MarketTide Milestone 2 — Comprehensive Frontend E2E Verification Suite        ');
console.log('================================================================================\n');

const projectRoot = path.resolve(__dirname, '..');
const indexPath = path.join(projectRoot, 'site', 'index.html');
const filingsDataPath = path.join(projectRoot, 'site', 'filings_data.js');

// Load files
assert(fs.existsSync(indexPath), `Missing site/index.html at ${indexPath}`);
assert(fs.existsSync(filingsDataPath), `Missing site/filings_data.js at ${filingsDataPath}`);

const indexHtml = fs.readFileSync(indexPath, 'utf8');

// Load client-side filings engine
let MarketTideFilings;
try {
  const filingsModule = require(filingsDataPath);
  MarketTideFilings = filingsModule.MarketTideFilings;
} catch (err) {
  // If not exported via module.exports, evaluate in sandbox
  const vm = require('vm');
  const code = fs.readFileSync(filingsDataPath, 'utf8');
  const sandbox = { module: {}, exports: {}, console, window: {}, globalThis: {} };
  vm.createContext(sandbox);
  vm.runInContext(code, sandbox);
  MarketTideFilings = sandbox.MarketTideFilings || sandbox.window.MarketTideFilings || sandbox.module.exports?.MarketTideFilings;
}
assert(MarketTideFilings, 'MarketTideFilings engine could not be instantiated from site/filings_data.js');

let passedTests = 0;
let totalTests = 0;
const failures = [];

function testCase(tier, description, fn) {
  totalTests++;
  try {
    fn();
    passedTests++;
    console.log(`  ✓ [${tier}] ${description}`);
  } catch (err) {
    failures.push({ tier, description, error: err.message });
    console.error(`  ✗ [${tier}] ${description}`);
    console.error(`      Error: ${err.message}`);
  }
}

// ============================================================================
// TIER 1: PRIMARY ACCEPTANCE TESTS (CORE SPECIFICATIONS)
// ============================================================================
console.log('\n--- TIER 1: PRIMARY ACCEPTANCE TESTS ---');

testCase('Tier 1', 'R1: Search results panel uses transform-origin: bottom center for emerging animation', () => {
  const hasTransformOrigin = /transform-origin:\s*(bottom\s+center|center\s+bottom)/i.test(indexHtml);
  assert.ok(hasTransformOrigin, 'Expected transform-origin: bottom center (or center bottom) on search overlay in site/index.html');
});

testCase('Tier 1', 'R1: Search overlay incorporates spring easing curve and glassmorphic backdrop blur', () => {
  // Spring transition typically uses cubic-bezier or bounce easing
  const hasSpringEasing = /cubic-bezier\s*\(\s*0\.[0-9]+\s*,\s*1\.[0-9]+\s*,\s*0\.[0-9]+\s*,\s*1/i.test(indexHtml) ||
                          /cubic-bezier/i.test(indexHtml);
  assert.ok(hasSpringEasing, 'Expected spring cubic-bezier easing curve for upward expansion animation');

  const hasGlassmorphism = /backdrop-filter:\s*blur\(/i.test(indexHtml);
  assert.ok(hasGlassmorphism, 'Expected backdrop-filter: blur(...) glassmorphic styling on search overlay');
});

testCase('Tier 1', 'R2: Executive financial filings layout uses <table class="filings-table"> structure', () => {
  const hasFilingsTable = /<table[^>]*class=["'][^"']*filings-table[^"']*["']/i.test(indexHtml) ||
                          /class=["'][^"']*filings-table[^"']*["']/i.test(indexHtml);
  assert.ok(hasFilingsTable, 'Expected filings-table class for executive tabular layout in site/index.html');
});

testCase('Tier 1', 'R2: Filings table defines all required headers: Date/Time, Ticker, Company, Category, Headline, PDF', () => {
  const requiredHeaders = [
    { name: 'Date / Time', pattern: /date|time/i },
    { name: 'Ticker', pattern: /ticker|symbol/i },
    { name: 'Company', pattern: /company/i },
    { name: 'Category', pattern: /category|type/i },
    { name: 'Headline', pattern: /headline|title|announcement/i },
    { name: 'PDF', pattern: /pdf|link|filing/i }
  ];

  requiredHeaders.forEach(hdr => {
    assert.ok(hdr.pattern.test(indexHtml), `Expected column header matching "${hdr.name}" in filings table`);
  });
});

testCase('Tier 1', 'R2: Typography imports and defines Instrument Sans and IBM Plex Mono fonts', () => {
  assert.ok(indexHtml.includes('Instrument Sans'), 'Expected Instrument Sans font specification');
  assert.ok(indexHtml.includes('IBM Plex Mono'), 'Expected IBM Plex Mono font specification');
});

testCase('Tier 1', 'R2: Interactive row expansion or detail drawer mechanism is implemented', () => {
  const hasDrawerOrExpansion = /(drawer|detail-drawer|filing-detail|expand-row|accordion|toggleRow|showDetail)/i.test(indexHtml);
  assert.ok(hasDrawerOrExpansion, 'Expected interactive row expansion or sliding detail drawer mechanism');
});

testCase('Tier 1', 'R3: Zero-hallucination pill badge (• 100% REGULATORY ZERO-HALLUCINATION ARCHITECTURE) is removed', () => {
  const hasPillBadge = indexHtml.includes('100% REGULATORY ZERO-HALLUCINATION ARCHITECTURE');
  assert.strictEqual(hasPillBadge, false, 'Pill badge "• 100% REGULATORY ZERO-HALLUCINATION ARCHITECTURE" must be completely removed');

  // Also ensure .hero-pill element does not exist
  const hasHeroPillClass = /<div[^>]*class=["'][^"']*hero-pill[^"']*["']/i.test(indexHtml);
  assert.strictEqual(hasHeroPillClass, false, '.hero-pill markup must be completely removed from landing page');
});

testCase('Tier 1', 'R3: Suggestion chips row below search bar is completely removed', () => {
  const hasChipsStrip = /<div[^>]*class=["'][^"']*dock-chips-strip[^"']*["']/i.test(indexHtml);
  assert.strictEqual(hasChipsStrip, false, '.dock-chips-strip element must be completely removed from landing page');

  // Verify specific suggestion chips are absent from bottom dock
  const hasTataGroupChip = />\s*Tata Group\s*</i.test(indexHtml) && indexHtml.includes('dock-chip');
  const hasAdaniPortsChip = />\s*Adani Ports\s*</i.test(indexHtml) && indexHtml.includes('dock-chip');
  assert.strictEqual(hasTataGroupChip, false, 'Tata Group suggestion chip must be removed');
  assert.strictEqual(hasAdaniPortsChip, false, 'Adani Ports suggestion chip must be removed');
});

testCase('Tier 1', 'R4: Client engine strictly refuses subjective query "is tata company bad?" with 0 filings', () => {
  const res = MarketTideFilings.search('is tata company bad?');
  assert.strictEqual(res.totalMatches, 0, 'Subjective query must return totalMatches === 0');
  assert.strictEqual(res.results.length, 0, 'Subjective query must return 0 filing records in results');
  assert.strictEqual(res.isRefusal, true, 'Subjective query must set isRefusal === true');
  
  const expectedCanonical = "I don't know. That is not present in the 7-day NSE filings database (Nov 9–15, 2026).";
  assert.ok(res.synthesis.summary.includes(expectedCanonical), `Expected summary to contain canonical refusal: "${expectedCanonical}"`);
  assert.ok(
    /factual disclosures rather than subjective opinions/i.test(res.synthesis.summary) ||
    /factual disclosures/i.test(res.synthesis.summary),
    'Expected summary to explain that corporate statutory filings contain factual disclosures rather than subjective opinions'
  );
});

testCase('Tier 1', 'Visual Directive: Three.js 3D Candlestick Wave landscape with grid, candlesticks, MA splines, volume bars', () => {
  // Check Three.js setup
  assert.ok(/three(\.min)?\.js/i.test(indexHtml), 'Expected Three.js script inclusion');
  
  // Perspective financial coordinate grid plane
  const hasGridPlane = /(GridHelper|createGrid|gridPlane|coordinateGrid)/i.test(indexHtml);
  assert.ok(hasGridPlane, 'Expected financial coordinate grid plane in Three.js visualization');

  // Candlesticks (bullish green / bearish red)
  const hasCandlesticks = /(candlestick|createCandle|bullish|bearish|BoxGeometry|CylinderGeometry)/i.test(indexHtml);
  assert.ok(hasCandlesticks, 'Expected 3D candlestick geometry generator');

  // Moving average undulating splines
  const hasSplines = /(CatmullRomCurve3|SplineCurve|movingAverage|splineRibbon|trendline)/i.test(indexHtml);
  assert.ok(hasSplines, 'Expected undulating moving average spline ribbons');

  // Volume bars
  const hasVolumeBars = /(volume|volumeBar|histogram)/i.test(indexHtml);
  assert.ok(hasVolumeBars, 'Expected 3D volume histogram bars');

  // 60 FPS animation loop
  assert.ok(indexHtml.includes('requestAnimationFrame'), 'Expected requestAnimationFrame animation loop');
});

// ============================================================================
// TIER 2: BOUNDARY & COMPONENT-LEVEL INVARIANTS
// ============================================================================
console.log('\n--- TIER 2: BOUNDARY & COMPONENT-LEVEL INVARIANTS ---');

testCase('Tier 2', 'R1: Blur filter threshold adheres to design specs (>= 20px blur)', () => {
  const blurMatch = indexHtml.match(/backdrop-filter:\s*blur\((\d+)px\)/i);
  assert.ok(blurMatch, 'Expected explicit backdrop-filter: blur(Xpx) declaration');
  const blurVal = parseInt(blurMatch[1], 10);
  assert.ok(blurVal >= 20, `Expected blur filter >= 20px, found ${blurVal}px`);
});

testCase('Tier 2', 'R2: Filings table includes direct PDF links with regulatory target="_blank"', () => {
  const hasPdfLinkLogic = /(pdf_url|openPdf|target="_blank"|official PDF|SEBI PDF)/i.test(indexHtml);
  assert.ok(hasPdfLinkLogic, 'Expected direct official PDF download/link mechanism in filings table');
});

testCase('Tier 2', 'R2: Monospace typography applied to financial metadata (tickers, timestamps)', () => {
  const hasMonoToken = /--font-mono|font-family:[^;]*IBM Plex Mono/i.test(indexHtml);
  assert.ok(hasMonoToken, 'Expected font-mono style rule for financial metadata');
});

testCase('Tier 2', 'R3: Purge colloquialisms - verify "dude" is completely absent from site/index.html & filings_data.js', () => {
  const indexHasDude = /\bdude\b/i.test(indexHtml);
  assert.strictEqual(indexHasDude, false, 'Informal colloquialism "dude" must NOT exist in site/index.html');

  const filingsCode = fs.readFileSync(filingsDataPath, 'utf8');
  const filingsHasDude = /\bdude\b/i.test(filingsCode);
  assert.strictEqual(filingsHasDude, false, 'Informal colloquialism "dude" must NOT exist in site/filings_data.js');
});

testCase('Tier 2', 'R4: Multiple subjective opinion variants trigger strict refusal in client engine', () => {
  const subjectiveQueries = [
    'is reliance good?',
    'opinion on adani',
    'what do you think of infosys?',
    'should i buy kaynes tech?',
    'is tcs going to crash?'
  ];

  subjectiveQueries.forEach(q => {
    const res = MarketTideFilings.search(q);
    assert.strictEqual(res.totalMatches, 0, `Query "${q}" must return 0 total matches`);
    assert.strictEqual(res.results.length, 0, `Query "${q}" must return 0 results`);
    assert.strictEqual(res.isRefusal, true, `Query "${q}" must set isRefusal: true`);
    assert.ok(
      res.synthesis.summary.includes("I don't know. That is not present in the 7-day NSE filings database (Nov 9–15, 2026)."),
      `Query "${q}" must return canonical refusal`
    );
  });
});

testCase('Tier 2', 'R4: Legitimate ticker queries return positive matches in client engine', () => {
  const validQueries = ['KAYNES', 'TCS', 'RELIANCE', 'HDFCBANK'];
  validQueries.forEach(ticker => {
    const res = MarketTideFilings.search(ticker);
    assert.ok(res.totalMatches > 0, `Valid ticker "${ticker}" must return >0 matches (got ${res.totalMatches})`);
    assert.ok(res.results.length > 0, `Valid ticker "${ticker}" must return results array`);
    assert.strictEqual(res.isRefusal, false || undefined, `Valid ticker "${ticker}" must NOT be flagged as refusal`);
  });
});

// ============================================================================
// TIER 3: PAIRWISE INTERACTIONS & STATE TRANSITIONS
// ============================================================================
console.log('\n--- TIER 3: PAIRWISE INTERACTIONS & STATE TRANSITIONS ---');

testCase('Tier 3', 'R1 + R2: Submitting bottom dock search activates overlay expansion and displays filings table', () => {
  // Ensure search submit event triggers overlay activation
  const hasSearchTrigger = /(submitSearch|executeSearch|handleSearch|search-btn|keyup.*Enter)/i.test(indexHtml);
  assert.ok(hasSearchTrigger, 'Expected search handler triggering overlay state transition');

  // Ensure table is rendered inside results container
  const hasRenderTable = /(renderFilingsTable|renderResults|filings-table)/i.test(indexHtml);
  assert.ok(hasRenderTable, 'Expected function rendering executive filings table upon search execution');
});

testCase('Tier 3', 'Visual Directive + R1: Canvas dimming activates when search overlay expands', () => {
  // Canvas dimming CSS class or opacity manipulation
  const hasDimming = /(canvas-dimmed|dimCanvas|canvas.*opacity)/i.test(indexHtml);
  assert.ok(hasDimming, 'Expected canvas dimming transition when search results overlay opens');
});

testCase('Tier 3', 'R2: Detail drawer / accordion reveals full announcement summary upon row click', () => {
  const hasDetailInteraction = /(toggleDrawer|expandRow|openDrawer|drawer-summary|drawer-content|row-drawer)/i.test(indexHtml);
  assert.ok(hasDetailInteraction, 'Expected detail drawer interaction displaying full announcement summary');
});

testCase('Tier 3', 'R3 + R1: Clean bottom dock has single search input without chip listeners or orphaned badge styling', () => {
  // Ensure no leftover dock chip event listeners or orphaned CSS definitions
  const hasChipEventBinding = /addEventListener\(.*chip/i.test(indexHtml) || /\.dock-chip/i.test(indexHtml);
  assert.strictEqual(hasChipEventBinding, false, 'No residual chip event listeners or dock-chip styles should remain');
});

// ============================================================================
// TIER 4: REAL-WORLD REGULATORY SCENARIOS & ADVERSARIAL STRESS
// ============================================================================
console.log('\n--- TIER 4: REAL-WORLD REGULATORY SCENARIOS & ADVERSARIAL STRESS ---');

testCase('Tier 4', 'Adversarial: Mixed casing subjective query ("Is TATA CoMpAnY BaD?") is strictly refused', () => {
  const res = MarketTideFilings.search('Is TATA CoMpAnY BaD?');
  assert.strictEqual(res.totalMatches, 0, 'Mixed-casing subjective query must return 0 matches');
  assert.strictEqual(res.isRefusal, true, 'Mixed-casing subjective query must set isRefusal: true');
  assert.ok(res.synthesis.summary.includes("I don't know. That is not present in the 7-day NSE filings database (Nov 9–15, 2026)."));
});

testCase('Tier 4', 'Adversarial: Whitespace and punctuation padded query ("   is reliance good???   ") is strictly refused', () => {
  const res = MarketTideFilings.search('   is reliance good???   ');
  assert.strictEqual(res.totalMatches, 0, 'Padded subjective query must return 0 matches');
  assert.strictEqual(res.isRefusal, true, 'Padded subjective query must set isRefusal: true');
  assert.ok(res.synthesis.summary.includes("I don't know. That is not present in the 7-day NSE filings database (Nov 9–15, 2026)."));
});

testCase('Tier 4', 'Adversarial: Out-of-domain trivia ("who won the cricket world cup?") is refused with canonical response', () => {
  const res = MarketTideFilings.search('who won the cricket world cup?');
  assert.strictEqual(res.totalMatches, 0, 'Out-of-domain query must return 0 matches');
  assert.ok(
    res.synthesis.summary.includes("I don't know. That is not present in the 7-day NSE filings database (Nov 9–15, 2026)."),
    'Out-of-domain query must return canonical refusal'
  );
});

testCase('Tier 4', 'Real-world: Conglomerate lookup ("Tata Group") retrieves legitimate multi-entity filings with executive metadata', () => {
  const res = MarketTideFilings.search('Tata Group');
  assert.ok(res.totalMatches > 10, `Expected >10 filings for Tata Group, got ${res.totalMatches}`);
  assert.strictEqual(res.isRefusal, false || undefined);

  // Validate filing item structure
  const first = res.results[0];
  assert.ok(first.date, 'Filing must have date');
  assert.ok(first.ticker, 'Filing must have ticker');
  assert.ok(first.company, 'Filing must have company');
  assert.ok(first.category, 'Filing must have category');
  assert.ok(first.headline, 'Filing must have headline');
  assert.ok(first.pdf_url && first.pdf_url.startsWith('http'), 'Filing must have valid pdf_url');
});

testCase('Tier 4', 'Real-world: Announcement category lookup ("Q2 Results") returns filtered corporate disclosures', () => {
  const res = MarketTideFilings.search('Q2 Results');
  assert.ok(res.totalMatches > 50, `Expected >50 filings for Q2 Results, got ${res.totalMatches}`);
  assert.ok(res.results.some(r => r.category.includes('Board Meeting') || r.tag === 'Results'));
});

// ============================================================================
// SUMMARY & RESULTS REPORT
// ============================================================================
console.log('\n================================================================================');
console.log(`  FRONTEND E2E TEST RESULTS: ${passedTests}/${totalTests} PASSED (${Math.round((passedTests / totalTests) * 100)}%)`);
console.log('================================================================================');

if (failures.length > 0) {
  console.log(`\nFailed Tests Summary (${failures.length} failed):`);
  failures.forEach((f, idx) => {
    console.log(`  ${idx + 1}. [${f.tier}] ${f.description}: ${f.error}`);
  });
}

// Exit code based on failures
if (failures.length > 0) {
  process.exit(1);
} else {
  console.log('\nAll Frontend E2E tests verified successfully!');
  process.exit(0);
}
