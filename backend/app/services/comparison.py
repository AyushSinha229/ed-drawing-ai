from dataclasses import dataclass
from statistics import mean
from typing import Any

import numpy as np


ANGLE_WEIGHT = 0.30
PROPORTION_WEIGHT = 0.25
ALIGNMENT_WEIGHT = 0.20
COMPLETENESS_WEIGHT = 0.25


@dataclass
class MatchResult:
    ref_index: int
    student_index: int
    angle_deviation: float
    length_ratio_diff: float
    midpoint_distance: float


def compare_drawings(reference: dict[str, Any], student: dict[str, Any], tolerance_degrees: float = 3.0) -> dict[str, Any]:
    line_matches = match_lines(reference.get("lines", []), student.get("lines", []))
    shape_matches = match_shapes(reference.get("shapes", []), student.get("shapes", []))

    angle_score, angle_errors = score_angles(line_matches, tolerance_degrees)
    proportion_score, proportion_errors = score_proportions(line_matches)
    alignment_score, alignment_errors = score_alignment(line_matches)
    completeness_score, completeness_errors = score_completeness(reference, student, line_matches, shape_matches)

    weighted_score = (
        angle_score * ANGLE_WEIGHT
        + proportion_score * PROPORTION_WEIGHT
        + alignment_score * ALIGNMENT_WEIGHT
        + completeness_score * COMPLETENESS_WEIGHT
    )
    score = round(max(0, min(weighted_score, 100)), 2)
    errors = angle_errors + proportion_errors + alignment_errors + completeness_errors

    return {
        "score": score,
        "component_scores": {
            "angles": round(angle_score, 2),
            "proportions": round(proportion_score, 2),
            "alignment": round(alignment_score, 2),
            "completeness": round(completeness_score, 2),
        },
        "errors": errors[:15],
        "line_matches": [match.__dict__ for match in line_matches],
        "shape_matches": shape_matches,
        "summary": build_summary(score, errors),
    }


def match_lines(reference_lines: list[dict[str, Any]], student_lines: list[dict[str, Any]]) -> list[MatchResult]:
    matches: list[MatchResult] = []
    used_students: set[int] = set()
    for ref_index, ref_line in enumerate(reference_lines):
        best: tuple[float, int, MatchResult] | None = None
        for student_index, student_line in enumerate(student_lines):
            if student_index in used_students:
                continue
            angle_deviation = angular_distance(ref_line["angle"], student_line["angle"])
            midpoint_distance = float(np.linalg.norm(np.array(ref_line["midpoint"]) - np.array(student_line["midpoint"])))
            length_ratio_diff = abs(ref_line["norm_length"] - student_line["norm_length"])
            cost = angle_deviation * 4 + midpoint_distance * 0.2 + length_ratio_diff * 180
            candidate = MatchResult(ref_index, student_index, angle_deviation, length_ratio_diff, midpoint_distance)
            if best is None or cost < best[0]:
                best = (cost, student_index, candidate)
        if best and best[0] < 90:
            used_students.add(best[1])
            matches.append(best[2])
    return matches


def match_shapes(reference_shapes: list[dict[str, Any]], student_shapes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    used: set[int] = set()
    for ref_shape in reference_shapes:
        best: tuple[float, int, dict[str, Any]] | None = None
        for idx, student_shape in enumerate(student_shapes):
            if idx in used or ref_shape["type"] != student_shape["type"]:
                continue
            center_distance = float(np.linalg.norm(np.array(ref_shape["center"]) - np.array(student_shape["center"])))
            area_ratio = abs(ref_shape["area"] - student_shape["area"]) / max(ref_shape["area"], 1)
            cost = center_distance * 0.5 + area_ratio * 100
            payload = {"type": ref_shape["type"], "center_distance": round(center_distance, 2), "area_ratio": round(area_ratio, 3)}
            if best is None or cost < best[0]:
                best = (cost, idx, payload)
        if best and best[0] < 100:
            used.add(best[1])
            matches.append(best[2])
    return matches


def score_angles(matches: list[MatchResult], tolerance_degrees: float) -> tuple[float, list[str]]:
    if not matches:
        return 0.0, ["No corresponding lines detected for angle evaluation."]
    deviations = [match.angle_deviation for match in matches]
    within = [value for value in deviations if value <= tolerance_degrees]
    score = 100 * (len(within) / len(deviations))
    errors = [f"Detected line pair deviates by {value:.1f}°." for value in deviations if value > tolerance_degrees]
    return score, errors[:6]


def score_proportions(matches: list[MatchResult]) -> tuple[float, list[str]]:
    if not matches:
        return 0.0, ["Proportion analysis failed because no matching lines were found."]
    avg_diff = mean(match.length_ratio_diff for match in matches)
    score = max(0.0, 100 - avg_diff * 900)
    errors = [f"Line proportion differs by {match.length_ratio_diff * 100:.1f}% from the reference." for match in matches if match.length_ratio_diff > 0.04]
    return score, errors[:6]


def score_alignment(matches: list[MatchResult]) -> tuple[float, list[str]]:
    if not matches:
        return 0.0, ["Alignment analysis failed because no matching lines were found."]
    avg_distance = mean(match.midpoint_distance for match in matches)
    score = max(0.0, 100 - avg_distance * 0.75)
    errors = [f"Element alignment offset is {match.midpoint_distance:.1f}px." for match in matches if match.midpoint_distance > 25]
    return score, errors[:6]


def score_completeness(
    reference: dict[str, Any],
    student: dict[str, Any],
    line_matches: list[MatchResult],
    shape_matches: list[dict[str, Any]],
) -> tuple[float, list[str]]:
    ref_lines = len(reference.get("lines", []))
    ref_shapes = len(reference.get("shapes", []))
    student_lines = len(student.get("lines", []))
    student_shapes = len(student.get("shapes", []))

    line_ratio = len(line_matches) / ref_lines if ref_lines else 1
    shape_ratio = len(shape_matches) / ref_shapes if ref_shapes else 1
    extra_penalty = max(student_lines - len(line_matches), 0) * 1.5 + max(student_shapes - len(shape_matches), 0) * 2.0
    score = max(0.0, min(100.0, ((line_ratio * 0.7) + (shape_ratio * 0.3)) * 100 - extra_penalty))

    errors: list[str] = []
    missing_lines = ref_lines - len(line_matches)
    missing_shapes = ref_shapes - len(shape_matches)
    if missing_lines > 0:
        errors.append(f"Missing approximately {missing_lines} expected line elements.")
    if missing_shapes > 0:
        errors.append(f"Missing approximately {missing_shapes} expected shape elements.")
    if student_lines > len(line_matches) + 2:
        errors.append("Extra construction or stray lines were detected.")
    return score, errors


def angular_distance(a: float, b: float) -> float:
    diff = abs(a - b) % 180
    return min(diff, 180 - diff)


def build_summary(score: float, errors: list[str]) -> str:
    if score >= 85:
        tone = "Strong geometric accuracy."
    elif score >= 65:
        tone = "Moderate accuracy with visible drafting deviations."
    else:
        tone = "Significant geometric deviations detected."
    if not errors:
        return f"{tone} The drawing closely matches the reference."
    return f"{tone} Primary issues: {' '.join(errors[:3])}"

