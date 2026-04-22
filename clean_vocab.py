"""
Comprehensive vocabulary cleaner for SpotmySkill.
Removes all categories of noise from the skill_vocab.json file.
"""
import json
import re
import spacy

try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("en_core_web_sm not found, using basic stop words only.")
    nlp = None

# ──────────────────────────────────────────────
# 1. STOP WORDS — common English words
# ──────────────────────────────────────────────
STOP_WORDS = set()
if nlp:
    STOP_WORDS.update(nlp.Defaults.stop_words)

STOP_WORDS.update({
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
    "of", "no", "not", "nor", "so", "up", "down",
})

# ──────────────────────────────────────────────
# 2. RESUME FILLER WORDS — generic descriptors
# ──────────────────────────────────────────────
RESUME_FILLER = {
    # Generic resume noise
    "proficient", "proficient in", "experienced", "experience", "experience in",
    "experiences", "expert", "expertise", "knowledge", "understanding",
    "years", "year", "month", "months", "day", "days", "week", "weeks",
    "5 years of", "5 years", "3 years", "10 years", "2 years", "years of",
    "years of experience", "responsible", "responsible for",
    "excellent", "strong", "good", "well", "able", "hands", "hands-on",
    "senior", "junior", "lead", "work", "working", "skills", "skill",
    "team", "teams", "management", "project", "projects", "support",
    "develop", "developed", "developing", "development",
    "design", "system", "systems", "data", "tools", "tool",
    "new", "high", "based", "full", "key", "set", "part",
    "level", "type", "end", "run", "test", "build", "plan",
    "help", "need", "range", "time", "best", "large", "small",
    "open", "close", "step", "area", "role", "field", "line",
    "rest", "cloud", "deployment", "day-to-day",
}

