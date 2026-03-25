from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any

import sympy as sp
from sympy import latex


class SeriesLimitSolverError(ValueError):
    pass


@dataclass
class SeriesLimitSolveResult:
    status: str
    message: str
    payload: dict[str, Any]


def _normalize_expression(expression: str) -> str:
    return expression.strip().replace("^", "**").replace("inf", "oo")


def _sympify(expression: str) -> sp.Expr:
    try:
        return sp.sympify(_normalize_expression(expression), locals={"pi": sp.pi, "e": sp.E, "oo": sp.oo, "inf": sp.oo})
    except Exception as exc:
        raise SeriesLimitSolverError(f"Ifoda o'qilmadi: {expression}") from exc


def _parse_arrow(auxiliary: str, fallback: str) -> tuple[sp.Symbol, sp.Expr, str]:
    match = re.match(r"\s*([A-Za-z]\w*)\s*->\s*(.+)\s*$", auxiliary or "")
    if not match:
        symbol = sp.Symbol(fallback)
        return symbol, sp.Integer(0), "0"
    symbol = sp.Symbol(match.group(1))
    target_raw = match.group(2).strip()
    return symbol, _sympify(target_raw), target_raw


def _parse_sum(expression: str) -> tuple[sp.Expr, sp.Symbol, sp.Expr, sp.Expr] | None:
    match = re.match(r"sum\((.+),\s*([A-Za-z]\w*)\s*=\s*(.+)\.\.(.+)\)$", expression.strip(), re.IGNORECASE)
    if not match:
        return None
    term = _sympify(match.group(1))
    index = sp.Symbol(match.group(2))
    start = _sympify(match.group(3))
    end = _sympify(match.group(4))
    return term, index, start, end


def _series_summary(term: sp.Expr, index: sp.Symbol, start: sp.Expr) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    term_points: list[dict[str, Any]] = []
    partial_points: list[dict[str, Any]] = []
    partial = 0.0
    for step in range(12):
        n_value = int(start) + step
        try:
            term_value = complex(term.subs(index, n_value).evalf())
        except Exception:
            break
        if abs(term_value.imag) > 1e-8:
            break
        term_real = float(term_value.real)
        partial += term_real
        term_points.append({"x": n_value, "y": term_real})
        partial_points.append({"x": n_value, "y": partial})
    return term_points, partial_points


def _expansion_preview(expr: sp.Expr, symbol: sp.Symbol, point: sp.Expr, order: int = 4) -> str | None:
    try:
        if point == sp.oo or point == -sp.oo:
            expansion = sp.aseries(expr, symbol, point, order)
        else:
            expansion = sp.series(expr, symbol, point, order)
        return latex(expansion)
    except Exception:
        return None


def _is_alternating(term: sp.Expr, index: sp.Symbol) -> bool:
    return term.has((-1) ** index) or term.has((-1) ** (index + 1)) or "(-1)**" in str(term)


def _p_series_exponent(term: sp.Expr, index: sp.Symbol) -> sp.Expr | None:
    candidate = sp.simplify(term * index)
    try:
        if not candidate.free_symbols or candidate.free_symbols == {index}:
            power = sp.simplify(-sp.degree(sp.denom(sp.together(term)), gen=index))
            if power != 0:
                return sp.simplify(-power)
    except Exception:
        pass

    for factor in sp.factor_terms(term).as_ordered_factors():
        if factor.is_Pow and factor.base == index:
            return sp.simplify(-factor.exp)
    numerator, denominator = sp.fraction(sp.simplify(term))
    if denominator.is_Pow and denominator.base == index:
        return sp.simplify(denominator.exp)
    return None


