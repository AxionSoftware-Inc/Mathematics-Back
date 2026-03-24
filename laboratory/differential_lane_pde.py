from __future__ import annotations

import re

import sympy as sp
from sympy import Eq, Function, latex, pdsolve

from .differential_lane_common import DifferentialSolveResult, DifferentialSolverError, infer_symbolic_taxonomy
from .sympy_service import build_sympy_locals


def _replace_pde_tokens(text: str, dep_name: str, indep_names: list[str]) -> str:
    updated = text
    func_call = f"{dep_name}({', '.join(indep_names)})"
    derivative_specs = [
        ("_xx", f"Derivative({func_call}, ({indep_names[0]}, 2))"),
        ("_yy", f"Derivative({func_call}, ({indep_names[1]}, 2))" if len(indep_names) > 1 else f"Derivative({func_call}, ({indep_names[0]}, 2))"),
        ("_tt", f"Derivative({func_call}, ({indep_names[-1]}, 2))"),
        ("_x", f"Derivative({func_call}, {indep_names[0]})"),
        ("_y", f"Derivative({func_call}, {indep_names[1]})" if len(indep_names) > 1 else f"Derivative({func_call}, {indep_names[0]})"),
        ("_t", f"Derivative({func_call}, {indep_names[-1]})"),
    ]
    for token, replacement in derivative_specs:
        updated = re.sub(rf"\b{re.escape(dep_name + token)}\b", replacement, updated)
    updated = re.sub(rf"\b{re.escape(dep_name)}\b(?!\s*\()", func_call, updated)
    return updated


def solve_pde_lane(
    expression: str,
    variable: str,
    point: str,
) -> DifferentialSolveResult:
    indep_names = [name.strip() for name in variable.split(",") if name.strip()] or ["x", "t"]
    dep_name = "u"

    parts = [part.strip() for part in re.split(r"[;\n]+", expression) if part.strip()]
    if not parts:
        raise DifferentialSolverError("PDE lane uchun equation kiritilmadi.")
    equation_text = parts[0]
    normalized_equation = _replace_pde_tokens(equation_text, dep_name, indep_names)

    if "=" in normalized_equation:
        lhs_text, rhs_text = [part.strip() for part in normalized_equation.split("=", 1)]
    else:
        lhs_text, rhs_text = normalized_equation, "0"

    locals_dict = build_sympy_locals(indep_names)
    dep_func = Function(dep_name)
    locals_dict[dep_name] = dep_func
    locals_dict["Derivative"] = sp.Derivative

    try:
        lhs = sp.sympify(lhs_text, locals=locals_dict)
        rhs = sp.sympify(rhs_text, locals=locals_dict)
    except Exception as exc:
        raise DifferentialSolverError(f"PDE parse xatosi: {exc}") from exc

    equation = Eq(lhs, rhs)
    try:
        solution = pdsolve(equation)
    except Exception as exc:
        raise DifferentialSolverError(f"PDE symbolic solve muvaffaqiyatsiz: {exc}") from exc

    taxonomy = infer_symbolic_taxonomy(rhs - lhs, "pde")

    return DifferentialSolveResult(
        status="exact",
        message="PDE symbolic lane result tayyor.",
        payload={
            "input": {
                "expression": expression,
                "variable": variable,
                "point": point,
                "lane": "pde",
            },
            "parser": {
                "expression_raw": expression,
                "expression_normalized": equation_text,
                "expression_latex": latex(equation),
                "variable": variable,
                "point_raw": point,
                "point_normalized": point.strip(),
                "notes": ["PDE shorthand symbolic Eq ga o'girdi."],
            },
            "diagnostics": {
                "continuity": "continuous",
                "differentiability": "differentiable",
                "domain_analysis": {
                    "constraints": [],
                    "assumptions": ["PDE lane limited pdsolve oilalarini qo'llaydi."],
                    "blockers": [],
                },
                "taxonomy": taxonomy,
            },
            "exact": {
                "method_label": "SymPy pdsolve",
                "derivative_latex": latex(solution),
                "evaluated_latex": None,
                "numeric_approximation": None,
                "taxonomy_family": taxonomy["family"],
                "steps": [
                    {
                        "title": "Equation Assembly",
                        "summary": "PDE shorthand symbolic Eq ga aylantirildi.",
                        "latex": latex(equation),
                        "tone": "neutral",
                    },
                    {
                        "title": "Symbolic PDE Solve",
                        "summary": "pdsolve qo'llab-quvvatlagan oilada yechim topildi.",
                        "latex": latex(solution),
                        "tone": "success",
                    },
                ],
            },
        },
    )
