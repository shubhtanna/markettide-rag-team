import re

# 1. Update filings_data.js
filings_data_path = 'markettide-rag-team/site/filings_data.js'
with open(filings_data_path, 'r', encoding='utf-8') as f:
    fdata = f.read()

s_marker = "    search(query, options = {}) {"
e_marker = "  global.MarketTideFilings = MarketTideFilingsEngine;"

s_idx = fdata.find(s_marker)
e_idx = fdata.find(e_marker)

if s_idx == -1 or e_idx == -1:
    print(f"Error finding markers in filings_data.js: s={s_idx}, e={e_idx}")
    exit(1)

new_filings_search_code = '''    search(query, options = {}) {
      if (!query || typeof query !== 'string' || !query.trim()) {
        return {
          query: '',
          results: [],
          totalMatches: 0,
          synthesis: null,
          matchedTicker: null,
          matchedConglomerate: null
        };
      }

      const qRaw = query.trim();
      const qLower = qRaw.toLowerCase();
      const qClean = qLower.replace(/[^a-z0-9\\s]/g, ' ').replace(/\\s+/g, ' ').trim();

      // Disallowed generic dictionary words that cannot trigger single-word company matches
      const DISALLOWED_GENERIC_WORDS = new Set([
        'smart', 'tea', 'market', 'world', 'chip', 'power', 'clean', 'fast', 'future',
        'prime', 'first', 'global', 'time', 'care', 'force', 'group', 'india', 'international',
        'industries', 'enterprises', 'services', 'solutions', 'limited', 'ltd', 'stack', 'digi',
        'think', 'yourself', 'very', 'good', 'bad', 'best', 'worst', 'great', 'life', 'happy',
        'love', 'god', 'gods', 'dumb', 'stupid', 'idiot', 'clever', 'fool', 'bot', 'assistant'
      ]);

      const STOP_WORDS = new Set([
        'a', 'about', 'above', 'after', 'again', 'against', 'all', 'am', 'an', 'and', 'any', 'are', 'aren',
        'as', 'at', 'be', 'because', 'been', 'before', 'being', 'below', 'between', 'both', 'but', 'by',
        'can', 'could', 'did', 'didn', 'do', 'does', 'doesn', 'doing', 'don', 'down', 'during', 'each',
        'few', 'for', 'from', 'further', 'had', 'hadn', 'has', 'hasn', 'have', 'haven', 'having', 'he',
        'her', 'here', 'hers', 'herself', 'him', 'himself', 'his', 'how', 'i', 'if', 'in', 'into', 'is',
        'isn', 'it', 'its', 'itself', 'just', 'me', 'might', 'more', 'most', 'my', 'myself', 'no', 'nor',
        'not', 'now', 'of', 'off', 'on', 'once', 'only', 'or', 'other', 'our', 'ours', 'ourselves', 'out',
        'over', 'own', 's', 'same', 'she', 'should', 'so', 'some', 'such', 't', 'than', 'that', 'the',
        'their', 'theirs', 'them', 'themselves', 'then', 'there', 'these', 'they', 'this', 'those', 'through',
        'to', 'too', 'under', 'until', 'up', 'very', 'was', 'wasn', 'we', 'were', 'weren', 'what', 'when',
        'where', 'which', 'while', 'who', 'whom', 'why', 'will', 'with', 'won', 'would', 'you', 'your',
        'yours', 'yourself', 'yourselves'
      ]);

      // 1. Direct Conversational / Rhetorical / Assistant Address (e.g. "do you think yourself as very smart?", "are you dumb??")
      const isConversational = /\\b(do\\s+you|did\\s+you|can\\s+you|could\\s+you|will\\s+you|would\\s+you|are\\s+you|aren't\\s+you|ain't\\s+you|who\\s+are\\s+you|what\\s+are\\s+you|how\\s+are\\s+you|why\\s+are\\s+you|where\\s+are\\s+you|tell\\s+me|help\\s+me|talk\\s+to\\s+me|am\\s+i|who\\s+am\\s+i|what\\s+am\\s+i|do\\s+i|are\\s+we|you\\s+think|yourself|you\\s+dumb|you\\s+smart|are\\s+you\\s+dumb|are\\s+you\\s+smart|you\\s+stupid|you\\s+idiot|your\\s+name|your\\s+opinion|what\\s+do\\s+you\\s+think|hello\\b|hi\\b|hey\\b|howdy|sup\\b)\\b/i.test(qLower);

      // 2. Subjective / Opinion Queries (e.g. "is tata company bad?", "should i buy reliance?")
      const isSubjective =
        /\\b(is|are|was|were)\\s+.*?\\b(bad|good|evil|corrupt|fraud|scam|better|worse|best|worst|safe|risky|reliable|ethical|unethical|trustworthy|overvalued|undervalued|overpriced|underpriced|terrible|horrible|poor|solid|shady|going\\s+to\\s+crash|worth\\s+(?:it|buying|investing))\\b/i.test(qLower) ||
        /\\b(is|are|was|were)\\s+.*?\\b(bad|good|evil|corrupt|fraud|scam|better|worse|best|worst|safe|risky|reliable|ethical|unethical|trustworthy|overvalued|undervalued|overpriced|underpriced|terrible|horrible|poor|solid|shady|going\\s+to\\s+crash|worth\\s+(?:it|buying|investing))\\b/i.test(qClean) ||
        /\\b(is|are)\\s+.*?\\b(good|bad|great|terrible|horrible|poor|solid|shady|best|worst)\\s+(company|stock|business|firm|group|investment)\\b/i.test(qLower) ||
        /\\b(good\\s+or\\s+bad|bad\\s+or\\s+good|good\\s+company|bad\\s+company|good\\s+stock|bad\\s+stock|worst\\s+company|best\\s+company|true\\s+or\\s+false|fraud\\s+rumors?|rumors?|worst\\s+investment)\\b/i.test(qLower) ||
        /\\b(?:personal\\s+)?(?:opinion|view|views|take|sentiment)\\s+on\\b/i.test(qLower) ||
        /\\bwhat\\s+(?:is\\s+your|do\\s+you)\\s+(?:personal\\s+)?(?:opinion|think|view|views|take)\\b/i.test(qLower) ||
        /\\bdo\\s+you\\s+like\\b/i.test(qLower) ||
        /\\b(?:personal\\s+)?recommendation\\b/i.test(qLower) ||
        /\\bdo\\s+you\\s+recommend\\b/i.test(qLower) ||
        /\\bwhy\\s+is\\s+.*?\\b(bad|good|evil|corrupt|falling|dropping|crashing|failing)\\b/i.test(qLower) ||
        /\\b(?:should\\s+i|shall\\s+i|can\\s+i)\\s+(?:buy|sell|invest)\\b/i.test(qLower) ||
        /\\b(?:best|worst)\\s+stock\\s+to\\s+buy\\b/i.test(qLower) ||
        /\\b(should\\s+i\\s+trust|reputation\\s+of|is\\s+it\\s+worth\\s+buying|is\\s+it\\s+worth\\s+investing|would\\s+you\\s+recommend)\\b/i.test(qLower);

      // 3. Out-of-Domain Non-Financial Topics (e.g. religion, trivia, sports, weather, cooking, coding)
      const isOOD =
        /\\b(god|gods|jesus|allah|buddha|religion|theology|soul|heaven|hell|afterlife|creator|creation|meaning\\s+of\\s+life|why\\s+are\\s+we\\s+here|existential|philosophy|divine|holy|sin|prayer|worship|faith)\\b/i.test(qLower) ||
        /\\b(cricket|football|soccer|tennis|virat\\s+kohli|rohit\\s+sharma|ipl|fifa|olympics|world\\s+cup|messi|ronaldo)\\b/i.test(qLower) ||
        /\\b(weather|temperature|forecast|climate|rain\\s+in|earthquake|storm)\\b/i.test(qLower) ||
        /\\b(recipe|bake|cook|chocolate\\s+chip|cookies|pizza|pasta|burger|coffee|tea)\\b/i.test(qLower) ||
        /\\b(quicksort|bubble\\s*sort|sorting\\s+algorithm|binary\\s*tree|leetcode|python\\s+code|how\\s+to\\s+write\\s+[a-z0-9_]+\\s+in\\s+python|in\\s+python)\\b/i.test(qLower) ||
        /\\b(capital\\s+of|president\\s+of|prime\\s+minister|tell\\s+me\\s+a\\s+joke|write\\s+a\\s+poem|distance\\s+to|speed\\s+of\\s+light|speed\\s+of\\s+sound|who\\s+invented)\\b/i.test(qLower);

      // 4. Natural Language Questions without ANY corporate indicator
      const isNLQuestion = /^(what|why|how|when|where|who|is|are|can|could|will|would|do|does|did|should)\\b/i.test(qClean);
      const hasExplicitCorpIndicator = /\\b(company|corporation|ltd|limited|inc|stock|stocks|share|shares|equity|equities|ticker|filing|filings|announcement|sebi|nse|bse|quarter|quarterly|q1|q2|q3|q4|results|earnings|buyback|dividend|board\\s+meeting|concall|investor|acquisition|merger|resignation|appointment|ceo|cfo|director|promoter|stake|revenue|profit|loss|ebitda)\\b/i.test(qLower);

      const knownTickers = ['TCS', 'INFY', 'RELIANCE', 'KAYNES', 'TATAMOTORS', 'HDFCBANK', 'ICICIBANK', 'SBIN', 'WIPRO', 'ITC', 'ADANIPORTS', 'DBOL', 'DCMSIL', 'ATAM'];
      const knownGroups = ['tata', 'adani', 'reliance', 'birla', 'mahindra', 'bajaj', 'godrej', 'vedanta'];
      const hasKnownEntity = knownTickers.some(t => new RegExp('\\\\b' + t + '\\\\b', 'i').test(qRaw)) ||
                             knownGroups.some(g => new RegExp('\\\\b' + g + '\\\\b', 'i').test(qLower));

      const isIrrelevantQuestion = isNLQuestion && !hasExplicitCorpIndicator && !hasKnownEntity;

      // Single disallowed dictionary word check
      const queryWords = qClean.split(/\\s+/).filter(Boolean);
      const isDisallowedSingleWord = queryWords.length === 1 && DISALLOWED_GENERIC_WORDS.has(queryWords[0]) && !hasExplicitCorpIndicator;

      if (isConversational || isSubjective || isOOD || isIrrelevantQuestion || isDisallowedSingleWord) {
        let refusalTitle = "Irrelevant / Out-of-Domain Scope Refusal";
        let refusalSummary = "I don't have filings for that query. This database strictly indexes verified SEBI Regulation 30 corporate statutory disclosures submitted to the National Stock Exchange (NSE) between Nov 9–15, 2026. Queries must relate to an NSE equity, company, or statutory disclosure category (e.g. Tata, Reliance, KAYNES, Q2 Results, Buybacks).";

        if (isSubjective) {
          refusalTitle = "Factual Disclosure Scope Notice";
          refusalSummary = "I don't have subjective opinions or investment advice. That is not present in the 7-day NSE filings database (Nov 9–15, 2026). Corporate statutory filings contain factual disclosures rather than subjective opinions.";
        } else if (isConversational) {
          refusalTitle = "Non-Corporate Conversational Query";
          refusalSummary = "I don't have filings for that query. This terminal is a factual corporate regulatory disclosure search engine for National Stock Exchange (NSE) filings (Nov 9–15, 2026). It does not answer personal, conversational, or conversational queries.";
        }

        return {
          query: qRaw,
          results: [],
          totalMatches: 0,
          isRefusal: true,
          matchedTicker: null,
          matchedConglomerate: null,
          synthesis: {
            title: refusalTitle,
            summary: refusalSummary,
            highlights: [],
            disclosuresCount: 0,
            verified: false
          }
        };
      }

      // Meaningful Non-Stopword Tokens (Excluding generic words when searching)
      const meaningfulTokens = queryWords.filter(tok => tok.length >= 2 && !STOP_WORDS.has(tok) && !DISALLOWED_GENERIC_WORDS.has(tok));

      let matchedTicker = null;
      let matchedConglomerate = null;
      let matchedTag = null;

      // 1. Check exact ticker match
      const candidateTicker = qRaw.toUpperCase();
      if (TICKER_MAP.has(candidateTicker)) {
        matchedTicker = candidateTicker;
      } else {
        for (const token of queryWords) {
          const upper = token.toUpperCase();
          if (TICKER_MAP.has(upper) && upper.length >= 3 && !DISALLOWED_GENERIC_WORDS.has(token.toLowerCase())) {
            matchedTicker = upper;
            break;
          }
        }
      }

      // 2. Check conglomerate match
      for (const [key, group] of Object.entries(CONGLOMERATE_GROUPS)) {
        if (group.pattern.test(qLower) || (key.length >= 4 && qLower.includes(key))) {
          matchedConglomerate = { key, ...group };
          break;
        }
      }

      // 3. Check tag / topic match
      const tagKeywords = {
        results: ["result", "results", "earning", "earnings", "financial", "q2", "quarter"],
        investor_meet: ["investor", "meet", "meeting", "concall", "call"],
        buyback: ["buyback", "share repurchase"],
        dividend: ["dividend", "distribution"],
        acquisition: ["acquisition", "takeover", "merger"],
        management: ["management", "director", "resignation", "appointment", "ceo", "cfo", "kmp"],
        order: ["order", "contract", "bagging"]
      };

      for (const [tagKey, words] of Object.entries(tagKeywords)) {
        if (words.some(w => qLower.includes(w))) {
          matchedTag = tagKey;
          break;
        }
      }

      // 4. Check if any meaningful token matches ANY company name on a whole-word boundary
      let hasCompanyWordMatch = false;
      const companyWordRegexes = meaningfulTokens.map(tok => new RegExp('\\\\b' + tok.replace(/[.*+?^${}()|[\\]\\\\]/g, '\\\\$&') + '\\\\b', 'i'));
      for (let i = 0; i < FILINGS_DATA.length; i++) {
        const comp = FILINGS_DATA[i].company;
        if (companyWordRegexes.some(rx => rx.test(comp))) {
          hasCompanyWordMatch = true;
          break;
        }
      }

      // 5. Strict Zero-Hallucination Grounding Gate
      if (!matchedTicker && !matchedConglomerate && !matchedTag && !hasCompanyWordMatch) {
        return {
          query: qRaw,
          results: [],
          totalMatches: 0,
          isRefusal: true,
          matchedTicker: null,
          matchedConglomerate: null,
          synthesis: {
            title: "No Statutory Filings Found",
            summary: "I don't have filings for \\"" + qRaw + "\\". No corporate statutory disclosures matching your query were found in the 7-day NSE reporting database (Nov 9–15, 2026). Try querying a listed company name (e.g. Tata, Reliance, KAYNES), ticker, or regulatory action (e.g. Q2 Results, Buybacks).",
            highlights: [],
            disclosuresCount: 0,
            verified: false
          }
        };
      }

      // 6. Scoring candidate filings with whole-word regex
      const scored = [];
      const conglomerateTickerSet = matchedConglomerate ? new Set(matchedConglomerate.tickers.map(t => t.toUpperCase())) : null;

      for (let i = 0; i < FILINGS_DATA.length; i++) {
        const f = FILINGS_DATA[i];
        let score = 0;
        const fTicker = f.ticker.toUpperCase();
        const fComp = f.company;
        const fHead = f.headline;
        const fDesc = f.description;
        const fTag = f.tag.toLowerCase();

        // Exact ticker boost
        if (matchedTicker && fTicker === matchedTicker) {
          score += 150;
        }

        // Conglomerate boost
        if (matchedConglomerate) {
          if (conglomerateTickerSet && conglomerateTickerSet.has(fTicker)) score += 100;
          if (new RegExp('\\\\b' + matchedConglomerate.key + '\\\\b', 'i').test(fComp)) score += 80;
        }

        // Tag matching boost
        if (matchedTag) {
          if (matchedTag === 'results' && (fTag.includes('result') || f.category.toLowerCase().includes('financial') || f.category.toLowerCase().includes('board meeting'))) {
            score += 45;
          } else if (matchedTag === 'investor_meet' && (fTag.includes('investor') || fTag.includes('concall'))) {
            score += 45;
          } else if (matchedTag === 'buyback' && (fTag.includes('buyback') || fHead.toLowerCase().includes('buyback'))) {
            score += 70;
          } else if (matchedTag === 'dividend' && (fTag.includes('dividend') || fHead.toLowerCase().includes('dividend'))) {
            score += 70;
          } else if (matchedTag === 'acquisition' && (fTag.includes('acquisition') || fHead.toLowerCase().includes('acquisition'))) {
            score += 60;
          } else if (matchedTag === 'management' && (fTag.includes('management') || f.category.toLowerCase().includes('management'))) {
            score += 55;
          } else if (matchedTag === 'order' && (fTag.includes('order') || fHead.toLowerCase().includes('order'))) {
            score += 50;
          }
        }

        // Whole-word non-stopword token matches
        for (let tIdx = 0; tIdx < meaningfulTokens.length; tIdx++) {
          const tok = meaningfulTokens[tIdx];
          const rx = companyWordRegexes[tIdx];
          if (fTicker.toLowerCase() === tok) {
            score += 80;
          } else if (rx.test(fComp)) {
            score += 40;
          } else if (rx.test(fHead)) {
            score += 25;
          } else if (rx.test(fDesc)) {
            score += 12;
          }
        }

        // Only include if there is a legitimate grounded match (score >= 35)
        if (score >= 35) {
          score += (f.importance_score || 50) * 0.15;
          scored.push({ filing: f, score });
        }
      }

      // Sort descending by score, then date/time
      scored.sort((a, b) => {
        if (b.score !== a.score) return b.score - a.score;
        return (b.filing.date + b.filing.time).localeCompare(a.filing.date + a.filing.time);
      });

      const limit = options.limit || 50;
      const topResults = scored.slice(0, limit).map(item => item.filing);

      if (topResults.length === 0) {
        return {
          query: qRaw,
          results: [],
          totalMatches: 0,
          isRefusal: true,
          matchedTicker: null,
          matchedConglomerate: null,
          synthesis: {
            title: "No Statutory Filings Found",
            summary: "I don't have filings for \\"" + qRaw + "\\". No corporate statutory disclosures matching your query were found in the 7-day NSE reporting window (Nov 9–15, 2026).",
            highlights: [],
            disclosuresCount: 0,
            verified: false
          }
        };
      }

      // Generate structured executive AI synthesis based strictly on retrieved filings
      const synthesis = this.generateSynthesis(qRaw, topResults, {
        matchedTicker,
        matchedConglomerate,
        matchedTag,
        totalMatches: scored.length
      });

      return {
        query: qRaw,
        results: topResults,
        totalMatches: scored.length,
        synthesis,
        matchedTicker,
        matchedConglomerate: matchedConglomerate ? matchedConglomerate.name : null
      };
    },

    generateSynthesis(query, results, meta) {
      if (!results || results.length === 0) {
        return {
          title: "No Regulatory Disclosures Located",
          summary: "I don't have filings for \\"" + query + "\\". That is not present in the 7-day NSE filings database (Nov 9–15, 2026). Corporate statutory filings contain factual disclosures rather than irrelevant or subjective queries.",
          highlights: [],
          disclosuresCount: 0,
          verified: false
        };
      }

      const topFiling = results[0];
      const entities = Array.from(new Set(results.slice(0, 8).map(r => r.ticker)));
      const avgScore = Math.round(results.slice(0, 10).reduce((acc, r) => acc + r.importance_score, 0) / Math.min(results.length, 10));

      let title = '';
      let summary = '';
      const highlights = [];

      if (meta.matchedConglomerate) {
        title = meta.matchedConglomerate.name + ": Regulatory Activity & Filings Analysis";
        summary = "Identified " + meta.totalMatches + " statutory disclosures across " + meta.matchedConglomerate.name + " entities in the active 7-day reporting cycle. Disclosures encompass board outcomes, quarterly financial performance, and capital allocation announcements.";
      } else if (meta.matchedTicker) {
        title = topFiling.company + " (" + meta.matchedTicker + "): Material Disclosures Dossier";
        summary = topFiling.company + " filed " + meta.totalMatches + " material regulatory announcement(s) on the National Stock Exchange (NSE). Average institutional importance score is " + avgScore + "/100.";
      } else if (meta.matchedTag) {
        title = "Corporate " + meta.matchedTag.toUpperCase() + " Disclosures Overview";
        summary = "Retrieved " + meta.totalMatches + " statutory filings categorized under " + meta.matchedTag + ". Recent disclosures highlight active corporate actions and executive updates across " + entities.length + " NSE listed firms.";
      } else {
        title = "Synthesis: \\"" + query + "\\" Regulatory Disclosures";
        summary = "Cross-referenced 2,766 corporate announcements on NSE. Found " + meta.totalMatches + " relevant regulatory filing(s) with an average importance rating of " + avgScore + "/100.";
      }

      // Extract top 4 highlight points
      results.slice(0, 4).forEach(r => {
        highlights.push({
          ticker: r.ticker,
          company: r.company,
          tag: r.tag,
          date: r.date,
          importance: r.importance_score,
          headline: r.headline,
          pdf: r.pdf_url
        });
      });

      return {
        title,
        summary,
        highlights,
        disclosuresCount: meta.totalMatches,
        entitiesCount: entities.length,
        avgImportance: avgScore,
        verified: true
      };
    }
  };'''

