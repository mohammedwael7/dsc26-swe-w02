# C2 · From vague prompt to spec

### 1. Vague prompt and output

**Prompt (fresh ChatGPT chat, verbatim):**

> Write an API endpoint that lets a courier mark an order as delivered.

**Output (trimmed; `[...]` marks omitted content):**

> A good mark as delivered endpoint should verify that the authenticated user is assigned as the courier for the order, ensure the order is eligible for delivery, and update its status safely.
>
> Here’s a REST API implementation using Node.js, Express, TypeScript, and PostgreSQL.
>
> Method: PATCH; URL: `/api/orders/:orderId/delivered`; Authentication: Required (courier); Success: 200 OK.
>
> Assume the orders table contains `id`, `courier_id`, `status`, and `delivered_at`, and authentication middleware attaches the verified courier's ID to `req.user.id`.
>
> `if (order.status === "delivered")` returns 200 with “Order already delivered”.
>
> `if (order.status !== "out_for_delivery")` returns 409.
>
> `UPDATE orders SET status = 'delivered', delivered_at = NOW()`
>
> “For production, consider recording the courier, timestamp, and delivery confirmation evidence in an audit log.”
>
> [...] The output also includes example responses and concurrency notes.

### 2. Diagnosis (problem → prompt gap)

- It chose Node.js/Express/TypeScript/PostgreSQL, while Tawseel's project uses Python 3.12 and FastAPI → **missing context and constraints**.
- It treats delivery evidence as an optional audit-log idea and never defines cash-on-delivery collection → **missing business rules and request fields**.
- It chose a new order route and made repeat delivery return 200, without defining how this endpoint fits the parcel event API or what repeated delivery means → **ambiguous contract and no success criteria**.

### 3. Success criteria and tests

1. Use the existing `POST /v1/parcels/{parcel_id}/events` contract with `type: "deliver"`.
2. Only the authenticated courier assigned to the parcel may deliver it; another courier gets 403 and no mutation.
3. Only `out_for_delivery` may transition; a repeated delivery gets 409 and preserves the original proof and timestamp.
4. Require recipient name and photo proof ID; collected COD must equal the parcel COD amount in piastres.
5. Success is 200 and returns delivered state, proof fields, and a server timestamp.
6. Unknown parcel is 404; invalid or missing fields are 422 problem documents; errors never mutate the parcel.

Tests: assigned courier, `out_for_delivery`, COD 500 and collected 500, valid proof → 200; wrong courier → 403 unchanged; already delivered → 409 with original proof/time unchanged; missing recipient name → 422 problem document; **edge case:** COD 0 and collected 0 with valid proof → 200.

### 4. My specification prompt

> Goal: Specify a contract-first FastAPI endpoint for a Tawseel courier to mark a parcel delivered. Do not write implementation code.
>
> Context: Python 3.12, FastAPI. The existing API has `POST /v1/parcels/{parcel_id}/events` with `{"type":"deliver"}`; Parcel has `id`, `cod_amount_piastres`, and `state`.
>
> Assumptions: trusted authentication middleware supplies `courier_id`; each parcel has `assigned_courier_id`; only `out_for_delivery` parcels can be delivered. Delivery proof is `recipient_name` plus `proof_photo_id`. For COD, `cod_collected_piastres` must exactly equal `cod_amount_piastres` (zero when COD is zero). State and proof are persisted together.
>
> Specify request fields, auth rule, state rule, success response, and error responses. Unknown parcel=404; wrong courier=403; wrong state including repeated delivery=409; invalid/missing proof or COD amount=422. Every error is `application/problem+json` with type, title, status; errors never mutate the parcel. Success=200 and includes the parcel, delivered state, server timestamp, and proof fields. Tests: give at least four input-to-expected-status cases, including one edge case. Output exactly two sections: (1) Contract table, (2) Test cases. Call out assumptions that must be checked with the client.

### 5. New output

**Output (fresh ChatGPT chat; trimmed):**

> **Contract table**
>
> Endpoint: `POST /v1/parcels/{parcel_id}/events`; body includes `type: "deliver"`, non-empty `recipient_name`, valid `proof_photo_id`, and non-negative integer `cod_collected_piastres`.
>
> Authentication: use trusted middleware's courier ID; do not accept it from the body. Authorization: `assigned_courier_id` must match or return 403.
>
> State: parcel must be `out_for_delivery`; any other state, including `delivered`, returns 409. COD collected must exactly equal `cod_amount_piastres`.
>
> Success: 200 with updated parcel, `state: "delivered"`, server-generated ISO 8601 `delivered_at`, recipient, photo ID, and COD amounts. Persist state and proof atomically.
>
> Errors: unknown parcel 404; wrong courier 403; wrong state 409; invalid request/proof/COD 422. All use `application/problem+json` with `type`, `title`, and matching `status`; all leave state and proof unchanged.
>
> **Test cases**
>
> Assigned courier + valid proof + COD 500/500 → 200, delivered with timestamp.
>
> Wrong courier → 403, parcel unchanged. Already delivered → 409, original proof/time unchanged.
>
> Missing recipient → 422, no mutation. **Edge:** COD 0, collected 0, valid proof → 200.
>
> [...] The output also calls out assumptions about proof-photo association, recipient rules, canonical problem types, and concurrent requests.

### 6. Check against criteria (criterion → pass/fail → evidence)

- Route and event contract → **Pass** → output names `POST /v1/parcels/{parcel_id}/events` and `type: "deliver"`.
- Assigned-courier authorization → **Pass** → it requires matching `assigned_courier_id`, otherwise 403.
- State and repeat behavior → **Pass** → only `out_for_delivery`; repeated delivery returns 409 without changing proof/time.
- Proof and COD → **Pass** → requires recipient/photo and exact COD match.
- Successful response → **Pass** → 200 includes delivered state and server timestamp.
- Error contract → **Pass** → 404/403/409/422 problem documents; errors leave the parcel unchanged.
- Test cases → **Pass** → five cases specify inputs and expected results, including zero-COD edge case.

### 7. What still fails

This is a contract proposal, not implemented code. The current parcel model does not yet store courier assignment or delivery proof, and the API has no authentication middleware. I would first confirm the identity source, photo ownership check, and delivery fields with the client, then add them with tests before exposing delivery through the endpoint.
