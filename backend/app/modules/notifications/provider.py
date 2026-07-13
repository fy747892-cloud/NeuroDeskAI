class MockEmailProvider:
    """Stands in for a real SMTP/transactional email provider (none configured yet)."""

    provider_name = "mock"

    async def send(self, *, to_email: str, title: str, body: str) -> None:
        if "[mock-fail]" in body.lower():
            raise RuntimeError("Mock email provider failed to send notification.")
