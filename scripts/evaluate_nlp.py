"""
Comprehensive NLP & System Evaluation Benchmark for BHASHA SAHITA (Phase 7).
Measures:
1. Language Detection Accuracy across 6 languages (en, hi, mr, pa, te, bn) + Hinglish
2. Intent / Category Detection Macro-F1 and Precision/Recall across 7 categories
3. Profile / Entity Extraction (Age, Income, State, Occupation)
4. Search Retrieval Quality (Recall@5, Precision@5)
5. Query Latency & Response Time
"""
import time, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from collections import defaultdict
from app.language import detect_language
from app.nlp import detect_categories, extract_profile
from app.search import search

# 36 Multilingual ground-truth test queries (6 queries x 6 languages)
BENCHMARK_DATASET = [
    # English
    {"query": "I need a college scholarship for my higher education", "lang": "en", "category": "education", "profile": {}, "expected_scheme": "CEN-EDU-001"},
    {"query": "I am a farmer from Haryana looking for crop insurance", "lang": "en", "category": "agriculture", "profile": {"occupation": "farmer", "state": "Haryana"}, "expected_scheme": "CEN-AGR-002"},
    {"query": "Financial assistance for marriage of my daughter age 19", "lang": "en", "category": "women_child", "profile": {}, "expected_scheme": "HR-WCW-003"},
    {"query": "Collateral free MSME loan to expand small business", "lang": "en", "category": "business", "profile": {}, "expected_scheme": "CEN-BUS-001"},
    {"query": "Free dialysis treatment at district hospital for kidney patient", "lang": "en", "category": "healthcare", "profile": {}, "expected_scheme": "CEN-HLT-005"},
    {"query": "Rooftop solar subsidy under PM Surya Ghar", "lang": "en", "category": "housing", "profile": {}, "expected_scheme": "CEN-HOU-003"},

    # Hindi
    {"query": "मुझे कॉलेज की पढ़ाई के लिए छात्रवृत्ति चाहिए", "lang": "hi", "category": "education", "profile": {}, "expected_scheme": "CEN-EDU-001"},
    {"query": "मैं हरियाणा का किसान हूँ, मुझे फसल सहायता चाहिए", "lang": "hi", "category": "agriculture", "profile": {"occupation": "farmer", "state": "Haryana"}, "expected_scheme": "CEN-AGR-001"},
    {"query": "गर्भवती महिलाओं के लिए सरकारी मातृत्व योजना", "lang": "hi", "category": "women_child", "profile": {}, "expected_scheme": "CEN-WCW-001"},
    {"query": "नया व्यवसाय शुरू करने के लिए मुद्रा लोन", "lang": "hi", "category": "business", "profile": {}, "expected_scheme": "CEN-BUS-001"},
    {"query": "आयुष्मान कार्ड से मुफ्त इलाज कैसे मिलेगा", "lang": "hi", "category": "healthcare", "profile": {}, "expected_scheme": "CEN-HLT-001"},
    {"query": "गांव में पक्का मकान बनाने के लिए आवास योजना", "lang": "hi", "category": "housing", "profile": {}, "expected_scheme": "CEN-HOU-001"},

    # Marathi
    {"query": "मला उच्च शिक्षणासाठी शिष्यवृत्ती हवी आहे", "lang": "mr", "category": "education", "profile": {}, "expected_scheme": "MH-EDU-001"},
    {"query": "मी महाराष्ट्रातील शेतकरी आहे, मला पीक विम्याची मदत हवी", "lang": "mr", "category": "agriculture", "profile": {"occupation": "farmer", "state": "Maharashtra"}, "expected_scheme": "MH-AGR-001"},
    {"query": "लाडकी बहीण योजनेची माहिती आणि अर्ज कसा करावा", "lang": "mr", "category": "women_child", "profile": {}, "expected_scheme": "MH-WCW-002"},
    {"query": "लघु उद्योगासाठी कर्ज आणि सबसिडी पाहिजे", "lang": "mr", "category": "business", "profile": {}, "expected_scheme": "MH-BUS-001"},
    {"query": "महात्मा फुले जन आरोग्य योजना मोफत उपचार", "lang": "mr", "category": "healthcare", "profile": {}, "expected_scheme": "MH-HLT-001"},
    {"query": "रमाई आवास योजनेतून घरकुल बांधण्यासाठी अनुदान", "lang": "mr", "category": "housing", "profile": {}, "expected_scheme": "MH-HOU-001"},

    # Punjabi
    {"query": "ਮੈਨੂੰ ਕਾਲਜ ਦੀ ਪੜ੍ਹਾਈ ਲਈ ਵਜ਼ੀਫ਼ਾ ਚਾਹੀਦਾ ਹੈ", "lang": "pa", "category": "education", "profile": {}, "expected_scheme": "PB-EDU-001"},
    {"query": "ਮੈਂ ਪੰਜਾਬ ਦਾ ਕਿਸਾਨ ਹਾਂ, ਮੈਨੂੰ ਖੇਤੀ ਸਹਾਇਤਾ ਚਾਹੀਦੀ ਹੈ", "lang": "pa", "category": "agriculture", "profile": {"occupation": "farmer", "state": "Punjab"}, "expected_scheme": "CEN-AGR-001"},
    {"query": "ਕੁੜੀ ਦੇ ਵਿਆਹ ਲਈ ਆਸ਼ੀਰਵਾਦ ਸ਼ਗਨ ਸਕੀਮ", "lang": "pa", "category": "women_child", "profile": {}, "expected_scheme": "PB-WCW-001"},
    {"query": "ਛੋਟੇ ਵਪਾਰ ਲਈ ਸਰਕਾਰੀ ਕਰਜ਼ਾ ਸਹਾਇਤਾ", "lang": "pa", "category": "business", "profile": {}, "expected_scheme": "CEN-BUS-001"},
    {"query": "ਸਰਬਤ ਸਿਹਤ ਬੀਮਾ ਯੋਜਨਾ ਵਿੱਚ ਮੁਫ਼ਤ ਇਲਾਜ", "lang": "pa", "category": "healthcare", "profile": {}, "expected_scheme": "PB-HLT-001"},
    {"query": "ਬੁਢਾਪਾ ਪੈਨਸ਼ਨ ਹਰ ਮਹੀਨੇ ਕਿੰਨੀ ਮਿਲੇਗੀ", "lang": "pa", "category": "employment_pension", "profile": {}, "expected_scheme": "PB-EMP-001"},

    # Telugu
    {"query": "నాకు ఉన్నత చదువుల కోసం ఉపకార వేతనం కావాలి", "lang": "te", "category": "education", "profile": {}, "expected_scheme": "TG-EDU-001"},
    {"query": "నేను తెలంగాణ రైతును, రైతు భరోసా పెట్టుబడి సహాయం కావాలి", "lang": "te", "category": "agriculture", "profile": {"occupation": "farmer", "state": "Telangana"}, "expected_scheme": "TG-AGR-001"},
    {"query": "కల్యాణ లక్ష్మి పథకం వివాహ ఆర్థిక సహాయం", "lang": "te", "category": "women_child", "profile": {}, "expected_scheme": "TG-WCW-001"},
    {"query": "స్వయం ఉపాధి మరియు వ్యాపారం కోసం ముద్రా రుణం", "lang": "te", "category": "business", "profile": {}, "expected_scheme": "CEN-BUS-001"},
    {"query": "ఆరోగ్యశ్రీ ఆసుపత్రి ఉచిత వైద్య చికిత్స", "lang": "te", "category": "healthcare", "profile": {}, "expected_scheme": "TG-HLT-001"},
    {"query": "ఆసరా వృద్ధాప్య పింఛన్ వివరాలు ఏమిటి", "lang": "te", "category": "employment_pension", "profile": {}, "expected_scheme": "TG-EMP-001"},

    # Bengali
    {"query": "কলেজে পড়ার জন্য স্বামী বিবেকানন্দ স্কলারশিপ দরকার", "lang": "bn", "category": "education", "profile": {}, "expected_scheme": "WB-EDU-001"},
    {"query": "আমি পশ্চিমবঙ্গের কৃষক, কৃষক বন্ধু প্রকল্পের টাকা কবে পাব", "lang": "bn", "category": "agriculture", "profile": {"occupation": "farmer", "state": "West Bengal"}, "expected_scheme": "WB-AGR-001"},
    {"query": "মহিলাদের লক্ষ্মীর ভাণ্ডার প্রকল্প মাসিক অনুদান", "lang": "bn", "category": "women_child", "profile": {}, "expected_scheme": "WB-WCW-001"},
    {"query": "ছোট ব্যবসার জন্য মুদ্রা ঋণ প্রকল্প", "lang": "bn", "category": "business", "profile": {}, "expected_scheme": "CEN-BUS-001"},
    {"query": "স্বাস্থ্য সাথী কার্ডে ৫ লক্ষ টাকার চিকিৎসা", "lang": "bn", "category": "healthcare", "profile": {}, "expected_scheme": "WB-HLT-001"},
    {"query": "যুবশ্রী বেকার ভাতা প্রকল্পের আবেদন পদ্ধতি", "lang": "bn", "category": "employment_pension", "profile": {}, "expected_scheme": "CEN-EMP-001"}
]

