from __future__ import annotations

import math
import random
import re

import sympy as sp

from .differential_lane_common import DifferentialSolveResult, DifferentialSolverError
from .sympy_service import build_sympy_locals


def _extract(pattern: str, text: str) -> str | None:
    match = re.search(pattern, text, flags=re.IGNORECASE)
    return match.group(1).strip() if match else None


def solve_sde_lane(
    expression: str,
    variable: str,
    point: str,
) -> DifferentialSolveResult:
    compact = expression.strip()
    if not compact:
        raise DifferentialSolverError("SDE lane uchun ifoda kiritilmadi.")

    drift_match = re.search(r"dX\s*=\s*(.+?)\*dt\s*\+\s*(.+?)\*dW", compact, flags=re.IGNORECASE)
    if not drift_match:
        raise DifferentialSolverError("SDE syntax: `dX = mu*dt + sigma*dW; X(0)=1; t:[0,1]; n=200` ko'rinishida bo'lishi kerak.")

    mu_text = drift_match.group(1).strip()
    sigma_text = drift_match.group(2).strip()
    x0_text = _extract(r"X\(0\)\s*=\s*([^;]+)", compact) or _extract(r"X\(0\)\s*=\s*([^;]+)", point) or "0"
    range_text = _extract(r"t:\s*\[([^\]]+)\]", compact) or _extract(r"t:\s*\[([^\]]+)\]", point) or "0,1"
    steps_text = _extract(r"n\s*=\s*([0-9]+)", compact) or _extract(r"n\s*=\s*([0-9]+)", point) or "200"

    try:
        t0_text, t1_text = [item.strip() for item in range_text.split(",", 1)]
    except ValueError as exc:
        raise DifferentialSolverError("SDE time range `t:[t0,t1]` ko'rinishida bo'lishi kerak.") from exc

    locals_dict = build_sympy_locals([variable or "t", "X"])
    t_symbol = locals_dict.get(variable or "t")
    x_symbol = locals_dict.get("X")

    try:
        mu_expr = sp.sympify(mu_text, locals=locals_dict)
        sigma_expr = sp.sympify(sigma_text, locals=locals_dict)
        x0 = float(sp.N(sp.sympify(x0_text, locals=locals_dict)))
        t0 = float(sp.N(sp.sympify(t0_text, locals=locals_dict)))
        t1 = float(sp.N(sp.sympify(t1_text, locals=locals_dict)))
        n_steps = max(20, min(2000, int(steps_text)))
    except Exception as exc:
        raise DifferentialSolverError(f"SDE parametrlarini parse qilishda xato: {exc}") from exc

    dt = (t1 - t0) / n_steps
    if dt <= 0:
        raise DifferentialSolverError("SDE time horizon musbat bo'lishi kerak.")

    rng = random.Random(42)
    t = t0
    x = x0
    path: list[tuple[float, float]] = [(t, x)]

    for _ in range(n_steps):
        scope = {t_symbol: t, x_symbol: x}
        mu = float(sp.N(mu_expr.subs(scope)))
        sigma = float(sp.N(sigma_expr.subs(scope)))
        dw = math.sqrt(dt) * rng.gauss(0.0, 1.0)
        x = x + mu * dt + sigma * dw
        t = t + dt
        path.append((t, x))

    terminal = path[-1][1]
    minimum = min(value for _, value in path)
    maximum = max(value for _, value in path)

    return DifferentialSolveResult(
        status="exact",
        message="SDE numeric lane result tayyor.",
        payload={
            "input": {
                "expression": expression,
                "variable": variable,
                "point": point,
                "lane": "sde",
            },
            "parser": {
                "expression_raw": expression,
                "expression_normalized": compact,
                "expression_latex": r"dX = \mu(X,t)\,dt + \sigma(X,t)\,dW_t",
                "variable": variable,
                "point_raw": point,
                "point_normalized": point.strip(),
                "notes": ["SDE lane Euler-Maruyama discretization bilan ishladi."],
            },
            "diagnostics": {
                "continuity": "partial",
                "differentiability": "partial",
                "domain_analysis": {
                    "constraints": [],
                    "assumptions": ["Single-path stochastic simulation; seed = 42 for reproducibility."],
                    "blockers": [],
                },
                "taxonomy": {
                    "lane": "sde",
                    "family": "stochastic_diffusion",
                    "tags": ["euler_maruyama", "sample_path", "stochastic"],
                    "summary": "Stochastic differential equation solved numerically via Euler-Maruyama.",
                },
            },
            "exact": {
                "method_label": "Euler-Maruyama",
                "derivative_latex": r"X_{n+1}=X_n+\mu(X_n,t_n)\Delta t+\sigma(X_n,t_n)\Delta W_n",
                "evaluated_latex": f"X(T) \\approx {terminal:.6f}",
                "numeric_approximation": f"{terminal:.6f}",
                "taxonomy_family": "stochastic_diffusion",
                "steps": [
                    {
                        "title": "Drift / Diffusion Parse",
                        "summary": "mu va sigma komponentlari ajratildi.",
                        "latex": rf"\mu={sp.latex(mu_expr)},\quad \sigma={sp.latex(sigma_expr)}",
                        "tone": "neutral",
                    },
                    {
                        "title": "Euler-Maruyama Discretization",
                        "summary": f"n = {n_steps}, dt = {dt:.6f}, reproducible seed = 42.",
                        "latex": r"X_{n+1}=X_n+\mu\Delta t+\sigma\Delta W",
                        "tone": "info",
                    },
                    {
                        "title": "Sample Path Summary",
                        "summary": f"Terminal value {terminal:.6f}, path range [{minimum:.6f}, {maximum:.6f}].",
                        "latex": None,
                        "tone": "success",
                    },
                ],
            },
        },
    )
