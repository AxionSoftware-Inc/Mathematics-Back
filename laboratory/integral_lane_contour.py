from __future__ import annotations

from sympy import Integral, Symbol, diff, latex, simplify
from sympy import integrate as sympy_integrate
from sympy import N as sympy_numeric

from .integral_lane_common import IntegralSolveResult, IntegralSolverError, build_diagnostics_payload
from .integral_lane_geometry import parse_geometry_expression, parse_interval
from .sympy_service import MathParserError, parse_user_math_input


def solve_contour_integral(expression: str) -> IntegralSolveResult:
    try:
        spec = parse_geometry_expression(expression, "contour")
        parameter_name = spec.fields.get("parameter", "t")
        parameter_interval = spec.fields.get(parameter_name) or spec.fields.get("t")
        if not parameter_interval:
            raise IntegralSolverError("Contour lane uchun t:[a,b] intervali kerak.")

        lower_text, upper_text = parse_interval(parameter_interval)
        path_expression = parse_user_math_input(spec.fields["path"], label="Contour path", variable_names=(parameter_name,)).expression
        integrand_expression = parse_user_math_input(spec.fields["f"], label="Contour integrand", variable_names=("z",)).expression
        parameter_symbol = parse_user_math_input(parameter_name, label="Contour parameter", variable_names=(parameter_name,)).expression
        lower_input = parse_user_math_input(lower_text, label="Contour lower")
        upper_input = parse_user_math_input(upper_text, label="Contour upper")

        pulled_integrand = simplify(integrand_expression.subs({Symbol("z", real=True): path_expression}) * diff(path_expression, parameter_symbol))
        definite_value = simplify(sympy_integrate(pulled_integrand, (parameter_symbol, lower_input.expression, upper_input.expression)))
        numeric_approximation = None if definite_value.has(Integral) else str(sympy_numeric(definite_value, 15))
        diagnostics = build_diagnostics_payload(
            expression_text=expression,
            expression=pulled_integrand,
            lower_expr=lower_input.expression,
            upper_expr=upper_input.expression,
            lower_text=lower_text,
            upper_text=upper_text,
            convergence="not_applicable",
            convergence_detail="Contour lane parametrik complex path bo'yicha finite interval ishlatadi.",
            convergence_reason="complex_parametric_path",
            singularity="possible" if "/" in latex(pulled_integrand) else "none",
        )
    except MathParserError as exc:
        raise IntegralSolverError(str(exc)) from exc
    except KeyError as exc:
        raise IntegralSolverError(f"Contour lane field missing: {exc.args[0]}") from exc
    except ValueError as exc:
        raise IntegralSolverError(str(exc)) from exc

    if definite_value.has(Integral):
        return IntegralSolveResult(
            status="needs_numerical",
            message="Contour integral closed-form ko'rinishga to'liq tushmadi.",
            payload={
                "input": {"expression": expression, "lane": "contour_integral"},
                "parser": {"expression_raw": expression, "expression_normalized": expression, "expression_latex": latex(Integral(pulled_integrand, (parameter_symbol, lower_input.expression, upper_input.expression))), "lower_raw": lower_text, "lower_normalized": lower_text, "lower_latex": lower_input.latex, "upper_raw": upper_text, "upper_normalized": upper_text, "upper_latex": upper_input.latex, "notes": []},
                "diagnostics": diagnostics,
                "reason": "contour_integral_unresolved",
                "can_offer_numerical": False,
                "exact": {"method_label": "Contour pullback", "method_summary": "Complex contour parametrga tortildi, lekin symbolic integral yakunlanmadi.", "antiderivative_latex": None, "definite_integral_latex": latex(Integral(pulled_integrand, (parameter_symbol, lower_input.expression, upper_input.expression))), "evaluated_latex": None, "numeric_approximation": None, "contains_special_functions": False, "steps": []},
            },
        )

    return IntegralSolveResult(
        status="exact",
        message="Contour integral parametrik complex lane orqali baholandi.",
        payload={
            "input": {"expression": expression, "lane": "contour_integral"},
            "parser": {"expression_raw": expression, "expression_normalized": expression, "expression_latex": latex(Integral(pulled_integrand, (parameter_symbol, lower_input.expression, upper_input.expression))), "lower_raw": lower_text, "lower_normalized": lower_text, "lower_latex": lower_input.latex, "upper_raw": upper_text, "upper_normalized": upper_text, "upper_latex": upper_input.latex, "notes": []},
            "diagnostics": diagnostics,
            "can_offer_numerical": False,
            "exact": {
                "method_label": "Contour pullback",
                "method_summary": "Complex contour z(t) va dz/dt orqali bitta parameter integralga o'tkazildi.",
                "antiderivative_latex": None,
                "definite_integral_latex": latex(Integral(pulled_integrand, (parameter_symbol, lower_input.expression, upper_input.expression))),
                "evaluated_latex": latex(definite_value),
                "numeric_approximation": numeric_approximation,
                "contains_special_functions": False,
                "steps": [
                    {"title": "Contour path", "summary": "Complex path parametrizatsiya qilindi.", "latex": latex(path_expression), "tone": "info"},
                    {"title": "Pullback", "summary": "f(z) dz ifodasi parameter integralga o'tkazildi.", "latex": latex(pulled_integrand), "tone": "info"},
                    {"title": "Contour result", "summary": "Contour integral baholandi.", "latex": latex(definite_value), "tone": "success"},
                ],
            },
        },
    )
