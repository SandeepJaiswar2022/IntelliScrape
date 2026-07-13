"""
Rate limiting for auth endpoints.

This is a *second, independent* layer of brute-force protection on top
of the per-account lockout in auth_service. The two guard against
different attack shapes:
  - Per-account lockout (auth_service): stops an attacker hammering
    ONE known email with many passwords.
  - This IP-based rate limit: stops an attacker hammering MANY emails
    (credential stuffing) or spamming /register to create junk accounts,
    from a single source.

storage_uri defaults to in-memory, which is correct for a single-process
MVP deployment. The moment this app runs as more than one process/
container (horizontal scaling), switch storage_uri to a Redis URL so all
instances share the same counters -- otherwise each instance enforces
the limit independently, effectively multiplying the real limit by the
number of instances.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