def _detect_primary_test(term: sp.Expr, index: sp.Symbol, auxiliary: str) -> tuple[str, str, str]:
    aux = auxiliary.lower()
    asymptotic_class = "general asymptotic series"
    proof_signal = "formal comparison still needed"

    if "ratio" in aux or term.has(sp.factorial):
        return "ratio test", "root/comparison cross-check", "factorial-exponential competition"
    if "root" in aux:
        return "root test", "ratio cross-check", "root-growth family"
    if "comparison" in aux:
        return "comparison test", "limit comparison", "comparison-ready decay"
    if _is_alternating(term, index):
        return "alternating series test", "absolute convergence screen", "alternating-decay family"

    p_value = _p_series_exponent(term, index)
    if p_value is not None:
        asymptotic_class = f"p-series class (p = {latex(p_value)})"
        proof_signal = "p-series threshold"
        return "comparison / p-series", "integral test", asymptotic_class

    ratio_probe = None
    try:
        ratio_probe = sp.simplify(sp.Abs(term.subs(index, index + 1) / term))
        ratio_limit = sp.limit(ratio_probe, index, sp.oo)
        if ratio_limit.is_real and ratio_limit != 1:
            asymptotic_class = f"ratio limit = {latex(ratio_limit)}"
            proof_signal = "ratio asymptotic resolved"
            return "ratio test", "root test", asymptotic_class
    except Exception:
        pass

    try:
        root_limit = sp.limit(sp.Abs(term) ** (1 / index), index, sp.oo)
        if root_limit.is_real and root_limit != 1:
            asymptotic_class = f"root limit = {latex(root_limit)}"
            proof_signal = "root asymptotic resolved"
            return "root test", "ratio test", asymptotic_class
    except Exception:
        pass

    return "comparison screen", "integral test", asymptotic_class


def _endpoint_status(term: sp.Expr, index: sp.Symbol, start: sp.Expr, end: sp.Expr, x_symbol: sp.Symbol, endpoint: sp.Expr) -> str:
    try:
        endpoint_term = sp.simplify(term.subs(x_symbol, endpoint))
        endpoint_series = sp.Sum(endpoint_term, (index, start, end))
        convergent = endpoint_series.is_convergent()
        if convergent is True:
            return f"x = {latex(endpoint)}: convergent"
        if convergent is False:
            return f"x = {latex(endpoint)}: divergent"
        return f"x = {latex(endpoint)}: unresolved"
    except Exception:
        return f"x = {latex(endpoint)}: unresolved"


def _estimate_radius(ratio_expr: sp.Expr, x_symbol: sp.Symbol) -> tuple[str, str]:
    simplified = sp.simplify(ratio_expr)
    try:
        interval = sp.solve_univariate_inequality(simplified < 1, x_symbol, relational=False)
        interval_text = latex(interval)
    except Exception:
        interval_text = latex(simplified) + " < 1"
    radius = "pending"
    if simplified == sp.Abs(x_symbol):
        radius = "1"
    else:
        coeff = simplified.coeff(sp.Abs(x_symbol))
        if coeff not in (0, 1) and simplified == coeff * sp.Abs(x_symbol):
            radius = latex(sp.simplify(1 / coeff))
    return radius, interval_text


def _build_limit(mode: str, expression: str, auxiliary: str, dimension: str) -> SeriesLimitSolveResult:
    variable, target, raw_target = _parse_arrow(auxiliary or "x -> 0", "x")
    expr = _sympify(expression)
    result = sp.limit(expr, variable, target)
    expansion = _expansion_preview(expr, variable, target if target not in {sp.oo, -sp.oo} else sp.Integer(0))
    dominant = "asymptotic cancellation" if expr.has(sp.sin, sp.cos) else "dominant algebraic balance"
    summary = {
        "detectedFamily": "local limit",
        "candidateResult": latex(result),
        "convergenceSignal": "two-sided symbolic limit",
        "dominantTerm": dominant,
        "riskSignal": "resolved symbolically",
        "shape": "single-variable limit",
        "asymptoticSignal": f"{variable} -> {raw_target}",
        "asymptoticClass": "local asymptotic balance",
        "proofSignal": "limit operator resolved directly",
        "expansionSignal": expansion,
    }
    steps = [
        {"title": "Parse target", "summary": f"Limit {variable} -> {raw_target} sifatida o'qildi.", "latex": f"{latex(variable)} \\to {latex(target)}"},
        {"title": "Dominant balance", "summary": dominant, "latex": latex(expr)},
        {"title": "Expansion preview", "summary": "Local expansion symbolic lane orqali qurildi." if expansion else "Expansion preview unavailable.", "latex": expansion},
        {"title": "Symbolic limit", "summary": "SymPy formal limit operator qo'llandi.", "latex": f"\\lim_{{{latex(variable)} \\to {latex(target)}}} {latex(expr)} = {latex(result)}"},
    ]
    return SeriesLimitSolveResult(
        status="exact",
        message="Limit symbolic solver yakunlandi.",
        payload={
            "input": {"mode": mode, "expression": expression, "auxiliary": auxiliary, "dimension": dimension},
            "parser": {"expression_raw": expression, "expression_latex": latex(expr), "auxiliary_raw": auxiliary},
            "diagnostics": {"lane": mode, "method": "Direct symbolic limit", "risk": "low", "convergence": "resolved"},
            "summary": summary,
            "exact": {
                "method_label": "Direct symbolic limit",
                "result_latex": latex(result),
                "auxiliary_latex": expansion or f"{latex(variable)} \\to {latex(target)}",
                "numeric_approximation": str(sp.N(result, 12)) if result.is_real else None,
                "steps": steps,
            },
        },
    )