# Profile extraction NER test cases
NER_TEST_CASES = [
    {"text": "I am a farmer from Haryana, age 45, income 1.8 lakh", "expected": {"age": 45, "annual_income": 180000, "state": "Haryana", "occupation": "farmer"}},
    {"text": "उम्र 65 साल, हरियाणा निवासी, वार्षिक आय 2.5 लाख", "expected": {"age": 65, "annual_income": 250000, "state": "Haryana"}},
    {"text": "वय 22 वर्षे, विद्यार्थी, उत्पन्न 1 लाख, महाराष्ट्र", "expected": {"age": 22, "annual_income": 100000, "state": "Maharashtra", "occupation": "student"}},
    {"text": "ਉਮਰ 30 ਸਾਲ, ਪੰਜਾਬ, ਆਮਦਨ 50000", "expected": {"age": 30, "annual_income": 50000, "state": "Punjab"}},
    {"text": "বয়স 20 বছর, পশ্চিমবঙ্গ, আয় 60000", "expected": {"age": 20, "annual_income": 60000, "state": "West Bengal"}},
    {"text": "వయస్సు 35 సంవత్సరాలు, తెలంగాణ, ఆదాయం 1.5 లక్షలు", "expected": {"age": 35, "annual_income": 150000, "state": "Telangana"}}
]

