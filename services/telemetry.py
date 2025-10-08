import os
from prometheus_client import Counter, Gauge

PROMETHEUS_ENABLED = os.getenv("PROMETHEUS_ENABLED", "false").lower() in {"1","true","yes"}

matches_total = Counter("matches_total", "Total successful matches")
queue_length = Gauge("queue_length", "Current queue length for matching")
active_sessions = Gauge("active_sessions", "Number of active chat sessions")
likes_total = Counter("likes_total", "Total likes processed")
fav_requests_total = Counter("fav_requests_total", "Total favorite requests processed")

def inc_match():
    if PROMETHEUS_ENABLED:
        matches_total.inc()

def set_queue_length(n: int):
    if PROMETHEUS_ENABLED:
        queue_length.set(n)

def set_active_sessions(n: int):
    if PROMETHEUS_ENABLED:
        active_sessions.set(n)

def inc_likes(n: int = 1):
    if PROMETHEUS_ENABLED:
        likes_total.inc(n)

def inc_fav_requests(n: int = 1):
    if PROMETHEUS_ENABLED:
        fav_requests_total.inc(n)


