from __future__ import annotations

from dataclasses import dataclass
from math import erf, exp, sqrt, pi
from random import Random
import re
from typing import Any


class ProbabilitySolverError(ValueError):
    pass


@dataclass
class ProbabilitySolveResult:
    status: str
    message: str
    payload: dict[str, Any]


def _parse_number_list(dataset: str) -> list[float]:
    values = []
    for token in re.split(r"[,;]+", dataset):
        token = token.strip()
        if not token:
            continue
        try:
            values.append(float(token))
        except ValueError:
            continue
    return values


def _parse_params(parameters: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for part in parameters.split(";"):
        part = part.strip()
        if not part or "=" not in part:
            continue
        key, value = part.split("=", 1)
        result[key.strip()] = value.strip()
    return result


def _normal_pdf(x: float, mu: float, sigma: float) -> float:
    z = (x - mu) / sigma
    return exp(-0.5 * z * z) / (sigma * sqrt(2 * pi))


def _normal_cdf(x: float, mu: float, sigma: float) -> float:
    return 0.5 * (1 + erf((x - mu) / (sigma * sqrt(2))))


def solve_probability(*, mode: str, dataset: str, parameters: str, dimension: str) -> ProbabilitySolveResult:
    params = _parse_params(parameters)
    parser = {
        "dataset_raw": dataset,
        "parameters_raw": parameters,
        "dimension": dimension,
    }

    if mode == "descriptive":
        values = _parse_number_list(dataset)
        if not values:
            raise ProbabilitySolverError("Descriptive lane uchun numeric dataset kerak.")
        avg = sum(values) / len(values)
        variance = sum((value - avg) ** 2 for value in values) / max(len(values) - 1, 1)
        std_dev = sqrt(max(variance, 0))
        summary = {
            "sampleSize": str(len(values)),
            "mean": f"{avg:.3f}",
            "variance": f"{variance:.3f}",
            "stdDev": f"{std_dev:.3f}",
            "riskSignal": "descriptive snapshot ready",
            "shape": "1d sample",
        }
        steps = [
            {"title": "Sample Parse", "summary": "Numeric sample backendda parse qilindi.", "latex": ", ".join(f"{value:.2f}" for value in values[:10])},
            {"title": "Moment Audit", "summary": "Mean, variance va standard deviation hisoblandi.", "latex": f"mean={avg:.3f}, s^2={variance:.3f}, s={std_dev:.3f}"},
        ]
        exact = {
            "method_label": "Descriptive Statistics",
            "result_latex": f"\\bar{{x}} = {avg:.3f}",
            "auxiliary_latex": f"s = {std_dev:.3f}",
            "numeric_approximation": f"{avg:.6f}",
            "steps": steps,
        }
        diagnostics = {"lane": mode, "sample_size": len(values), "family": "empirical", "risk": "low"}
        return ProbabilitySolveResult("exact", "Probability descriptive result tayyor.", {"input": {"mode": mode, "dataset": dataset, "parameters": parameters, "dimension": dimension}, "parser": parser, "diagnostics": diagnostics, "summary": summary, "exact": exact})

    if mode == "distributions":
        mu = float(params.get("mu", "0"))
        sigma = float(params.get("sigma", "1"))
        family = params.get("family", "normal")
        match = re.search(r"x\s*=\s*(-?\d*\.?\d+)", dataset, re.I)
        x_value = float(match.group(1)) if match else 0.0
        pdf = _normal_pdf(x_value, mu, sigma)
        cdf = _normal_cdf(x_value, mu, sigma)
        summary = {
            "sampleSize": "analytic",
            "mean": f"{mu:.3f}",
            "variance": f"{sigma * sigma:.3f}",
            "stdDev": f"{sigma:.3f}",
            "distributionFamily": family,
            "confidenceInterval": f"P(X≤{x_value:.2f}) = {cdf:.4f}",
            "riskSignal": "model-based probability lane",
            "shape": "1d distribution",
        }
        exact = {
            "method_label": "Normal Distribution Audit",
            "result_latex": f"f({x_value:.2f}) = {pdf:.4f}",
            "auxiliary_latex": f"F({x_value:.2f}) = {cdf:.4f}",
            "numeric_approximation": f"{cdf:.6f}",
            "steps": [
                {"title": "Parameter Parse", "summary": "Distribution parametrlari parse qilindi.", "latex": f"mu={mu:.3f}, sigma={sigma:.3f}"},
                {"title": "Density / CDF", "summary": "PDF va CDF qiymati baholandi.", "latex": f"pdf={pdf:.4f}, cdf={cdf:.4f}"},
            ],
        }
        diagnostics = {"lane": mode, "sample_size": None, "family": family, "risk": "model"}
        return ProbabilitySolveResult("exact", "Probability distribution audit tayyor.", {"input": {"mode": mode, "dataset": dataset, "parameters": parameters, "dimension": dimension}, "parser": parser, "diagnostics": diagnostics, "summary": summary, "exact": exact})

    if mode == "inference":
        match = re.search(r"control:\s*(\d+)\/(\d+)\s*;\s*variant:\s*(\d+)\/(\d+)", dataset, re.I)
        if not match:
            raise ProbabilitySolverError("Inference lane uchun `control: a/n; variant: b/m` formati kerak.")
        c_success, c_total, v_success, v_total = map(int, match.groups())
        p1 = c_success / c_total
        p2 = v_success / v_total
        pooled = (c_success + v_success) / (c_total + v_total)
        se = sqrt(pooled * (1 - pooled) * (1 / c_total + 1 / v_total))
        z_score = (p2 - p1) / se
        p_value = 2 * (1 - _normal_cdf(abs(z_score), 0, 1))
        ci_se = sqrt((p1 * (1 - p1)) / c_total + (p2 * (1 - p2)) / v_total)
        diff = p2 - p1
        low = diff - 1.96 * ci_se
        high = diff + 1.96 * ci_se
        summary = {
            "sampleSize": str(c_total + v_total),
            "pValue": f"{p_value:.4f}",
            "confidenceInterval": f"[{low * 100:.2f}%, {high * 100:.2f}%]",
            "riskSignal": "statistically significant" if p_value < 0.05 else "inconclusive",
            "shape": "two-group inference",
        }
        exact = {
            "method_label": "Two Proportion Z-Test",
            "result_latex": f"\\Delta = {diff * 100:.2f}\\%",
            "auxiliary_latex": f"p = {p_value:.4f}",
            "numeric_approximation": f"{p_value:.6f}",
            "steps": [
                {"title": "Conversion Rates", "summary": "Control va variant conversion rate hisoblandi.", "latex": f"p1={p1:.4f}, p2={p2:.4f}"},
                {"title": "Z Test", "summary": "Ikki proporsiya uchun z-test baholandi.", "latex": f"z={z_score:.3f}, p={p_value:.4f}"},
            ],
        }
        diagnostics = {"lane": mode, "sample_size": c_total + v_total, "family": "proportion-test", "risk": summary["riskSignal"]}
        return ProbabilitySolveResult("exact", "Probability inference result tayyor.", {"input": {"mode": mode, "dataset": dataset, "parameters": parameters, "dimension": dimension}, "parser": parser, "diagnostics": diagnostics, "summary": summary, "exact": exact})

    if mode == "regression":
        matches = re.findall(r"\((-?\d*\.?\d+)\s*,\s*(-?\d*\.?\d+)\)", dataset)
        if len(matches) < 2:
            raise ProbabilitySolverError("Regression lane uchun kamida 2 ta `(x,y)` nuqta kerak.")
        points = [(float(x), float(y)) for x, y in matches]
        xs = [x for x, _ in points]
        ys = [y for _, y in points]
        x_bar = sum(xs) / len(xs)
        y_bar = sum(ys) / len(ys)
        numerator = sum((x - x_bar) * (y - y_bar) for x, y in points)
        denominator = sum((x - x_bar) ** 2 for x in xs)
        slope = numerator / denominator if denominator else 0.0
        intercept = y_bar - slope * x_bar
        ss_tot = sum((y - y_bar) ** 2 for y in ys)
        ss_res = sum((y - (slope * x + intercept)) ** 2 for x, y in points)
        r2 = 1 - ss_res / ss_tot if ss_tot else 1.0
        summary = {
            "sampleSize": str(len(points)),
            "regressionFit": f"y ≈ {slope:.3f}x + {intercept:.3f}",
            "riskSignal": f"R² ≈ {r2:.3f}",
            "shape": "2d trend fit",
        }
        exact = {
            "method_label": "Least Squares Regression",
            "result_latex": f"y = {slope:.3f}x + {intercept:.3f}",
            "auxiliary_latex": f"R^2 = {r2:.3f}",
            "numeric_approximation": f"{r2:.6f}",
            "steps": [
                {"title": "Point Parse", "summary": "Scatter nuqtalar regression lane'ga yuklandi.", "latex": f"{len(points)} points"},
                {"title": "Fit Audit", "summary": "Linear least-squares fit hisoblandi.", "latex": f"slope={slope:.3f}, intercept={intercept:.3f}, R^2={r2:.3f}"},
            ],
        }
        diagnostics = {"lane": mode, "sample_size": len(points), "family": "linear-regression", "risk": summary["riskSignal"]}
        return ProbabilitySolveResult("exact", "Probability regression result tayyor.", {"input": {"mode": mode, "dataset": dataset, "parameters": parameters, "dimension": dimension}, "parser": parser, "diagnostics": diagnostics, "summary": summary, "exact": exact})

    if mode == "monte-carlo":
        samples = int(params.get("samples", "5000"))
        seed = int(params.get("seed", "42"))
        random = Random(seed)
        inside = 0
        for _ in range(samples):
            x = random.random()
            y = random.random()
            if x * x + y * y <= 1:
                inside += 1
        estimate = 4 * inside / samples
        summary = {
            "sampleSize": str(samples),
            "monteCarloEstimate": f"pi ≈ {estimate:.4f}",
            "variance": f"{abs(pi - estimate):.4f}",
            "riskSignal": "stochastic estimate",
            "shape": "simulation lane",
        }
        exact = {
            "method_label": "Monte Carlo Estimator",
            "result_latex": f"pi_hat = {estimate:.4f}",
            "auxiliary_latex": f"|pi - pi_hat| = {abs(pi - estimate):.4f}",
            "numeric_approximation": f"{estimate:.6f}",
            "steps": [
                {"title": "Simulation Setup", "summary": "Seed va sample size parse qilindi.", "latex": f"N={samples}, seed={seed}"},
                {"title": "Estimator", "summary": "Quarter circle estimator hisoblandi.", "latex": f"pi_hat={estimate:.4f}"},
            ],
        }
        diagnostics = {"lane": mode, "sample_size": samples, "family": "monte-carlo", "risk": "stochastic"}
        return ProbabilitySolveResult("exact", "Probability Monte Carlo result tayyor.", {"input": {"mode": mode, "dataset": dataset, "parameters": parameters, "dimension": dimension}, "parser": parser, "diagnostics": diagnostics, "summary": summary, "exact": exact})

    raise ProbabilitySolverError(f"Noma'lum probability mode: {mode}")
