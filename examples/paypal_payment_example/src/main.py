import json

import flet as ft

import flet_paypal_payment as ftp

PRODUCT_NAME = "Flet T-Shirt"
PRODUCT_PRICE = "19.99"
PRODUCT_CURRENCY = "USD"
PRODUCT_EMOJI = "\U0001F455"  # 👕


def _get(d: dict, *path: str):
    """Defensively walk a nested dict, returning None on any missing key."""
    cur = d
    for key in path:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(key)
    return cur


def _extract_receipt(data: dict) -> dict:
    """
    Best-effort extraction of human-friendly fields from PayPal's raw
    onSuccess payload. Exact field names aren't guaranteed across PayPal
    API versions, so every lookup is defensive and falls back to None -
    the raw response is always available too (see the "View raw response"
    expander in ReceiptCard).
    """
    transactions = data.get("transactions") or []
    first_txn = transactions[0] if transactions else {}
    first_name = _get(data, "payer", "payer_info", "first_name")
    last_name = _get(data, "payer", "payer_info", "last_name")
    return {
        "payment_id": data.get("id"),
        "state": data.get("state"),
        "payer_email": _get(data, "payer", "payer_info", "email"),
        "payer_name": " ".join(filter(None, [first_name, last_name])) or None,
        "amount": _get(first_txn, "amount", "total"),
        "currency": _get(first_txn, "amount", "currency"),
    }


@ft.component
def ReceiptRow(label: str, value):
    if value is None:
        return ft.Container(height=0)
    return ft.Row(
        [
            ft.Text(label, size=12, color=ft.Colors.GREY_600, width=90),
            ft.Text(
                str(value),
                size=13,
                weight=ft.FontWeight.W_600,
                selectable=True,
                expand=True,
            ),
        ],
        spacing=8,
    )


@ft.component
def ResultCard(
    icon,
    icon_color,
    accent_color,
    title: str,
    subtitle: str,
    reset,
    extra=None,
):
    """Shared shell for the success / error / cancelled result cards."""
    children = [
        ft.Row(
            [
                ft.Container(
                    content=ft.Icon(icon, color=icon_color, size=22),
                    bgcolor=ft.Colors.with_opacity(0.12, icon_color),
                    width=40,
                    height=40,
                    border_radius=100,
                    alignment=ft.Alignment.CENTER,
                ),
                ft.Column(
                    [
                        ft.Text(title, size=15, weight=ft.FontWeight.W_600),
                        ft.Text(subtitle, size=12, color=ft.Colors.GREY_600),
                    ],
                    spacing=2,
                    tight=True,
                ),
            ],
            spacing=12,
        ),
    ]
    if extra is not None:
        children.append(extra)
    children.append(
        ft.OutlinedButton(
            content=ft.Text("Buy again"),
            on_click=lambda e: reset(),
        )
    )

    return ft.Container(
        content=ft.Column(children, spacing=14),
        bgcolor=ft.Colors.WHITE,
        border=ft.Border(left=ft.BorderSide(width=4, color=accent_color)),
        border_radius=14,
        padding=18,
        width=340,
    )


@ft.component
def SuccessCard(result, reset):
    receipt = _extract_receipt(result.data or {})
    raw_json = json.dumps(result.data or {}, indent=2, default=str)

    return ResultCard(
        icon=ft.Icons.CHECK_CIRCLE,
        icon_color=ft.Colors.GREEN_600,
        accent_color=ft.Colors.GREEN_600,
        title="Payment successful",
        subtitle="Thanks for your order!",
        reset=reset,
        extra=ft.Column(
            [
                ReceiptRow("Payment ID", receipt["payment_id"]),
                ReceiptRow("Status", receipt["state"]),
                ReceiptRow("Payer", receipt["payer_name"]),
                ReceiptRow("Email", receipt["payer_email"]),
                ReceiptRow(
                    "Amount",
                    f"{receipt['amount']} {receipt['currency']}"
                    if receipt["amount"]
                    else None,
                ),
                ft.ExpansionTile(
                    title=ft.Text("View raw response", size=12),
                    tile_padding=ft.Padding.symmetric(horizontal=0),
                    controls=[
                        ft.Container(
                            content=ft.Text(
                                raw_json,
                                size=11,
                                font_family="monospace",
                                selectable=True,
                            ),
                            bgcolor=ft.Colors.GREY_100,
                            border_radius=8,
                            padding=10,
                        ),
                    ],
                ),
            ],
            spacing=6,
        ),
    )


@ft.component
def ErrorCard(result, reset):
    return ResultCard(
        icon=ft.Icons.ERROR_OUTLINE,
        icon_color=ft.Colors.RED_600,
        accent_color=ft.Colors.RED_600,
        title="Payment failed",
        subtitle=result.error or "Something went wrong.",
        reset=reset,
    )


@ft.component
def CancelledCard(reset):
    return ResultCard(
        icon=ft.Icons.CANCEL_OUTLINED,
        icon_color=ft.Colors.GREY_600,
        accent_color=ft.Colors.GREY_400,
        title="Checkout cancelled",
        subtitle="No charge was made.",
        reset=reset,
    )


