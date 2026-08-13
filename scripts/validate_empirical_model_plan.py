#!/usr/bin/env python3
"""Validate the B01 annual-report and two-model analysis plan."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ALLOWED_MODELS = {
    "market_share",
    "synergy",
    "did_cultural_premium",
    "dea_tobit",
}

MODEL_REQUIRED_FIELDS = {
    "market_share": {"numerator", "denominator", "same_scope_check"},
    "synergy": {"event", "outcome", "pre_period", "post_period", "counterfactual"},
    "did_cultural_premium": {
        "treatment_group",
        "control_group",
        "treatment_time",
        "outcome",
        "panel_id",
        "time_id",
        "parallel_trends_plan",
        "inference_plan",
    },
    "dea_tobit": {
        "dmu_definition",
        "dmu_count",
        "inputs",
        "outputs",
        "orientation",
        "returns_to_scale",
        "sample_adequacy_rule",
        "second_stage_covariates",
        "bias_correction_or_bootstrap_plan",
    },
}


def filled(value: object) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip()) and "【" not in value
    if isinstance(value, list):
        return bool(value) and all(filled(item) for item in value)
    if isinstance(value, dict):
        return bool(value) and all(filled(item) for item in value.values())
    return True


def validate_model(model: dict, errors: list[str]) -> None:
    code = model.get("code")
    prefix = f"model[{code or '?'}]"
    if code not in ALLOWED_MODELS:
        errors.append(f"{prefix}: unsupported model code")
        return
    if model.get("status") != "READY":
        errors.append(f"{prefix}: selected model status must be READY")
    for field in ("research_question", "estimand", "data_period", "source_ids", "assumptions", "variables"):
        if not filled(model.get(field)):
            errors.append(f"{prefix}: missing {field}")
    variables = model.get("variables", {})
    if isinstance(variables, dict):
        for field in MODEL_REQUIRED_FIELDS[code]:
            if not filled(variables.get(field)):
                errors.append(f"{prefix}: variables.{field} is required")
        if code == "market_share" and variables.get("same_scope_check") is not True:
            errors.append(f"{prefix}: variables.same_scope_check must be true")
        if code == "dea_tobit":
            dmu_count = variables.get("dmu_count")
            if not isinstance(dmu_count, int) or dmu_count <= 0:
                errors.append(f"{prefix}: variables.dmu_count must be a positive integer")
    visuals = model.get("visuals", [])
    if not isinstance(visuals, list) or not visuals:
        errors.append(f"{prefix}: at least one result or diagnostic visual is required")
    else:
        for index, visual in enumerate(visuals, start=1):
            for field in ("chart_id", "question", "output_file", "source_ids"):
                if not filled(visual.get(field)):
                    errors.append(f"{prefix}.visual[{index}]: missing {field}")


def validate(plan: dict, allow_template: bool = False) -> list[str]:
    errors: list[str] = []
    if plan.get("template_mode"):
        if not allow_template:
            return ["template_mode is true; fill the plan and set it to false"]
        required = {
            "annual_reports",
            "annual_report_charts",
            "candidate_assessment",
            "selected_models",
            "research_framework",
            "notebook",
        }
        missing = sorted(required - set(plan))
        return [f"template missing top-level key: {item}" for item in missing]

    if not filled(plan.get("enterprise")):
        errors.append("enterprise is required")
    if not filled(plan.get("research_question")):
        errors.append("research_question is required")

    reports = plan.get("annual_reports", [])
    if not isinstance(reports, list) or not reports:
        errors.append("at least one annual report is required")
    else:
        for index, report in enumerate(reports, start=1):
            for field in ("year", "source", "access_date", "page_scope", "consolidation_scope", "currency", "unit"):
                if not filled(report.get(field)):
                    errors.append(f"annual_report[{index}]: missing {field}")
        if len(reports) < 3 and not filled(plan.get("annual_report_coverage_limit")):
            errors.append("fewer than 3 annual reports requires annual_report_coverage_limit")

    metric_count = plan.get("annual_report_metric_count", 0)
    if not isinstance(metric_count, int) or metric_count < 5:
        errors.append("annual_report_metric_count must be at least 5")

    annual_charts = plan.get("annual_report_charts", [])
    if not isinstance(annual_charts, list) or len(annual_charts) < 2:
        errors.append("at least two annual-report descriptive charts/tables are required")
    else:
        for index, chart in enumerate(annual_charts, start=1):
            for field in ("chart_id", "question", "chart_type", "source_ids", "output_file"):
                if not filled(chart.get(field)):
                    errors.append(f"annual_report_chart[{index}]: missing {field}")

    framework = plan.get("research_framework", {})
    if framework.get("status") != "READY":
        errors.append("research_framework.status must be READY")
    for field in ("source_ids", "output_file"):
        if not filled(framework.get(field)):
            errors.append(f"research_framework.{field} is required")

    selected = plan.get("selected_models", [])
    if not isinstance(selected, list) or len(selected) != 2:
        errors.append("selected_models must contain exactly two models")
    else:
        codes = [model.get("code") for model in selected]
        if len(set(codes)) != 2:
            errors.append("selected models must be unique")
        for model in selected:
            validate_model(model, errors)

    assessment = plan.get("candidate_assessment", {})
    for code in ALLOWED_MODELS:
        if assessment.get(code) not in {"READY", "CONDITIONAL", "BLOCKED", "NOT_RELEVANT"}:
            errors.append(f"candidate_assessment.{code} has invalid status")
    if selected and any(assessment.get(model.get("code")) != "READY" for model in selected):
        errors.append("every selected model must also be READY in candidate_assessment")

    if plan.get("model_selection_status") != "MODEL_SELECTION_READY":
        errors.append("model_selection_status must be MODEL_SELECTION_READY")
    if not filled(plan.get("selection_rationale")):
        errors.append("selection_rationale is required")

    notebook = plan.get("notebook", {})
    if not str(notebook.get("path", "")).endswith(".ipynb"):
        errors.append("notebook.path must end with .ipynb")
    if notebook.get("executed") is not True or notebook.get("execution_status") != "PASS":
        errors.append("notebook must be executed successfully")
    if not filled(notebook.get("data_version")):
        errors.append("notebook.data_version is required")
    return errors


def sample_model(code: str) -> dict:
    variables = {
        "market_share": {"numerator": "company_sales", "denominator": "market_sales", "same_scope_check": True},
        "synergy": {"event": "integration", "outcome": "cost", "pre_period": "2022", "post_period": "2023", "counterfactual": "matched_unit"},
    }[code]
    return {
        "code": code,
        "status": "READY",
        "research_question": "test question",
        "estimand": "target quantity",
        "data_period": "2021-2023",
        "source_ids": ["E001"],
        "assumptions": ["scope consistency"],
        "variables": variables,
        "visuals": [{"chart_id": f"FIG-{code}", "question": "result", "output_file": f"figures/{code}.svg", "source_ids": ["E001"]}],
    }


def self_test() -> int:
    report = {"year": "2023", "source": "exchange", "access_date": "2026-08-13", "page_scope": "p.1", "consolidation_scope": "group", "currency": "CNY", "unit": "million"}
    plan = {
        "template_mode": False,
        "enterprise": "Example",
        "research_question": "Question",
        "annual_reports": [{**report, "year": str(year)} for year in (2021, 2022, 2023)],
        "annual_report_metric_count": 5,
        "annual_report_charts": [
            {"chart_id": "FIG-4-1", "question": "trend", "chart_type": "bar", "source_ids": ["E001"], "output_file": "figures/a.svg"},
            {"chart_id": "FIG-4-2", "question": "mix", "chart_type": "stacked_bar", "source_ids": ["E001"], "output_file": "figures/b.svg"},
        ],
        "candidate_assessment": {"market_share": "READY", "synergy": "READY", "did_cultural_premium": "BLOCKED", "dea_tobit": "BLOCKED"},
        "selected_models": [sample_model("market_share"), sample_model("synergy")],
        "research_framework": {"status": "READY", "source_ids": ["E001"], "output_file": "figures/framework.svg"},
        "notebook": {"path": "analysis/B01_empirical_analysis.ipynb", "executed": True, "execution_status": "PASS", "data_version": "v1"},
        "model_selection_status": "MODEL_SELECTION_READY",
        "selection_rationale": "Both models fit the question and available data.",
    }
    errors = validate(plan)
    if errors:
        print("FAIL:", *errors, sep="\n- ")
        return 1
    invalid = dict(plan)
    invalid["selected_models"] = [sample_model("market_share")]
    if not validate(invalid):
        print("FAIL: invalid one-model plan was accepted")
        return 1
    print("PASS: empirical model plan self-test")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("plan", nargs="?")
    parser.add_argument("--allow-template", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if not args.plan:
        parser.error("plan is required unless --self-test is used")
    plan = json.loads(Path(args.plan).read_text(encoding="utf-8"))
    errors = validate(plan, allow_template=args.allow_template)
    if errors:
        print("FAIL:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS: empirical model plan")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
