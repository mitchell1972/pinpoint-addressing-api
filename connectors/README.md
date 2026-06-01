# Pinpoint connector kits

Example glue for common stacks. These are starting points, not installable plugins —
copy and adapt. All of them ultimately call the same `/v1` API (see the Python SDK in
`../clients/python/` for the canonical shapes).

| File | Platform | What it shows |
|------|----------|---------------|
| `shopify-checkout.js` | Shopify / any web checkout | Embed the checkout widget; capture the verified token on the order |
| `woocommerce.php` | WooCommerce (PHP) | Validate the delivery address server-side at checkout |
| `paystack_webhook.py` | Paystack (webhook) | On `charge.success`, verify the buyer's delivery address (KYC) |

Two integration patterns:
- **Front-end**: drop in the checkout widget (`/widget/widget.js`); it returns a verified
  address code you store on the order.
- **Back-end**: call `/v1/geocode`, `/v1/verify`, etc. with a server key (use the SDK).
