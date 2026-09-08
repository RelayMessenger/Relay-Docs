"""Canonical agent surfaces must match their cache-busted responses."""

CANONICAL_PATHS = ("", "guides", "llms.txt", "llms-full.txt", "skill.md")


def canonical_cache_pairs(fetch):
    """Yield verified response pairs; fetch is injected for offline regression."""
    for path in CANONICAL_PATHS:
        canonical = fetch(path)
        cache_busted = fetch(path, cache_busted=True)
        if canonical["body"] != cache_busted["body"]:
            raise SystemExit(
                f"/{path} canonical body {canonical['sha256']} does not match "
                f"current origin body {cache_busted['sha256']}"
            )
        yield path, canonical, cache_busted
