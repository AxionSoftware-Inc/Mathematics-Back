from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sympy import Integral, Symbol, exp, latex, log, simplify
from sympy import integrate as sympy_integrate
from sympy import sin, cos, tan
from sympy import N as sympy_numeric

from .sympy_service import MathParserError, ParsedMathInput, parse_user_math_input


X_SYMBOL = Symbol("x", real=True)


class IntegralSolverError(ValueError):
    pass


@dataclass
class IntegralSolveResult:
    status: str
    message: str
    payload: dict[str, Any]


def solve_single_integral(expression: str, lower: str, upper: str) -> IntegralSolveResult:
    try:
        integrand_input = parse_user_math_input(
            expression,
            label="Ifoda",
            variable_names=("x",),
        )
        lower_input = parse_user_math_input(
            lower,
            label="Quyi chegara",
            require_numeric=True,
        )
        upper_input = parse_user_math_input(
            upper,
            label="Yuqori chegara",
            require_numeric=True,
        )
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

    parser_payload = {
        "expression_raw": integrand_input.raw,
        "expression_normalized": integrand_input.normalized,
        "expression_latex": integrand_input.latex,
        "lower_raw": lower_input.raw,
        "lower_normalized": lower_input.normalized,
        "lower_latex": lower_input.latex,
        "upper_raw": upper_input.raw,
        "upper_normalized": upper_input.normalized,
        "upper_latex": upper_input.latex,
        "notes": [
            *integrand_input.notes,
            *[f"Quyi chegara: {note}" for note in lower_input.notes],
            *[f"Yuqori chegara: {note}" for note in upper_input.notes],
        ],
    }

    base_payload = {
        "input": {
            "expression": expression,
            "lower": lower,
            "upper": upper,
            "expression_latex": integrand_input.latex,
            "lower_latex": lower_input.latex,
            "upper_latex": upper_input.latex,
        },
        "parser": parser_payload,
    }

    if unresolved_definite:
        return IntegralSolveResult(
            status="needs_numerical",
            message="Analitik closed-form yechim topilmadi. Numerik hisoblashni alohida tasdiqlash kerak.",
            payload={
                **base_payload,
                "reason": "sympy_could_not_resolve_definite_integral",
                "can_offer_numerical": True,
                "exact": {
                    "method_label": _describe_integration_strategy(integrand)["label"],
                    "method_summary": _describe_integration_strategy(integrand)["summary"],
                    "antiderivative_latex": None if unresolved_antiderivative else latex(antiderivative),
                    "definite_integral_latex": latex(Integral(integrand, (X_SYMBOL, lower_bound, upper_bound))),
                    "evaluated_latex": None,
                    "numeric_approximation": None,
                    "contains_special_functions": False,
                    "steps": _build_unresolved_steps(
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
    method_meta = _describe_integration_strategy(integrand)

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
                "steps": _build_exact_steps(
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


def _describe_integration_strategy(integrand: Any) -> dict[str, str]:
    if integrand.is_polynomial(X_SYMBOL):
        return {
            "label": "Power Rule",
            "summary": "Ifoda polinomial shaklda. SymPy kuchlar qoidasi va algebraik soddalashtirish bilan primitive topdi.",
        }
    if integrand.is_rational_function(X_SYMBOL):
        return {
            "label": "Rational Reduction",
            "summary": "Ifoda ratsional tuzilishga ega. SymPy algebraik ajratish va logarifmik komponentlar orqali primitive qidirdi.",
        }
    if integrand.has(exp):
        return {
            "label": "Exponential Structure",
            "summary": "Ifoda eksponentsial komponentlarni o'z ichiga oladi. SymPy eksponentsial qoidalar va symbolic reduction ishlatdi.",
        }
    if integrand.has(sin) or integrand.has(cos) or integrand.has(tan):
        return {
            "label": "Trigonometric Structure",
            "summary": "Ifoda trigonometrik komponentlarni o'z ichiga oladi. SymPy trig identities va symbolic integration ishlatdi.",
        }
    if integrand.has(log):
        return {
            "label": "Logarithmic Structure",
            "summary": "Ifoda logarifmik komponentlarga ega. SymPy symbolic reduction va transformatsiyalar bilan primitive qidirdi.",
        }
    return {
        "label": "Symbolic Reduction",
        "summary": "SymPy ifodani umumiy symbolic reduction orqali qayta yozib, closed-form primitive qidirishga urinib ko'rdi.",
    }


def _build_exact_steps(
    *,
    integrand_input: ParsedMathInput,
    lower_input: ParsedMathInput,
    upper_input: ParsedMathInput,
    antiderivative: Any,
    definite_value: Any,
    numeric_approximation: str | None,
    method_meta: dict[str, str],
) -> list[dict[str, Any]]:
    antiderivative_latex = latex(antiderivative)
    interval_integral_latex = latex(Integral(integrand_input.expression, (X_SYMBOL, lower_input.expression, upper_input.expression)))
    bounds_evaluation_latex = (
        rf"\left[{antiderivative_latex}\right]_{{{lower_input.latex}}}^{{{upper_input.latex}}}"
    )

    steps: list[dict[str, Any]] = [
        {
            "title": "Parser Translation",
            "summary": "Foydalanuvchi yozuvi SymPy uchun normalizatsiya qilindi va symbolic ifodaga aylantirildi.",
            "latex": rf"f(x) = {integrand_input.latex}",
            "tone": "neutral",
        },
        {
            "title": "Method Detection",
            "summary": f"{method_meta['label']}: {method_meta['summary']}",
            "latex": None,
            "tone": "info",
        },
        {
            "title": "Antiderivative",
            "summary": "Primitive topildi va keyingi bosqichda chegaralarda baholash uchun saqlandi.",
            "latex": rf"F(x) = {antiderivative_latex}",
            "tone": "info",
        },
        {
            "title": "Bounds Evaluation",
            "summary": "Definite integral fundamental theorem orqali yuqori va quyi chegaralarda baholandi.",
            "latex": rf"{interval_integral_latex} = {bounds_evaluation_latex}",
            "tone": "info",
        },
        {
            "title": "Exact Result",
            "summary": "Yakuniy symbolic natija soddalashtirildi.",
            "latex": rf"{interval_integral_latex} = {latex(definite_value)}",
            "tone": "success",
        },
    ]

    if numeric_approximation:
        steps.append(
            {
                "title": "Numeric Check",
                "summary": "Exact natijaning decimal ko'rinishi ham chiqarildi.",
                "latex": rf"{latex(definite_value)} \approx {numeric_approximation}",
                "tone": "neutral",
            }
        )

    return steps


def _build_unresolved_steps(
    *,
    integrand_input: ParsedMathInput,
    lower_input: ParsedMathInput,
    upper_input: ParsedMathInput,
    antiderivative_latex: str | None,
) -> list[dict[str, Any]]:
    steps: list[dict[str, Any]] = [
        {
            "title": "Parser Translation",
            "summary": "Foydalanuvchi yozuvi symbolic ko'rinishga normalizatsiya qilindi.",
            "latex": rf"f(x) = {integrand_input.latex}",
            "tone": "neutral",
        },
        {
            "title": "Definite Integral Setup",
            "summary": "Chegaralar symbolic shaklda tayyorlandi, lekin closed-form baholash yakuniga yetmadi.",
            "latex": latex(Integral(integrand_input.expression, (X_SYMBOL, lower_input.expression, upper_input.expression))),
            "tone": "warn",
        },
    ]

    if antiderivative_latex:
        steps.append(
            {
                "title": "Partial Symbolic Result",
                "summary": "Primitive topilgan bo'lishi mumkin, lekin definite integral closed-form ko'rinishga to'liq tushmadi.",
                "latex": rf"F(x) = {antiderivative_latex}",
                "tone": "info",
            }
        )

    steps.append(
        {
            "title": "Numerical Confirmation Needed",
            "summary": "Shu sabab numerik hisoblashni foydalanuvchi alohida tasdiqlashi kerak.",
            "latex": None,
            "tone": "warn",
        }
    )

    return steps
