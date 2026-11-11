import os
import json
import re
from typing import List, Dict, Any, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "statutes.json")

class LegalRAGEngine:
    """
    Retrieval-Augmented Generation (RAG) Engine for the AI Justice Department Assistant.
    Combines dense TF-IDF n-gram vectorization, lexical boosting, and dual-mode response generation.
    """
    def __init__(self, data_file: str = DATA_PATH):
        self.data_file = data_file
        self.statutes: List[Dict[str, Any]] = []
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.doc_vectors = None
        self.corpus_texts: List[str] = []
        self.load_corpus()
        self.build_index()

    def load_corpus(self):
        if not os.path.exists(self.data_file):
            raise FileNotFoundError(f"Corpus file not found: {self.data_file}")
        with open(self.data_file, "r", encoding="utf-8") as f:
            self.statutes = json.load(f)

    def build_index(self):
        """Constructs vector search index using TF-IDF n-gram features."""
        self.corpus_texts = []
        for s in self.statutes:
            # Enrich text representation with keywords, legacy codes, and definitions
            kw_str = " ".join(s.get("keywords", []))
            doc_str = (
                f"{s['act']} {s['section']} {s.get('legacy_code', '')} "
                f"{s['title']} {s['category']} {s['summary']} "
                f"{s['full_text']} {kw_str} {s.get('punishment', '')}"
            )
            self.corpus_texts.append(doc_str)

        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            sublinear_tf=True,
            stop_words="english"
        )
        self.doc_vectors = self.vectorizer.fit_transform(self.corpus_texts)

    def search_statutes(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Retrieves top-k most relevant legal provisions for a given query.
        Uses hybrid cosine similarity + lexical boosting on section numbers and key phrases.
        """
        if not query.strip():
            return []

        # Vector cosine similarity
        query_vec = self.vectorizer.transform([query])
        cos_sims = cosine_similarity(query_vec, self.doc_vectors)[0]

        # Lexical boost
        query_lower = query.lower()
        query_tokens = set(re.findall(r"\w+", query_lower))

        scored_results = []
        for idx, s in enumerate(self.statutes):
            score = float(cos_sims[idx])

            # Section number exact match boost (e.g. "420", "318", "173", "22")
            sec_num = re.sub(r"[^\d]", "", s.get("section", ""))
            legacy_num = re.sub(r"[^\d]", "", s.get("legacy_code", ""))
            
            for token in query_tokens:
                if token.isdigit() and len(token) >= 2:
                    if token == sec_num or token == legacy_num:
                        score += 0.55
                if token in s.get("keywords", []):
                    score += 0.15

            # Keyword phrase match boost
            for kw in s.get("keywords", []):
                if kw in query_lower:
                    score += 0.25

            scored_results.append((score, s))

        scored_results.sort(key=lambda x: x[0], reverse=True)
        top_matches = [
            {**item[1], "relevance_score": round(min(item[0], 1.0), 3)}
            for item in scored_results[:top_k]
        ]
        return top_matches

    def convert_code(self, code_query: str) -> Dict[str, Any]:
        """
        Cross-references historical IPC/CrPC sections with current BNS/BNSS sections.
        Example: '420' -> Section 318 BNS
        """
        clean_q = code_query.strip().lower()
        extracted_digits = re.findall(r"\d+", clean_q)
        target_num = extracted_digits[0] if extracted_digits else clean_q

        matches = []
        for s in self.statutes:
            legacy = s.get("legacy_code", "").lower()
            section = s.get("section", "").lower()
            if target_num in legacy or target_num in section or clean_q in s["title"].lower():
                matches.append(s)

        if matches:
            m = matches[0]
            return {
                "found": True,
                "queried": code_query,
                "current_law": f"{m['act']} - {m['section']}",
                "legacy_law": m.get("legacy_code", "N/A"),
                "offence_title": m["title"],
                "summary": m["summary"],
                "bailable": m.get("bailable", "N/A"),
                "cognizable": m.get("cognizable", "N/A"),
                "punishment": m.get("punishment", "N/A")
            }
        
        return {
            "found": False,
            "queried": code_query,
            "message": f"No direct mapping found in the primary database for '{code_query}'."
        }

    def _generate_with_anthropic(self, query: str, context_statutes: List[Dict[str, Any]]) -> Optional[str]:
        """Attempts generation using Anthropic Claude if ANTHROPIC_API_KEY is available."""
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            return None

        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            
            context_text = "\n\n".join([
                f"### {s['act']} - {s['section']} ({s.get('legacy_code', '')})\n"
                f"**Title**: {s['title']}\n"
                f"**Classification**: {s.get('cognizable', '')} | {s.get('bailable', '')}\n"
                f"**Statutory Provision**: {s['full_text']}\n"
                f"**Punishment**: {s.get('punishment', '')}\n"
                f"**Recommended Legal Steps**: {'; '.join(s.get('remedy_steps', []))}"
                for s in context_statutes
            ])

            prompt = (
                f"You are the AI Justice Department Assistant, an official conversational assistant "
                f"for Indian law and justice. Help ordinary citizens understand their legal rights.\n\n"
                f"Strict Grounding Rules:\n"
                f"1. Explain the legal answers in simple, compassionate natural language.\n"
                f"2. Reference the exact Section and Act from the provided Legal Context.\n"
                f"3. Clearly contrast Bharatiya Nyaya Sanhita (BNS 2023) or BNSS with older IPC/CrPC sections where relevant.\n"
                f"4. Provide step-by-step practical remedies (e.g. FIR filing, 1930 cyber helpline, consumer portal).\n"
                f"5. End with the official disclaimer: 'Disclaimer: This assistant provides legal literacy and informational assistance; it does not constitute formal legal counsel.'\n\n"
                f"LEGAL CONTEXT:\n{context_text}\n\n"
                f"CITIZEN QUERY: {query}\n\n"
                f"RESPONSE:"
            )

            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=800,
                messages=[{"role": "user", "content": prompt}]
            )
            if response.content and len(response.content) > 0:
                return response.content[0].text
        except Exception as e:
            # Silently fall back to built-in generator
            pass
        return None

    def _generate_deterministic_answer(self, query: str, top_matches: List[Dict[str, Any]]) -> str:
        """
        Built-in high-fidelity legal synthesis engine.
        Produces structured, clear, and verified answers without requiring third-party API availability.
        """
        if not top_matches or top_matches[0]["relevance_score"] < 0.12:
            return (
                "### ⚖️ Inquiry Assessment\n\n"
                "I could not locate an exact statutory match in the primary repository for your query. "
                "However, under Indian jurisprudence, every citizen is entitled to legal assistance and access to justice:\n\n"
                "- **Free Legal Assistance:** Under **Article 39A of the Constitution of India**, if you cannot afford a private advocate, "
                "you can contact the **National Legal Services Authority (NALSA)** at toll-free **15100** or visit your local District Legal Services Authority (DLSA).\n"
                "- **Emergency Help:** Dial **112** for police emergencies or **1930** for financial cyber scams.\n\n"
                "*Disclaimer: This assistant provides general legal information and does not constitute formal legal counsel.*"
            )

        primary = top_matches[0]
        secondary = top_matches[1] if len(top_matches) > 1 and top_matches[1]["relevance_score"] > 0.2 else None

        ans = f"### ⚖️ Legal Overview & Applicable Indian Laws\n\n"
        ans += f"Based on your query, the primary governing law is **{primary['act']} — {primary['section']}**"
        if primary.get("legacy_code"):
            ans += f" *(formerly known as {primary['legacy_code']})*.\n\n"
        else:
            ans += ".\n\n"

        ans += f"**Key Meaning & Legal Principle:**\n{primary['summary']}\n\n"

        # Offence classification details if applicable
        if primary.get("bailable") != "N/A" or primary.get("cognizable") != "N/A":
            ans += f"**Offence Classification & Penalties:**\n"
            if primary.get("cognizable"):
                ans += f"- **Police Power:** {primary['cognizable']}\n"
            if primary.get("bailable"):
                ans += f"- **Bail Status:** {primary['bailable']}\n"
            if primary.get("punishment"):
                ans += f"- **Statutory Punishment:** {primary['punishment']}\n"
            ans += "\n"

        # Secondary statute reference if correlated
        if secondary:
            ans += (
                f"**Associated Provision:**\n"
                f"- **{secondary['act']} ({secondary['section']})**: {secondary['summary']}\n\n"
            )

        # Actionable Remedies
        if primary.get("remedy_steps"):
            ans += "### 📋 What You Should Do (Step-by-Step Practical Remedies):\n"
            for idx, step in enumerate(primary["remedy_steps"], 1):
                ans += f"{idx}. {step}\n"
            ans += "\n"

        # Relevant Helplines
        ans += "### 📞 Official Emergency & Redressal Helplines:\n"
        query_l = query.lower()
        if "cyber" in query_l or "money" in query_l or "scam" in query_l or "cheat" in query_l or "upi" in query_l:
            ans += "- **National Cyber Crime Helpline:** Dial **1930** or report online at [cybercrime.gov.in](https://cybercrime.gov.in)\n"
        if "arrest" in query_l or "police" in query_l or "detain" in query_l or "lawyer" in query_l:
            ans += "- **NALSA Free Legal Aid:** Dial **15100** (24/7 National Legal Services Authority)\n"
        if "consumer" in query_l or "defective" in query_l or "refund" in query_l or "product" in query_l:
            ans += "- **National Consumer Helpline:** Dial **1915** or portal at [consumerhelpline.gov.in](https://consumerhelpline.gov.in)\n"
        if "woman" in query_l or "stalk" in query_l or "domestic" in query_l or "harass" in query_l:
            ans += "- **National Emergency & Women Helpline:** Dial **112** or **1091** / **181**\n"
        ans += "- **All-India Emergency Number:** Dial **112**\n\n"

        ans += (
            "---\n"
            "*Disclaimer: This response is generated by the AI Justice Department Assistant for public legal literacy "
            "and informational orientation under Article 39A. It does not replace professional advice from a licensed advocate.*"
        )
        return ans

    def answer_query(self, query: str) -> Dict[str, Any]:
        """
        Main query orchestration pipeline.
        Searches statutes, attempts LLM synthesis with fallback to deterministic generation,
        and returns structured result.
        """
        top_matches = self.search_statutes(query, top_k=3)
        
        # Try Claude if available, else deterministic RAG
        llm_answer = self._generate_with_anthropic(query, top_matches)
        mode = "LLM-Grounded (Anthropic Claude)" if llm_answer else "Deterministic Extractive RAG"
        final_answer = llm_answer if llm_answer else self._generate_deterministic_answer(query, top_matches)

        # Dynamic follow-up recommendations
        followups = []
        if top_matches:
            top_cat = top_matches[0].get("category", "")
            if "Criminal" in top_cat:
                followups = [
                    "Can the police arrest someone without a warrant for this?",
                    "How to file a Zero-FIR if the crime occurred in another city?",
                    "What documents are needed to apply for anticipatory bail?"
                ]
            elif "Consumer" in top_cat:
                followups = [
                    "How do I file a complaint on e-Daakhil without hiring a lawyer?",
                    "What is the maximum compensation I can claim in the District Commission?",
                    "What are the timelines for resolving a consumer dispute?"
                ]
            elif "Constitutional" in top_cat or "Arrest" in top_cat:
                followups = [
                    "Can the police keep an accused person for more than 24 hours?",
                    "How can I get free legal aid from NALSA?",
                    "What is a Habeas Corpus petition?"
                ]
            else:
                followups = [
                    "What are the penalties if the authority fails to respond in 30 days?",
                    "How do I file a first appeal under Section 19 of RTI?",
                    "What should I do if an FIR is refused?"
                ]

        return {
            "query": query,
            "answer": final_answer,
            "citations": top_matches,
            "mode": mode,
            "suggested_followups": followups
        }
