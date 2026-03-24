from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sympy import Integral, Symbol, exp, latex, log, simplify
from sympy import sin, cos, tan

from .sympy_service import ParsedMathInput


X_SYMBOL = Symbol("x", real=True)


class IntegralSolverError(ValueError):
    pass


@dataclass
class IntegralSolveResult:
    status: str
    message: str
    payload: dict[str, Any]


def infer_domain_constraints(expression_text: str) -> list[str]:
    normalized = expression_text.replace(" ", "").lower()
    constraints: list[str] = []
    if "log(" in normalized or "ln(" in normalized:
        constraints.append("Log arguments must stay positive.")
    if "sqrt(" in normalized:
        constraints.append("Square-root radicands must stay nonnegative.")
    if "/" in normalized:
        constraints.append("Denominators must stay nonzero on the active domain.")
    return constraints


def infer_hazards(expression_text: str, lower_text: str | None = None, upper_text: str | None = None) -> list[str]:
    normalized = expression_text.replace(" ", "").lower()
    lower_value = (lower_text or "").strip().lower()
    upper_value = (upper_text or "").strip().lower()
    hazards: list[str] = []
    if "/x" in normalized and (lower_value == "0" or upper_value == "0"):
        hazards.append("Endpoint pole at x = 0.")
    if "1/sqrt(x)" in normalized and (lower_value == "0" or upper_value == "0"):
        hazards.append("Endpoint root singularity at x = 0.")
    if "log(x)" in normalized and lower_value == "0":
        hazards.append("Log singularity at x = 0.")
    if any(token in lower_value for token in ("inf", "infinity", "oo")) or any(token in upper_value for token in ("inf", "infinity", "oo")):
        hazards.append("Infinite integration bound detected.")
    return hazards


def infer_piecewise_regions(expression_text: str) -> list[dict[str, str]]:
    normalized = expression_text.replace(" ", "").lower()
    regions: list[dict[str, str]] = []
    if "abs(x)" in normalized:
        regions.extend(
            [
                {"region": "x < 0", "behavior": "abs(x) = -x"},
                {"region": "x >= 0", "behavior": "abs(x) = x"},
            ]
        )
    if "sign(x)" in normalized:
        regions.extend(
            [
                {"region": "x < 0", "behavior": "sign(x) = -1"},
                {"region": "x = 0", "behavior": "sign(x) = 0"},
                {"region": "x > 0", "behavior": "sign(x) = 1"},
            ]
        )
    if "piecewise" in normalized:
        regions.append({"region": "multiple branches", "behavior": "Explicit SymPy Piecewise expression detected."})
    if "max(" in normalized or "min(" in normalized:
        regions.append({"region": "comparison split", "behavior": "max/min introduces branch-dependent regions."})
    return regions


def build_diagnostics_payload(
    *,
    expression_text: str,
    lower_text: str | None = None,
    upper_text: str | None = None,
    convergence: str = "not_applicable",
    convergence_detail: str = "",
    singularity: str = "none",
) -> dict[str, Any]:
    piecewise_regions = infer_piecewise_regions(expression_text)
    return {
        "convergence": convergence,
        "convergence_detail": convergence_detail,
        "singularity": singularity,
        "domain_constraints": infer_domain_constraints(expression_text),
        "hazards": infer_hazards(expression_text, lower_text, upper_text),
        "piecewise": {
            "active": bool(piecewise_regions),
            "regions": piecewise_regions,
        },
    }


def build_parser_payload(
    *,
    integrand_input: ParsedMathInput,
    lower_input: ParsedMathInput | None = None,
    upper_input: ParsedMathInput | None = None,
) -> dict[str, Any]:
    return {
        "expression_raw": integrand_input.raw,
        "expression_normalized": integrand_input.normalized,
        "expression_latex": integrand_input.latex,
        "lower_raw": lower_input.raw if lower_input else "",
        "lower_normalized": lower_input.normalized if lower_input else "",
        "lower_latex": lower_input.latex if lower_input else "",
        "upper_raw": upper_input.raw if upper_input else "",
        "upper_normalized": upper_input.normalized if upper_input else "",
        "upper_latex": upper_input.latex if upper_input else "",
        "notes": [
            *integrand_input.notes,
            *([f"Quyi chegara: {note}" for note in lower_input.notes] if lower_input else []),
            *([f"Yuqori chegara: {note}" for note in upper_input.notes] if upper_input else []),
        ],
    }


def describe_integration_strategy(integrand: Any) -> dict[str, str]:
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


def build_exact_steps(
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
    bounds_evaluation_latex = rf"\left[{antiderivative_latex}\right]_{{{lower_input.latex}}}^{{{upper_input.latex}}}"

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


def build_unresolved_steps(
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


def build_indefinite_steps(
    *,
    integrand_input: ParsedMathInput,
    antiderivative: Any,
    method_meta: dict[str, str],
) -> list[dict[str, Any]]:
    antiderivative_latex = latex(antiderivative)
    return [
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
            "summary": "Aniqmas integral uchun primitive topildi.",
            "latex": rf"\int {integrand_input.latex}\,dx = {antiderivative_latex} + C",
            "tone": "success",
        },
    ]
