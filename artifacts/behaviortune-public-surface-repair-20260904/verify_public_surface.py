#!/usr/bin/env python3
"""Anonymous, read-only verification for the BehaviorTune public surface."""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import quote, urljoin, urlparse
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[2]
DATASET_ID = "aamish-ahmad/behaviortune-v1-1-r1"
MODEL_ID = "aamish-ahmad/behaviortune-v1-1-r1-adapter"
SPLITS = [
    "train",
    "dev",
    "eval_core",
    "holdout_principal",
    "holdout_family",
    "holdout_joint",
]
EXPECTED_TOPICS = {
    "llm",
    "qlora",
    "peft",
    "post-training",
    "model-evaluation",
    "behavioral-evaluation",
    "qwen",
    "synthetic-data",
}
EXPECTED_DESCRIPTION = (
    "Reproducible QLoRA post-training and behavioral evaluation on Qwen3-4B "
    "with matched BASE, SYSTEM, CONTEXT, and adapter conditions."
)
EXPECTED_HOMEPAGE = (
    "https://huggingface.co/aamish-ahmad/behaviortune-v1-1-r1-adapter"
)
EXPECTED_ADAPTER_SHA = (
    "8d16ef2cb6ff7a982511fd58f21eff52538761f4d198b4cc5cbfd73ca7c9d4de"
)


def fetch(url: str) -> tuple[int, bytes, dict[str, str]]:
    request = Request(
        url,
        headers={
            "User-Agent": "BehaviorTune-anonymous-public-verifier/1.0",
            "Accept": "application/vnd.github+json, application/json, text/html;q=0.9, */*;q=0.8",
        },
    )
    try:
        with urlopen(request, timeout=45) as response:
            return response.status, response.read(), dict(response.headers.items())
    except HTTPError as error:
        return error.code, error.read(), dict(error.headers.items())


def fetch_json(url: str) -> tuple[int, object, dict[str, str]]:
    status, body, headers = fetch(url)
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        payload = {"unparseable_body_prefix": body[:200].decode("utf-8", "replace")}
    return status, payload, headers


def find_lfs_sha(siblings: list[dict[str, object]], filename: str) -> tuple[str | None, int | None]:
    for sibling in siblings:
        if sibling.get("rfilename") == filename:
            lfs = sibling.get("lfs") or {}
            if isinstance(lfs, dict):
                return lfs.get("sha256"), lfs.get("size")
    return None, None


