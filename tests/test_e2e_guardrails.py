"""
test_e2e_guardrails.py - Comprehensive Backend E2E Guardrails Test Suite for Milestone 2

Validates Tiers 1-4 requirements from ORIGINAL_REQUEST.md and PROJECT.md:
- Tier 1: In-scope ticker/org queries (Tata, TCS, Reliance, TMPV, HDFCBANK, Adani, Kaynes Tech)
          return legitimate corporate filings and display source dossiers.
- Tier 2: Subjective opinion queries ("is tata company bad?", "is reliance good?", "opinion on adani", etc.)
          strictly return 0 filings, suppress source dossiers, and yield the exact canonical refusal string:
          "I don't know. That is not present in the 7-day NSE filings database (Nov 9–15, 2026)."
          along with an explanation that corporate statutory filings contain factual disclosures rather than subjective opinions.
- Tier 3: Out-of-domain queries, general coding, and trivia return 0 filings and the canonical refusal string.
- Tier 4: Adversarial edge cases: mixed casing, excessive whitespace, punctuation stress, entity names
          combined with sentiment/opinion terms, and colloquialism purge invariant (no "dude").
"""

import os
import re
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

CANONICAL_REFUSAL_EXACT = "I don't know. That is not present in the 7-day NSE filings database (Nov 9–15, 2026)."


