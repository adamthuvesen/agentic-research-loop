# Stripe (read-only)

**Server:** official Stripe MCP server
([`@stripe/mcp`](https://github.com/stripe/agent-toolkit)) — local stdio via npx.
(A hosted OAuth endpoint `https://mcp.stripe.com` also exists.)

**Read-only enforcement (`scope:restricted-key-read` — credential-enforced at the
API):** read-only is provable here, like PostHog. Create a Stripe **Restricted API
Key (`rk_…`)** with **Read** permission (and **None** for write) on the resources you
need (subscriptions, invoices, payment intents, customers, disputes, …). Stripe's API
rejects every write from it with a 403, regardless of what tools the server exposes.

**Warning — the server ships write tools** (`create_refund`, `cancel_subscription`,
`create_invoice`, `create_payment_link`) that move money / change billing. The
restricted read-only key is what neutralizes them — **never use a secret key (`sk_`)
or a write-scoped key.**

## Enable

1. `uv run research source enable stripe` (or merge the bundle by hand).
2. Export the restricted read-only key via your environment (never committed config):
   ```bash
   export STRIPE_SECRET_KEY="$(op read 'op://vault/stripe-readonly/rk')"
   ```

## Notes

- Covers subscriptions, invoices, payment intents, customers, disputes, prices,
  products, balance, and resource search.
- Defense in depth: you can also pin `--tools` to read tools (e.g.
  `--tools=customers.read,invoices.read,subscriptions.read`) in the snippet.
