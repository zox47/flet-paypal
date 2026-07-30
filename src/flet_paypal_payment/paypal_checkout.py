from typing import Optional

import flet as ft

from flet_paypal_payment.types import (
    PaypalCheckoutOutcome,
    PaypalCheckoutResult,
    PaypalTransaction,
)

__all__ = ["PaypalCheckout"]


@ft.control("PaypalCheckout")
class PaypalCheckout(ft.DialogControl):
    """
    A control that opens PayPal's hosted checkout screen (sandbox or live) as
    a full-screen page and reports back whether the payment succeeded,
    failed, or was cancelled.

    This control renders nothing itself — add it to `page.overlay` and call
    [`checkout`][..] to push the checkout screen on top of the current page.

    Wraps the [`flutter_paypal_payment`](https://pub.dev/packages/flutter_paypal_payment)
    package.
    """

    client_id: str = ""
    """Your PayPal REST API Client ID (sandbox or live, matching
    [`sandbox_mode`][..])."""

    secret_key: str = ""
    """Your PayPal REST API Secret (sandbox or live, matching
    [`sandbox_mode`][..])."""

    sandbox_mode: bool = True
    """Whether to use PayPal's sandbox environment instead of live/production."""

    note: Optional[str] = None
    """Default note shown to the buyer (e.g. "Contact us with any questions
    about your order."). Can be overridden per-call via
    [`checkout`][..]'s `note` argument."""

    on_success: Optional[ft.ControlEventHandler["PaypalCheckout"]] = None
    """Fires when the buyer completes a payment.

    The [`data`][flet.Event.data] property of the event handler argument
    contains the raw payment response data from PayPal.
    """

    on_error: Optional[ft.ControlEventHandler["PaypalCheckout"]] = None
    """Fires when checkout fails with an error.

    The [`data`][flet.Event.data] property of the event handler argument
    contains the error message.
    """

    on_cancel: Optional[ft.ControlEventHandler["PaypalCheckout"]] = None
    """Fires when the buyer closes the checkout screen before completing
    payment."""

    async def checkout(
        self,
        transactions: list[PaypalTransaction],
        note: Optional[str] = None,
        timeout: float = 300,
    ) -> PaypalCheckoutResult:
        """
        Opens the PayPal checkout screen for the given transactions and waits
        for the buyer to complete, cancel, or fail the payment.

        Args:
            transactions: One or more [`PaypalTransaction`][flet_paypal_payment.PaypalTransaction]
                to charge. Most integrations pass exactly one.
            note: A note shown to the buyer for this checkout. Falls back to
                [`PaypalCheckout.note`][..] when omitted.
            timeout: The maximum amount of time (in seconds) to wait for the
                buyer to finish interacting with the checkout screen.

        Returns:
            A [`PaypalCheckoutResult`][flet_paypal_payment.PaypalCheckoutResult]
            describing the outcome.

        Raises:
            TimeoutError: If the request times out (the checkout screen is
                left open in this case).
        """
        r = await self._invoke_method(
            method_name="checkout",
            arguments={
                "client_id": self.client_id,
                "secret_key": self.secret_key,
                "sandbox_mode": self.sandbox_mode,
                "note": note if note is not None else self.note,
                "transactions": [t.to_payload() for t in transactions],
            },
            timeout=timeout,
        )
        outcome = PaypalCheckoutOutcome(r["outcome"])
        return PaypalCheckoutResult(
            outcome=outcome,
            data=r.get("data"),
            error=r.get("error"),
        )
