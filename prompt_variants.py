# prompt_variants.py
from sentence_transformers import SentenceTransformer, util

model = SentenceTransformer("all-MiniLM-L6-v2")

def is_paraphrase(text1, text2, threshold=0.8):
    emb1 = model.encode(text1, convert_to_tensor=True)
    emb2 = model.encode(text2, convert_to_tensor=True)
    sim = float(util.pytorch_cos_sim(emb1, emb2))
    return sim >= threshold, sim

def suggest_variants(prompt, existing_prompts, threshold=0.75, max_count=3):
    variants = []
    for item in existing_prompts:
        match, score = is_paraphrase(prompt, item)
        if match and item != prompt:
            variants.append((item, score))
    variants = sorted(variants, key=lambda x: -x[1])
    return [v[0] for v in variants[:max_count]]
