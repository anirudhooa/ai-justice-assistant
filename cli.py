#!/usr/bin/env python3
"""
AI Justice Department Assistant - Command Line Interface (CLI)
Interactive terminal for querying Indian laws, BNS 2023, BNSS 2023, and Constitutional rights.
"""

import sys
import os
from core.rag_engine import LegalRAGEngine

def clear_screen():
    print("\033[H\033[J", end="")

def print_banner():
    banner = r"""
========================================================================
   ⚖️  AI JUSTICE DEPARTMENT ASSISTANT  ⚖️
   Retrieval-Augmented Generation for Indian Laws & Citizen Rights
========================================================================
    """
    print(banner)
    print(" [1] Ask a Legal Question (Chat)")
    print(" [2] BNS ⇄ IPC Code Converter")
    print(" [3] Search Statutes by Keyword")
    print(" [4] View Emergency Helplines")
    print(" [5] Exit")
    print("=" * 72)

def main():
    try:
        engine = LegalRAGEngine()
    except Exception as e:
        print(f"Error initializing RAG engine: {e}")
        sys.exit(1)

    while True:
        print_banner()
        choice = input("\nSelect an option [1-5]: ").strip()

        if choice == "1":
            print("\n--- Legal Assistant Chat Mode (Type 'back' to return to menu) ---")
            while True:
                q = input("\nEnter your legal question / situation:\n> ").strip()
                if not q:
                    continue
                if q.lower() in ["back", "exit", "quit", "b"]:
                    break
                
                print("\n[AI Assistant is searching Indian statutes...]\n")
                res = engine.answer_query(q)
                
                print("=" * 72)
                print(f"Mode: {res['mode']}")
                print("=" * 72)
                print(res["answer"])
                print("=" * 72)
                
                if res.get("citations"):
                    print("\n[VERIFIED STATUTORY CITATIONS]")
                    for idx, c in enumerate(res["citations"], 1):
                        print(f" {idx}. {c['section']} ({c['act']})")
                        if c.get("legacy_code"):
                            print(f"    Legacy: {c['legacy_code']}")
                        print(f"    Title: {c['title']}")
                        print(f"    Relevance: {int(c['relevance_score']*100)}%")
                print("=" * 72)

        elif choice == "2":
            print("\n--- BNS ⇄ IPC / CrPC Cross-Reference Engine ---")
            code = input("Enter section number (e.g. 420, 154, 506, 500) or offence name: ").strip()
            if code:
                res = engine.convert_code(code)
                print("\n" + "=" * 50)
                if res.get("found"):
                    print(f"REFORMED LAW : {res['current_law']}")
                    print(f"REPEALED LAW : {res['legacy_law']}")
                    print(f"OFFENCE      : {res['offence_title']}")
                    print(f"SUMMARY      : {res['summary']}")
                    print(f"BAIL STATUS  : {res['bailable']}")
                    print(f"POLICE POWER : {res['cognizable']}")
                    print(f"PUNISHMENT   : {res['punishment']}")
                else:
                    print(f"Result: {res['message']}")
                print("=" * 50)
            input("\nPress Enter to continue...")

        elif choice == "3":
            print("\n--- Statute Keyword Search ---")
            kw = input("Enter search term (e.g., arrest, cyber, consumer, theft): ").strip()
            if kw:
                results = engine.search_statutes(kw, top_k=5)
                print(f"\nFound {len(results)} matching provisions:")
                for r in results:
                    print(f"\n• {r['section']} - {r['act']}")
                    print(f"  Title: {r['title']}")
                    print(f"  Category: {r['category']}")
                    print(f"  Summary: {r['summary'][:150]}...")
            input("\nPress Enter to continue...")

        elif choice == "4":
            print("\n" + "=" * 50)
            print("🚨 OFFICIAL 24/7 CITIZEN HELPLINES (INDIA)")
            print("=" * 50)
            print(" • National Cyber Crime Helpline: 1930 (or cybercrime.gov.in)")
            print(" • NALSA Free Legal Aid:          15100 (Toll-Free)")
            print(" • National Consumer Helpline:    1915 (or consumerhelpline.gov.in)")
            print(" • National Emergency (Police):   112")
            print(" • Women in Distress Helpline:    181 / 1091")
            print("=" * 50)
            input("\nPress Enter to continue...")

        elif choice == "5":
            print("\nExiting AI Justice Department Assistant. Jai Hind! 🇮🇳\n")
            break
        else:
            print("Invalid selection. Please choose 1 to 5.")

if __name__ == "__main__":
    main()