new_fdata = fdata[:s_idx] + new_filings_search_code + fdata[e_idx:]
with open(filings_data_path, 'w', encoding='utf-8') as f:
    f.write(new_fdata)
print("Updated filings_data.js successfully!")

# 2. Update index.html
index_path = 'markettide-rag-team/site/index.html'
with open(index_path, 'r', encoding='utf-8') as f:
    idx_content = f.read()

# Update script tag version to v=2.2.0
idx_content = re.sub(r'filings_data\.js(\?v=[0-9.]+)?', 'filings_data.js?v=2.2.0', idx_content)

# Update executeSearch in index.html to include comprehensive relevance check
search_func_start = "    function executeSearch() {"
s_func_idx = idx_content.find(search_func_start)
if s_func_idx != -1:
    # Find closing of executeSearch
    # Search for function close before closeSearchResults
    next_func = "    function closeSearchResults() {"
    n_idx = idx_content.find(next_func)
    if n_idx != -1:
        new_execute_search = '''    function executeSearch() {
      const q = searchInput.value.trim();
      if (!q) return;

      // Micro-interaction pulse on search dock
      const dockCard = document.querySelector('.dock-glass-card');
      if (dockCard) {
        dockCard.classList.remove('search-pulse');
        void dockCard.offsetWidth; // trigger reflow
        dockCard.classList.add('search-pulse');
      }

      // 1. Dynamic background transition: apply .canvas-dimmed class
      // 3D scene continues running smoothly at 60fps in background!
      canvasContainer.classList.add('canvas-dimmed');
      heroHud.classList.add('hidden');

      // 2. Query 2,766 dataset engine
      let searchData = null;
      if (window.MarketTideFilings) {
        searchData = window.MarketTideFilings.search(q, { limit: 60 });
      } else {
        searchData = {
          query: q,
          results: [],
          totalMatches: 0,
          synthesis: {
            title: "MarketTide Filings Engine Initializing",
            summary: "Indexed filing engine is active.",
            highlights: []
          }
        };
      }

      // 3. Render foreground search results overlay
      renderSearchResults(searchData);

      // 4. Reveal overlay with upward spring transition
      searchOverlay.classList.add('active');

      // 5. Emit event on MarketTideBus if available
      if (window.MarketTideBus) {
        window.MarketTideBus.emit('market-tide:scene-action', {
          action: 'SEARCH_SUBMITTED',
          query: q,
          matches: searchData.totalMatches,
          timestamp: Date.now()
        });
      }
    }
'''
        idx_content = idx_content[:s_func_idx] + new_execute_search + idx_content[n_idx:]
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(idx_content)
        print("Updated index.html successfully!")
