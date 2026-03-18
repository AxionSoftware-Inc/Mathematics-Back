from rest_framework import status
from rest_framework.test import APITestCase

from application.models import Article, Project
from paper_builder.models import ScientificPaper


class ScientificPaperApiTests(APITestCase):
    def setUp(self):
        self.project = Project.objects.create(name="Quantum Uz", slug="quantum-uz")

    def test_published_paper_syncs_to_public_article(self):
        response = self.client.post(
            "/api/builder/papers/",
            {
                "title": "Fourier Analysis Notes",
                "abstract": "A concise overview of Fourier techniques.",
                "content": "# Fourier\n\nThis paper studies transforms.",
                "authors": "A. Mathematician",
                "status": "published",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        paper = ScientificPaper.objects.get(pk=response.data["id"])

        self.assertIsNotNone(paper.article_id)
        self.assertIsNotNone(paper.slug)
        self.assertIsNotNone(paper.published_at)
        self.assertEqual(paper.article.title, paper.title)
        self.assertEqual(paper.article.summary, paper.abstract)
        self.assertEqual(paper.article.author, paper.authors)
        self.assertTrue(paper.article.is_published)
        self.assertEqual(paper.article.project, self.project)

    def test_published_paper_requires_title_and_content(self):
        response = self.client.post(
            "/api/builder/papers/",
            {
                "title": "",
                "content": "",
                "status": "published",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("title", response.data)

    def test_switching_to_draft_unpublishes_public_article(self):
        paper = ScientificPaper.objects.create(
            title="Topology Draft",
            abstract="Abstract",
            content="Initial content",
            status="published",
        )

        response = self.client.patch(
            f"/api/builder/papers/{paper.id}/",
            {"status": "draft"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        paper.refresh_from_db()
        self.assertIsNotNone(paper.article_id)
        self.assertIsNone(paper.published_at)
        self.assertFalse(paper.article.is_published)

    def test_list_supports_status_and_search_filters(self):
        ScientificPaper.objects.create(title="Algebra Draft", content="x", status="draft")
        ScientificPaper.objects.create(title="Geometry Final", content="x", status="published")

        response = self.client.get("/api/builder/papers/?status=published&q=Geometry")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["title"], "Geometry Final")


class PublicArticleSyncTests(APITestCase):
    def setUp(self):
        self.project = Project.objects.create(name="Quantum Uz", slug="quantum-uz")

    def test_synced_article_is_visible_in_public_articles_api(self):
        paper = ScientificPaper.objects.create(
            title="Number Theory",
            abstract="Prime numbers and more.",
            content="# Number Theory\n\nPrime exploration.",
            authors="N. Researcher",
            status="published",
        )

        response = self.client.get(f"/api/articles/{paper.article.slug}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Number Theory")
        self.assertEqual(response.data["summary"], "Prime numbers and more.")
        self.assertEqual(Article.objects.filter(source_paper=paper).count(), 1)

    def test_synced_article_appears_in_project_filtered_public_list(self):
        ScientificPaper.objects.create(
            title="Combinatorics",
            abstract="Counting methods.",
            content="Published content",
            status="published",
        )

        response = self.client.get("/api/articles/?project=quantum-uz")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["title"], "Combinatorics")

    def test_unpublished_synced_article_is_hidden_from_public_articles_api(self):
        paper = ScientificPaper.objects.create(
            title="Hidden draft",
            content="Still in progress",
            status="published",
        )
        paper.status = "draft"
        paper.save()

        response = self.client.get("/api/articles/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(any(item["id"] == paper.article_id for item in response.data))
