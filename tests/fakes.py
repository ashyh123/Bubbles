from types import SimpleNamespace


class FakeCompletions:
    def __init__(self, replies, *, fail_effort=False):
        self.replies = list(replies)
        self.calls = []
        self.fail_effort = fail_effort

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.fail_effort and kwargs.get("extra_body"):
            raise RuntimeError("Unsupported parameter: reasoning_effort")
        if not self.replies:
            raise AssertionError("model client received an extra call")
        content = self.replies.pop(0)
        message = SimpleNamespace(content=content)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


class FakeClient:
    def __init__(self, replies, *, fail_effort=False):
        self.chat = SimpleNamespace(completions=FakeCompletions(replies, fail_effort=fail_effort))
