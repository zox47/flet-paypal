import 'package:flet/flet.dart';
import 'package:flutter/widgets.dart';

import 'paypal_checkout.dart';

class Extension extends FletExtension {
  @override
  Widget? createWidget(Key? key, Control control) {
    switch (control.type) {
      case "PaypalCheckout":
        return PaypalCheckoutControl(key: key, control: control);
      default:
        return null;
    }
  }
}
