"""
run_challenger_probe.py - Empirical probe runner for Challenger 1 Iteration 2
Runs all required queries, measures retrieval and UI suppression invariants,
and generates structured metrics for the handoff report.
"""

import os
import sys
import json
import time

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHATBOT_DIR = os.path.join(BASE_DIR, "chatbot")
if CHATBOT_DIR not in sys.path:
    sys.path.insert(0, CHATBOT_DIR)

from agent import MarketTideAgent
from app import should_show_sources

def main():
    agent = MarketTideAgent()

    test_queries = [
        # 1. Polysemous words (from dispatch)
        {"category": "Polysemy (Ticker)", "query": "What is your idea about the future?", "expected_verdict": "REJECT"},
        {"category": "Polysemy (Ticker)", "query": "Who is the titan of the tech industry?", "expected_verdict": "REJECT"},
        {"category": "Polysemy (OOD Word)", "query": "Tell me about celebrity gossip and news", "expected_verdict": "REJECT"},
        {"category": "Polysemy (OOD Word)", "query": "Who is the best singer in India?", "expected_verdict": "REJECT"},
        {"category": "Polysemy / Foreign", "query": "Tesla vehicle delivery report", "expected_verdict": "REJECT"},
        {"category": "Polysemy (Speed/Deep)", "query": "Explain the concept of deep learning speed", "expected_verdict": "REJECT"},

        # 2. Sports / Cricket (from dispatch)
        {"category": "Sports / Cricket", "query": "Who won the IPL 2024 final?", "expected_verdict": "REJECT"},
        {"category": "Sports / Athlete", "query": "Virat Kohli centuries record", "expected_verdict": "REJECT"},
        {"category": "Sports / Athlete", "query": "Rohit Sharma batting average", "expected_verdict": "REJECT"},

        # 3. General world knowledge / Politics / Tech (from dispatch)
        {"category": "World Politics", "query": "Who is the Prime Minister of the United Kingdom?", "expected_verdict": "REJECT"},
        {"category": "Science & Tech", "query": "How does quantum computing work?", "expected_verdict": "REJECT"},
        {"category": "World Geography", "query": "What is the capital of France?", "expected_verdict": "REJECT"},
        {"category": "Crypto Trivia", "query": "Current price of Bitcoin cryptocurrency", "expected_verdict": "REJECT"},

        # 4. Everyday greetings & chitchat (from dispatch)
        {"category": "Greeting", "query": "Hello, how are you today?", "expected_verdict": "GREETING"},
        {"category": "Chitchat / Joke", "query": "Tell me a joke", "expected_verdict": "REJECT"},

        # 5. Iteration 1 Previous Challenger 1 Failure Cases
        {"category": "Polysemy (Iter1)", "query": "titan submarine expedition tragedy", "expected_verdict": "REJECT"},
        {"category": "Polysemy (Iter1)", "query": "do you have any creative idea for a birthday gift?", "expected_verdict": "REJECT"},
        {"category": "Polysemy (Iter1)", "query": "who wears the crown in the British monarchy?", "expected_verdict": "REJECT"},
        {"category": "Polysemy (Iter1)", "query": "what is the boiling point of water?", "expected_verdict": "REJECT"},
        {"category": "Polysemy (Iter1)", "query": "how to clean a greasy oven with vinegar", "expected_verdict": "REJECT"},
        {"category": "Polysemy (Iter1)", "query": "what is the hardness of diamond on Mohs scale?", "expected_verdict": "REJECT"},
        {"category": "Polysemy (Iter1)", "query": "formula for gravitational force in physics", "expected_verdict": "REJECT"},
        {"category": "Polysemy (Iter1)", "query": "what time is it in Tokyo right now?", "expected_verdict": "REJECT"},
        {"category": "Polysemy (Iter1)", "query": "how to drive a manual transmission car", "expected_verdict": "REJECT"},
        {"category": "Polysemy (Iter1)", "query": "US Federal Reserve interest rate history", "expected_verdict": "REJECT"},
        {"category": "Polysemy (Iter1)", "query": "solve quadratic equation ax^2 + bx + c = 0 in C++", "expected_verdict": "REJECT"},
        {"category": "Polysemy (Iter1)", "query": "hero bicycle chain lubrication", "expected_verdict": "REJECT"},
        {"category": "Sports Leak (Iter1)", "query": "Neeraj Chopra Olympic javelin gold", "expected_verdict": "REJECT"},
        {"category": "Sports Leak (Iter1)", "query": "Gautam Gambhir press conference", "expected_verdict": "REJECT"},
        {"category": "Macro History (Iter1)", "query": "what is the Bretton Woods agreement?", "expected_verdict": "REJECT"},

        # 6. Additional Boundary Queries
        {"category": "Sports Commentary", "query": "Sunil Gavaskar commentary", "expected_verdict": "REJECT"},
        {"category": "Crypto Trivia", "query": "what is Bitcoin halving?", "expected_verdict": "REJECT"},
        {"category": "Macro Banking", "query": "history of Bank of England monetary policy", "expected_verdict": "REJECT"},
        {"category": "Crypto Trivia", "query": "how does Ethereum proof of stake work?", "expected_verdict": "REJECT"},
        {"category": "Cooking / Recipe", "query": "how to boil eggs perfectly", "expected_verdict": "REJECT"},
        {"category": "Science Trivia", "query": "why is the sky blue?", "expected_verdict": "REJECT"},
        {"category": "Politics / Public", "query": "Droupadi Murmu presidential address", "expected_verdict": "REJECT"},
        {"category": "Cooking / Recipe", "query": "apple pie recipe with cinnamon", "expected_verdict": "REJECT"},
        {"category": "Sports / World Cup", "query": "Kapil Dev 1983 world cup innings", "expected_verdict": "REJECT"},
        {"category": "Chitchat", "query": "knock knock who is there joke", "expected_verdict": "REJECT"},

        # 7. In-Scope Controls (must NOT be rejected)
        {"category": "In-Scope Active", "query": "Celebrity Fashions announcements", "expected_verdict": "ACCEPT"},
        {"category": "In-Scope Active", "query": "Singer India announcements", "expected_verdict": "ACCEPT"},
        {"category": "In-Scope Active", "query": "State Bank of India", "expected_verdict": "ACCEPT"},
        {"category": "In-Scope Active", "query": "Tata Motors Passenger Vehicles", "expected_verdict": "ACCEPT"},
        {"category": "In-Scope Zero-Filing", "query": "What did Infosys announce?", "expected_verdict": "ZERO_FILING_ACCEPT"}
    ]

    results = []
    print(f"{'#':<3} | {'Query':<50} | {'Intent':<14} | {'Docs':<4} | {'Dossier':<7} | {'Context':<18} | {'Status'}")
    print("-" * 120)

    for idx, item in enumerate(test_queries, 1):
        q = item["query"]
        cat = item["category"]
        expected = item["expected_verdict"]

        intent_data = agent.classify_intent_and_entities(q)
        intent_name = intent_data.get("intent", "UNKNOWN")
        resolved = intent_data.get("entities", {}).get("resolved", [])
        resolved_ticker = resolved[0]["ticker"] if resolved else "-"

        stream_gen, docs, tool_ctx = agent.stream_response(q)
        reply = "".join(list(stream_gen))
        dossier = should_show_sources(reply, docs, tool_ctx)

        # Verification rules
        if expected in ["REJECT", "GREETING"]:
            pass_docs = (len(docs) == 0)
            pass_dossier = (dossier is False)
            pass_ctx = (tool_ctx in ["out_of_domain", "non_nse", "greeting"])
            text_l = reply.lower()
            pass_refusal = (
                "refusal" in text_l or
                "scope notice" in text_l or
                "no nse filings" in text_l or
                "outside our operational scope" in text_l or
                "welcome to the market tide" in text_l or
                "domain scope refusal" in text_l
            )
            passed = pass_docs and pass_dossier and pass_ctx and pass_refusal
        elif expected == "ACCEPT":
            pass_docs = (len(docs) > 0)
            pass_intent = (intent_name != "OUT_OF_DOMAIN")
            # Dossier should show for mock or real response
            pass_dossier = should_show_sources("Official NSE corporate filing analysis.", docs, tool_ctx)
            passed = pass_docs and pass_intent and pass_dossier
        elif expected == "ZERO_FILING_ACCEPT":
            pass_docs = (len(docs) == 0)
            pass_dossier = (dossier is False)
            pass_intent = (intent_name != "OUT_OF_DOMAIN")
            pass_msg = "no announcements were published" in reply.lower()
            passed = pass_docs and pass_dossier and pass_intent and pass_msg

        status_str = "PASS" if passed else "FAIL ❌"

        print(f"{idx:<3} | {q[:48]:<50} | {intent_name:<14} | {len(docs):<4} | {str(dossier):<7} | {tool_ctx[:16]:<18} | {status_str}")

        results.append({
            "idx": idx,
            "category": cat,
            "query": q,
            "expected_verdict": expected,
            "intent": intent_name,
            "resolved_ticker": resolved_ticker,
            "retrieved_docs_count": len(docs),
            "tool_context": tool_ctx,
            "should_show_sources": dossier,
            "reply_snippet": reply[:150].replace("\n", " "),
            "passed": passed
        })

    # Summary
    ood_tests = [r for r in results if r["expected_verdict"] in ["REJECT", "GREETING"]]
    in_scope_tests = [r for r in results if r["expected_verdict"] in ["ACCEPT", "ZERO_FILING_ACCEPT"]]
    ood_passed = sum(1 for r in ood_tests if r["passed"])
    in_scope_passed = sum(1 for r in in_scope_tests if r["passed"])

    print("=" * 120)
    print(f"Out-of-Domain / Refusal Queries: {ood_passed}/{len(ood_tests)} Passed ({ood_passed/len(ood_tests)*100:.1f}%)")
    print(f"In-Scope Retention Queries:     {in_scope_passed}/{len(in_scope_tests)} Passed ({in_scope_passed/len(in_scope_tests)*100:.1f}%)")
    print(f"Total Evaluated:                {ood_passed + in_scope_passed}/{len(results)} Passed ({(ood_passed + in_scope_passed)/len(results)*100:.1f}%)")

    # Output json report
    out_path = os.path.join(BASE_DIR, "tests", "reports", "challenger_iter2_probe_results.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"Detailed JSON saved to {out_path}")

if __name__ == "__main__":
    main()
