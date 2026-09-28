"""
MedMatch Phase 10 Explainability & Evidence Graph Experiment Harness.
Phase 10: Explainability & Evidence Graph Foundation.

Coordinates:
- Loading and reconstituting Phase 10 development fixtures
- Graph validation against invariants G1–G12
- Deterministic explanation generation for criterion evaluations and decisions
- Explanation validation against grounding and contradiction disclosure guardrails
- Explainability metrics computation (EC, DTR, CTR, PVR, ESR, UECR, CDR, GIR)
- Strict empirical benchmark guardrails (has_validated_benchmark() == False)
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from scripts.evidence_graph_schema import (
        EdgeType,
        EvidenceGraph,
        EvidenceGraphEdge,
        EvidenceGraphNode,
        NodeType,
    )
    from scripts.evidence_graph_validator import EvidenceGraphValidator, GraphValidationResult
    from scripts.explanation_generator import DeterministicExplanationGenerator
    from scripts.explanation_schema import ExplanationClaim, StructuredExplanation
    from scripts.explanation_validator import ExplanationValidationResult, ExplanationValidator
    from scripts.explainability_metrics import (
        ExplainabilityMetricsCalculator,
        ExplainabilityMetricsReport,
    )
except ImportError:
    from evidence_graph_schema import (
        EdgeType,
        EvidenceGraph,
        EvidenceGraphEdge,
        EvidenceGraphNode,
        NodeType,
    )
    from evidence_graph_validator import EvidenceGraphValidator, GraphValidationResult
    from explanation_generator import DeterministicExplanationGenerator
    from explanation_schema import ExplanationClaim, StructuredExplanation
    from explanation_validator import ExplanationValidationResult, ExplanationValidator
    from explainability_metrics import (
        ExplainabilityMetricsCalculator,
        ExplainabilityMetricsReport,
    )


def has_validated_benchmark() -> bool:
    """
    Empirical benchmark guardrail:
    Returns True only if an external, clinically validated benchmark has been ingested.
    Must strictly return False during Phase 10 development.
    """
    return False


class ExplainabilityExperimentHarness:
    """
    Execution harness for Phase 10 explainability and evidence graph evaluation.
    """

    def __init__(self, fixture_path: Optional[str] = None):
        if fixture_path is None:
            base_dir = Path(__file__).resolve().parent.parent
            self.fixture_path = base_dir / "data" / "fixtures" / "phase10" / "explainability_fixtures.json"
        else:
            self.fixture_path = Path(fixture_path)

    def load_fixtures(self) -> List[Dict[str, Any]]:
        """Loads the synthetic development fixtures from disk."""
        if not self.fixture_path.exists():
            raise FileNotFoundError(f"Fixture file not found: {self.fixture_path}")
        with open(self.fixture_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def run_case(self, fixture: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes an individual test fixture through graph validation, explanation
        synthesis, and explanation verification.
        """
        fixture_id = fixture["fixture_id"]
        is_valid_expected = fixture["is_valid"]
        expected_errors = fixture.get("expected_errors", [])
        graph_data = fixture.get("graph_data", {})

        # Reconstitute graph
        graph = EvidenceGraph.from_dict(graph_data)

        # Validate graph
        graph_val_res: GraphValidationResult = EvidenceGraphValidator.validate_graph(graph)

        # If fixture supplied custom explanation (e.g. for testing invalid claims)
        explanation: Optional[StructuredExplanation] = None
        exp_val_res: Optional[ExplanationValidationResult] = None

        if "explanation_data" in fixture:
            explanation = StructuredExplanation.model_validate(fixture["explanation_data"])
            exp_val_res = ExplanationValidator.validate_explanation(explanation, graph)
        else:
            # If graph is valid, generate canonical explanations
            eval_nodes = graph.get_nodes_by_type(NodeType.CRITERION_EVALUATION)
            decision_nodes = graph.get_nodes_by_type(NodeType.ELIGIBILITY_DECISION)
            res_nodes = graph.get_nodes_by_type(NodeType.REVIEW_RESOLUTION)

            generated_exps: List[StructuredExplanation] = []
            for en in eval_nodes:
                try:
                    exp = DeterministicExplanationGenerator.explain_criterion_evaluation(graph, en.node_id)
                    generated_exps.append(exp)
                except Exception:
                    pass

            for dn in decision_nodes:
                try:
                    exp = DeterministicExplanationGenerator.explain_eligibility_decision(graph, dn.node_id)
                    generated_exps.append(exp)
                except Exception:
                    pass

            for rn in res_nodes:
                try:
                    exp = DeterministicExplanationGenerator.explain_review_resolution(graph, rn.node_id)
                    generated_exps.append(exp)
                except Exception:
                    pass

            if generated_exps:
                explanation = generated_exps[0]
                exp_val_res = ExplanationValidator.validate_explanation(explanation, graph)

        return {
            "fixture_id": fixture_id,
            "description": fixture["description"],
            "graph": graph,
            "graph_validation": graph_val_res,
            "explanation": explanation,
            "explanation_validation": exp_val_res,
            "is_valid_expected": is_valid_expected,
            "expected_errors": expected_errors,
        }

    def run_all(self) -> Tuple[List[Dict[str, Any]], ExplainabilityMetricsReport]:
        """
        Executes all fixtures and computes summary metrics across valid instances.
        """
        fixtures = self.load_fixtures()
        case_results = [self.run_case(f) for f in fixtures]

        # Filter valid graphs and explanations for metric evaluation
        all_graphs = [r["graph"] for r in case_results]
        all_explanations = [r["explanation"] for r in case_results if r["explanation"] is not None]

        metrics = ExplainabilityMetricsCalculator.calculate_metrics(
            graphs=all_graphs,
            explanations=all_explanations
        )

        return case_results, metrics


