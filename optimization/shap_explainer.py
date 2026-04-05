"""
Explainable AI module using SHAP for train delay analysis.

Trains a surrogate GradientBoosting model across multiple delay-factor
variations, then uses SHAP TreeExplainer to explain what drives each
train's delay in the current solution.
"""

import contextlib
import io
import numpy as np
from typing import Dict, List, Tuple

import shap
from sklearn.ensemble import GradientBoostingRegressor

FEATURE_NAMES = [
    "weather_delay",
    "maintenance_delay",
    "congestion_delay",
    "operational_delay",
    "bottleneck_sections",
    "steep_grade_sections",
    "single_track_sections",
    "train_priority",
    "delay_factor",
]

FEATURE_LABELS = {
    "weather_delay":        "Weather Delay",
    "maintenance_delay":    "Maintenance Delay",
    "congestion_delay":     "Congestion Delay",
    "operational_delay":    "Operational Delay",
    "bottleneck_sections":  "Bottleneck Sections",
    "steep_grade_sections": "Steep Grade Sections",
    "single_track_sections":"Single Track Sections",
    "train_priority":       "Train Priority",
    "delay_factor":         "Global Delay Factor",
}


def _extract_train_features(optimizer, solution: Dict, train_id: str) -> List[float]:
    """Build a numeric feature vector for one train from a solved solution."""
    train_data = solution["train_schedules"][train_id]
    delays_by_station = train_data["delays"]

    total_weather      = sum(d.get("weather", 0)     for d in delays_by_station.values())
    total_maintenance  = sum(d.get("maintenance", 0) for d in delays_by_station.values())
    total_congestion   = sum(d.get("congestion", 0)  for d in delays_by_station.values())
    total_operational  = sum(d.get("operational", 0) for d in delays_by_station.values())

    train = next(t for t in optimizer.trains if t["id"] == train_id)
    route = train["route"]

    bottleneck_count   = 0
    steep_count        = 0
    single_track_count = 0

    for i in range(len(route) - 1):
        track = optimizer.find_track(route[i], route[i + 1])
        if track:
            if track.get("bottleneck", False):
                bottleneck_count += 1
            if track.get("gradient") == "steep_climb":
                steep_count += 1
            if track.get("tracks", 2) == 1:
                single_track_count += 1

    return [
        float(total_weather),
        float(total_maintenance),
        float(total_congestion),
        float(total_operational),
        float(bottleneck_count),
        float(steep_count),
        float(single_track_count),
        float(train["priority"]),
        float(optimizer.custom_delay_factor),
    ]