# ──────────────────────────────────────────────
# 3. GENERIC ENGLISH WORDS — not skills
# ──────────────────────────────────────────────
GENERIC_ENGLISH = {
    "able", "access", "account", "across", "act", "action", "active",
    "activities", "activity", "add", "added", "addition", "additional",
    "address", "advance", "advanced", "ago", "along", "already", "amount",
    "analysis", "approach", "appropriate", "attention", "available", "average",
    "aware", "basic", "basis", "became", "become", "begin", "beginning",
    "benefit", "better", "big", "bit", "board", "body", "book", "bottom",
    "box", "bring", "broad", "brought", "building", "built", "business",
    "called", "came", "case", "cases", "cause", "center", "central",
    "certain", "certainly", "change", "changed", "changes", "check", "child",
    "children", "choice", "choose", "city", "class", "clear", "clearly",
    "client", "clients", "close", "closely", "closer", "code", "college",
    "combined", "come", "comes", "coming", "common", "commonly",
    "communication", "community", "companies", "company", "complete",
    "completed", "completely", "complex", "comprehensive", "computer",
    "concept", "condition", "conditions", "conduct", "consider",
    "considered", "consistent", "contact", "content", "context", "continue",
    "continued", "contract", "contribute", "control", "core", "correct",
    "cost", "country", "couple", "course", "cover", "create", "created",
    "creating", "creation", "critical", "cross", "culture", "current",
    "currently", "customer", "customers", "daily", "deal", "decided",
    "decision", "deep", "defined", "deliver", "delivered", "demand",
    "department", "describe", "desired", "detail", "detailed", "details",
    "determine", "different", "difficult", "digital", "direct", "direction",
    "directly", "discuss", "document", "documentation", "done", "drive",
    "driven", "due", "early", "easy", "education", "effective",
    "effectively", "effort", "element", "emerging", "employee", "employees",
    "enable", "enabled", "engage", "engaged", "engineering", "enhance",
    "enhanced", "ensure", "ensured", "ensuring", "entire", "environment",
    "environments", "equipment", "essential", "establish", "established",
    "evaluate", "evaluation", "event", "events", "every", "evidence",
    "exact", "example", "examples", "executive", "existing", "expect",
    "expected", "extensive", "external", "extra", "face", "facility",
    "fact", "factor", "fast", "feature", "features", "feel", "final",
    "finally", "find", "first", "fit", "focus", "focused", "follow",
    "following", "force", "form", "found", "foundation", "free", "front",
    "fully", "function", "functional", "functions", "fundamental",
    "further", "future", "gain", "gained", "general", "generate", "given",
    "global", "goal", "goals", "great", "group", "groups", "grow",
    "growing", "growth", "guide", "handle", "hard", "head", "health",
    "held", "helped", "helping", "highly", "hold", "home", "hour", "human",
    "idea", "ideal", "identify", "immediate", "impact", "implement",
    "implementation", "implemented", "implementing", "important", "improve",
    "improved", "improvement", "include", "included", "includes",
    "including", "increase", "increased", "increasing", "individual",
    "individuals", "industry", "information", "initial", "initiative",
    "input", "inside", "insight", "install", "instead", "institution",
    "integrate", "integrated", "integration", "interest", "interested",
    "internal", "international", "interview", "introduce", "introduced",
    "investment", "involve", "involved", "involves", "involving", "issue",
    "issues", "item", "items", "job", "join", "joined", "keep", "keeping",
    "kind", "know", "known", "lack", "latest", "launch", "launched",
    "leading", "learn", "learned", "learning", "left", "legal", "let",
    "life", "limited", "list", "live", "local", "location", "long", "look",
    "looking", "lot", "low", "made", "main", "maintain", "maintained",
    "maintaining", "major", "manage", "managed", "managing", "market",
    "material", "materials", "matter", "mean", "means", "measure", "media",
    "meet", "meeting", "meetings", "member", "members", "method", "methods",
    "mind", "model", "models", "modern", "monitor", "monitoring", "move",
    "multiple", "national", "natural", "nature", "near", "necessary",
    "needs", "network", "note", "notice", "number", "numbers", "objective",
    "objectives", "obtain", "offer", "office", "often", "old", "online",
    "operations", "opportunity", "option", "options", "order",
    "organization", "original", "outside", "overall", "own", "owner",
    "paper", "particular", "partner", "partners", "past", "path", "pay",
    "people", "percent", "perform", "performance", "period", "person",
    "personal", "perspective", "phase", "physical", "pick", "place",
    "planning", "platform", "play", "player", "point", "policy", "position",
    "positive", "possible", "potential", "power", "powerful", "practice",
    "practices", "prepare", "prepared", "present", "presented", "previous",
    "previously", "primary", "principle", "prior", "priority", "problem",
    "problems", "procedure", "procedures", "process", "processes",
    "produce", "product", "production", "products", "professional",
    "professionals", "profile", "program", "programs", "progress",
    "promote", "proper", "properly", "property", "proposal", "propose",
    "proposed", "protect", "provide", "provided", "provider", "providers",
    "providing", "public", "purpose", "pursue", "put", "quality",
    "question", "questions", "quick", "quickly", "raise", "rate", "reach",
    "read", "ready", "real", "receive", "received", "recent", "recently",
    "recognize", "recommend", "record", "records", "reduce", "reduced",
    "reference", "region", "regular", "regularly", "related", "relation",
    "relationship", "relationships", "release", "relevant", "remain",
    "remove", "report", "reports", "represent", "request", "require",
    "required", "requirements", "research", "resolution", "resolve",
    "resource", "resources", "respond", "response", "responsibilities",
    "result", "results", "return", "review", "reviewed", "reviews", "right",
    "risk", "role", "roles", "round", "rule", "rules", "running", "safe",
    "sale", "sales", "sample", "save", "scale", "schedule", "school",
    "scope", "search", "second", "section", "secure", "security", "select",
    "selected", "send", "sense", "separate", "series", "serve", "served",
    "serves", "service", "services", "session", "setting", "setup",
    "several", "share", "shared", "shift", "short", "show", "side",
    "significant", "significantly", "similar", "simple", "simply", "since",
    "single", "site", "situation", "size", "social", "solution",
    "solutions", "solve", "source", "sources", "space", "special",
    "specific", "specifically", "staff", "stage", "stand", "standard",
    "standards", "start", "started", "starting", "state", "status", "stay",
    "stop", "store", "story", "strategy", "strength", "strong", "structure",
    "student", "students", "study", "subject", "submit", "success",
    "successful", "successfully", "suite", "summary", "supply", "sure",
    "table", "take", "taken", "talent", "target", "task", "tasks", "teach",
    "teaching", "technical", "technique", "techniques", "technology",
    "term", "terms", "testing", "third", "thought", "throughout", "today",
    "together", "top", "total", "touch", "toward", "track", "tracking",
    "trade", "traditional", "train", "trained", "training", "transfer",
    "trend", "turn", "understand", "unit", "update", "updated", "upper",
    "usage", "utilize", "utilized", "utilizing", "value", "various",
    "vendor", "vendors", "version", "view", "vision", "visit", "volume",
    "want", "watch", "water", "way", "ways", "week", "weekly", "wide",
    "within", "word", "write", "writing", "written",
    
    # Extra generic words caught in pass 2 & 3
    "ability", "abs", "abstracts", "also", "always", "among",
    "asked", "away", "back", "basically", "because", "being",
    "beside", "besides", "both", "briefly", "came", "coming",
    "considering", "currently", "each", "either", "enough",
    "entirely", "especially", "essentially", "eventually",
    "every", "everything", "exactly", "few", "formerly",
    "frequently", "generally", "getting", "goes", "gone",
    "hence", "however", "instead", "itself", "mainly",
    "making", "maybe", "meanwhile", "merely", "moreover",
    "mostly", "namely", "neither", "nevertheless", "next",
    "nobody", "nonetheless", "nothing", "now", "obviously",
    "otherwise", "overall", "own", "particularly", "perhaps",
    "please", "plus", "possibly", "practically", "precisely",
    "primarily", "probably", "quite", "rather", "really",
    "recently", "regardless", "roughly", "same", "since",
    "slightly", "somehow", "sometimes", "somewhat", "soon",
    "still", "sure", "surely", "thereby", "therefore", "though",
    "thus", "together", "typically", "ultimately", "undoubtedly",
    "unfortunately", "unlike", "usually", "utterly", "virtually",
    "whatever", "whenever", "wherever", "whether", "whoever",
    "wholly", "yet",
    
    # Additional non-tech nouns from pass 4
    "wounds","woven shirts","letters","levels","ledgers","ledger",
    "lecturer","lending","letters and memos","lesson plans","lessons learned",
    "levy officer","liability","liaison","lighting","listening","litigation",
    "works","workshops","workstations","wound care","writer","wounds",
    "youth","yoga","accounts","accountant","accountability",
}

