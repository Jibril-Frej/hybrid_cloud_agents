"""Integration tests for mTLS transport security.

Asserts that mTLS is enforced between the orchestrator (private) and public
worker (public), so that clients without valid certificates are rejected.
See specs/v2-spec.md.
"""