def _build_sequence(mode: str, expression: str, auxiliary: str, dimension: str) -> SeriesLimitSolveResult:
    variable, target, raw_target = _parse_arrow(auxiliary or "n -> oo", "n")
    expr = _sympify(expression)
    result = sp.limit(expr, variable, target)
    expansion = _expansion_preview(expr, variable, target)
    samples = [sp.N(expr.subs(variable, index), 8) for index in range(1, 7)]
    monotone = "mixed"
    if len(samples) >= 2:
        deltas = [float(samples[index] - samples[index - 1]) for index in range(1, len(samples))]
        if all(delta >= -1e-8 for delta in deltas):
            monotone = "increasing"
        elif all(delta <= 1e-8 for delta in deltas):
            monotone = "decreasing"
    asymptotic_class = "exponential-stabilizing" if "n" in expression and "^n" in expression else "sequence tail limit"
    summary = {
        "detectedFamily": "sequence",
        "candidateResult": latex(result),
        "convergenceSignal": "sequence limit computed",
        "dominantTerm": "n-asymptotic growth",
        "riskSignal": "resolved symbolically",
        "shape": "discrete sequence",
        "monotonicity": monotone,
        "boundedness": f"samples {', '.join(str(sample) for sample in samples[:4])}",
        "asymptoticSignal": f"{variable} -> {raw_target}",
        "asymptoticClass": asymptotic_class,
        "proofSignal": "tail-limit symbolic resolution",
        "expansionSignal": expansion,
    }
    steps = [
        {"title": "Sequence parse", "summary": f"Sequence {variable} -> {raw_target} bo'yicha audit qilindi.", "latex": latex(expr)},
        {"title": "Tail profile", "summary": f"Monotonicity signal: {monotone}.", "latex": ", ".join(str(sample) for sample in samples[:4])},
        {"title": "Asymptotic preview", "summary": "Sequence asymptotic expansion preview.", "latex": expansion},
        {"title": "Tail limit", "summary": "Sequence limiti symbolic tarzda baholandi.", "latex": f"\\lim_{{{latex(variable)} \\to {latex(target)}}} {latex(expr)} = {latex(result)}"},
    ]
    return SeriesLimitSolveResult(
        status="exact",
        message="Sequence solver yakunlandi.",
        payload={
            "input": {"mode": mode, "expression": expression, "auxiliary": auxiliary, "dimension": dimension},
            "parser": {"expression_raw": expression, "expression_latex": latex(expr), "auxiliary_raw": auxiliary},
            "diagnostics": {"lane": mode, "method": "Sequence limit", "risk": "low", "convergence": "resolved"},
            "summary": summary,
            "exact": {
                "method_label": "Sequence limit",
                "result_latex": latex(result),
                "auxiliary_latex": expansion or f"{latex(variable)} \\to {latex(target)}",
                "numeric_approximation": str(sp.N(result, 12)) if result.is_real else None,
                "steps": steps,
            },
        },
    )


