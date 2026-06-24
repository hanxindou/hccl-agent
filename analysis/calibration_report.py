#!/usr/bin/env python3
"""Generate a human-readable calibration report."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from calibration.calibration_registry import get_registry


def main():
    reg = get_registry()
    profile = reg.current_profile()
    d = profile.to_dict()

    lines = [
        "# Calibration Report", "",
        f"**Profile:** {d['version']}",
        f"**Author:** {d['author']}",
        f"**Description:** {d['description']}",
        "",
        "## Algorithm Efficiency", "",
        "| Algorithm | Efficiency |",
        "|-----------|-----------|",
    ]
    for algo, eff in sorted(d["algorithm_efficiency"].items()):
        lines.append(f"| {algo:20s} | {eff:.2f} |")

    lines += [
        "",
        "## Contention Coefficients", "",
        "| Algorithm | Coefficient |",
        "|-----------|------------|",
    ]
    for algo, coeff in sorted(d["contention_coefficients"].items()):
        lines.append(f"| {algo:20s} | {coeff:.2f} |")

    lines += [
        "",
        "## Scoring Parameters", "",
        f"- latency_scale: {d['latency_scale']}",
        f"- bandwidth_weight: {d['bandwidth_weight']}",
        f"- latency_weight: {d['latency_weight']}",
        f"- hardware_tier: {d['hardware_tier']}",
        f"- overlap_factor_default: {d['overlap_factor_default']}",
        f"- mesh_effective_steps_coeff: {d['mesh_effective_steps_coeff']}",
    ]

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "calibration_report.md")
    with open(out, "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
