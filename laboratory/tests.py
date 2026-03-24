from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import LaboratoryModule


class LaboratoryModuleApiTests(APITestCase):
    def setUp(self):
        self.integral_module = LaboratoryModule.objects.get(slug="integral-studio")
        LaboratoryModule.objects.create(
            title="Disabled Module",
            slug="disabled-module",
            summary="Disabled module.",
            description="This one should stay hidden.",
            category="custom",
            computation_mode="client",
            is_enabled=False,
            sort_order=99,
        )

    def test_list_modules_returns_only_enabled_integral_module(self):
        url = reverse("laboratory-module-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        returned_slugs = [item["slug"] for item in response.data]

        self.assertIn("integral-studio", returned_slugs)
        self.assertNotIn("matrix-workbench", returned_slugs)
        self.assertNotIn("differential-lab", returned_slugs)
        self.assertNotIn("disabled-module", returned_slugs)
        self.assertEqual(len(returned_slugs), 1)

    def test_retrieve_module_supports_slug_lookup(self):
        url = reverse("laboratory-module-detail", args=[self.integral_module.slug])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], self.integral_module.title)
        self.assertEqual(response.data["category"], "integral")


class IntegralSolveApiTests(APITestCase):
    def test_exact_single_integral_solution(self):
        url = reverse("laboratory-integral-solve")
        response = self.client.post(
            url,
            {"expression": "x^2", "lower": "0", "upper": "1"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "exact")
        self.assertEqual(response.data["exact"]["evaluated_latex"], "\\frac{1}{3}")
        self.assertEqual(response.data["exact"]["numeric_approximation"], "0.333333333333333")

    def test_parser_translates_keyboard_style_expression(self):
        url = reverse("laboratory-integral-solve")
        response = self.client.post(
            url,
            {"expression": "2x^2 + ln(x)", "lower": "1", "upper": "e"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "exact")
        self.assertEqual(response.data["parser"]["expression_normalized"], "2x^2 + log(x)")
        self.assertEqual(response.data["exact"]["method_label"], "Logarithmic Structure")
        self.assertTrue(len(response.data["exact"]["steps"]) >= 4)

    def test_non_elementary_integral_requests_numerical_confirmation(self):
        url = reverse("laboratory-integral-solve")
        response = self.client.post(
            url,
            {"expression": "exp(-x^2) / log(x)", "lower": "2", "upper": "3"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "needs_numerical")
        self.assertTrue(response.data["can_offer_numerical"])

    def test_indefinite_integral_lane_returns_antiderivative(self):
        url = reverse("laboratory-integral-solve")
        response = self.client.post(
            url,
            {"expression": "x^2", "lower": "", "upper": ""},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "exact")
        self.assertFalse(response.data["can_offer_numerical"])
        self.assertEqual(response.data["input"]["lane"], "indefinite_single")
        self.assertEqual(response.data["exact"]["evaluated_latex"], "\\frac{x^{3}}{3} + C")

    def test_improper_integral_lane_handles_infinite_bound(self):
        url = reverse("laboratory-integral-solve")
        response = self.client.post(
            url,
            {"expression": "exp(-x)", "lower": "0", "upper": "inf"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "exact")
        self.assertFalse(response.data["can_offer_numerical"])
        self.assertEqual(response.data["input"]["lane"], "improper_single")
        self.assertEqual(response.data["exact"]["evaluated_latex"], "1")

    def test_endpoint_singularity_uses_improper_lane(self):
        url = reverse("laboratory-integral-solve")
        response = self.client.post(
            url,
            {"expression": "1/sqrt(x)", "lower": "0", "upper": "1"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "exact")
        self.assertEqual(response.data["input"]["lane"], "improper_single")
        self.assertEqual(response.data["exact"]["evaluated_latex"], "2")
