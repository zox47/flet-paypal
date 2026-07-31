import 'dart:async';

import 'package:flet/flet.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_paypal_payment/flutter_paypal_payment.dart';

/// Flutter counterpart of the Python `PaypalCheckout` control.
///
/// This is a [DialogControl][flet.dev]-style control: it does not occupy any
/// space in the layout (it always builds to [SizedBox.shrink]). Instead, it
/// listens for an invoked `checkout` method call and, when one arrives,
/// pushes PayPal's [PaypalCheckoutView] as a full-screen route on top of the
/// current page using its own [BuildContext].
class PaypalCheckoutControl extends StatefulWidget {
  final Control control;

  const PaypalCheckoutControl({super.key, required this.control});

  @override
  State<PaypalCheckoutControl> createState() => _PaypalCheckoutControlState();
}

class _PaypalCheckoutControlState extends State<PaypalCheckoutControl> {
  @override
  void initState() {
    super.initState();
    widget.control.addInvokeMethodListener(_invokeMethod);
  }

  Future<dynamic> _invokeMethod(String name, dynamic args) async {
    debugPrint("PaypalCheckout.$name($args)");
    switch (name) {
      case "checkout":
        return await _openCheckout(Map<String, dynamic>.from(args ?? {}));
      default:
        throw Exception("Unknown PaypalCheckout method: $name");
    }
  }

  Future<Map<String, dynamic>> _openCheckout(
      Map<String, dynamic> args) async {
    final completer = Completer<Map<String, dynamic>>();

    void complete(Map<String, dynamic> result) {
      if (!completer.isCompleted) {
        completer.complete(result);
      }
    }

    final transactions = ((args["transactions"] as List?) ?? [])
        .map((t) => Map<String, dynamic>.from(t as Map))
        .toList();

    if (!mounted) {
      return {"outcome": "error", "error": "PaypalCheckout is not mounted"};
    }

    await Navigator.of(context).push(MaterialPageRoute(
      builder: (routeContext) {
        // flutter_paypal_payment detects cancellation by watching for a
        // specific redirect URL inside its internal WebView. That
        // detection doesn't always fire (URL pattern mismatches, locale
        // differences, PayPal UI changes), which leaves the buyer stuck on
        // a spinner with no way out. To guarantee an exit regardless of
        // what the WebView is doing internally, we add our own always-
        // visible close button and intercept the hardware back button.
        void cancelAndClose() {
          widget.control.triggerEvent("cancel", null);
          complete({"outcome": "cancelled"});
          if (routeContext.mounted && Navigator.of(routeContext).canPop()) {
            Navigator.of(routeContext).pop();
          }
        }

        return PopScope(
          canPop: false,
          onPopInvokedWithResult: (didPop, result) {
            if (!didPop) cancelAndClose();
          },
          child: Stack(
            children: [
              PaypalCheckoutView(
                sandboxMode: (args["sandbox_mode"] as bool?) ?? true,
                clientId: (args["client_id"] as String?) ?? "",
                secretKey: (args["secret_key"] as String?) ?? "",
                transactions: transactions,
                note: args["note"] as String?,
                onSuccess: (Map params) async {
                  final data = Map<String, dynamic>.from(params);
                  widget.control.triggerEvent("success", data);
                  complete({"outcome": "success", "data": data});
                  if (routeContext.mounted &&
                      Navigator.of(routeContext).canPop()) {
                    Navigator.of(routeContext).pop();
                  }
                },
                onError: (error) {
                  final message = error.toString();
                  widget.control.triggerEvent("error", message);
                  complete({"outcome": "error", "error": message});
                  if (routeContext.mounted &&
                      Navigator.of(routeContext).canPop()) {
                    Navigator.of(routeContext).pop();
                  }
                },
                onCancel: cancelAndClose,
              ),
              // Manual escape hatch: always on top, always tappable, works
              // even if the checkout view underneath is stuck.
              SafeArea(
                child: Align(
                  alignment: Alignment.topRight,
                  child: Padding(
                    padding: const EdgeInsets.all(8.0),
                    child: Material(
                      color: Colors.black54,
                      shape: const CircleBorder(),
                      child: IconButton(
                        icon: const Icon(Icons.close, color: Colors.white),
                        tooltip: "Cancel",
                        onPressed: cancelAndClose,
                      ),
                    ),
                  ),
                ),
              ),
            ],
          ),
        );
      },
    ));

    // Safety net: if the view was popped some other way without any of the
    // callbacks firing, treat it as a cancel rather than hanging the
    // Python-side await forever.
    complete({"outcome": "cancelled"});

    return completer.future;
  }

  @override
  void dispose() {
    widget.control.removeInvokeMethodListener(_invokeMethod);
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    // Non-visual (dialog-style) control: it occupies no space itself, it
    // only pushes a route on demand.
    return const SizedBox.shrink();
  }
}
