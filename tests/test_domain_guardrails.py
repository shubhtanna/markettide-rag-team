"""
test_domain_guardrails.py - Automated Adversarial Test Suite for Market Tide
Verifies strict domain boundary enforcement, zero retrieval on out-of-domain queries,
complete source dossier suppression, and robust in-scope filing answers.
Implemented using Python's standard library `unittest`.
"""

import json
import os
import sys
import unittest

# Ensure chatbot modules can be imported
TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(TESTS_DIR)
CHATBOT_DIR = os.path.join(PROJECT_DIR, "chatbot")
if CHATBOT_DIR not in sys.path:
    sys.path.insert(0, CHATBOT_DIR)

from agent import MarketTideAgent
from app import should_show_sources
from tools import MarketTools, DISALLOWED_SINGLE_WORDS
from retriever import HybridRetriever, BM25_STOPWORDS

FIXTURES_PATH = os.path.join(TESTS_DIR, "fixtures", "synthetic_queries.json")


class TestDomainGuardrails(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Initialize MarketTideAgent and tools once for test suite performance."""
        cls.agent = MarketTideAgent()
        cls.tools = cls.agent.tools
        cls.retriever = cls.tools.retriever
        with open(FIXTURES_PATH, "r", encoding="utf-8") as f:
            cls.fixtures = json.load(f)

    def test_fixtures_loaded(self):
        """Confirm synthetic fixtures exist and have queries."""
        self.assertIn("queries", self.fixtures)
        self.assertGreater(len(self.fixtures["queries"]), 30)

    # =========================================================================
    # 1. OUT-OF-DOMAIN REJECTION & SUPPRESSION TESTS (R1 & R2)
    # =========================================================================

    def test_out_of_domain_queries_strict_rejection(self):
        """
        Verify all out-of-domain queries (sports, celebrities, world trivia,
        science, recipes, coding, polysemy, jokes) are strictly rejected with:
        - Exactly 0 retrieved docs
        - Verified Source Dossier suppressed (should_show_sources is False)
        - Tool context is 'out_of_domain'
        - Explicit domain boundary refusal text present
        - Zero pre-trained answers (forbidden keywords absent)
        """
        ood_queries = [
            q for q in self.fixtures["queries"]
            if q["category"].startswith("out_of_domain")
        ]
        self.assertGreater(len(ood_queries), 15, "Insufficient OOD test fixtures")

        for item in ood_queries:
            query = item["query"]
            with self.subTest(query=query):
                intent_data = self.agent.classify_intent_and_entities(query)
                self.assertEqual(
                    intent_data["intent"],
                    "OUT_OF_DOMAIN",
                    f"Query '{query}' was not classified as OUT_OF_DOMAIN. Got: {intent_data}"
                )

                stream_gen, docs, tool_context = self.agent.stream_response(query)
                full_reply = "".join(list(stream_gen))
                dossier_visible = should_show_sources(full_reply, docs, tool_context)

                # Strict Verification Invariants
                self.assertEqual(
                    len(docs),
                    0,
                    f"OOD Query '{query}' leaked {len(docs)} retrieved filings!"
                )
                self.assertFalse(
                    dossier_visible,
                    f"OOD Query '{query}' displayed source dossier in UI!"
                )
                self.assertEqual(
                    tool_context,
                    "out_of_domain",
                    f"OOD Query '{query}' unexpected tool_context: {tool_context}"
                )

                # Explicit refusal text must be present
                reply_lower = full_reply.lower()
                self.assertTrue(
                    any(kw.lower() in reply_lower for kw in item.get("refusal_keywords", ["refusal"])),
                    f"OOD Query '{query}' reply missing explicit refusal notice: {full_reply[:120]}"
                )

                # Forbidden pre-trained knowledge hallucination keywords must NOT be present
                for forbidden in item.get("forbidden_keywords", []):
                    import re
                    has_forbidden = re.search(r'\b' + re.escape(forbidden.lower()) + r'\b', reply_lower) is not None
                    self.assertFalse(
                        has_forbidden,
                        f"OOD Query '{query}' hallucinated pre-trained answer containing '{forbidden}'"
                    )

    def test_subjective_opinion_queries_strict_rejection(self):
        """
        Verify subjective or opinion queries (e.g. 'is tata company bad?', 'what is your opinion on reliance?')
        are strictly classified as SUBJECTIVE_OPINION, return 0 filings, suppress source dossiers,
        and yield the exact canonical refusal response accompanied by the factual disclosures notice.
        """
        subjective_cases = [
            "is tata company bad?",
            "what is your opinion on reliance?",
            "is adani good or bad?",
            "is tcs a bad stock?",
            "should i buy kaynes tech?",
            "what do you think of infosys?"
        ]
        canonical = "I don't know. That is not present in the 7-day NSE filings database (Nov 9–15, 2026)."

        for query in subjective_cases:
            with self.subTest(query=query):
                intent_data = self.agent.classify_intent_and_entities(query)
                self.assertEqual(
                    intent_data["intent"],
                    "SUBJECTIVE_OPINION",
                    f"Subjective query '{query}' expected SUBJECTIVE_OPINION, got {intent_data['intent']}"
                )

                stream_gen, docs, tool_context = self.agent.stream_response(query)
                full_reply = "".join(list(stream_gen))
                dossier_visible = should_show_sources(full_reply, docs, tool_context)

                self.assertEqual(len(docs), 0, f"Subjective query '{query}' leaked {len(docs)} documents!")
                self.assertFalse(dossier_visible, f"Subjective query '{query}' displayed source dossier in UI!")
                self.assertIn(canonical, full_reply, f"Subjective query '{query}' missing canonical refusal string")
                self.assertIn("factual disclosures rather than subjective opinions", full_reply.lower())

    def test_foreign_non_nse_rejection(self):
        """Verify queries regarding foreign / non-NSE equities are rejected with 0 docs and 0 dossiers."""
        foreign_queries = [
            q for q in self.fixtures["queries"]
            if q["category"] == "foreign_non_nse"
        ]
        for item in foreign_queries:
            query = item["query"]
            with self.subTest(query=query):
                intent_data = self.agent.classify_intent_and_entities(query)
                self.assertEqual(intent_data["intent"], "NON_NSE")

                stream_gen, docs, tool_context = self.agent.stream_response(query)
                full_reply = "".join(list(stream_gen))
                dossier_visible = should_show_sources(full_reply, docs, tool_context)

                self.assertEqual(len(docs), 0, f"Foreign query '{query}' returned docs")
                self.assertFalse(dossier_visible, f"Foreign query '{query}' displayed dossier")
                self.assertTrue(
                    "nasdaq" in full_reply.lower() or "not file disclosures" in full_reply.lower(),
                    f"Foreign query '{query}' missing non-NSE explanation"
                )

    def test_greeting_guardrails(self):
        """Verify conversational greetings receive desk welcome with 0 docs and 0 dossiers."""
        greeting_queries = [
            q for q in self.fixtures["queries"]
            if q["category"] == "greeting"
        ]
        for item in greeting_queries:
            query = item["query"]
            with self.subTest(query=query):
                intent_data = self.agent.classify_intent_and_entities(query)
                self.assertEqual(intent_data["intent"], "GREETING")

                stream_gen, docs, tool_context = self.agent.stream_response(query)
                full_reply = "".join(list(stream_gen))
                dossier_visible = should_show_sources(full_reply, docs, tool_context)

                self.assertEqual(len(docs), 0, f"Greeting '{query}' returned docs")
                self.assertFalse(dossier_visible, f"Greeting '{query}' displayed dossier")
                self.assertEqual(tool_context, "greeting")
                self.assertIn("Welcome to the Market Tide", full_reply)

    # =========================================================================
    # 2. IN-SCOPE NSE FILING RETRIEVAL TESTS
    # =========================================================================

    def test_in_scope_active_filings_retrieval(self):
        """
        Verify valid NSE corporate filing queries retrieve relevant documents,
        display source dossiers, and generate institutional answers.
        """
        active_in_scope = [
            q for q in self.fixtures["queries"]
            if q["category"] in ["in_scope_company", "in_scope_category", "in_scope_top_filings", "in_scope_comparison"]
        ]
        self.assertGreater(len(active_in_scope), 5, "Insufficient in-scope test fixtures")

        for item in active_in_scope:
            query = item["query"]
            with self.subTest(query=query):
                intent_data = self.agent.classify_intent_and_entities(query)
                self.assertEqual(
                    intent_data["intent"],
                    item["expected_intent"],
                    f"In-scope query '{query}' unexpected intent: {intent_data['intent']}"
                )

                stream_gen, docs, tool_context = self.agent.stream_response(query)
                full_reply = "".join(list(stream_gen))
                dossier_visible = should_show_sources(full_reply, docs, tool_context)

                self.assertGreater(
                    len(docs),
                    0,
                    f"In-scope query '{query}' returned zero docs!"
                )
                self.assertTrue(
                    dossier_visible,
                    f"In-scope query '{query}' failed to display source dossier!"
                )
                self.assertNotIn("Domain Scope Refusal", full_reply)

    def test_in_scope_zero_filings_dossier_suppression(self):
        """
        Verify legitimate NSE companies with zero filings in the 7-day window
        (e.g., Infosys) do NOT show a source dossier drawer.
        """
        zero_queries = [
            q for q in self.fixtures["queries"]
            if q["category"] == "in_scope_zero_filings"
        ]
        for item in zero_queries:
            query = item["query"]
            with self.subTest(query=query):
                stream_gen, docs, tool_context = self.agent.stream_response(query)
                full_reply = "".join(list(stream_gen))
                dossier_visible = should_show_sources(full_reply, docs, tool_context)

                # Source dossier must be suppressed
                self.assertFalse(
                    dossier_visible,
                    f"Zero-filing query '{query}' displayed source dossier!"
                )
                self.assertIn("No announcements were published", full_reply)

    # =========================================================================
    # 3. COMPONENT-LEVEL DEFENSE-IN-DEPTH TESTS
    # =========================================================================

    def test_entity_resolution_disallowed_words(self):
        """
        Verify tools.resolve_company rejects single dictionary / celebrity / trivia words
        unless accompanied by explicit corporate indicators.
        """
        test_words = [
            "swift", "world", "modi", "shah", "prime", "delhi", "ipl",
            "learning", "market", "tea", "chip", "india", "impact", "social"
        ]
        for w in test_words:
            with self.subTest(word=w):
                resolved = self.tools.resolve_company(w)
                self.assertEqual(
                    resolved,
                    [],
                    f"resolve_company unexpectedly matched disallowed single word '{w}': {resolved}"
                )

    def test_entity_resolution_valid_companies(self):
        """Verify tools.resolve_company accurately resolves legitimate NSE companies."""
        valid_queries = [
            ("Tata Motors", "TMCV"),
            ("Adani Power", "ADANIPOWER"),
            ("Zee Entertainment", "ZEEL"),
            ("Tata Power", "TATAPOWER")
        ]
        for query, expected_ticker in valid_queries:
            with self.subTest(query=query):
                resolved = self.tools.resolve_company(query)
                self.assertGreater(len(resolved), 0, f"Failed to resolve company '{query}'")
                tickers = [r["ticker"] for r in resolved]
                self.assertIn(expected_ticker, tickers)

    def test_bm25_stopwords_filtering(self):
        """Verify retriever.bm25_search removes interrogative and corporate stopwords."""
        stopwords_to_check = ["who", "what", "where", "how", "why", "is", "are", "announcements", "filings"]
        for sw in stopwords_to_check:
            self.assertIn(
                sw,
                BM25_STOPWORDS,
                f"Stopword '{sw}' missing from retriever.BM25_STOPWORDS"
            )

    def test_should_show_sources_unit_logic(self):
        """Directly verify edge cases of should_show_sources."""
        # 1. Empty sources -> False
        self.assertFalse(should_show_sources("Some reply", [], "company:Tata Motors"))
        self.assertFalse(should_show_sources("Some reply", None, "company:Tata Motors"))

        # 2. Refusal / suppressed tool contexts -> False
        fake_docs = [{"ticker": "TEST", "company": "Test Ltd"}]
        self.assertFalse(should_show_sources("Text", fake_docs, "out_of_domain"))
        self.assertFalse(should_show_sources("Text", fake_docs, "greeting"))
        self.assertFalse(should_show_sources("Text", fake_docs, "no_matches"))
        self.assertFalse(should_show_sources("Text", fake_docs, "non_nse"))
        self.assertFalse(should_show_sources("Text", fake_docs, "out_of_window"))

        # 3. Refusal text phrases -> False even if docs non-empty
        self.assertFalse(should_show_sources("Market Tide — Domain Scope Refusal notice", fake_docs, "general_hybrid"))
        self.assertFalse(should_show_sources("**No corporate announcements found for XYZ**", fake_docs, "general_hybrid"))
        self.assertFalse(should_show_sources("Zero official filings were published during this window", fake_docs, "general_hybrid"))

        # 4. Genuine positive response -> True
        valid_text = "Tata Motors announced a dividend of Rs. 3 per share with record date Nov 12, 2026."
        self.assertTrue(should_show_sources(valid_text, fake_docs, "company:Tata Motors (TMCV)"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
