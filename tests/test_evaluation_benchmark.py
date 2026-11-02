"""
Evaluation benchmark pytest verification (Phase 7).
Ensures accuracy and F1 metrics remain within expected thresholds.
"""
from scripts.evaluate_nlp import run_evaluation

def test_evaluation_benchmarks():
    metrics = run_evaluation()
    assert metrics["language_accuracy"] >= 90.0, f"Language accuracy below 90%: {metrics['language_accuracy']}%"
    assert metrics["intent_macro_f1"] >= 85.0, f"Intent F1 below 85%: {metrics['intent_macro_f1']}%"
    assert metrics["ner_accuracy"] >= 85.0, f"NER accuracy below 85%: {metrics['ner_accuracy']}%"
    assert metrics["recall_at_5"] >= 80.0, f"Recall@5 below 80%: {metrics['recall_at_5']}%"
    assert metrics["avg_latency_ms"] < 50.0, f"Latency exceeds 50ms: {metrics['avg_latency_ms']}ms"