def _build_series(mode: str, expression: str, auxiliary: str, dimension: str) -> SeriesLimitSolveResult:
    parsed = _parse_sum(expression)
    if not parsed:
        raise SeriesLimitSolverError("Series ifodasi `sum(term, n=1..inf)` formatida bo'lishi kerak.")
    term, index, start, end = parsed
    summation = sp.Sum(term, (index, start, end))
    try:
        result = sp.summation(term, (index, start, end))
    except Exception:
        result = summation
    try:
        convergent = summation.is_convergent()
    except Exception:
        convergent = None
    primary_test, secondary_test, asymptotic_class = _detect_primary_test(term, index, auxiliary)
    expansion = _expansion_preview(term, index, sp.oo)
    term_points, partial_points = _series_summary(term, index, start)
    comparison_signal = "absolute convergence unresolved"
    if _is_alternating(term, index):
        try:
            abs_series = sp.Sum(sp.Abs(term), (index, start, end))
            abs_convergent = abs_series.is_convergent()
            comparison_signal = "absolute convergence" if abs_convergent else "conditional convergence candidate"
        except Exception:
            comparison_signal = "alternating lane"
    summary = {
        "detectedFamily": "infinite series",
        "candidateResult": latex(result),
        "convergenceSignal": "convergent" if convergent is True else "divergent" if convergent is False else "symbolic test inconclusive",
        "dominantTerm": latex(sp.simplify(term)),
        "riskSignal": "endpoint and borderline cases need proof" if convergent is None else "formal result available",
        "shape": "series lane",
        "testFamily": primary_test,
        "secondaryTestFamily": secondary_test,
        "partialSumSignal": f"S_{partial_points[-1]['x']} ≈ {partial_points[-1]['y']:.6f}" if partial_points else "pending",
        "asymptoticClass": asymptotic_class,
        "proofSignal": "comparison ladder established" if convergent is not None else "symbolic proof incomplete",
        "comparisonSignal": comparison_signal,
        "expansionSignal": expansion,
    }
    steps = [
        {"title": "Term parse", "summary": "Infinite series hadi va indeks oralig'i ajratildi.", "latex": latex(term)},
        {"title": "Primary test", "summary": f"Candidate convergence family: {primary_test}.", "latex": latex(summation)},
        {"title": "Secondary check", "summary": f"Backup lane: {secondary_test}. {comparison_signal}.", "latex": latex(sp.simplify(term))},
        {"title": "Asymptotic preview", "summary": "Term asymptotic expansion preview.", "latex": expansion},
        {"title": "Summation", "summary": "Formal sum symbolic tarzda baholandi.", "latex": f"{latex(summation)} = {latex(result)}"},
    ]
    return SeriesLimitSolveResult(
        status="exact",
        message="Series solver yakunlandi.",
        payload={
            "input": {"mode": mode, "expression": expression, "auxiliary": auxiliary, "dimension": dimension},
            "parser": {"expression_raw": expression, "expression_latex": latex(summation), "auxiliary_raw": auxiliary},
            "diagnostics": {
                "lane": mode,
                "method": "Infinite series audit",
                "test_family": primary_test,
                "risk": summary["riskSignal"],
                "convergence": summary["convergenceSignal"],
            },
            "summary": summary,
            "exact": {
                "method_label": "Infinite series audit",
                "result_latex": latex(result),
                "auxiliary_latex": expansion or f"tests: {primary_test}; {secondary_test}",
                "numeric_approximation": str(sp.N(result, 12)) if result.is_real else None,
                "steps": steps,
            },
            "preview": {"lineSeries": term_points, "secondaryLineSeries": partial_points},
        },
    )


