"""Unit tests for Backend Retrieval Fix (Requirement R4).

Verifies that the unindented return at line 491 of chatbot/agent.py is resolved,
allowing general hybrid retrieval to execute properly for queries with GENERAL intent,
while keeping single-company and conglomerate group resolution intact.
"""

import os
import sys
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "chatbot"))

from agent import MarketTideAgent


class TestBackendRetrievalFix(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.agent = MarketTideAgent()

    def test_general_hybrid_retrieval_executes(self):
        """Verify that general queries fall through to hybrid_search and return docs."""
        test_queries = [
            "Outcome of Board Meeting",
            "Board meetings",
            "power sector agreements",
        ]
        for query in test_queries:
            with self.subTest(query=query):
                intent_data = self.agent.classify_intent_and_entities(query)
                self.assertEqual(
                    intent_data["intent"],
                    "GENERAL",
                    f"Query '{query}' expected GENERAL intent but got {intent_data['intent']}",
                )
                docs, tool_context = self.agent.execute_tools(intent_data, query)
                self.assertEqual(
                    tool_context,
                    "general_hybrid",
                    f"Query '{query}' expected 'general_hybrid' context but got {tool_context}",
                )
                self.assertGreater(
                    len(docs),
                    0,
                    f"In-scope query '{query}' retrieved 0 documents!",
                )

    def test_single_and_conglomerate_routing_unaffected(self):
        """Ensure fixing line 491 does not break single or conglomerate company retrieval."""
        # Single company
        intent_single = self.agent.classify_intent_and_entities("ADANIPOWER")
        self.assertEqual(intent_single["intent"], "COMPANY")
        docs_single, ctx_single = self.agent.execute_tools(intent_single, "ADANIPOWER")
        self.assertTrue(ctx_single.startswith("company:Adani Power Limited (ADANIPOWER)"))
        self.assertGreater(len(docs_single), 0)

        # Single company 2
        intent_single2 = self.agent.classify_intent_and_entities("ZEEL")
        self.assertEqual(intent_single2["intent"], "COMPANY")
        docs_single2, ctx_single2 = self.agent.execute_tools(intent_single2, "ZEEL")
        self.assertTrue(ctx_single2.startswith("company:Zee Entertainment Enterprises Limited (ZEEL)"))
        self.assertGreater(len(docs_single2), 0)

        # Conglomerate group
        intent_group = self.agent.classify_intent_and_entities("Tata group announcements")
        self.assertEqual(intent_group["intent"], "COMPANY")
        docs_group, ctx_group = self.agent.execute_tools(intent_group, "Tata group announcements")
        self.assertTrue(ctx_group.startswith("group:Tata"))
        self.assertGreater(len(docs_group), 0)


if __name__ == "__main__":
    unittest.main()