def main() -> None:
    print("================================================================================")
    print("MEDMATCH PHASE 10: EXPLAINABILITY & EVIDENCE GRAPH EXPERIMENT HARNESS")
    print("================================================================================")
    harness = ExplainabilityExperimentHarness()
    results, metrics = harness.run_all()
    print(f"Loaded and executed {len(results)} development test fixtures.\n")

    for res in results:
        fid = res["fixture_id"]
        gv = res["graph_validation"]
        g_status = "PASS" if gv.is_valid else f"FAIL ({len(gv.errors)} errors: {[e.error_code.value for e in gv.errors]})"
        exp_status = "N/A"
        if res["explanation_validation"]:
            ev = res["explanation_validation"]
            exp_status = "PASS" if ev.is_valid else f"FAIL ({len(ev.errors)} errors: {[e.error_code.value for e in ev.errors]})"
        print(f" - {fid:<45} | Graph: {g_status:<30} | Explanation: {exp_status}")

    print("\n--------------------------------------------------------------------------------")
    print("PHASE 10 EXPLAINABILITY METRICS (DEVELOPMENT FIXTURES ONLY)")
    print("--------------------------------------------------------------------------------")
    print(f"Total Graphs Evaluated:              {metrics.total_graphs}")
    print(f"Total Criteria Evaluations:          {metrics.total_criteria_evaluations}")
    print(f"Total Eligibility Decisions:         {metrics.total_decisions}")
    print(f"Total Evidence Nodes:                {metrics.total_evidence_nodes}")
    print(f"Total Explanation Claims:            {metrics.total_explanation_claims}")
    print(f"Total Contradictory Cases:           {metrics.total_contradictory_cases}")
    print(f"Evidence Coverage (EC):              {metrics.evidence_coverage:.4f}")
    print(f"Decision Traceability Rate (DTR):    {metrics.decision_traceability_rate:.4f}")
    print(f"Criterion Traceability Rate (CTR):   {metrics.criterion_traceability_rate:.4f}")
    print(f"Provenance Validity Rate (PVR):      {metrics.provenance_validity_rate:.4f}")
    print(f"Explanation Support Rate (ESR):      {metrics.explanation_support_rate:.4f}")
    print(f"Unsupported Claim Rate (UECR):       {metrics.unsupported_explanation_claim_rate:.4f}")
    print(f"Contradiction Disclosure Rate (CDR): {metrics.contradiction_disclosure_rate:.4f}")
    print(f"Graph Integrity Rate (GIR):          {metrics.graph_integrity_rate:.4f}")

    print("\n================================================================================")
    print("EMPIRICAL BENCHMARK GUARDRAIL STATUS")
    print("================================================================================")
    print(f"External Research Benchmark Ingested: {has_validated_benchmark()}")
    print("Notice: The above metrics evaluate synthetic development test fixtures only.")
    print("Empirical clinical performance claims are strictly prohibited until a validated")
    print("external clinical decision-support benchmark is formally ingested.")
    print("================================================================================")


if __name__ == "__main__":
    main()