# ──────────────────────────────────────────────
# 4. COMMON VERBS — resume action verbs
# ──────────────────────────────────────────────
COMMON_VERBS = {
    "achieve", "achieved", "achieving", "act", "acted", "acting",
    "apply", "applied", "applying", "arrange", "arranged", "assist",
    "assisted", "assisting", "attend", "attended", "attending",
    "begin", "began", "brought", "buy", "call", "called", "carry",
    "carried", "cause", "caused", "check", "checked", "clean", "cleaned",
    "collect", "collected", "come", "complete", "completed", "consider",
    "considered", "continue", "continued", "contribute", "contributed",
    "coordinate", "coordinated", "coordinating", "cover", "covered",
    "deliver", "delivered", "delivering", "demonstrate", "demonstrated",
    "determine", "determined", "direct", "directed", "discuss", "discussed",
    "distribute", "distributed", "earn", "earned", "enable", "enabled",
    "encourage", "encouraged", "engage", "engaged", "ensure", "ensured",
    "ensuring", "enter", "entered", "establish", "established", "evaluate",
    "evaluated", "examine", "examined", "execute", "executed", "exercise",
    "expand", "expanded", "expect", "expected", "explore", "explored",
    "extend", "extended", "facilitate", "facilitated", "fill", "filled",
    "find", "follow", "followed", "form", "formed", "gain", "gained",
    "gather", "gathered", "generate", "generated", "get", "give", "given",
    "go", "grew", "grow", "growing", "grown", "handle", "handled",
    "handling", "helped", "identify", "identified", "implement",
    "implemented", "implementing", "improve", "improved", "improving",
    "include", "included", "including", "increase", "increased",
    "increasing", "indicate", "indicated", "initiate", "initiated",
    "inspect", "inspected", "install", "installed", "interact",
    "interacted", "introduce", "introduced", "investigate", "investigated",
    "involve", "involved", "involving", "issue", "issued", "join",
    "joined", "keep", "keeping", "kept", "launch", "launched", "learn",
    "learned", "led", "maintain", "maintained", "maintaining", "manage",
    "managed", "managing", "meet", "met", "monitor", "monitored",
    "monitoring", "move", "moved", "obtain", "obtained", "offer",
    "offered", "operate", "operated", "operating", "organize", "organized",
    "organizing", "oversee", "oversaw", "participate", "participated",
    "perform", "performed", "performing", "place", "placed", "plan",
    "planned", "planning", "play", "played", "prepare", "prepared",
    "present", "presented", "process", "processed", "produce", "produced",
    "promote", "promoted", "provide", "provided", "providing", "pursue",
    "pursued", "raise", "raised", "reach", "reached", "receive",
    "received", "recognize", "recognized", "recommend", "recommended",
    "record", "recorded", "reduce", "reduced", "refer", "referred",
    "release", "released", "remain", "remained", "remove", "removed",
    "report", "reported", "represent", "represented", "request",
    "requested", "require", "required", "research", "researched",
    "resolve", "resolved", "respond", "responded", "restore", "restored",
    "result", "resulted", "retain", "retained", "return", "returned",
    "review", "reviewed", "run", "running", "save", "saved", "schedule",
    "scheduled", "secure", "secured", "seek", "seeking", "select",
    "selected", "sell", "send", "sent", "serve", "served", "serving",
    "set", "setting", "share", "shared", "show", "showed", "shown",
    "solve", "solved", "sort", "sorted", "speak", "speaking", "start",
    "started", "starting", "stay", "stayed", "stop", "stopped", "store",
    "stored", "submit", "submitted", "succeed", "succeeded", "suggest",
    "suggested", "supervise", "supervised", "supply", "supplied",
    "support", "supported", "supporting", "take", "taken", "talk",
    "teach", "taught", "tell", "think", "thought", "track", "tracked",
    "tracking", "train", "trained", "training", "transfer", "transferred",
    "travel", "traveled", "treat", "treated", "turn", "turned",
    "understand", "understood", "update", "updated", "updating", "use",
    "used", "using", "utilize", "utilized", "utilizing", "verify",
    "verified", "visit", "visited", "walk", "want", "wanted", "watch",
    "win", "won", "work", "worked", "working", "write", "wrote", "written",
}

