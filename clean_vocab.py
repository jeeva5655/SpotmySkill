import json
import spacy

try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("en_core_web_sm not found, using basic stop words.")
    nlp = None

# Custom stop words specifically for this domain
CUSTOM_STOP_WORDS = {
    "the", "with", "users", "user", "use", "using", "used", "make", "making",
    "all", "any", "some", "many", "much", "other", "another", "such",
    "and", "or", "but", "if", "then", "else", "when", "where", "why", "how",
    "this", "that", "these", "those", "is", "am", "are", "was", "were", "be",
    "been", "being", "have", "has", "had", "do", "does", "did", "doing",
    "a", "an", "for", "in", "on", "at", "to", "from", "by", "about", "as",
    "into", "like", "through", "after", "over", "between", "out", "against",
    "during", "without", "before", "under", "around", "among", "we", "they",
    "it", "you", "he", "she", "i", "me", "him", "her", "us", "them", "my",
    "your", "their", "our", "its", "whose", "who", "whom", "which", "what",
    "can", "will", "would", "should", "could", "may", "might", "must", "very",
    "too", "also", "just", "only", "even", "more", "most", "less", "least",
    "experience", "experiences", "expert", "expertise", "knowledge",
    "understanding", "years", "year", "month", "months", "day", "days"
}

if nlp:
    spacy_stops = nlp.Defaults.stop_words
    CUSTOM_STOP_WORDS.update(spacy_stops)

with open("model/skill_vocab.json", "r", encoding="utf-8") as f:
    vocab = json.load(f)

print(f"Original vocab size: {len(vocab)}")

cleaned_vocab = []
for word in vocab:
    w = word.strip().lower()
    
    # 1. Skip empty
    if not w:
        continue
    
    # 2. Skip single characters unless it's known skill like "C", "R" (they are usually uppercase but here we are in lower)
    # Wait, "c" and "r" are valid skills. "a" is stop word.
    
    if w in CUSTOM_STOP_WORDS:
        continue
        
    # If it's a single char and not c/r, we might want to skip it, 
    # but to be safe, just rely on stop words (which includes 'a', 'i').
    
    # Check if purely digits
    if w.isdigit():
        continue
        
    cleaned_vocab.append(word.strip())

# Remove duplicates while preserving list
cleaned_vocab = list(set(cleaned_vocab))

print(f"Cleaned vocab size: {len(cleaned_vocab)}")

with open("model/skill_vocab.json", "w", encoding="utf-8") as f:
    json.dump(cleaned_vocab, f, indent=4)

print("Vocabulary cleaned and saved in place.")