def _generate_training_data(
    scenario_date, maintenance_preset: int
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Run the optimizer at 10 different delay factors to build a training dataset.
    Optimizer console output is suppressed to keep the report clean.
    """
    from optimizer import EnhancedIndianRailwayOptimizer

    delay_factors = [0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8, 2.0]
    X_rows: List[List[float]] = []
    y_rows: List[float] = []

    for df in delay_factors:
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                opt = EnhancedIndianRailwayOptimizer(
                    scenario_date=scenario_date,
                    custom_delay_factor=df,
                    maintenance_preset=maintenance_preset,
                )
                sol = opt.solve_optimization()

            if sol.get("error"):
                continue

            for train in opt.trains:
                tid = train["id"]
                features = _extract_train_features(opt, sol, tid)
                target   = float(sol["train_schedules"][tid]["total_delay"])
                X_rows.append(features)
                y_rows.append(target)
        except Exception:
            continue

    return np.array(X_rows, dtype=float), np.array(y_rows, dtype=float)


def run_shap_analysis(optimizer, solution: Dict) -> Dict:
    """
    Train a surrogate GradientBoosting model and compute SHAP values for the
    current optimization solution.

    Returns a result dict containing:
      - expected_value   : surrogate model baseline (mean prediction)
      - feature_names    : ordered list of feature names
      - global_importance: {feature: mean |SHAP value|}
      - train_shap       : per-train SHAP breakdown
    """
    preset = optimizer.maintenance_preset if optimizer.maintenance_preset is not None else 5

    print("\n  [SHAP] Running optimizer variations to build surrogate training data...")
    X_train, y_train = _generate_training_data(optimizer.scenario_date, preset)

    if len(X_train) < 10:
        return {
            "error": (
                f"Insufficient training samples ({len(X_train)}) — "
                "need at least 10 to fit a surrogate model."
            )
        }

    model = GradientBoostingRegressor(
        n_estimators=150, max_depth=3, learning_rate=0.1, random_state=42
    )
    model.fit(X_train, y_train)
    print(f"  [SHAP] Surrogate model trained on {len(X_train)} samples.")

    X_current = np.array(
        [_extract_train_features(optimizer, solution, t["id"]) for t in optimizer.trains],
        dtype=float,
    )

    explainer    = shap.TreeExplainer(model, X_train)
    shap_values  = explainer.shap_values(X_current)
    expected_val = float(explainer.expected_value)

    mean_abs_shap = np.abs(shap_values).mean(axis=0)
    global_importance = {
        name: float(val) for name, val in zip(FEATURE_NAMES, mean_abs_shap)
    }

    train_shap: Dict[str, Dict] = {}
    for i, train in enumerate(optimizer.trains):
        tid = train["id"]
        actual    = solution["train_schedules"][tid]["total_delay"]
        predicted = float(model.predict(X_current[i : i + 1])[0])
        train_shap[tid] = {
            "shap_values":    shap_values[i].tolist(),
            "feature_values": X_current[i].tolist(),
            "predicted_delay": predicted,
            "actual_delay":    actual,
        }

    return {
        "expected_value":    expected_val,
        "feature_names":     FEATURE_NAMES,
        "global_importance": global_importance,
        "train_shap":        train_shap,
    }


def print_shap_report(optimizer, solution: Dict, shap_results: Dict) -> None:
    """Print the SHAP explainability section as part of the Full Detailed Report."""
    print("\n" + "=" * 80)
    print("EXPLAINABLE AI  -  SHAP DELAY DRIVER ANALYSIS")
    print("=" * 80)

    if shap_results.get("error"):
        print(f"\n  SHAP Analysis unavailable: {shap_results['error']}")
        return

    expected = shap_results["expected_value"]
    print(f"\n  Surrogate model baseline (mean predicted delay): {expected:.1f} min")
    print("  SHAP values quantify how much each factor ADDS (+) or REMOVES (-)")
    print("  minutes of delay relative to that baseline for each train.\n")

    # ------------------------------------------------------------------ #
    # Global feature importance
    # ------------------------------------------------------------------ #
    print("  GLOBAL FEATURE IMPORTANCE  (Mean |SHAP Value| across all trains)")
    print("  " + "-" * 60)
    importance    = shap_results["global_importance"]
    sorted_imp    = sorted(importance.items(), key=lambda x: x[1], reverse=True)
    max_imp_val   = sorted_imp[0][1] if sorted_imp[0][1] > 0 else 1.0

    for feat, val in sorted_imp:
        label   = FEATURE_LABELS.get(feat, feat)
        bar_len = int(30 * val / max_imp_val)
        bar     = "#" * bar_len
        print(f"  {label:<28}: {val:5.2f} min  [{bar}]")

    # ------------------------------------------------------------------ #
    # Per-train SHAP breakdown
    # ------------------------------------------------------------------ #
    print(f"\n  PER-TRAIN SHAP CONTRIBUTIONS")
    print("  " + "-" * 60)

    feature_names = shap_results["feature_names"]

    for train in optimizer.trains:
        tid = train["id"]
        if tid not in shap_results["train_shap"]:
            continue

        entry        = shap_results["train_shap"][tid]
        actual       = entry["actual_delay"]
        predicted    = entry["predicted_delay"]
        contribs     = list(zip(feature_names, entry["shap_values"]))
        contribs_sig = [(f, v) for f, v in contribs if abs(v) >= 0.05]
        contribs_sig.sort(key=lambda x: abs(x[1]), reverse=True)

        max_contrib = max((abs(v) for _, v in contribs_sig), default=1.0)

        print(f"\n  [{tid.replace('_', ' ')}]")
        print(f"    Actual Delay      : {actual:>4} min")
        print(f"    Surrogate Predict : {predicted:>6.1f} min")
        print(f"    Baseline          : {expected:>6.1f} min")
        print(f"    SHAP Contributions (sorted by magnitude):")

        for feat, sv in contribs_sig[:6]:
            label   = FEATURE_LABELS.get(feat, feat)
            bar_len = max(1, int(20 * abs(sv) / max_contrib))
            bar     = ("+" if sv > 0 else "-") * bar_len
            effect  = "increases delay" if sv > 0 else "reduces  delay"
            print(f"      {label:<28}: {sv:+6.2f} min  [{bar:<20}]  ({effect})")

    print()