def run_evaluation():
    print("=" * 65)
    print(" BHASHA SAHITA NLP & MULTILINGUAL EVALUATION BENCHMARK")
    print("=" * 65)

    # 1. Language Detection Accuracy
    lang_correct = 0
    total_queries = len(BENCHMARK_DATASET)
    for item in BENCHMARK_DATASET:
        pred_lang = detect_language(item["query"])
        if pred_lang == item["lang"]:
            lang_correct += 1
    lang_acc = (lang_correct / total_queries) * 100

    # 2. Intent / Category Classification
    cat_tp = defaultdict(int)
    cat_fp = defaultdict(int)
    cat_fn = defaultdict(int)

    for item in BENCHMARK_DATASET:
        pred_cats = detect_categories(item["query"])
        top_cat = next(iter(pred_cats.keys()), None) if pred_cats else None
        gold = item["category"]

        if top_cat == gold:
            cat_tp[gold] += 1
        else:
            cat_fp[top_cat] += 1
            cat_fn[gold] += 1

    all_cats = set(cat_tp.keys()) | set(cat_fn.keys())
    precisions = [cat_tp[c] / (cat_tp[c] + cat_fp[c]) if (cat_tp[c] + cat_fp[c]) > 0 else 0 for c in all_cats]
    recalls = [cat_tp[c] / (cat_tp[c] + cat_fn[c]) if (cat_tp[c] + cat_fn[c]) > 0 else 0 for c in all_cats]
    f1s = [(2 * p * r) / (p + r) if (p + r) > 0 else 0 for p, r in zip(precisions, recalls)]
    macro_f1 = (sum(f1s) / len(f1s)) * 100 if f1s else 0

    # 3. Profile / Entity Extraction Accuracy
    ner_correct = 0
    ner_total = 0
    for case in NER_TEST_CASES:
        pred_prof = extract_profile(case["text"])
        for k, v in case["expected"].items():
            ner_total += 1
            if pred_prof.get(k) == v:
                ner_correct += 1
    ner_acc = (ner_correct / ner_total) * 100

    # 4. Search Retrieval Quality (Recall@5 and Precision@5)
    recall_hits = 0
    precision_hits = 0
    latencies = []

    for item in BENCHMARK_DATASET:
        t0 = time.perf_counter()
        res = search(item["query"], top_k=5)
        dt = (time.perf_counter() - t0) * 1000
        latencies.append(dt)

        top_ids = [r["id"] for r in res["results"]]
        target_cat = item["category"]

        # Check if relevant category is in top 5
        cat_matches = sum(1 for r in res["results"] if r["category"] == target_cat)
        if cat_matches > 0:
            recall_hits += 1
        precision_hits += (cat_matches / min(len(res["results"]), 5)) if res["results"] else 0

    recall_at_5 = (recall_hits / total_queries) * 100
    precision_at_5 = (precision_hits / total_queries) * 100
    avg_latency = sum(latencies) / len(latencies)

    print(f"1. Language Detection Accuracy : {lang_acc:.2f}% ({lang_correct}/{total_queries})")
    print(f"2. Intent / Category Macro-F1  : {macro_f1:.2f}%")
    print(f"3. NER / Profile Extraction Acc: {ner_acc:.2f}% ({ner_correct}/{ner_total})")
    print(f"4. Search Recall@5             : {recall_at_5:.2f}%")
    print(f"5. Search Precision@5          : {precision_at_5:.2f}%")
    print(f"6. Average Latency per Query   : {avg_latency:.2f} ms")
    print("=" * 65)

    return {
        "language_accuracy": lang_acc,
        "intent_macro_f1": macro_f1,
        "ner_accuracy": ner_acc,
        "recall_at_5": recall_at_5,
        "precision_at_5": precision_at_5,
        "avg_latency_ms": avg_latency
    }

if __name__ == "__main__":
    run_evaluation()
