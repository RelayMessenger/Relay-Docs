"""Canonical surfaces must match their cache-busted responses byte for byte."""

CANONICAL_PATHS = ("", "start/quickstart", "llms.txt", "llms-full.txt", "skill.md", "agent-prompt.md")


def canonical_cache_pairs(fetch, expected_bodies=None, *, paths=None):
    """Verify default or discovered paths; inject fetch for offline regressions.

    Normalization belongs to rendered-content checks, never to this cache gate.
    A pair of equally stale responses must still fail the checkout-byte gate.
    """
    for path in dict.fromkeys(CANONICAL_PATHS if paths is None else paths):
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