# ──────────────────────────────────────────────
# 5. ADJECTIVE DESCRIPTORS — soft personality words
# ──────────────────────────────────────────────
ADJECTIVE_DESCRIPTORS = {
    "strong", "excellent", "good", "great", "better", "best",
    "effective", "efficient", "reliable", "responsible",
    "dedicated", "motivated", "organized", "detail-oriented",
    "creative", "innovative", "proactive", "enthusiastic",
    "professional", "flexible", "adaptable", "consistent",
    "dependable", "resourceful", "analytical", "strategic",
    "dynamic", "passionate", "hardworking", "self-motivated",
    "diverse", "various", "certain", "several", "specific",
    "significant", "successful", "positive", "negative",
    "independent", "collaborative", "experienced",
}

# ──────────────────────────────────────────────
# 6. SECTION HEADERS — resume sections
# ──────────────────────────────────────────────
SECTION_HEADERS = {
    "education", "experience", "summary", "objective", "references",
    "certifications", "awards", "publications", "interests", "hobbies",
    "languages", "projects", "achievements", "qualifications",
    "professional experience", "work experience", "professional summary",
    "career objective", "career summary", "additional information",
    "contact information", "personal information", "technical skills",
}

# ──────────────────────────────────────────────
# 7. LOCATION NAMES — cities, states, countries
# ──────────────────────────────────────────────
LOCATION_NAMES = {
    "new york", "los angeles", "chicago", "houston", "phoenix",
    "philadelphia", "san antonio", "san diego", "dallas", "austin",
    "san francisco", "seattle", "denver", "boston", "nashville",
    "portland", "las vegas", "memphis", "louisville", "baltimore",
    "milwaukee", "atlanta", "miami", "tampa", "california", "texas",
    "florida", "ohio", "georgia", "michigan", "illinois", "pennsylvania",
    "north carolina", "new jersey", "virginia", "washington",
    "massachusetts", "arizona", "tennessee", "indiana", "missouri",
    "maryland", "wisconsin", "colorado", "minnesota", "south carolina",
    "alabama", "louisiana", "kentucky", "oregon", "oklahoma",
    "connecticut", "utah", "iowa", "nevada", "arkansas", "mississippi",
    "kansas", "nebraska", "new mexico", "west virginia", "idaho",
    "hawaii", "maine", "montana", "delaware", "wyoming",
    "north dakota", "south dakota", "vermont", "new hampshire",
    "rhode island", "alaska",
    # Countries
    "united states", "canada", "united kingdom", "australia", "india",
    "china", "japan", "germany", "france", "brazil", "mexico",
}