class TestE2EGuardrailsMilestone2(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Initialize MarketTideAgent once for performance."""
        cls.agent = MarketTideAgent()
        cls.tools = cls.agent.tools

    # =========================================================================
    # TIER 1: IN-SCOPE ENTITY & TICKER RETRIEVAL (>= 7 IN-SCOPE ENTITIES)
    # =========================================================================

    def test_tier1_in_scope_ticker_and_org_queries(self):
        """
        Verify in-scope ticker and conglomerate inquiries retrieve legitimate
        corporate filings from the 7-day NSE dataset and display verified source dossiers.
        Covers: Tata, TCS, Reliance, TMPV, HDFCBANK, Adani, Kaynes Tech.
        """
        in_scope_queries = [
            ("Tata", ["TATAPOWER", "TCS", "TATASTEEL", "TMPV", "TMCV", "TATACHEM"]),
            ("TCS", ["TCS"]),
            ("Reliance", ["RELIANCE", "RELINFRA", "RPOWER"]),
            ("TMPV", ["TMPV"]),
            ("HDFCBANK", ["HDFCBANK"]),
            ("Adani", ["ADANIENT", "ADANIENSOL", "ADANIPOWER"]),
            ("Kaynes Tech", ["KAYNES"])
        ]

        for query, expected_tickers in in_scope_queries:
            with self.subTest(query=query):
                intent_data = self.agent.classify_intent_and_entities(query)
                self.assertIn(
                    intent_data["intent"],
                    ["COMPANY", "TICKER", "CONGLOMERATE"],
                    f"In-scope query '{query}' was misclassified as {intent_data['intent']}"
                )

                stream_gen, docs, tool_context = self.agent.stream_response(query)
                full_reply = "".join(list(stream_gen))
                dossier_visible = should_show_sources(full_reply, docs, tool_context)

                # Must return documents
                self.assertGreater(
                    len(docs),
                    0,
                    f"In-scope query '{query}' returned 0 documents! Expected filings from: {expected_tickers}"
                )

                # Source dossier must be visible in UI
                self.assertTrue(
                    dossier_visible,
                    f"In-scope query '{query}' failed to display source dossier in UI"
                )

                # Must NOT contain refusal text
                self.assertNotIn(
                    CANONICAL_REFUSAL_EXACT,
                    full_reply,
                    f"In-scope query '{query}' was erroneously rejected with canonical refusal"
                )

                # Docs must be relevant to the requested company/tickers
                retrieved_tickers = {d.get("ticker", "").upper() for d in docs}
                has_matching_ticker = any(t in retrieved_tickers for t in expected_tickers)
                self.assertTrue(
                    has_matching_ticker,
                    f"Retrieved tickers {retrieved_tickers} do not match expected tickers {expected_tickers} for '{query}'"
                )

    # =========================================================================
    # TIER 2: SUBJECTIVE OPINION REFUSAL (ZERO-FILING RETRIEVAL & CANONICAL TEXT)
    # =========================================================================

    def test_tier2_subjective_opinion_queries_strictly_refused(self):
        """
        Verify subjective or opinion queries (e.g., 'is tata company bad?', 'is reliance good?')
        strictly return 0 filings, suppress source dossiers, and return the exact canonical refusal:
        'I don't know. That is not present in the 7-day NSE filings database (Nov 9–15, 2026).'
        accompanied by an explanation that corporate statutory filings contain factual disclosures
        rather than subjective opinions.
        """
        subjective_queries = [
            "is tata company bad?",
            "is reliance good?",
            "opinion on adani",
            "what do you think of infosys?",
            "should i buy kaynes tech?",
            "is hdfc bank overpriced?",
            "best stock to buy right now?",
            "is tcs going to crash?",
            "do you recommend investing in tata motors?",
            "is tmpv a good company or bad?"
        ]

        for query in subjective_queries:
            with self.subTest(query=query):
                intent_data = self.agent.classify_intent_and_entities(query)
                self.assertEqual(
                    intent_data["intent"],
                    "SUBJECTIVE_OPINION",
                    f"Subjective query '{query}' should be classified as SUBJECTIVE_OPINION, got: {intent_data['intent']}"
                )

                stream_gen, docs, tool_context = self.agent.stream_response(query)
                full_reply = "".join(list(stream_gen))
                dossier_visible = should_show_sources(full_reply, docs, tool_context)

                # Strict Zero-Hallucination Invariants:
                # 1. 0 filings returned (never dump filings on subjective keywords)
                self.assertEqual(
                    len(docs),
                    0,
                    f"Subjective query '{query}' leaked {len(docs)} filings! Must return exactly 0 docs."
                )

                # 2. Source dossier drawer strictly suppressed
                self.assertFalse(
                    dossier_visible,
                    f"Subjective query '{query}' displayed source dossier drawer in UI!"
                )

                # 3. Exact Canonical Refusal present
                self.assertIn(
                    CANONICAL_REFUSAL_EXACT,
                    full_reply,
                    f"Subjective query '{query}' missing exact canonical refusal string: '{CANONICAL_REFUSAL_EXACT}'"
                )

                # 4. Factual Disclosures Explanation present
                has_explanation = (
                    "factual disclosures rather than subjective opinions" in full_reply.lower() or
                    "factual disclosures" in full_reply.lower()
                )
                self.assertTrue(
                    has_explanation,
                    f"Subjective query '{query}' missing factual disclosures vs subjective opinion explanation: {full_reply}"
                )

    # =========================================================================
    # TIER 3: OUT-OF-DOMAIN, GENERAL CODING, & TRIVIA REFUSAL
    # =========================================================================

    def test_tier3_out_of_domain_and_trivia_refusal(self):
        """
        Verify out-of-domain queries, coding questions, and general trivia return 0 filings
        and the canonical refusal response.
        """
        ood_queries = [
            # Sports
            "who won the IPL 2024 final match?",
            "cricket world cup score live updates",
            # Science / Trivia
            "what is the capital of France?",
            "how does photosynthesis work in plants?",
            # Recipes / Domestic
            "how to bake a chocolate chip cake at home",
            "recipe for butter chicken curry",
            # General Coding
            "write a python function to reverse a linked list",
            "how to implement binary search in typescript",
            # Jokes / Creative
            "tell me a funny joke about wall street",
            "write a haiku about money"
        ]

        for query in ood_queries:
            with self.subTest(query=query):
                intent_data = self.agent.classify_intent_and_entities(query)
                self.assertEqual(
                    intent_data["intent"],
                    "OUT_OF_DOMAIN",
                    f"Query '{query}' expected OUT_OF_DOMAIN, got: {intent_data['intent']}"
                )

                stream_gen, docs, tool_context = self.agent.stream_response(query)
                full_reply = "".join(list(stream_gen))
                dossier_visible = should_show_sources(full_reply, docs, tool_context)

                # Zero retrieval & dossier suppression
                self.assertEqual(len(docs), 0, f"OOD query '{query}' returned docs")
                self.assertFalse(dossier_visible, f"OOD query '{query}' displayed dossier")

                # Canonical refusal string present
                self.assertIn(
                    CANONICAL_REFUSAL_EXACT,
                    full_reply,
                    f"OOD query '{query}' missing exact canonical refusal: {full_reply}"
                )

    # =========================================================================
    # TIER 4: ADVERSARIAL EDGE CASES & INTEGRITY INVARIANTS
    # =========================================================================

    def test_tier4_mixed_casing_subjective_queries(self):
        """Verify casing variations do not evade subjective guardrails."""
        cases = [
            "Is TATA CoMpAnY BaD?",
            "IS RELIANCE GOOD?",
            "OpInIoN oN aDaNi",
            "sHoUlD i BuY kAyNeS tEcH?"
        ]
        for query in cases:
            with self.subTest(query=query):
                intent_data = self.agent.classify_intent_and_entities(query)
                self.assertEqual(
                    intent_data["intent"],
                    "SUBJECTIVE_OPINION",
                    f"Mixed-casing query '{query}' bypassed SUBJECTIVE_OPINION gate"
                )
                _, docs, _ = self.agent.stream_response(query)
                self.assertEqual(len(docs), 0, f"Query '{query}' leaked {len(docs)} docs")

    def test_tier4_whitespace_and_punctuation_stress(self):
        """Verify excessive whitespace and trailing punctuation do not bypass guardrails."""
        cases = [
            "   is   tata   company   bad  ???   ",
            "reliance - is it good or bad???!!!",
            "adani power: should I invest or is it terrible?!",
            "what is your personal opinion on TCS?????"
        ]
        for query in cases:
            with self.subTest(query=query):
                intent_data = self.agent.classify_intent_and_entities(query)
                self.assertEqual(
                    intent_data["intent"],
                    "SUBJECTIVE_OPINION",
                    f"Stress query '{query}' bypassed SUBJECTIVE_OPINION gate"
                )
                _, docs, _ = self.agent.stream_response(query)
                self.assertEqual(len(docs), 0)

    def test_tier4_sentiment_combined_with_entity_names(self):
        """
        Verify queries combining entity names with sentiment/opinion terms
        (fraud rumors, failing, worst investment) are refused rather than dumping filings.
        """
        cases = [
            "Tata Motors fraud rumors true or false?",
            "Why is TCS stock failing?",
            "Is HDFCBANK the worst investment right now?"
        ]
        for query in cases:
            with self.subTest(query=query):
                intent_data = self.agent.classify_intent_and_entities(query)
                self.assertIn(
                    intent_data["intent"],
                    ["SUBJECTIVE_OPINION", "OUT_OF_DOMAIN"],
                    f"Entity+sentiment query '{query}' was treated as factual company search"
                )
                _, docs, _ = self.agent.stream_response(query)
                self.assertEqual(len(docs), 0)

    def test_tier4_pure_opinion_words_without_entity(self):
        """Verify generic opinion queries without named entities are refused."""
        cases = [
            "is this stock good or bad?",
            "what is your personal recommendation?",
            "should I buy or sell right now?",
            "is this company terrible?"
        ]
        for query in cases:
            with self.subTest(query=query):
                intent_data = self.agent.classify_intent_and_entities(query)
                self.assertIn(
                    intent_data["intent"],
                    ["SUBJECTIVE_OPINION", "OUT_OF_DOMAIN"]
                )
                _, docs, _ = self.agent.stream_response(query)
                self.assertEqual(len(docs), 0)

    def test_tier4_colloquialism_purge_invariant(self):
        """
        Verify that across ALL refusal responses (subjective, out-of-domain, zero filings),
        informal colloquialisms like 'dude', 'bro', 'hey man' are strictly purged.
        """
        test_queries = [
            "is tata company bad?",
            "who won the IPL?",
            "what is the weather in Delhi?",
            "write a python script",
            "Infosys",  # zero filings in 7-day window
            "Google"    # foreign non-NSE
        ]
        for query in test_queries:
            with self.subTest(query=query):
                stream_gen, _, _ = self.agent.stream_response(query)
                reply = "".join(list(stream_gen))
                for colloquialism in [r"\bdude\b", r"\bbro\b", r"\bhey man\b", r"\byo\b"]:
                    self.assertIsNone(
                        re.search(colloquialism, reply, re.IGNORECASE),
                        f"Refusal for '{query}' contained informal colloquialism matching '{colloquialism}': {reply}"
                    )


if __name__ == "__main__":
    unittest.main()
