import hashlib

import pytest
import redis

from app.services.token_bucket import TOKEN_BUCKET_SCRIPT, TokenBucket


class FakeRedis:
    def __init__(self):
        self.script_load_calls = 0
        self.evalsha_calls = []
        self.eval_calls = []
        self.script_load_result = "loaded-sha"
        self.evalsha_result = [1, 9]
        self.eval_result = [0, 0]
        self.raise_on_script_load = None
        self.raise_on_evalsha = None
        self.raise_on_eval = None

    def script_load(self, script):
        self.script_load_calls += 1
        assert script == TOKEN_BUCKET_SCRIPT
        if self.raise_on_script_load is not None:
            raise self.raise_on_script_load
        return self.script_load_result

    def evalsha(self, sha, numkeys, *args):
        self.evalsha_calls.append((sha, numkeys, args))
        if self.raise_on_evalsha is not None:
            raise self.raise_on_evalsha
        return self.evalsha_result

    def eval(self, script, numkeys, *args):
        self.eval_calls.append((script, numkeys, args))
        if self.raise_on_eval is not None:
            raise self.raise_on_eval
        return self.eval_result


def test_init_uses_provided_redis_client_and_sets_defaults():
    fake_redis = FakeRedis()

    limiter = TokenBucket(redis_client=fake_redis)

    assert limiter.redis is fake_redis
    assert limiter.capacity == 10
    assert limiter.refill_rate == 1
    assert limiter.refill_interval == 1.0
    assert limiter._script_loaded is False
    assert limiter._script_sha == hashlib.sha1(
        TOKEN_BUCKET_SCRIPT.encode("utf-8")
    ).hexdigest()


def test_ensure_script_loaded_loads_script_once():
    fake_redis = FakeRedis()
    limiter = TokenBucket(redis_client=fake_redis)

    limiter._ensure_script_loaded()
    limiter._ensure_script_loaded()

    assert fake_redis.script_load_calls == 1
    assert limiter._script_loaded is True
    assert limiter._script_sha == "loaded-sha"


def test_ensure_script_loaded_ignores_redis_error():
    fake_redis = FakeRedis()
    fake_redis.raise_on_script_load = redis.RedisError("boom")
    limiter = TokenBucket(redis_client=fake_redis)

    limiter._ensure_script_loaded()

    assert fake_redis.script_load_calls == 1
    assert limiter._script_loaded is False
    assert limiter._script_sha == hashlib.sha1(
        TOKEN_BUCKET_SCRIPT.encode("utf-8")
    ).hexdigest()


def test_allow_uses_evalsha_and_returns_allowed_and_remaining(monkeypatch):
    fake_redis = FakeRedis()
    limiter = TokenBucket(
        redis_client=fake_redis,
        capacity=5,
        refill_rate=2,
        refill_interval=3.5,
    )
    monkeypatch.setattr("app.services.token_bucket.time.time", lambda: 123.456)

    allowed, remaining = limiter.allow("user:123")

    assert allowed is True
    assert remaining == 9.0
    assert fake_redis.script_load_calls == 1
    assert len(fake_redis.evalsha_calls) == 1
    assert fake_redis.eval_calls == []

    sha, numkeys, args = fake_redis.evalsha_calls[0]
    assert sha == "loaded-sha"
    assert numkeys == 1
    assert args == ("user:123", 5, 2, 3.5, 123.456)


def test_allow_falls_back_to_eval_on_noscript_error(monkeypatch):
    fake_redis = FakeRedis()
    fake_redis.raise_on_evalsha = redis.exceptions.NoScriptError("missing script")
    fake_redis.eval_result = [0, 4]
    limiter = TokenBucket(redis_client=fake_redis)
    monkeypatch.setattr("app.services.token_bucket.time.time", lambda: 99.0)

    allowed, remaining = limiter.allow("api:endpoint:xyz")

    assert allowed is False
    assert remaining == 4.0
    assert fake_redis.script_load_calls == 1
    assert len(fake_redis.evalsha_calls) == 1
    assert len(fake_redis.eval_calls) == 1
    assert limiter._script_loaded is False

    script, numkeys, args = fake_redis.eval_calls[0]
    assert script == TOKEN_BUCKET_SCRIPT
    assert numkeys == 1
    assert args == ("api:endpoint:xyz", 10, 1, 1.0, 99.0)


def test_allow_uses_updated_script_sha_after_loading(monkeypatch):
    fake_redis = FakeRedis()
    limiter = TokenBucket(redis_client=fake_redis)
    monkeypatch.setattr("app.services.token_bucket.time.time", lambda: 1.0)

    limiter.allow("user:1")

    assert fake_redis.script_load_calls == 1
    assert fake_redis.evalsha_calls[0][0] == "loaded-sha"


def test_allow_propagates_non_noscript_evalsha_errors(monkeypatch):
    fake_redis = FakeRedis()
    fake_redis.raise_on_evalsha = redis.RedisError("unexpected redis error")
    limiter = TokenBucket(redis_client=fake_redis)
    monkeypatch.setattr("app.services.token_bucket.time.time", lambda: 7.0)

    with pytest.raises(redis.RedisError, match="unexpected redis error"):
        limiter.allow("user:999")

    assert fake_redis.script_load_calls == 1
    assert len(fake_redis.evalsha_calls) == 1
    assert fake_redis.eval_calls == []


def test_allow_accepts_custom_capacity_and_refill_values(monkeypatch):
    fake_redis = FakeRedis()
    limiter = TokenBucket(
        redis_client=fake_redis,
        capacity=25,
        refill_rate=7,
        refill_interval=12.5,
    )
    monkeypatch.setattr("app.services.token_bucket.time.time", lambda: 42.0)

    limiter.allow("tenant:a")

    _, _, args = fake_redis.evalsha_calls[0]
    assert args == ("tenant:a", 25, 7, 12.5, 42.0)