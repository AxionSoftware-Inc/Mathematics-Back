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

    def test_piecewise_branch_metadata_is_returned(self):
        url = reverse("laboratory-integral-solve")
        response = self.client.post(
            url,
            {"expression": "abs(x)", "lower": "-1", "upper": "1"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["diagnostics"]["piecewise"]["active"])
        self.assertEqual(len(response.data["diagnostics"]["piecewise"]["regions"]), 2)
        self.assertEqual(response.data["diagnostics"]["piecewise"]["source"], "abs")

    def test_structured_domain_diagnostics_are_returned(self):
        url = reverse("laboratory-integral-solve")
        response = self.client.post(
            url,
            {"expression": "log(x)/(x-1)", "lower": "2", "upper": "3"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        constraints = response.data["diagnostics"]["domain_analysis"]["constraints"]
        hazards = response.data["diagnostics"]["hazard_details"]
        self.assertTrue(any(item["kind"] == "log_argument_positive" for item in constraints))
        self.assertTrue(any(item["kind"] == "denominator_nonzero" for item in constraints))
        self.assertTrue(any(item["kind"] == "pole" for item in hazards))

    def test_improper_diagnostics_include_convergence_reason(self):
        url = reverse("laboratory-integral-solve")
        response = self.client.post(
            url,
            {"expression": "exp(-x)", "lower": "0", "upper": "inf"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["diagnostics"]["convergence"], "convergent")
        self.assertEqual(response.data["diagnostics"]["convergence_reason"], "finite_symbolic_limit")

    def test_line_integral_lane_solves_parametric_circulation(self):
        url = reverse("laboratory-integral-solve")
        response = self.client.post(
            url,
            {"expression": "line(P=-y, Q=x, path=(cos(t), sin(t)), t:[0, 2*pi])", "lower": "", "upper": ""},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "exact")
        self.assertEqual(response.data["input"]["lane"], "line_integral")
        self.assertEqual(response.data["exact"]["evaluated_latex"], "2 \\pi")

    def test_surface_integral_lane_solves_parametric_flux(self):
        url = reverse("laboratory-integral-solve")
        response = self.client.post(
            url,
            {"expression": "surface(f=(0, 0, 1), patch=(u, v, u + v), u:[0,1], v:[0,1])", "lower": "", "upper": ""},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "exact")
        self.assertEqual(response.data["input"]["lane"], "surface_integral")
        self.assertEqual(response.data["exact"]["evaluated_latex"], "1")

    def test_contour_integral_lane_solves_parametric_path(self):
        url = reverse("laboratory-integral-solve")
        response = self.client.post(
            url,
            {"expression": "contour(f=1/z, path=exp(I*t), t:[0, 2*pi])", "lower": "", "upper": ""},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "exact")
        self.assertEqual(response.data["input"]["lane"], "contour_integral")
        self.assertEqual(response.data["exact"]["evaluated_latex"], "2 i \\pi")


class DifferentialSolveApiTests(APITestCase):
    def test_derivative_lane_returns_exact_result(self):
        url = reverse("laboratory-differential-solve")
        response = self.client.post(
            url,
            {"mode": "derivative", "expression": "x^3", "variable": "x", "point": "2", "order": "1"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "exact")
        self.assertEqual(response.data["input"]["lane"], "derivative")
        self.assertTrue(response.data["exact"]["numeric_approximation"].startswith("12."))

    def test_directional_lane_uses_direction_vector(self):
        url = reverse("laboratory-differential-solve")
        response = self.client.post(
            url,
            {
                "mode": "directional",
                "expression": "x^2 + y^2",
                "variable": "x, y",
                "point": "1, 0",
                "direction": "1, 1",
                "coordinates": "cartesian",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "exact")
        self.assertEqual(response.data["input"]["lane"], "directional")
        self.assertTrue(response.data["diagnostics"]["directional"]["active"])
        self.assertEqual(response.data["exact"]["method_label"], "Symbolic Directional Derivative")
        self.assertIsNotNone(response.data["exact"]["evaluated_latex"])

    def test_jacobian_lane_returns_matrix_diagnostics(self):
        url = reverse("laboratory-differential-solve")
        response = self.client.post(
            url,
            {
                "mode": "jacobian",
                "expression": "[x + y, x - y]",
                "variable": "x, y",
                "point": "1, 2",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "exact")
        self.assertEqual(response.data["diagnostics"]["matrix"]["lane"], "jacobian")
        self.assertEqual(response.data["diagnostics"]["matrix"]["shape"], "2x2")
        self.assertIn(response.data["diagnostics"]["matrix"]["determinant_status"], {"invertible", "near_singular"})

    def test_hessian_lane_returns_curvature_diagnostics(self):
        url = reverse("laboratory-differential-solve")
        response = self.client.post(
            url,
            {
                "mode": "hessian",
                "expression": "x^2 + y^2",
                "variable": "x, y",
                "point": "0, 0",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "exact")
        self.assertEqual(response.data["diagnostics"]["matrix"]["lane"], "hessian")
        self.assertEqual(response.data["diagnostics"]["matrix"]["critical_point_type"], "Local minimum")
        self.assertEqual(response.data["exact"]["critical_point_type"], "Local minimum")

    def test_ode_lane_solves_first_order_ivp(self):
        url = reverse("laboratory-differential-solve")
        response = self.client.post(
            url,
            {
                "mode": "ode",
                "expression": "y' = y; y(0)=1",
                "variable": "x",
                "point": "y(0)=1",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "exact")
        self.assertEqual(response.data["input"]["lane"], "ode")
        self.assertIn("y", response.data["exact"]["derivative_latex"])

    def test_pde_lane_solves_first_order_transport_family(self):
        url = reverse("laboratory-differential-solve")
        response = self.client.post(
            url,
            {
                "mode": "pde",
                "expression": "u_t = u_x",
                "variable": "x, t",
                "point": "",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "exact")
        self.assertEqual(response.data["input"]["lane"], "pde")
        self.assertEqual(response.data["exact"]["method_label"], "SymPy pdsolve")

    def test_sde_lane_runs_euler_maruyama(self):
        url = reverse("laboratory-differential-solve")
        response = self.client.post(
            url,
            {
                "mode": "sde",
                "expression": "dX = 0.4*X*dt + 0.2*X*dW; X(0)=1; t:[0,1]; n=64",
                "variable": "t",
                "point": "X(0)=1; t:[0,1]; n=64",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "exact")
        self.assertEqual(response.data["input"]["lane"], "sde")
        self.assertEqual(response.data["exact"]["method_label"], "Euler-Maruyama")


class MatrixSolveApiTests(APITestCase):
    def test_algebra_lane_returns_determinant(self):
        url = reverse("laboratory-matrix-solve")
        response = self.client.post(
            url,
            {"mode": "algebra", "expression": "2 1; 1 3", "rhs": "", "dimension": "2x2"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "exact")
        self.assertEqual(response.data["summary"]["determinant"], "5")
        self.assertTrue(response.data["summary"]["inverseAvailable"])

    def test_systems_lane_solves_linear_system(self):
        url = reverse("laboratory-matrix-solve")
        response = self.client.post(
            url,
            {"mode": "systems", "expression": "2 1; 1 3", "rhs": "1; 0", "dimension": "2x2"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["exact"]["method_label"], "Linear System Solve")
        self.assertIn("x =", response.data["exact"]["result_latex"])

    def test_decomposition_lane_returns_spectrum(self):
        url = reverse("laboratory-matrix-solve")
        response = self.client.post(
            url,
            {"mode": "decomposition", "expression": "4 1; 1 3", "rhs": "", "dimension": "2x2"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["exact"]["method_label"], "Spectral Decomposition")
        self.assertEqual(response.data["summary"]["eigenSummary"], "Eigen spectrum extracted")

    def test_transform_lane_maps_probe_vector(self):
        url = reverse("laboratory-matrix-solve")
        response = self.client.post(
            url,
            {"mode": "transform", "expression": "1 2; 0 1", "rhs": "1; 1", "dimension": "2x2"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["exact"]["method_label"], "Linear Transform")
        self.assertIn("T(v)", response.data["exact"]["result_latex"])


class ProbabilitySolveApiTests(APITestCase):
    def test_descriptive_lane_returns_moments(self):
        url = reverse("laboratory-probability-solve")
        response = self.client.post(
            url,
            {"mode": "descriptive", "dataset": "1,2,3,4,5", "parameters": "bins=4", "dimension": "1d"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "exact")
        self.assertEqual(response.data["summary"]["sampleSize"], "5")
        self.assertEqual(response.data["exact"]["method_label"], "Descriptive Statistics")

    def test_inference_lane_returns_p_value(self):
        url = reverse("laboratory-probability-solve")
        response = self.client.post(
            url,
            {"mode": "inference", "dataset": "control: 42/210; variant: 57/205", "parameters": "alpha=0.05", "dimension": "2-group"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "exact")
        self.assertIn("pValue", response.data["summary"])

    def test_regression_lane_returns_fit(self):
        url = reverse("laboratory-probability-solve")
        response = self.client.post(
            url,
            {"mode": "regression", "dataset": "(1,2.1), (2,2.9), (3,4.2), (4,5.1), (5,6.2)", "parameters": "model=linear", "dimension": "2d"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "exact")
        self.assertIn("regressionFit", response.data["summary"])

    def test_bayesian_lane_returns_posterior(self):
        url = reverse("laboratory-probability-solve")
        response = self.client.post(
            url,
            {"mode": "bayesian", "dataset": "successes=58; trials=100", "parameters": "prior_alpha=2; prior_beta=3", "dimension": "posterior lane"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "exact")
        self.assertIn("posteriorMean", response.data["summary"])
        self.assertEqual(response.data["exact"]["method_label"], "Beta-Binomial Posterior")

    def test_multivariate_lane_returns_structure(self):
        url = reverse("laboratory-probability-solve")
        response = self.client.post(
            url,
            {"mode": "multivariate", "dataset": "1,2,3; 2,3,4; 3,4,5; 4,5,6", "parameters": "labels=a,b,c", "dimension": "3-variable"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "exact")
        self.assertIn("correlationSignal", response.data["summary"])

    def test_time_series_lane_returns_forecast(self):
        url = reverse("laboratory-probability-solve")
        response = self.client.post(
            url,
            {"mode": "time-series", "dataset": "112,118,121,126,133,129,138,144", "parameters": "window=3; horizon=2", "dimension": "1d temporal"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "exact")
        self.assertIn("forecast", response.data["summary"])

    def test_distribution_lane_supports_exponential(self):
        url = reverse("laboratory-probability-solve")
        response = self.client.post(
            url,
            {"mode": "distributions", "dataset": "x=1.5", "parameters": "family=exponential; lambda=1.2", "dimension": "1d"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["summary"]["distributionFamily"], "exponential")

    def test_regression_lane_supports_quadratic(self):
        url = reverse("laboratory-probability-solve")
        response = self.client.post(
            url,
            {"mode": "regression", "dataset": "(1,2.4), (2,3.1), (3,4.9), (4,7.8), (5,11.6), (6,16.1)", "parameters": "model=quadratic", "dimension": "2d"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "exact")
        self.assertEqual(response.data["exact"]["method_label"], "Quadratic Least Squares")
