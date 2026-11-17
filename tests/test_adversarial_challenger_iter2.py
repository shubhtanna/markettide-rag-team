"""
test_adversarial_challenger_iter2.py - Independent Adversarial Probe Test Suite
Written by Challenger 1 (Iteration 2) for strict empirical verification of:
1. 100% Out-of-Domain Rejection
2. Zero Retrieved Documents (len(docs) == 0)
3. Zero Source Dossier Display (should_show_sources == False)
4. Explicit Refusal / Domain Boundary Notification in response text
5. Preservation of Legitimate In-Scope Companies (Zero False Rejections)
"""

import os
import sys
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHATBOT_DIR = os.path.join(BASE_DIR, "chatbot")
if CHATBOT_DIR not in sys.path:
    sys.path.insert(0, CHATBOT_DIR)

from agent import MarketTideAgent
from app import should_show_sources
from tools import MarketTools


class TestAdversarialChallengerIter2(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.agent = MarketTideAgent()
        cls.tools = cls.agent.tools

    # -------------------------------------------------------------------------
    # 1. Polysemous Word Adversarial Probes
    # -------------------------------------------------------------------------
    def test_polysemous_queries_strict_rejection(self):
        """
        Verify polysemous ticker / company words (idea, titan, crown, point, etc.)
        used in non-financial contexts do NOT trigger company entity matching or doc retrieval.
        """
        polysemy_cases = [
            # Dispatch required:
            ("What is your idea about the future?", ["idea"]),
            ("Who is the titan of the tech industry?", ["titan"]),
            ("Tell me about celebrity gossip and news", ["celebrity"]),
            ("Who is the best singer in India?", ["singer"]),
            ("Tesla vehicle delivery report", ["tesla", "vehicle", "delivery", "report"]),
            ("Explain the concept of deep learning speed", ["deep", "speed"]),
            # Iteration 1 failure queries:
            ("titan submarine expedition tragedy", ["titan"]),
            ("do you have any creative idea for a birthday gift?", ["idea"]),
            ("who wears the crown in the British monarchy?", ["crown"]),
            ("what is the boiling point of water?", ["point"]),
            ("how to clean a greasy oven with vinegar", ["clean"]),
            ("what is the hardness of diamond on Mohs scale?", ["diamond"]),
            ("formula for gravitational force in physics", ["force"]),
            ("what time is it in Tokyo right now?", ["time"]),
            ("how to drive a manual transmission car", ["drive"]),
            ("US Federal Reserve interest rate history", ["federal"]),
            ("solve quadratic equation ax^2 + bx + c = 0 in C++", ["solve"]),
            ("hero bicycle chain lubrication", ["hero"]),
        ]

        for query, tokens in polysemy_cases:
            with self.subTest(query=query):
                intent_data = self.agent.classify_intent_and_entities(query)
                stream_gen, docs, tool_context = self.agent.stream_response(query)
                full_text = "".join(list(stream_gen))
                show_dossier = should_show_sources(full_text, docs, tool_context)

                # Empirical Invariant 1: Exactly 0 retrieved docs
                self.assertEqual(
                    len(docs), 0,
                    f"Polysemy query '{query}' leaked {len(docs)} documents! Intent: {intent_data['intent']}"
                )

                # Empirical Invariant 2: Zero source dossier visible in UI
                self.assertFalse(
                    show_dossier,
                    f"Polysemy query '{query}' displayed source dossier in UI! Context: {tool_context}"
                )

                # Empirical Invariant 3: Tool context must be refusal or non-NSE
                self.assertIn(
                    tool_context, ["out_of_domain", "non_nse", "greeting"],
                    f"Polysemy query '{query}' had unexpected tool_context: {tool_context}"
                )

                # Empirical Invariant 4: Explicit refusal text present
                text_lower = full_text.lower()
                has_refusal = (
                    "refusal" in text_lower or
                    "scope notice" in text_lower or
                    "no nse filings" in text_lower or
                    "outside our operational scope" in text_lower or
                    "falls outside" in text_lower or
                    "domain scope refusal" in text_lower
                )
                self.assertTrue(
                    has_refusal,
                    f"Polysemy query '{query}' missing refusal text! Reply: {full_text[:120]}"
                )

    # -------------------------------------------------------------------------
    # 2. Sports / Cricket Adversarial Probes
    # -------------------------------------------------------------------------
    def test_sports_queries_strict_rejection(self):
        """
        Verify sports, athletes, tournaments, and cricket queries are strictly rejected
        with zero retrieved documents and zero dossier display.
        """
        sports_cases = [
            "Who won the IPL 2024 final?",
            "Virat Kohli centuries record",
            "Rohit Sharma batting average",
            "Neeraj Chopra Olympic javelin gold",
            "Gautam Gambhir press conference",
            "Sunil Gavaskar commentary",
            "Who won the FIFA World Cup 2022?",
            "Kapil Dev 1983 world cup innings",
        ]

        for query in sports_cases:
            with self.subTest(query=query):
                intent_data = self.agent.classify_intent_and_entities(query)
                stream_gen, docs, tool_context = self.agent.stream_response(query)
                full_text = "".join(list(stream_gen))
                show_dossier = should_show_sources(full_text, docs, tool_context)

                self.assertEqual(
                    len(docs), 0,
                    f"Sports query '{query}' leaked {len(docs)} filings! Intent: {intent_data['intent']}"
                )
                self.assertFalse(
                    show_dossier,
                    f"Sports query '{query}' displayed source dossier in UI!"
                )
                self.assertEqual(
                    tool_context, "out_of_domain",
                    f"Sports query '{query}' unexpected tool_context: {tool_context}"
                )
                self.assertIn(
                    "refusal", full_text.lower(),
                    f"Sports query '{query}' missing explicit refusal header!"
                )

    # -------------------------------------------------------------------------
    # 3. General World Knowledge, Politics, Science, Crypto, Recipes
    # -------------------------------------------------------------------------
    def test_general_world_knowledge_rejection(self):
        """
        Verify general world knowledge, geography, world politics, crypto, and recipes
        are rejected with zero docs and zero source dossiers.
        """
        general_cases = [
            "Who is the Prime Minister of the United Kingdom?",
            "How does quantum computing work?",
            "What is the capital of France?",
            "Current price of Bitcoin cryptocurrency",
            "what is the Bretton Woods agreement?",
            "what is Bitcoin halving?",
            "history of Bank of England monetary policy",
            "how does Ethereum proof of stake work?",
            "how to boil eggs perfectly",
            "why is the sky blue?",
            "Droupadi Murmu presidential address",
            "apple pie recipe with cinnamon",
        ]

        for query in general_cases:
            with self.subTest(query=query):
                intent_data = self.agent.classify_intent_and_entities(query)
                stream_gen, docs, tool_context = self.agent.stream_response(query)
                full_text = "".join(list(stream_gen))
                show_dossier = should_show_sources(full_text, docs, tool_context)

                self.assertEqual(
                    len(docs), 0,
                    f"General knowledge query '{query}' leaked {len(docs)} filings! Intent: {intent_data['intent']}"
                )
                self.assertFalse(
                    show_dossier,
                    f"General knowledge query '{query}' displayed source dossier in UI!"
                )
                self.assertEqual(
                    tool_context, "out_of_domain",
                    f"General knowledge query '{query}' unexpected tool_context: {tool_context}"
                )
                self.assertIn(
                    "refusal", full_text.lower(),
                    f"General knowledge query '{query}' missing explicit refusal header!"
                )

    # -------------------------------------------------------------------------
    # 4. Everyday Greetings & Chitchat
    # -------------------------------------------------------------------------
    def test_greetings_and_chitchat(self):
        """
        Verify greetings and chitchat receive appropriate greeting / refusal responses
        with exactly 0 retrieved documents and zero source dossiers.
        """
        greetings = [
            "Hello, how are you today?",
            "Hi",
            "Good morning",
        ]
        for query in greetings:
            with self.subTest(query=query):
                stream_gen, docs, tool_context = self.agent.stream_response(query)
                full_text = "".join(list(stream_gen))
                show_dossier = should_show_sources(full_text, docs, tool_context)

                self.assertEqual(len(docs), 0, f"Greeting '{query}' returned docs")
                self.assertFalse(show_dossier, f"Greeting '{query}' displayed dossier")
                self.assertEqual(tool_context, "greeting")
                self.assertIn("Welcome to the Market Tide", full_text)

        chitchat = [
            "Tell me a joke",
            "knock knock who is there joke",
            "Who are you and what do you do?",
        ]
        for query in chitchat:
            with self.subTest(query=query):
                stream_gen, docs, tool_context = self.agent.stream_response(query)
                full_text = "".join(list(stream_gen))
                show_dossier = should_show_sources(full_text, docs, tool_context)

                self.assertEqual(len(docs), 0, f"Chitchat '{query}' returned docs")
                self.assertFalse(show_dossier, f"Chitchat '{query}' displayed dossier")
                self.assertEqual(tool_context, "out_of_domain")
                self.assertIn("refusal", full_text.lower())

    # -------------------------------------------------------------------------
    # 5. Legitimate In-Scope Control Retention Matrix (Zero False Rejections)
    # -------------------------------------------------------------------------
    def test_in_scope_legitimate_control_matrix(self):
        """
        Verify that domain guardrails do NOT break legitimate in-scope NSE company queries.
        """
        in_scope_active = [
            "Tata Motors Passenger Vehicles",
            "Adani Power",
            "ZEEL",
            "Celebrity Fashions announcements",
            "Singer India announcements",
            "State Bank of India",
        ]
        for query in in_scope_active:
            with self.subTest(query=query):
                intent_data = self.agent.classify_intent_and_entities(query)
                docs, tool_context = self.agent.execute_tools(intent_data, query)
                self.assertNotEqual(
                    intent_data["intent"], "OUT_OF_DOMAIN",
                    f"In-scope query '{query}' was falsely classified as OUT_OF_DOMAIN!"
                )
                self.assertGreater(
                    len(docs), 0,
                    f"In-scope query '{query}' returned 0 documents!"
                )
                # Mock legitimate answer
                mock_reply = f"Official NSE filings analysis for {query}."
                show_dossier = should_show_sources(mock_reply, docs, tool_context)
                self.assertTrue(
                    show_dossier,
                    f"In-scope query '{query}' failed to show source dossier!"
                )

        # In-scope legitimate company with 0 filings (e.g. Infosys)
        zero_filing_query = "What did Infosys announce?"
        intent_data = self.agent.classify_intent_and_entities(zero_filing_query)
        self.assertNotEqual(intent_data["intent"], "OUT_OF_DOMAIN")
        stream_gen, docs, tool_context = self.agent.stream_response(zero_filing_query)
        full_text = "".join(list(stream_gen))
        show_dossier = should_show_sources(full_text, docs, tool_context)

        self.assertEqual(len(docs), 0, f"Zero-filing query returned docs: {len(docs)}")
        self.assertFalse(show_dossier, f"Zero-filing query displayed dossier!")
        self.assertIn("No announcements were published", full_text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