# ──────────────────────────────────────────────
# Combine all blocklists
# ──────────────────────────────────────────────
ALL_BLOCKED = set()
for wordset in [STOP_WORDS, RESUME_FILLER, GENERIC_ENGLISH, COMMON_VERBS,
                ADJECTIVE_DESCRIPTORS, SECTION_HEADERS, LOCATION_NAMES]:
    ALL_BLOCKED.update(wordset)

# Explicit list of things that are definitively NOT skills (caught in passes 2 & 3)
NON_SKILLS = {
    "abc 7 news", "abc.com", "abcnews.com", "lionel richie",
    "lighthouse ministries", "linus project", "zyrtec", "year 2000",
    "youth participants", "yahoo and", "accomplishments",
    "accomplishments created", "academic", "accessories",
    "accommodations", "aardwolf", "abandon rate", "account analysis &",
    "limited to", "literate", "llc's", "live-type", "live or digital",
    "line sheets", "year end", "year-end", "year-end w-2s",
    "access information", "access systems: solar",
    "listen effectively", "listen intently", "listening skills",
    "literary analysis", "linguistic behaviors",
    "light bookkeeping knowledge", "life support",
    "wsam image", "wsam-dc fiber", "x-51 hypersonic engine",
    "writing test",
}
ALL_BLOCKED.update(NON_SKILLS)


