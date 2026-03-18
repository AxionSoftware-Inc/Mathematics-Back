from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from application.models import Project
from .models import LaboratoryModule


class LaboratoryModuleApiTests(APITestCase):
    def setUp(self):
        self.quantum_project = Project.objects.create(name="Quantum Uz", slug="quantum-uz")
        self.ket_project = Project.objects.create(name="Ket Studio", slug="ket")
        self.matrix_module = LaboratoryModule.objects.get(slug="matrix-workbench")
        self.quantum_module = LaboratoryModule.objects.create(
            project=self.quantum_project,
            title="Quantum Differential Extension",
            slug="quantum-differential-extension",
            summary="Project-specific differential playground.",
            description="Extra module for the quantum project.",
            category="differential",
            computation_mode="client",
            sort_order=20,
        )
        LaboratoryModule.objects.create(
            project=self.ket_project,
            title="Hidden Module",
            slug="hidden-module",
            summary="Should not leak into quantum project.",
            description="Different project module.",
            category="custom",
            computation_mode="client",
            sort_order=3,
        )
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

    def test_list_modules_returns_enabled_global_and_project_modules(self):
        url = reverse("laboratory-module-list")
        response = self.client.get(url, {"project": "quantum-uz"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        returned_slugs = [item["slug"] for item in response.data]

        self.assertIn("matrix-workbench", returned_slugs)
        self.assertIn("integral-studio", returned_slugs)
        self.assertIn("differential-lab", returned_slugs)
        self.assertIn(self.quantum_module.slug, returned_slugs)
        self.assertNotIn("hidden-module", returned_slugs)
        self.assertNotIn("disabled-module", returned_slugs)

    def test_retrieve_module_supports_slug_lookup(self):
        url = reverse("laboratory-module-detail", args=[self.matrix_module.slug])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], self.matrix_module.title)
        self.assertEqual(response.data["category"], "matrix")
