import pytest


class TestRateLimit:

    def test_logged_rate_limited_allows_calls_within_budget(self, stub_ratelimit, monkeypatch):
        from gameinsights.utils.ratelimit import logged_rate_limited

        sleep_calls = []

        def fake_sleep(duration):
            sleep_calls.append(duration)

        monkeypatch.setattr("gameinsights.utils.ratelimit.time.sleep", fake_sleep)

        class Dummy:
            def __init__(self):
                self.calls = 2
                self.period = 5

            @logged_rate_limited()
            def do_work(self):
                return "ok"

        dummy = Dummy()

        assert dummy.do_work() == "ok"
        assert dummy.do_work() == "ok"

        assert sleep_calls == []
        assert stub_ratelimit.limits_invocations == 1

    def test_logged_rate_limited_retries_and_logs(self, stub_ratelimit, monkeypatch, caplog):
        from gameinsights.utils.ratelimit import logged_rate_limited

        sleep_calls = []

        def fake_sleep(duration):
            sleep_calls.append(duration)

        monkeypatch.setattr("gameinsights.utils.ratelimit.time.sleep", fake_sleep)
        caplog.set_level("INFO")

        class Dummy:
            def __init__(self):
                self.calls = 1
                self.period = 3
                self.invocations = 0

            @logged_rate_limited()
            def do_work(self):
                self.invocations += 1
                return self.invocations

        dummy = Dummy()

        assert dummy.do_work() == 1
        assert dummy.do_work() == 2

        assert sleep_calls == [float(dummy.period)]
        assert any("Rate limit exceeded" in message for message in caplog.messages)

    def test_logged_rate_limited_caches_per_instance(self, stub_ratelimit):
        from gameinsights.utils.ratelimit import logged_rate_limited

        class Dummy:
            def __init__(self):
                self.calls = 1
                self.period = 3

            @logged_rate_limited()
            def do_work(self):
                return None

        dummy = Dummy()

        dummy.do_work()
        assert stub_ratelimit.limits_invocations == 1

        dummy.do_work()
        assert stub_ratelimit.limits_invocations == 1

        dummy.calls = 2
        dummy.do_work()
        assert stub_ratelimit.limits_invocations == 2

    def test_logged_rate_limited_propagates_non_ratelimit_error(self, stub_ratelimit):
        from gameinsights.utils.ratelimit import logged_rate_limited

        class Dummy:
            def __init__(self):
                self.calls = 1
                self.period = 1

            @logged_rate_limited()
            def do_work(self):
                raise ValueError("non rate limit failure")

        dummy = Dummy()

        with pytest.raises(ValueError):
            dummy.do_work()