def is_noisy(entry):
    """Return True if the entry is noise and should be removed."""
    w = entry.strip()
    wl = w.lower()

    # Empty
    if not w:
        return True

    # Single character (unless c or r — programming languages)
    if len(w) <= 1 and wl not in ("c", "r"):
        return True

    # Purely numeric or date-like patterns (01/2015, 000, etc.)
    if re.match(r'^[\d/\-\.\\,\s]+$', w):
        return True

    # Starts with a number (e.g. "000 employees", "25 web site")
    if re.match(r'^\d', w):
        return True

    # Contains dollar amounts
    if '$' in w:
        return True

    # Contains unicode garbage (\xa0, \u200b, \ufffd, \u25cf, etc.)
    if '\xa0' in w or '\u200b' in w or '\ufffd' in w or '\u25cf' in w:
        return True
        
    # Any entry containing non-ASCII special symbols that aren't tech symbols
    for ch in w:
        code = ord(ch)
        if code > 127 and ch not in ('é', 'ñ', 'ü', 'ö', 'ä', 'ß'):
            return True

    # Starts with punctuation / bullets (* - + " ' \)
    if re.match(r'^[\*\-\+\u2022\u2013\u2014"\'\\\\]', w):
        return True
        
    # Starts with ". " or "/ " or ", " — parsing fragments
    if re.match(r'^[\.\/,;:]\s', w):
        return True

    # Contains ampersand fragments from bad parsing (& Diaspora, & Restaurants)
    if w.startswith('&') or w.startswith('\u0026') or w.endswith(' &') or w.endswith(' and'):
        return True

    # Contains parentheses fragments — partial parsing artifacts
    if w.startswith('(') and not w.endswith(')'):
        return True
    if w.startswith('(') and w.endswith(')'):
        return True
    if w.endswith(')') and '(' not in w:
        return True

    # Ends with a period followed by nothing — sentence endings
    # Keep ".NET", "A.I.", etc.
    if w.endswith('.') and len(w) > 5 and not re.match(r'^[\w\.\+\#]+$', w):
        return True
        
    # Entries containing a colon followed by space (looks like "Category: value")
    if re.search(r':\s', w) and not any(tech in wl for tech in [
        'c:', 'c#', 'http:', 'https:', 'tcp:', 'udp:', 'ftp:',
    ]):
        return True

    # Entries with "LACP" pattern — incomplete parenthetical
    if w.endswith('(LACP') or re.search(r'\([A-Z]+$', w):
        return True

    # Exact match against blocklists (case-insensitive)
    if wl in ALL_BLOCKED:
        return True

    # Very long phrase (>45 chars) or 4+ words — almost certainly a sentence fragment, not a skill
    words = w.split()
    if len(w) > 45 or len(words) >= 4:
        return True

    # Starts with lowercase "a " or "an " — these are sentence fragments
    if re.match(r'^a\s', wl) or re.match(r'^an\s', wl):
        return True

    # Starts with "ability to" or "able to" — soft skill phrases, not skills
    if wl.startswith("ability to") or wl.startswith("able to"):
        return True

    # Contains "continued." — parsing artifact
    if "continued" in wl:
        return True
        
    # Entries starting with these noise patterns
    starter_noise = {'such as', 'into a', 'being hands', 'while supervising', 
                     'needed as', 'eager for', 'requests.'}
    if any(wl.startswith(s) for s in starter_noise):
        return True
        
    # All-caps noise
    if wl in {'of an', 'of a', 'of the'}:
        return True

    # Entries ending with a stop word (incomplete phrases)
    stop_endings = {'and', 'or', 'for', 'in', 'to', 'of', 'the', 'with', 'at', 'by', 'on', 'as', 'an', 'a'}
    if len(words) >= 2 and words[-1].lower() in stop_endings:
        # Exception: 'Single Sign On' is a real tech term
        if wl not in {'single sign on', 'single sign-on'}:
            return True

    # Contains tab characters — formatting artifact
    if '\t' in w:
        return True

    # Multiple consecutive spaces — formatting artifact
    if '  ' in w:
        return True
        
    # Very short single words — keep only known tech: C, R, Go, SQL, etc
    if len(words) == 1 and len(w) <= 4 and wl.isalpha():
        known_short = {
            "c", "r", "go", "sql", "css", "html", "php", "xml", "api",
            "aws", "gcp", "npm", "git", "vim", "ssh", "tcp", "udp",
            "dns", "sap", "erp", "crm", "ios", "ux", "ui", "qa",
            "ci", "cd", "ai", "ml", "nlp", "ocr", "rpa", "etl",
            "seo", "sem", "ppc", "roi", "kpi", "vpn", "lan", "wan",
            "ip", "os", "db", "oop", "dba", "bi", "emr", "ehr",
            "bls", "cpr", "rn", "lpn", "cna", "cma", "emt",
            "hvac", "osha", "cad", "bim", "gis", "plc",
            "iot", "sdk", "ide",
            # Finance / accounting
            "gaap", "ifrs", "cpa", "aml", "kyc",
            # Common tool abbreviations
            "jira", "asana", "figma",
        }
        if wl not in known_short:
            # Check if it's all uppercase (likely an acronym) — keep it
            if not w.isupper():
                return True

    return False