def main() -> int:
    checks: list[dict[str, object]] = []

    def record(name: str, passed: bool, **evidence: object) -> None:
        checks.append({"name": name, "passed": bool(passed), **evidence})

    github_api_status, github_api, _ = fetch_json(
        "https://api.github.com/repos/aamish-ahmad/behavior-tune"
    )
    record(
        "github_repository_api_public",
        github_api_status == 200
        and isinstance(github_api, dict)
        and github_api.get("private") is False
        and github_api.get("visibility") == "public",
        http=github_api_status,
        private=github_api.get("private") if isinstance(github_api, dict) else None,
        visibility=github_api.get("visibility") if isinstance(github_api, dict) else None,
        default_branch=github_api.get("default_branch") if isinstance(github_api, dict) else None,
        main_sha=github_api.get("pushed_at") if isinstance(github_api, dict) else None,
    )
    record(
        "github_recruiter_description",
        isinstance(github_api, dict) and github_api.get("description") == EXPECTED_DESCRIPTION,
        description=github_api.get("description") if isinstance(github_api, dict) else None,
    )
    record(
        "github_recruiter_homepage",
        isinstance(github_api, dict) and github_api.get("homepage") == EXPECTED_HOMEPAGE,
        homepage=github_api.get("homepage") if isinstance(github_api, dict) else None,
    )

    topics_status, topics_payload, _ = fetch_json(
        "https://api.github.com/repos/aamish-ahmad/behavior-tune/topics"
    )
    topics = set(topics_payload.get("names", [])) if isinstance(topics_payload, dict) else set()
    record(
        "github_topics_exact",
        topics_status == 200 and topics == EXPECTED_TOPICS,
        http=topics_status,
        topics=sorted(topics),
    )

    release_status, release_payload, _ = fetch_json(
        "https://api.github.com/repos/aamish-ahmad/behavior-tune/releases/tags/v1.0.0"
    )
    release_url = (
        release_payload.get("html_url") if isinstance(release_payload, dict) else None
    )
    record(
        "github_release_published",
        release_status == 200
        and isinstance(release_payload, dict)
        and release_payload.get("draft") is False
        and release_payload.get("prerelease") is False,
        http=release_status,
        url=release_url,
    )

    deployment_status, deployment_payload, _ = fetch_json(
        "https://api.github.com/repos/aamish-ahmad/behavior-tune/deployments"
    )
    record(
        "github_no_deployments",
        deployment_status == 200
        and isinstance(deployment_payload, list)
        and not deployment_payload,
        http=deployment_status,
        count=len(deployment_payload) if isinstance(deployment_payload, list) else None,
    )

    github_page_status, github_page, _ = fetch(
        "https://github.com/aamish-ahmad/behavior-tune"
    )
    github_html = github_page.decode("utf-8", "replace")
    record(
        "github_anonymous_page_and_about_render",
        github_page_status == 200
        and EXPECTED_DESCRIPTION in github_html
        and "behaviortune-v1-1-r1-adapter" in github_html
        and all(topic in github_html for topic in EXPECTED_TOPICS),
        http=github_page_status,
        description_rendered=EXPECTED_DESCRIPTION in github_html,
        homepage_rendered="behaviortune-v1-1-r1-adapter" in github_html,
        topics_rendered=all(topic in github_html for topic in EXPECTED_TOPICS),
        packages_section_visible='href="/aamish-ahmad/behavior-tune/packages"' in github_html,
        deployments_section_visible='href="/aamish-ahmad/behavior-tune/deployments"' in github_html,
    )
    raw_status, raw_readme, _ = fetch(
        "https://raw.githubusercontent.com/aamish-ahmad/behavior-tune/main/README.md"
    )
    record(
        "github_anonymous_raw_readme",
        raw_status == 200 and b"BehaviorTune" in raw_readme,
        http=raw_status,
    )

    dataset_status, dataset_api, _ = fetch_json(
        f"https://huggingface.co/api/datasets/{DATASET_ID}"
    )
    dataset_revision = dataset_api.get("sha") if isinstance(dataset_api, dict) else None
    dataset_tags = set(dataset_api.get("tags", [])) if isinstance(dataset_api, dict) else set()
    record(
        "hf_dataset_public_and_presented",
        dataset_status == 200
        and isinstance(dataset_api, dict)
        and dataset_api.get("private") is False
        and {"llm", "peft", "post-training", "model-evaluation", "qwen"}.issubset(dataset_tags),
        http=dataset_status,
        private=dataset_api.get("private") if isinstance(dataset_api, dict) else None,
        revision=dataset_revision,
        tags=sorted(dataset_tags),
    )

    model_status, model_api, _ = fetch_json(f"https://huggingface.co/api/models/{MODEL_ID}")
    model_revision = model_api.get("sha") if isinstance(model_api, dict) else None
    model_tags = set(model_api.get("tags", [])) if isinstance(model_api, dict) else set()
    tree_status, model_tree, _ = fetch_json(
        f"https://huggingface.co/api/models/{MODEL_ID}/tree/main?recursive=true&expand=true"
    )
    tree_files = model_tree if isinstance(model_tree, list) else []
    adapter_sha = None
    adapter_size = None
    for tree_file in tree_files:
        if isinstance(tree_file, dict) and tree_file.get("path") == "adapter_model.safetensors":
            lfs = tree_file.get("lfs") or {}
            if isinstance(lfs, dict):
                adapter_sha = lfs.get("oid") or lfs.get("sha256")
                adapter_size = lfs.get("size")
            break
    record(
        "hf_adapter_public_presented_and_immutable",
        model_status == 200
        and tree_status == 200
        and isinstance(model_api, dict)
        and model_api.get("private") is False
        and {"llm", "post-training", "model-evaluation", "qwen", "synthetic-data"}.issubset(model_tags)
        and adapter_sha == EXPECTED_ADAPTER_SHA,
        http=model_status,
        private=model_api.get("private") if isinstance(model_api, dict) else None,
        revision=model_revision,
        tree_http=tree_status,
        adapter_lfs_sha256=adapter_sha,
        adapter_lfs_size=adapter_size,
        tags=sorted(model_tags),
    )

    public_pages = {
        "hf_profile": "https://huggingface.co/aamish-ahmad",
        "hf_dataset": f"https://huggingface.co/datasets/{DATASET_ID}",
        "hf_adapter": f"https://huggingface.co/{MODEL_ID}",
        "github_release": "https://github.com/aamish-ahmad/behavior-tune/releases/tag/v1.0.0",
        "github_results": "https://github.com/aamish-ahmad/behavior-tune/blob/main/docs/RESULTS.md",
        "github_claim_map": "https://github.com/aamish-ahmad/behavior-tune/blob/main/docs/CV_CLAIM_MAP.md",
    }
    page_statuses = {name: fetch(url)[0] for name, url in public_pages.items()}
    record(
        "anonymous_public_pages",
        all(status == 200 for status in page_statuses.values()),
        statuses=page_statuses,
    )

    encoded_dataset = quote(DATASET_ID, safe="")
    valid_status, valid_payload, valid_headers = fetch_json(
        f"https://datasets-server.huggingface.co/is-valid?dataset={encoded_dataset}"
    )
    record(
        "hf_dataset_viewer_valid",
        valid_status == 200
        and isinstance(valid_payload, dict)
        and valid_payload.get("viewer") is True
        and valid_payload.get("preview") is True,
        http=valid_status,
        payload=valid_payload,
        revision=valid_headers.get("x-revision") or valid_headers.get("X-Revision"),
    )

    split_status, split_payload, _ = fetch_json(
        f"https://datasets-server.huggingface.co/splits?dataset={encoded_dataset}"
    )
    split_names = {
        item.get("split")
        for item in (split_payload.get("splits", []) if isinstance(split_payload, dict) else [])
        if isinstance(item, dict)
    }
    pending = split_payload.get("pending", []) if isinstance(split_payload, dict) else []
    failed = split_payload.get("failed", []) if isinstance(split_payload, dict) else []
    record(
        "hf_dataset_six_splits_ready",
        split_status == 200 and split_names == set(SPLITS) and not pending and not failed,
        http=split_status,
        splits=sorted(name for name in split_names if name),
        pending=len(pending),
        failed=len(failed),
    )

    row_statuses: dict[str, int] = {}
    row_counts: dict[str, int | None] = {}
    for split in SPLITS:
        url = (
            "https://datasets-server.huggingface.co/rows"
            f"?dataset={encoded_dataset}&config=default&split={quote(split)}&offset=0&length=1"
        )
        status, payload, _ = fetch_json(url)
        row_statuses[split] = status
        row_counts[split] = payload.get("num_rows_total") if isinstance(payload, dict) else None
    record(
        "hf_dataset_all_splits_render_rows",
        all(status == 200 for status in row_statuses.values())
        and row_counts
        == {
            "train": 240,
            "dev": 48,
            "eval_core": 64,
            "holdout_principal": 64,
            "holdout_family": 64,
            "holdout_joint": 64,
        },
        statuses=row_statuses,
        row_counts=row_counts,
    )

    link_sources = [
        ROOT / "README.md",
        ROOT / "release/dataset/README.md",
        ROOT / "release/adapter/README.md",
        ROOT / "docs/RESULTS.md",
        ROOT / "docs/CV_CLAIM_MAP.md",
    ]
    absolute_urls: set[str] = set()
    missing_relative: list[str] = []
    for source in link_sources:
        text = source.read_text(encoding="utf-8")
        for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
            if target.startswith(("https://", "http://")):
                absolute_urls.add(target)
            elif not target.startswith("#"):
                resolved = (source.parent / target.split("#", 1)[0]).resolve()
                if not resolved.exists():
                    missing_relative.append(f"{source.relative_to(ROOT)} -> {target}")
    link_failures: dict[str, int] = {}
    for url in sorted(absolute_urls):
        status, _, _ = fetch(url)
        if status != 200:
            link_failures[url] = status
    record(
        "cards_claims_and_results_links_resolve",
        not missing_relative and not link_failures,
        checked_absolute_urls=len(absolute_urls),
        missing_relative=missing_relative,
        http_failures=link_failures,
    )

    result = {
        "schema_version": 1,
        "verified_at": datetime.now(timezone.utc).isoformat(),
        "mode": "anonymous_no_auth_headers",
        "verdict": "VERIFIED" if all(item["passed"] for item in checks) else "FAILED",
        "github_main_commit": "97d8189cf76a69b58dd0e31320d82aacedf510f5",
        "hf_dataset_revision": dataset_revision,
        "hf_adapter_revision": model_revision,
        "checks": checks,
        "forbidden_work_performed": False,
        "secrets_used_by_verifier": False,
    }
    destination = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if destination:
        destination.write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    return 0 if result["verdict"] == "VERIFIED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
