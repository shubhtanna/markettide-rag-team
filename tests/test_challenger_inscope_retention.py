"""
test_challenger_inscope_retention.py - Adversarial Verification Harness for In-Scope Retention
Written by Challenger 2 (Empirical Challenger) to verify that domain guardrails and retriever cutoffs
do NOT inadvertently suppress or break legitimate NSE corporate filing queries.
"""

import unittest
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "chatbot"))

from agent import MarketTideAgent
from tools import MarketTools
from app import should_show_sources


class TestInScopeLegitimateFilingsRetention(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.agent = MarketTideAgent()
        cls.tools = cls.agent.tools

    def test_in_scope_active_filings_retention_matrix(self):
        """
        Verify that core active filing companies and category queries across the
        2,766-filing dataset return documents and display verified source dossiers.
        """
        queries = [
            ("Tata Motors Passenger Vehicles", "TMPV"),
            ("TMPV", "TMPV"),
            ("Tata Motors", "TMPV"),
            ("Adani Power", "ADANIPOWER"),
            ("ADANIPOWER", "ADANIPOWER"),
            ("Zee Entertainment", "ZEEL"),
            ("ZEEL", "ZEEL"),
            ("Ind-Swift Laboratories", "INDSWFTLAB"),
            ("INDSWFTLAB", "INDSWFTLAB"),
            ("Premier Explosives", "PREMEXPLN"),
            ("PREMEXPLN", "PREMEXPLN"),
            ("Reliance", "RELIANCE"),
            ("Board meetings", "Outcome of Board Meeting"),
            ("Outcome of Board Meeting", "Outcome of Board Meeting"),
            ("Buybacks", "Buyback"),
            ("Dividends", "Dividend"),
            ("Contract/order wins", "Order"),
            ("Resignations/Appointments", "Change in Management"),
            ("Compare Tata Motors and ZEEL filings", "comparison"),
            ("Tata Motors vs ZEEL", "comparison"),
            ("What are the most significant high-impact filings published this week?", "top_filings"),
        ]

        for q, expected_tag_or_ticker in queries:
            with self.subTest(query=q):
                intent_data = self.agent.classify_intent_and_entities(q)
                docs, tool_context = self.agent.execute_tools(intent_data, q)
                
                self.assertNotEqual(
                    intent_data["intent"], "OUT_OF_DOMAIN",
                    f"In-scope query '{q}' was falsely classified as OUT_OF_DOMAIN!"
                )
                self.assertGreater(
                    len(docs), 0,
                    f"In-scope query '{q}' retrieved 0 documents!"
                )
                
                # Verify that dossiers are visible when responses are generated
                # Mock a standard Dalal street response text
                sample_response = f"Official NSE corporate filing analysis for {expected_tag_or_ticker}. Dalal Street Desk."
                show_dossier = should_show_sources(sample_response, docs, tool_context)
                self.assertTrue(
                    show_dossier,
                    f"In-scope query '{q}' failed should_show_sources check!"
                )

    def test_state_bank_of_india_entity_resolution(self):
        """
        Adversarial Test: Verify that State Bank of India (SBIN) can be resolved
        by tools.resolve_company and does not get blocked by DISALLOWED_SINGLE_WORDS.
        """
        resolved_name = self.tools.resolve_company("State Bank of India")
        self.assertTrue(
            len(resolved_name) > 0 and resolved_name[0]["ticker"] == "SBIN",
            f"State Bank of India failed to resolve! Got: {resolved_name}"
        )

        resolved_query = self.tools.resolve_company("What did State Bank of India announce?")
        self.assertTrue(
            len(resolved_query) > 0 and resolved_query[0]["ticker"] == "SBIN",
            f"'What did State Bank of India announce?' failed to resolve SBIN! Got: {resolved_query}"
        )

    def test_legitimate_companies_with_ood_words_not_suppressed(self):
        """
        Adversarial Test: Verify that legitimate NSE listed companies whose names
        contain dictionary words ('celebrity', 'singer', 'films', 'galaxy') are
        NOT hijacked by OUT_OF_DOMAIN_PATTERNS.
        """
        test_cases = [
            ("Celebrity Fashions announcements", "CELEBRITY"),
            ("Celebrity Fashions Limited filings", "CELEBRITY"),
            ("Singer India announcements", "SINGERIND"),
            ("Singer India Limited", "SINGERIND"),
            ("Inspire Films announcements", "INSPIRE"),
            ("Jindal Poly Films filings", "JINDALPOLY"),
            ("Garware Hi-Tech Films", "GRWRHITECH"),
            ("Galaxy Medicare announcements", "GML"),
            ("Essen Speciality Films filings", "ESFL"),
        ]

        for query, expected_ticker in test_cases:
            with self.subTest(query=query):
                intent_data = self.agent.classify_intent_and_entities(query)
                self.assertNotEqual(
                    intent_data["intent"], "OUT_OF_DOMAIN",
                    f"Legitimate NSE company query '{query}' was falsely classified as OUT_OF_DOMAIN!"
                )
                docs, tool_ctx = self.agent.execute_tools(intent_data, query)
                self.assertGreater(
                    len(docs), 0,
                    f"Legitimate NSE company query '{query}' retrieved 0 documents!"
                )

    def test_zero_filing_legitimate_company_suppression(self):
        """
        Adversarial Test: Verify that a legitimate NSE company with 0 filings in the window
        (e.g., Infosys) does NOT leak unrelated source dossiers.
        """
        query = "What did Infosys announce?"
        intent_data = self.agent.classify_intent_and_entities(query)
        
        # When stream_response is called
        stream_gen, docs, tool_ctx = self.agent.stream_response(query)
        full_text = "".join(list(stream_gen))
        show_dossier = should_show_sources(full_text, docs, tool_ctx)
        
        # If docs are retrieved from unrelated companies, show_dossier MUST NOT be True!
        self.assertFalse(
            show_dossier,
            f"Zero-filing query '{query}' displayed source dossier of unrelated filings! Docs: {len(docs)}"
        )


if __name__ == "__main__":
    unittest.main()
