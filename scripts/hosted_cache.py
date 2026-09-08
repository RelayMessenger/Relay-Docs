"""Canonical agent surfaces must match their cache-busted responses."""

CANONICAL_PATHS = ("", "guides", "llms.txt", "llms-full.txt", "skill.md")


def canonical_cache_pairs(fetch, expected_bodies=None):
    """Yield verified response pairs; fetch is injected for offline regression."""
    for path in CANONICAL_PATHS:
        canonical = fetch(path)
        cache_busted = fetch(path, cache_busted=True)
        if canonical["body"] != cache_busted["body"]:
            raise SystemExit(
                f"/{path} canonical body {canonical['sha256']} does not match "
                f"current origin body {cache_busted['sha256']}"
            )
        if expected_bodies is not None and path in expected_bodies:
            if canonical["body"] != expected_bodies[path]:
                raise SystemExit(f"/{path} served body does not match expected checkout source bytes")
        yield path, canonical, cache_busted
