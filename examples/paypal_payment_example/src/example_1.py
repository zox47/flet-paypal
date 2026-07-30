import flet as ft

import flet_paypal_payment as ftp


@ft.component
def App(paypal: ftp.PaypalCheckout):
    result, set_result = ft.use_state(None)
    loading, set_loading = ft.use_state(False)

    async def handle_checkout(e: ft.Event[ft.Button]):
        set_loading(True)
        r = await paypal.checkout(
            transactions=[
                ftp.PaypalTransaction(
                    total="19.99",
                    currency="USD",
                    description="A really nice Flet t-shirt",
                    items=[
                        ftp.PaypalItem(
                            name="Flet T-Shirt", quantity=1, price="19.99"
                        ),
                    ],
                ),
            ],
        )
        set_loading(False)
        set_result(r)

    if loading:
        status = "Opening checkout..."
    elif result is None:
        status = ""
    elif result.outcome == ftp.PaypalCheckoutOutcome.SUCCESS:
        status = f"Payment successful! {result.data}"
    elif result.outcome == ftp.PaypalCheckoutOutcome.ERROR:
        status = f"Payment failed: {result.error}"
    else:
        status = "Checkout cancelled."

    return ft.Column(
        [
            ft.Text("Paypal Checkout Example", style=ft.TextThemeStyle.HEADLINE_SMALL),
            ft.Button(
                content="Buy for $19.99",
                on_click=handle_checkout,
                disabled=loading,
            ),
            ft.Text(status),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )


def main(page: ft.Page):
    page.title = "Paypal Checkout Example"
    page.scroll = ft.ScrollMode.ADAPTIVE
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    # PaypalCheckout renders nothing itself, so it just needs to be mounted
    # somewhere in the control tree - page.overlay is the usual place.
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
