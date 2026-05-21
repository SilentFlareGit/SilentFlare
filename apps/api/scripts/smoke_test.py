import argparse
import sys
import time
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
            self.test_authenticated_admin_list()

            draft = self.create_post(
                {
                    "title": f"Smoke Draft {suffix}",
                    "summary": "Smoke draft summary.",
                    "content_markdown": "# Smoke Draft",
                    "status": "draft",
                    "category": "Tests",
                    "tags": ["smoke", "draft"],
                    "slug": draft_slug,
                },
                "draft",
            )
            self.check_admin_contains(draft_slug, True, "draft post appears in admin list")
            self.check_public_contains(draft_slug, False, "draft post is hidden from public list")

            published = self.create_post(
                {
                    "title": f"Smoke Published {suffix}",
                    "summary": "Smoke published summary.",
                    "content_markdown": "# Smoke Published",
                    "status": "published",
                    "category": "Tests",
                    "tags": ["smoke", "published"],
                    "slug": published_slug,
                },
                "published",
            )
            self.check_public_contains(published_slug, True, "published post appears in public list")
            self.test_public_detail(published_slug)
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

    def test_authenticated_admin_list(self) -> None:
        status_code, payload = self.get_json("/api/v1/admin/posts", self.auth_headers())
        self.check(
            "GET /api/v1/admin/posts with auth",
            status_code == 200 and isinstance(payload.get("items"), list),
            str(payload),
        )

    def create_post(self, payload: dict, expected_status: str) -> dict:
        status_code, data = self.post_json("/api/v1/admin/posts", payload, self.auth_headers())
        post_id = data.get("id")
        if isinstance(post_id, int):
            self.created_ids.append(post_id)

        self.check(
            f"POST /api/v1/admin/posts creates {expected_status}",
            status_code == 201 and data.get("status") == expected_status and data.get("slug") == payload["slug"],
            str(data),
        )
        return data

    def check_admin_contains(self, slug: str, expected: bool, name: str) -> None:
        status_code, payload = self.get_json("/api/v1/admin/posts", self.auth_headers())
        slugs = [item.get("slug") for item in payload.get("items", [])]
        self.check(name, status_code == 200 and (slug in slugs) is expected, str(slugs))

    def check_public_contains(self, slug: str, expected: bool, name: str) -> None:
        status_code, payload = self.get_json("/api/v1/posts")
        slugs = [item.get("slug") for item in payload.get("items", [])]
        self.check(name, status_code == 200 and (slug in slugs) is expected, str(slugs))

    def test_public_detail(self, slug: str) -> None:
        status_code, payload = self.get_json(f"/api/v1/posts/{slug}")
        self.check(
            "GET /api/v1/posts/{slug} for published post",
            status_code == 200 and payload.get("slug") == slug,
            str(payload),
        )

    def test_update_changes_updated_at(self, post: dict) -> None:
        post_id = post.get("id")
        old_updated_at = post.get("updated_at")
        time.sleep(1)

        response = self.client.put(
            f"/api/v1/admin/posts/{post_id}",
            json={"summary": "Updated by smoke test."},
            headers=self.auth_headers(),
        )
        payload = response.json()
        self.check(
            "PUT /api/v1/admin/posts/{id} changes updated_at",
            response.status_code == 200
            and payload.get("summary") == "Updated by smoke test."
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

    def cleanup(self) -> None:
        for post_id in list(self.created_ids):
            try:
                self.client.delete(f"/api/v1/admin/posts/{post_id}", headers=self.auth_headers())
            except httpx.HTTPError:
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
