// Shopify / generic web checkout connector (example).
// Embed the Pinpoint widget and store the verified address code on the order.
//
// 1) Add a container + the widget script to your checkout/theme:
//      <div id="pinpoint-widget" data-api-key="pk_live_YOUR_PUBLISHABLE_KEY"></div>
//      <script src="https://api.pinpoint.ng/widget/widget.js"></script>
//
// 2) When the shopper picks an address, capture the token and attach it to the order
//    (here: a Shopify cart attribute; adapt to your platform).

document.getElementById("pinpoint-widget").addEventListener("pinpoint:selected", async (e) => {
  const code = e.detail.code; // verified address token

  // Example: persist as a Shopify cart attribute so it lands on the order.
  await fetch("/cart/update.js", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ attributes: { pinpoint_address_code: code } }),
  });

  // Or just drop it into a hidden form field:
  // document.querySelector('input[name="pinpoint_code"]').value = code;
});