@ft.component
def ResultPanel(state: str, result, reset):
    """Loading spinner while checking out, then a result card once done."""
    if state == "loading":
        return ft.Row(
            [
                ft.ProgressRing(width=18, height=18, stroke_width=2, color=ft.Colors.WHITE),
                ft.Text("Opening PayPal checkout...", color=ft.Colors.WHITE),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10,
        )

    if state == "success":
        return SuccessCard(result, reset)

    if state == "error":
        return ErrorCard(result, reset)

    if state == "cancelled":
        return CancelledCard(reset)

    return ft.Container(height=0)  # idle


@ft.component
def App(paypal: ftp.PaypalCheckout):
    # state can be: "idle" | "loading" | "success" | "error" | "cancelled"
    state, set_state = ft.use_state("idle")
    result, set_result = ft.use_state(None)

    def reset():
        set_state("idle")
        set_result(None)

    async def buy(e: ft.Event[ft.Button]):
        set_state("loading")
        set_result(None)
        r = await paypal.checkout(
            transactions=[
                ftp.PaypalTransaction(
                    total=PRODUCT_PRICE,
                    currency=PRODUCT_CURRENCY,
                    description=f"A really nice {PRODUCT_NAME}",
                    items=[
                        ftp.PaypalItem(
                            name=PRODUCT_NAME, quantity=1, price=PRODUCT_PRICE
                        ),
                    ],
                ),
            ],
        )
        set_result(r)
        set_state(r.outcome.value)  # "success" | "error" | "cancelled"

    is_busy = state == "loading"
    is_done = state in ("success", "error", "cancelled")

    product_card = ft.Container(
        content=ft.Column(
            [
                ft.Container(
                    content=ft.Text(PRODUCT_EMOJI, size=56),
                    alignment=ft.Alignment.CENTER,
                    width=96,
                    height=96,
                    bgcolor=ft.Colors.with_opacity(0.08, ft.Colors.BLACK),
                    border_radius=20,
                ),
                ft.Text(PRODUCT_NAME, size=18, weight=ft.FontWeight.W_600),
                ft.Text(
                    "Soft, breathable, and printed with the Flet logo.",
                    size=13,
                    color=ft.Colors.GREY_600,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Divider(height=24, color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK)),
                ft.Row(
                    [
                        ft.Text("Total", size=13, color=ft.Colors.GREY_600),
                        ft.Text(
                            f"${PRODUCT_PRICE}",
                            size=22,
                            weight=ft.FontWeight.BOLD,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
        ),
        bgcolor=ft.Colors.WHITE,
        border_radius=20,
        padding=24,
        shadow=ft.BoxShadow(
            blur_radius=24,
            spread_radius=0,
            color=ft.Colors.with_opacity(0.12, ft.Colors.BLACK),
            offset=ft.Offset(0, 8),
        ),
        width=340,
    )

    buy_button = ft.Container(
        content=ft.Button(
            content=ft.Row(
                [
                    ft.ProgressRing(width=16, height=16, stroke_width=2, color=ft.Colors.WHITE)
                    if is_busy
                    else ft.Icon(ft.Icons.LOCK_OUTLINE, size=16, color=ft.Colors.WHITE),
                    ft.Text(
                        "Processing..." if is_busy else f"Pay ${PRODUCT_PRICE} with PayPal",
                        weight=ft.FontWeight.W_600,
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=8,
                tight=True,
            ),
            on_click=buy,
            disabled=is_busy,
            bgcolor=ft.Colors.BLUE_900,
            color=ft.Colors.WHITE,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=12),
                padding=ft.Padding.symmetric(vertical=16, horizontal=16),
            ),
            width=340,
        ),
        visible=not is_done,  # hide the buy button once a result card is showing
    )

    return ft.Container(
        content=ft.Column(
            [
                ft.Column(
                    [
                        ft.Text(
                            "Paypal Checkout Example",
                            size=24,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.WHITE,
                        ),
                        ft.Container(
                            content=ft.Row(
                                [
                                    ft.Icon(
                                        ft.Icons.SCIENCE_OUTLINED,
                                        size=14,
                                        color=ft.Colors.AMBER_200,
                                    ),
                                    ft.Text(
                                        "Sandbox mode — no real charge",
                                        size=12,
                                        color=ft.Colors.AMBER_200,
                                    ),
                                ],
                                spacing=6,
                                tight=True,
                            ),
                            bgcolor=ft.Colors.with_opacity(0.15, ft.Colors.AMBER),
                            padding=ft.Padding.symmetric(vertical=6, horizontal=12),
                            border_radius=100,
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=10,
                ),
                product_card if not is_done else ft.Container(height=0),
                buy_button,
                ResultPanel(state, result, reset),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=24,
        ),
        expand=True,
        alignment=ft.Alignment.CENTER,
        padding=32,
        gradient=ft.LinearGradient(
            begin=ft.Alignment.TOP_CENTER,
            end=ft.Alignment.BOTTOM_CENTER,
            colors=[ft.Colors.BLUE_900, ft.Colors.INDIGO_900],
        ),
    )


def main(page: ft.Page):
    page.title = "Paypal Checkout Example"
    page.padding = 0
    page.theme_mode = ft.ThemeMode.LIGHT

    # PaypalCheckout renders nothing itself — it just needs to be mounted
    # somewhere in the control tree. page.overlay is the usual place.
    paypal = ftp.PaypalCheckout(
        # Replace with your own PayPal REST API sandbox app credentials:
        # https://developer.paypal.com/dashboard/applications/sandbox
        client_id="YOUR_SANDBOX_CLIENT_ID",
        secret_key="YOUR_SANDBOX_SECRET_KEY",
        sandbox_mode=True,
        note="Contact us for any questions about your order.",
    )
    page.overlay.append(paypal)

    page.render(App, paypal)


ft.run(main)
