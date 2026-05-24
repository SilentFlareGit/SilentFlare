import argparse
import sys
import time
from pathlib import Path
from uuid import uuid4

import httpx


class SmokeTest:
    def __init__(self, base_url: str, username: str, password: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.client = httpx.Client(base_url=self.base_url, timeout=10.0)
        self.token: str | None = None
        self.created_ids: list[int] = []
        self.created_upload_paths: list[str] = []
        self.failures: list[str] = []

    def auth_headers(self) -> dict[str, str]:
        if self.token is None:
            return {}
        return {"Authorization": f"Bearer {self.token}"}

    def check(self, name: str, condition: bool, detail: str = "") -> None:
        if condition:
            print(f"PASS {name}")
            return

        message = f"FAIL {name}"
        if detail:
            message = f"{message}: {detail}"
        print(message)
        self.failures.append(message)

    def get_json(self, path: str, headers: dict[str, str] | None = None) -> tuple[int, dict]:
        response = self.client.get(path, headers=headers)
        try:
            payload = response.json()
        except ValueError:
            payload = {}
        return response.status_code, payload

    def post_json(
        self,
        path: str,
        payload: dict,
        headers: dict[str, str] | None = None,
    ) -> tuple[int, dict]:
        response = self.client.post(path, json=payload, headers=headers)
        try:
            data = response.json()
        except ValueError:
            data = {}
        return response.status_code, data

    def run(self) -> int:
        suffix = uuid4().hex[:8]
        draft_slug = f"smoke-draft-{suffix}"
        published_slug = f"smoke-published-{suffix}"

        try:
            self.test_health()
            self.test_public_posts_load()
            self.test_login()
            self.test_unauthenticated_admin_rejected()
            self.test_unauthenticated_upload_rejected()
            self.test_authenticated_admin_list()
            unused_cover = self.test_authenticated_cover_upload()
            self.test_cover_list_contains_upload(unused_cover, expected_used=False)
            self.test_unused_cover_can_be_deleted(unused_cover)
            self.test_non_image_upload_rejected()
            used_cover = self.upload_cover("used-cover.png")

            draft = self.create_post(
                {
                    "title": f"Smoke Draft {suffix}",
                    "summary": "Smoke draft summary.",
                    "seo_title": f"Smoke Draft SEO {suffix}",
                    "meta_description": "Smoke draft meta description.",
                    "content_markdown": "# Smoke Draft",
                    "cover_url": used_cover.get("cover_url", ""),
                    "status": "draft",
                    "category": "Tests",
                    "tags": ["smoke", "draft"],
                    "slug": draft_slug,
                },
                "draft",
            )
            self.test_cover_list_contains_upload(used_cover, expected_used=True, expected_post_id=draft.get("id"))
            self.test_used_cover_cannot_be_deleted(used_cover)
            self.check_admin_contains(draft_slug, True, "draft post appears in admin list")
            self.check_public_contains(draft_slug, False, "draft post is hidden from public list")

            published = self.create_post(
                {
                    "title": f"Smoke Published {suffix}",
                    "summary": "Smoke published summary.",
                    "seo_title": f"Smoke Published SEO {suffix}",
                    "meta_description": "Smoke published meta description.",
                    "content_markdown": "# Smoke Published",
                    "status": "published",
                    "category": "Tests",
                    "tags": ["smoke", "published"],
                    "slug": published_slug,
                },
                "published",
            )
            self.check_public_contains(
                published_slug,
                True,
                "published post appears in public list",
                expected_seo_title=published.get("seo_title"),
                expected_meta_description=published.get("meta_description"),
            )
            self.test_public_detail(
                published_slug,
                expected_seo_title=published.get("seo_title"),
                expected_meta_description=published.get("meta_description"),
            )
            self.test_update_changes_updated_at(draft)
            self.test_delete_removes_from_admin(draft)
            self.test_delete_removes_from_admin(published)
            self.test_docs()
        finally:
            self.cleanup()
            self.client.close()

        if self.failures:
            print(f"\n{len(self.failures)} smoke test(s) failed.")
            return 1

        print("\nAll smoke tests passed.")
        return 0

    def test_health(self) -> None:
        status_code, payload = self.get_json("/api/v1/health")
        self.check("GET /api/v1/health", status_code == 200 and payload == {"status": "ok"}, str(payload))

    def test_public_posts_load(self) -> None:
        status_code, payload = self.get_json("/api/v1/posts")
        self.check(
            "GET /api/v1/posts",
            status_code == 200 and isinstance(payload.get("items"), list) and isinstance(payload.get("total"), int),
            str(payload),
        )

    def test_login(self) -> None:
        status_code, payload = self.post_json(
            "/api/v1/auth/login",
            {"username": self.username, "password": self.password},
        )
        self.token = payload.get("access_token")
        self.check(
            "POST /api/v1/auth/login",
            status_code == 200 and payload.get("token_type") == "bearer" and bool(self.token),
            str(payload),
        )

    def test_unauthenticated_admin_rejected(self) -> None:
        status_code, _ = self.get_json("/api/v1/admin/posts")
        self.check("GET /api/v1/admin/posts without auth", status_code in {401, 403}, f"status {status_code}")

    def test_unauthenticated_upload_rejected(self) -> None:
        response = self.client.post(
            "/api/v1/admin/uploads/cover",
            files={"file": ("cover.png", self.tiny_png(), "image/png")},
        )
        self.check("POST /api/v1/admin/uploads/cover without auth", response.status_code in {401, 403}, response.text)

    def test_authenticated_admin_list(self) -> None:
        status_code, payload = self.get_json("/api/v1/admin/posts", self.auth_headers())
        self.check(
            "GET /api/v1/admin/posts with auth",
            status_code == 200 and isinstance(payload.get("items"), list),
            str(payload),
        )

    def upload_cover(self, filename: str = "cover.png") -> dict:
        response = self.client.post(
            "/api/v1/admin/uploads/cover",
            headers=self.auth_headers(),
            files={"file": (filename, self.tiny_png(), "image/png")},
        )
        try:
            payload = response.json()
        except ValueError:
            payload = {}

        path = payload.get("path")
        if isinstance(path, str):
            self.created_upload_paths.append(path)

        self.check(
            "POST /api/v1/admin/uploads/cover with auth",
            response.status_code == 200
            and isinstance(payload.get("cover_url"), str)
            and payload["cover_url"].endswith(path or "")
            and isinstance(path, str)
            and path.startswith("/uploads/covers/")
            and path.endswith(".png"),
            str(payload),
        )

        if isinstance(path, str):
            uploaded = self.client.get(path)
            self.check(
                "GET uploaded cover file",
                uploaded.status_code == 200 and uploaded.content.startswith(b"\x89PNG\r\n\x1a\n"),
                f"status {uploaded.status_code}",
            )

        return payload

    def test_authenticated_cover_upload(self) -> dict:
        return self.upload_cover()

    def test_cover_list_contains_upload(
        self,
        cover: dict,
        expected_used: bool,
        expected_post_id: int | None = None,
    ) -> None:
        cover_path = cover.get("path")
        status_code, payload = self.get_json("/api/v1/admin/uploads/covers", self.auth_headers())
        items = payload.get("items", [])
        match = next((item for item in items if item.get("path") == cover_path), None)
        used_by_post_ids = match.get("used_by_post_ids", []) if isinstance(match, dict) else []

        self.check(
            "GET /api/v1/admin/uploads/covers includes uploaded cover",
            status_code == 200
            and isinstance(payload.get("total"), int)
            and isinstance(match, dict)
            and match.get("filename")
            and match.get("cover_url", "").endswith(cover_path or "")
            and isinstance(match.get("size_bytes"), int)
            and isinstance(match.get("modified_at"), str)
            and match.get("used") is expected_used
            and isinstance(used_by_post_ids, list)
            and (expected_post_id is None or expected_post_id in used_by_post_ids),
            str(payload),
        )

    def test_unused_cover_can_be_deleted(self, cover: dict) -> None:
        path = cover.get("path")
        filename = path.rsplit("/", 1)[-1] if isinstance(path, str) else ""
        response = self.client.delete(f"/api/v1/admin/uploads/covers/{filename}", headers=self.auth_headers())
        try:
            payload = response.json()
        except ValueError:
            payload = {}

        self.check(
            "DELETE /api/v1/admin/uploads/covers/{filename} deletes unused cover",
            response.status_code == 200 and payload == {"status": "deleted", "filename": filename},
            str(payload),
        )

        if isinstance(path, str) and response.status_code == 200 and path in self.created_upload_paths:
            self.created_upload_paths.remove(path)

    def test_used_cover_cannot_be_deleted(self, cover: dict) -> None:
        path = cover.get("path")
        filename = path.rsplit("/", 1)[-1] if isinstance(path, str) else ""
        response = self.client.delete(f"/api/v1/admin/uploads/covers/{filename}", headers=self.auth_headers())
        self.check(
            "DELETE /api/v1/admin/uploads/covers/{filename} rejects used cover",
            response.status_code == 409,
            response.text,
        )

    def test_non_image_upload_rejected(self) -> None:
        response = self.client.post(
            "/api/v1/admin/uploads/cover",
            headers=self.auth_headers(),
            files={"file": ("cover.txt", b"not an image", "text/plain")},
        )
        self.check("POST /api/v1/admin/uploads/cover rejects non-image", response.status_code == 400, response.text)

    def create_post(self, payload: dict, expected_status: str) -> dict:
        status_code, data = self.post_json("/api/v1/admin/posts", payload, self.auth_headers())
        post_id = data.get("id")
        if isinstance(post_id, int):
            self.created_ids.append(post_id)

        self.check(
            f"POST /api/v1/admin/posts creates {expected_status}",
            status_code == 201
            and data.get("status") == expected_status
            and data.get("slug") == payload["slug"]
            and data.get("seo_title") == payload["seo_title"]
            and data.get("meta_description") == payload["meta_description"],
            str(data),
        )
        return data

    def check_admin_contains(self, slug: str, expected: bool, name: str) -> None:
        status_code, payload = self.get_json("/api/v1/admin/posts", self.auth_headers())
        slugs = [item.get("slug") for item in payload.get("items", [])]
        self.check(name, status_code == 200 and (slug in slugs) is expected, str(slugs))

    def check_public_contains(
        self,
        slug: str,
        expected: bool,
        name: str,
        expected_seo_title: str | None = None,
        expected_meta_description: str | None = None,
    ) -> None:
        status_code, payload = self.get_json("/api/v1/posts")
        items = payload.get("items", [])
        match = next((item for item in items if item.get("slug") == slug), None)
        has_expected_seo = (
            not expected
            or (
                isinstance(match, dict)
                and match.get("seo_title") == expected_seo_title
                and match.get("meta_description") == expected_meta_description
            )
        )
        self.check(name, status_code == 200 and (match is not None) is expected and has_expected_seo, str(items))

    def test_public_detail(
        self,
        slug: str,
        expected_seo_title: str | None = None,
        expected_meta_description: str | None = None,
    ) -> None:
        status_code, payload = self.get_json(f"/api/v1/posts/{slug}")
        self.check(
            "GET /api/v1/posts/{slug} for published post",
            status_code == 200
            and payload.get("slug") == slug
            and payload.get("seo_title") == expected_seo_title
            and payload.get("meta_description") == expected_meta_description,
            str(payload),
        )

    def test_update_changes_updated_at(self, post: dict) -> None:
        post_id = post.get("id")
        old_updated_at = post.get("updated_at")
        time.sleep(1)

        response = self.client.put(
            f"/api/v1/admin/posts/{post_id}",
            json={"summary": "Updated by smoke test.", "meta_description": "Updated smoke test meta description."},
            headers=self.auth_headers(),
        )
        payload = response.json()
        self.check(
            "PUT /api/v1/admin/posts/{id} changes updated_at",
            response.status_code == 200
            and payload.get("summary") == "Updated by smoke test."
            and payload.get("meta_description") == "Updated smoke test meta description."
            and payload.get("updated_at") != old_updated_at,
            str(payload),
        )

    def test_delete_removes_from_admin(self, post: dict) -> None:
        post_id = post.get("id")
        slug = post.get("slug")
        response = self.client.delete(f"/api/v1/admin/posts/{post_id}", headers=self.auth_headers())
        self.check(
            "DELETE /api/v1/admin/posts/{id}",
            response.status_code == 200 and response.json().get("status") == "deleted",
            response.text,
        )

        if isinstance(post_id, int) and post_id in self.created_ids:
            self.created_ids.remove(post_id)

        status_code, payload = self.get_json("/api/v1/admin/posts", self.auth_headers())
        slugs = [item.get("slug") for item in payload.get("items", [])]
        self.check("deleted post no longer appears in admin list", status_code == 200 and slug not in slugs, str(slugs))

    def test_docs(self) -> None:
        response = self.client.get("/docs")
        self.check("GET /docs", response.status_code == 200 and "Swagger UI" in response.text, f"status {response.status_code}")

    def tiny_png(self) -> bytes:
        return (
            b"\x89PNG\r\n\x1a\n"
            b"\x00\x00\x00\rIHDR"
            b"\x00\x00\x00\x01\x00\x00\x00\x01"
            b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
            b"\x00\x00\x00\nIDATx\x9cc`\x00\x00\x00\x02\x00\x01"
            b"\xe2!\xbc3"
            b"\x00\x00\x00\x00IEND\xaeB`\x82"
        )

    def cleanup(self) -> None:
        for post_id in list(self.created_ids):
            try:
                self.client.delete(f"/api/v1/admin/posts/{post_id}", headers=self.auth_headers())
            except httpx.HTTPError:
                pass

        for upload_path in list(self.created_upload_paths):
            try:
                path = Path(*upload_path.lstrip("/").split("/"))
                file_path = Path(__file__).resolve().parents[1] / path
                if file_path.is_file() and file_path.resolve().is_relative_to(
                    (Path(__file__).resolve().parents[1] / "uploads" / "covers").resolve()
                ):
                    file_path.unlink()
            except OSError:
                pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run SilentFlare API smoke tests.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--username", default="admin")
    parser.add_argument("--password", default="admin123")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    return SmokeTest(args.base_url, args.username, args.password).run()


if __name__ == "__main__":
    sys.exit(main())
