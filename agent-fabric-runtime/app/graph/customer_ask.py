from typing import Any


class CustomerAskWaiting(Exception):
    """Raised when Pattern 1 ASK needs a customer locator before the next CALL."""

    def __init__(
        self,
        *,
        message: str,
        step: int,
        resume_loop_step: int,
        state: dict[str, Any],
    ) -> None:
        self.stage_id = "customer_ask"
        self.gate_index = step
        self.resume_index = step
        self.resume_loop_step = resume_loop_step
        self.state = state
        self.message = message
        super().__init__("customer_ask waiting for locator")