# ──────────────────────────────────────────────
# Main cleaning
# ──────────────────────────────────────────────
if __name__ == "__main__":
    import os
    
    # Allow running from anywhere, assuming it's run from the root of the project
    vocab_path = "model/skill_vocab.json"
    if not os.path.exists(vocab_path):
        # Maybe we're running it from some other directory
        print(f"File {vocab_path} not found.")
        
    with open(vocab_path, "r", encoding="utf-8") as f:
        vocab = json.load(f)

    print(f"Original vocab size: {len(vocab)}")

    # Track removal reasons for reporting
    removal_reasons = {}
    cleaned = []

    for entry in vocab:
        if is_noisy(entry):
            # Categorize
            w = entry.strip()
            wl = w.lower()
            if not w:
                reason = "empty"
            elif re.match(r'^[\d/\-\.\\,\s]+$', w) or re.match(r'^\d', w):
                reason = "numeric/date"
            elif '$' in w:
                reason = "dollar_amount"
            elif '\xa0' in w or '\u200b' in w or '\ufffd' in w or '\u25cf' in w or '' in w:
                reason = "unicode_garbage"
            elif re.match(r'^[\*\-\+\u2022\u2013\u2014"\'\\\\]', w):
                reason = "punctuation_start"
            elif w.startswith('&') or w.startswith('('):
                reason = "fragment"
            elif '\t' in w or '  ' in w:
                reason = "formatting"
            elif len(w) > 45 or len(w.split()) >= 4:
                reason = "too_long_or_many_words"
            elif wl in STOP_WORDS:
                reason = "stop_word"
            elif wl in RESUME_FILLER:
                reason = "resume_filler"
            elif wl in GENERIC_ENGLISH:
                reason = "generic_english"
            elif wl in COMMON_VERBS:
                reason = "common_verb"
            elif wl in ADJECTIVE_DESCRIPTORS:
                reason = "adjective"
            elif wl in SECTION_HEADERS:
                reason = "section_header"
            elif wl in LOCATION_NAMES:
                reason = "location"
            elif len(w.split()) >= 2 and w.split()[-1].lower() in {'and', 'or', 'for', 'in', 'to', 'of', 'the', 'with', 'at', 'by', 'on', 'as', 'an', 'a'} and wl not in {'single sign on', 'single sign-on'}:
                reason = "stop_word_ending"
            else:
                reason = "other"

            removal_reasons[reason] = removal_reasons.get(reason, 0) + 1
        else:
            cleaned.append(entry.strip())

    # Deduplicate (case-insensitive) — keep first occurrence
    seen = set()
    deduped = []
    for skill in cleaned:
        key = skill.lower()
        if key not in seen:
            seen.add(key)
            deduped.append(skill)

    deduped.sort(key=str.lower)
    dups_removed = len(cleaned) - len(deduped)

    print(f"\n--- Removal Breakdown ---")
    for reason, count in sorted(removal_reasons.items(), key=lambda x: -x[1]):
        print(f"  {reason:20s}: {count}")
    print(f"  {'duplicates':20s}: {dups_removed}")
    total_removed = len(vocab) - len(deduped)
    print(f"\n  TOTAL REMOVED: {total_removed}")
    print(f"  Cleaned vocab size: {len(deduped)}")

    with open(vocab_path, "w", encoding="utf-8") as f:
        json.dump(deduped, f, indent=2, ensure_ascii=False)

    print(f"\nVocabulary cleaned and saved to {vocab_path}")