def _build_power_series(mode: str, expression: str, auxiliary: str, dimension: str) -> SeriesLimitSolveResult:
    parsed = _parse_sum(expression)
    if not parsed:
        raise SeriesLimitSolverError("Power series `sum(term, n=0..inf)` formatida bo'lishi kerak.")
    term, index, start, end = parsed
    x_symbol = next((symbol for symbol in term.free_symbols if symbol.name != index.name), sp.Symbol("x"))
    ratio = sp.simplify(sp.Abs(term.subs(index, index + 1) / term))
    try:
        ratio_limit = sp.limit(ratio, index, sp.oo)
    except Exception:
        ratio_limit = ratio
    radius, interval_signal = _estimate_radius(ratio_limit, x_symbol)
    endpoints: list[str] = []
    endpoint_details: list[str] = []
    if radius != "pending":
        try:
            radius_expr = _sympify(radius)
            endpoints = [
                _endpoint_status(term, index, start, end, x_symbol, radius_expr),
                _endpoint_status(term, index, start, end, x_symbol, -radius_expr),
            ]
            endpoint_details = endpoints
        except Exception:
            endpoints = []
    term_points, partial_points = _series_summary(term.subs(x_symbol, sp.Rational(1, 2)), index, start)
    expansion = _expansion_preview(term, index, sp.oo)
    summary = {
        "detectedFamily": "power series",
        "candidateResult": interval_signal,
        "convergenceSignal": "ratio limit constructed",
        "dominantTerm": latex(term),
        "radiusSignal": radius,
        "riskSignal": "endpoint proofs still matter" if endpoints else "ratio estimate only",
        "shape": "power-series lane",
        "intervalSignal": interval_signal,
        "endpointSignal": "; ".join(endpoints) if endpoints else "endpoint audit pending",
        "endpointDetails": endpoint_details,
        "testFamily": "ratio test",
        "secondaryTestFamily": "endpoint comparison / alternating screen",
        "partialSumSignal": f"S_{partial_points[-1]['x']}({latex(sp.Rational(1, 2))}) ≈ {partial_points[-1]['y']:.6f}" if partial_points else "pending",
        "asymptoticClass": "coefficient-growth radius lane",
        "proofSignal": "ratio test gives radius; endpoints need separate proof",
        "comparisonSignal": "endpoint-specific convergence class",
        "expansionSignal": expansion,
    }
    steps = [
        {"title": "Series term", "summary": "Power series term parsed from sum syntax.", "latex": latex(term)},
        {"title": "Ratio limit", "summary": "Radius estimate ratio limit orqali qurildi.", "latex": f"\\lim_{{n\\to\\infty}} {latex(ratio)} = {latex(ratio_limit)}"},
        {"title": "Interval screen", "summary": "Formal inequality solve orqali interval preview olindi.", "latex": interval_signal},
        {"title": "Endpoint audit", "summary": summary["endpointSignal"], "latex": f"R = {radius}"},
        {"title": "Coefficient asymptotics", "summary": "Coefficient decay preview for radius reasoning.", "latex": expansion},
    ]
    return SeriesLimitSolveResult(
        status="exact",
        message="Power series solver yakunlandi.",
        payload={
            "input": {"mode": mode, "expression": expression, "auxiliary": auxiliary, "dimension": dimension},
            "parser": {"expression_raw": expression, "expression_latex": latex(sp.Sum(term, (index, start, end))), "auxiliary_raw": auxiliary},
            "diagnostics": {"lane": mode, "method": "Power series audit", "test_family": "ratio test", "risk": summary["riskSignal"], "convergence": "interval derived"},
            "summary": summary,
            "exact": {
                "method_label": "Power series audit",
                "result_latex": interval_signal,
                "auxiliary_latex": expansion or f"R = {radius}; endpoints: {summary['endpointSignal']}",
                "numeric_approximation": None,
                "steps": steps,
            },
            "preview": {"lineSeries": term_points, "secondaryLineSeries": partial_points},
        },
    )


def solve_series_limit(mode: str, expression: str, auxiliary: str = "", dimension: str = "") -> SeriesLimitSolveResult:
    if mode == "limits":
        return _build_limit(mode, expression, auxiliary, dimension)
    if mode == "sequences":
        return _build_sequence(mode, expression, auxiliary, dimension)
    if mode in {"series", "convergence"}:
        return _build_series(mode, expression, auxiliary, dimension)
    if mode == "power-series":
        return _build_power_series(mode, expression, auxiliary, dimension)
    raise SeriesLimitSolverError(f"Qo'llab-quvvatlanmaydigan mode: {mode}")
