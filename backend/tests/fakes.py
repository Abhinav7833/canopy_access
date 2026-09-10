class FakeLLMClient:
    """Test double for LLMClient — returns a canned response and records inputs."""

    def __init__(self, response: str = "ok") -> None:
        self.response = response
        self.last_system: str | None = None
        self.last_user: str | None = None
        self.calls = 0

    def complete(self, system: str, user: str, *, json_object: bool = False) -> str:
        self.last_system = system
        self.last_user = user
        self.last_json_object = json_object
        self.calls += 1
        return self.response
