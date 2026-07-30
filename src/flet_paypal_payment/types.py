from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

__all__ = [
    "PaypalCheckoutOutcome",
    "PaypalCheckoutResult",
    "PaypalItem",
    "PaypalShippingAddress",
    "PaypalTransaction",
]


class PaypalCheckoutOutcome(Enum):
    """The outcome of a PayPal checkout attempt."""

    SUCCESS = "success"
    """The buyer completed the payment."""

    ERROR = "error"
    """The checkout failed with an error (declined, network issue, etc.)."""

    CANCELLED = "cancelled"
    """The buyer closed the checkout screen before finishing."""


@dataclass
class PaypalItem:
    """A single line item within a [`PaypalTransaction`][..]."""

    name: str
    """Name of the item."""

    quantity: int
    """Quantity of the item being purchased."""

    price: str
    """Unit price of the item, as a string (e.g. `"5"`, `"9.99"`)."""

    currency: str = "USD"
    """ISO currency code for the item price."""


@dataclass
class PaypalShippingAddress:
    """Optional shipping address attached to a [`PaypalTransaction`][..]."""

    recipient_name: Optional[str] = None
    line1: Optional[str] = None
    line2: Optional[str] = None
    city: Optional[str] = None
    country_code: Optional[str] = None
    postal_code: Optional[str] = None
    phone: Optional[str] = None
    state: Optional[str] = None


@dataclass
class PaypalTransaction:
    """
    Describes a single transaction to charge, matching the shape expected by
    the underlying `flutter_paypal_payment` package's `transactions` list.
    """

    total: str
    """Total amount of the transaction, as a string (e.g. `"70"`, `"19.99"`)."""

    description: str = ""
    """A short description of what is being purchased."""

    currency: str = "USD"
    """ISO currency code for the transaction."""

    subtotal: Optional[str] = None
    """Subtotal before shipping/discounts. Defaults to [`total`][..] if omitted."""

    shipping: str = "0"
    """Shipping cost, as a string."""

    shipping_discount: float = 0
    """Discount applied to shipping."""

    items: list[PaypalItem] = field(default_factory=list)
    """Line items included in this transaction."""

    shipping_address: Optional[PaypalShippingAddress] = None
    """Optional shipping address for this transaction."""

    def to_payload(self) -> dict[str, Any]:
        """Converts this transaction into the raw dict shape expected by Dart."""
        payload: dict[str, Any] = {
            "amount": {
                "total": self.total,
                "currency": self.currency,
                "details": {
                    "subtotal": self.subtotal
                    if self.subtotal is not None
                    else self.total,
                    "shipping": self.shipping,
                    "shipping_discount": self.shipping_discount,
                },
            },
            "description": self.description,
        }
        if self.items:
            item_list: dict[str, Any] = {
                "items": [
                    {
                        "name": i.name,
                        "quantity": i.quantity,
                        "price": i.price,
                        "currency": i.currency,
                    }
                    for i in self.items
                ]
            }
            if self.shipping_address is not None:
                a = self.shipping_address
                item_list["shipping_address"] = {
                    "recipient_name": a.recipient_name,
                    "line1": a.line1,
                    "line2": a.line2,
                    "city": a.city,
                    "country_code": a.country_code,
                    "postal_code": a.postal_code,
                    "phone": a.phone,
                    "state": a.state,
                }
            payload["item_list"] = item_list
        return payload


@dataclass
class PaypalCheckoutResult:
    """The result of a [`PaypalCheckout.checkout`][flet_paypal_payment.PaypalCheckout.checkout] call."""

    outcome: PaypalCheckoutOutcome
    """Whether the checkout succeeded, errored, or was cancelled."""

    data: Optional[dict[str, Any]] = None
    """
    Raw payment/response data from PayPal on success (the `params` map from
    the underlying package's `onSuccess` callback). `None` otherwise.
    """

    error: Optional[str] = None
    """Error message, only set when [`outcome`][..] is
    [`PaypalCheckoutOutcome.ERROR`][..]."""
