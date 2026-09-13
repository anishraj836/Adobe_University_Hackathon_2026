#!/usr/bin/env python3
"""
Dedicated Fact Quotability & Entity-Sentence Binding Evaluator (Round 2 Appendix B & C).
Simulates neural retrieval passage slicing (500 chars) to detect unresolved anaphora
where key factual assertions lack explicit entity binding.
"""

import re

def evaluate_quotability(html: str, brand_hint: str = "") -> dict:
    """
    Evaluates passage-level quotability.
    Grounded in Appendix B & C: Assistants look for passages they can 'easily quote a clear fact from'.
    Safeguards:
    1. Scope-gated to <main> and <article>, explicitly excluding narrative blogs and founder letters.
    2. Hierarchical context: Prepends nearest parent heading (H1 > H2 > H3).
    3. Expletive pronoun filter: Ignores dummy subjects ('It is...', 'It was...').
    4. Conservative threshold: Only flags if >= 2 real dangling chunks and score < 50.
    """
    main_match = re.search(r'<(main|article)\b[^>]*>(.*?)<\/\1>', html, re.DOTALL | re.IGNORECASE)
    eval_html = main_match.group(2) if main_match else html

    # Scope Gate: Exclude narrative/editorial blog containers
    if re.search(r'\b(founder-letter|personal-story|blog-post|author-bio)\b', eval_html, re.I):
        return {"flagged": False, "score": 100, "evidence": "Narrative container exempted by scope gate."}

    sections = re.split(r'(<h[1-4]\b[^>]*>.*?<\/h[1-4]>)', eval_html, flags=re.I | re.DOTALL)
    current_heading = "General"
    chunks = []

    for part in sections:
        part_clean = part.strip()
        if not part_clean:
            continue
        h_match = re.match(r'<h[1-4]\b[^>]*>(.*?)<\/h[1-4]>', part_clean, re.I | re.DOTALL)
        if h_match:
            current_heading = re.sub(r'<[^>]+>', '', h_match.group(1)).strip()
        else:
            prose = re.sub(r'<[^>]+>', ' ', part_clean)
            prose = re.sub(r'\s+', ' ', prose).strip()
            words = prose.split()
            buffer = []
            char_count = 0
            for w in words:
                buffer.append(w)
                char_count += len(w) + 1
                if char_count >= 500:
                    chunk_text = f"[{current_heading}] " + " ".join(buffer)
                    chunks.append(chunk_text)
                    buffer = []
                    char_count = 0
            if buffer and len(buffer) > 15:
                chunks.append(f"[{current_heading}] " + " ".join(buffer))

    if len(chunks) < 3:
        return {"flagged": False, "score": 100, "evidence": "Insufficient chunk volume for RAG simulation."}

    dangling_count = 0
    expletive_pattern = re.compile(r'\bit\s+(?:is|was|takes|seems|appears|has\s+been)\b', re.I)
    pronoun_start_pattern = re.compile(r'(?:^|[\.\?!]\s+)(?:it|they|this|these|the platform|the system)\b', re.I)

    for ch in chunks:
        if brand_hint and len(brand_hint) >= 3 and re.search(r'\b' + re.escape(brand_hint) + r'\b', ch, re.I):
            continue
        iter_matches = list(pronoun_start_pattern.finditer(ch))
        if iter_matches:
            real_dangling = False
            for match_obj in iter_matches:
                start_idx = match_obj.start()
                surrounding = ch[start_idx:start_idx+35]
                if not expletive_pattern.search(surrounding):
                    real_dangling = True
                    break
            if real_dangling:
                dangling_count += 1

    aqs = int(((len(chunks) - dangling_count) / len(chunks)) * 100)
    flagged = aqs < 50 and dangling_count >= 2

    return {
        "flagged": flagged,
        "score": aqs,
        "total_chunks": len(chunks),
        "dangling_chunks": dangling_count,
        "evidence": f"Simulated {len(chunks)} passage chunks (500 chars); {dangling_count}/{len(chunks)} ({int((dangling_count/len(chunks))*100)}%) rely on dangling pronouns without explicit entity binding. Atomic Quotability Score: {aqs}/100."
    }
