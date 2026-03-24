from __future__ import annotations

from sympy import Integral, latex, simplify
from sympy import integrate as sympy_integrate
from sympy import N as sympy_numeric

from .integral_lane_common import (
    X_SYMBOL,
    IntegralSolveResult,
    IntegralSolverError,
    build_exact_steps,
    build_parser_payload,
    build_unresolved_steps,
    describe_integration_strategy,
)
from .sympy_service import MathParserError, parse_user_math_input


def solve_definite_single_integral(expression: str, lower: str, upper: str) -> IntegralSolveResult:
    try:
        integrand_input = parse_user_math_input(expression, label="Ifoda", variable_names=("x",))
        lower_input = parse_user_math_input(lower, label="Quyi chegara", require_numeric=True)
        upper_input = parse_user_math_input(upper, label="Yuqori chegara", require_numeric=True)
    except MathParserError as exc:
        raise IntegralSolverError(str(exc)) from exc

    integrand = integrand_input.expression
    lower_bound = lower_input.expression
    upper_bound = upper_input.expression

    if (upper_bound - lower_bound).is_real is False:
        raise IntegralSolverError("Chegaralar haqiqiy son bo'lishi kerak.")

    try:
        if float(sympy_numeric(upper_bound - lower_bound, 20)) <= 0:
            raise IntegralSolverError("Yuqori chegara quyi chegaradan katta bo'lishi kerak.")
    except TypeError as exc:
        raise IntegralSolverError("Chegaralarni son sifatida baholab bo'lmadi.") from exc

    antiderivative = simplify(sympy_integrate(integrand, X_SYMBOL))
    definite_value = simplify(sympy_integrate(integrand, (X_SYMBOL, lower_bound, upper_bound)))

    unresolved_antiderivative = antiderivative.has(Integral)
    unresolved_definite = definite_value.has(Integral)
    parser_payload = build_parser_payload(integrand_input=integrand_input, lower_input=lower_input, upper_input=upper_input)
    base_payload = {
        "input": {
            "expression": expression,
            "lower": lower,
            "upper": upper,
            "expression_latex": integrand_input.latex,
            "lower_latex": lower_input.latex,
            "upper_latex": upper_input.latex,
            "lane": "definite_single",
        },
        "parser": parser_payload,
    }

    if unresolved_definite:
        method_meta = describe_integration_strategy(integrand)
        return IntegralSolveResult(
            status="needs_numerical",
            message="Analitik closed-form yechim topilmadi. Numerik hisoblashni alohida tasdiqlash kerak.",
            payload={
                **base_payload,
                "reason": "sympy_could_not_resolve_definite_integral",
                "can_offer_numerical": True,
                "exact": {
                    "method_label": method_meta["label"],
                    "method_summary": method_meta["summary"],
                    "antiderivative_latex": None if unresolved_antiderivative else latex(antiderivative),
                    "definite_integral_latex": latex(Integral(integrand, (X_SYMBOL, lower_bound, upper_bound))),
                    "evaluated_latex": None,
                    "numeric_approximation": None,
                    "contains_special_functions": False,
                    "steps": build_unresolved_steps(
                        integrand_input=integrand_input,
                        lower_input=lower_input,
                        upper_input=upper_input,
                        antiderivative_latex=None if unresolved_antiderivative else latex(antiderivative),
                    ),
                },
            },
        )

    numeric_approximation = None
    try:
        numeric_approximation = str(sympy_numeric(definite_value, 15))
    except Exception:
        numeric_approximation = None

    contains_special_functions = any(
        token in latex(definite_value)
        for token in ("operatorname{erf}", "operatorname{Si}", "operatorname{Ci}", "Fresnel", "Gamma", "log")
    )
    method_meta = describe_integration_strategy(integrand)

    return IntegralSolveResult(
        status="exact",
        message="Analitik yechim topildi.",
        payload={
            **base_payload,
            "can_offer_numerical": True,
            "exact": {
                "method_label": method_meta["label"],
                "method_summary": method_meta["summary"],
                "antiderivative_latex": None if unresolved_antiderivative else latex(antiderivative),
                "definite_integral_latex": latex(Integral(integrand, (X_SYMBOL, lower_bound, upper_bound))),
                "evaluated_latex": latex(definite_value),
                "numeric_approximation": numeric_approximation,
                "contains_special_functions": contains_special_functions,
                "steps": build_exact_steps(
                    integrand_input=integrand_input,
                    lower_input=lower_input,
                    upper_input=upper_input,
                    antiderivative=antiderivative,
                    definite_value=definite_value,
                    numeric_approximation=numeric_approximation,
                    method_meta=method_meta,
                ),
            },
        },
    )
