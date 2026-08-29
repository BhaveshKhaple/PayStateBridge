# India Payment Domain Primer — PayState Bridge

**Purpose:** Learn the payment domain before writing code. This is educational project context, not legal or financial advice. Re-check primary sources before publication because app flows and RBI/NPCI rules can change.

## 1. The payment path in simple language

A UPI payment can look instant to a customer but contains several separate systems:

```text
Customer
  → TPAP / payment app (PhonePe, Google Pay, bank app)
  → PSP / remitter bank
  → NPCI UPI rail
  → beneficiary / acquiring bank
  → payment gateway (where used)
  → merchant payment and order systems
```

### Important terms

| Term | Plain meaning |
|---|---|
| TPAP | Third-party app provider: an app such as PhonePe or Google Pay. |
| PSP bank | Bank that connects the customer/app to UPI services. |
| Remitter | Person/bank sending money. |
| Beneficiary | Person/merchant/bank receiving money. |
| UTR / RRN | Transaction reference used to trace payment. Exact format and naming can vary by rail/provider. |
| Payment gateway | Merchant-side payment infrastructure such as Razorpay. |
| Merchant order system | The merchant database that decides whether to fulfil an order. |
| Reversal | A system returns money because a payment failed or could not complete. |
| Refund | Merchant returns money after a successful payment/order. |
| Chargeback/dispute | Formal bank/payment dispute process; not a normal merchant refund. |

## 2. The cases customers often confuse

Do not treat every debit as the same problem.

| Customer statement | Actual category | Who can act | What PayState Bridge may do |
|---|---|---|---|
| “My money was debited but recipient/merchant did not get it.” | Failed/pending technical transaction | Banks/rail/app follow reversal process | Stop retry, reconcile merchant/gateway evidence, explain verified next state. |
| “I paid again because first payment looked stuck.” | Potential duplicate payment | Merchant + gateway + bank/app depending on final state | Detect duplicate success, recover one captured payment/order, open refund-review case. |
| “I sent money to the wrong UPI ID.” | Successful wrong-recipient transfer | Recipient consent, banks, NPCI complaint route | Produce evidence packet and official route. Never promise reversal. |
| “I do not recognize this transaction.” | Unauthorized/fraud allegation | Bank, app, cybercrime process | Stop normal recovery flow; route to human/bank/cyber escalation. |
| “Merchant received money but I have no order.” | Captured-unlinked merchant payment | Merchant/gateway | Link payment to order or issue order confirmation. |
| “Merchant says no payment, but app says success.” | Evidence conflict | Merchant/gateway/bank/app | Mark outcome unknown; do not ask customer to pay again until reconciled. |

## 3. Official resolution rules relevant to the prototype

### RBI failed-transaction framework

RBI’s TAT framework distinguishes UPI failure situations. Current official material states:

- For **account debited but beneficiary not credited** in UPI fund transfer, auto-reversal is expected by the beneficiary bank no later than **T+1 day**.
- For **account debited but merchant confirmation not received**, the UPI merchant-payment scenario has an outer reversal timeline of **T+5 days**.
- The RBI material states ₹100/day compensation for delay beyond applicable timeline in the listed failed-transaction cases, and says compensation should be made suo moto where applicable.

**Source:** [RBI TAT / compensation framework](https://www.rbi.org.in/commonman/English/scripts/Notification.aspx?Id=3074)

### Do not overgeneralize TAT

- App help pages can show different user-facing wait periods because they describe their own workflow or when a ticket becomes available.
- A successful wrong-recipient transfer is not equivalent to a failed technical transaction and is not automatically reversible.
- The prototype must display an evidence-based suggested route, not make legal eligibility claims.

### UPI complaint escalation order

NPCI’s UPI dispute mechanism says an end user first raises a complaint in the relevant TPAP/PSP app. If unresolved, escalation proceeds through PSP bank, then the bank holding the user account, then NPCI; after those options, the customer can approach the relevant ombudsman channel.

**Source:** [NPCI UPI dispute mechanism](https://www.npci.org.in/what-we-do/upi/dispute-redressal-mechanism) (the official site may intermittently error; the current mechanism is reflected in NPCI guidance/search results).

### RBI CMS / Ombudsman

RBI’s current Integrated Ombudsman Scheme, 2026 describes CMS as a central portal for eligible unresolved complaints against covered regulated entities. It is an escalation route, not an instant transaction reversal service.

**Sources:** [RBI complaint portal](https://cms.rbi.org.in/) · [RB-IOS 2026 FAQ](https://www.rbi.org.in/commonman/English/Scripts/FAQs.aspx?Id=3407)

## 4. App and gateway facts

### Google Pay

Google Pay tells customers not to repeat a merchant payment while it is processing. Its help flow differentiates successful, processing, and failed states. For debit/no merchant credit or unresolved cases it directs the user through bank, in-app ticket, and NPCI routes.

**Source:** [Google Pay merchant-payment help](https://support.google.com/pay/india/answer/9494510?hl=en)

### PhonePe

PhonePe says a wrong successful transfer is challenging to reverse because recipient consent is required. For pending transactions, it instructs users to report in app, wait for the bank to update final state, and use UTR while escalating.

**Source:** [PhonePe pending/wrong-transfer guidance](https://www.phonepe.com/blog/trust-and-safety/how-to-reverse-upi-payments-when-money-is-wrongly-transferred-or-is-in-pending-status/)

### NPCI UPI Help

NPCI runs UPI Help, currently presenting payment Q&A, transaction status/grievance support, and mandate management. This means **PayState Bridge must not be positioned as a replacement consumer complaint portal**.

**Source:** [UPI Help](https://upihelp.npci.org.in/)

### Razorpay

Razorpay Payment Links can be created, fetched, cancelled, and verified by callback/webhook. Its customer refund guidance says Razorpay cannot make refunds on behalf of a business; customers should contact the business, then use dispute/bank paths if necessary. For duplicate transactions, Razorpay tells customers to contact the seller with transaction details.

**Sources:** [Payment Link APIs](https://razorpay.com/docs/payments/payment-links/apis/) · [Customer refunds](https://razorpay.com/docs/payments/customers/customer-refunds/)

## 5. What the prototype is allowed to claim

### Safe claims

- “This case is classified from available merchant-side and synthetic evidence.”
- “Do not issue a replacement link while original payment outcome is unresolved.”
- “This merchant-side workflow can reconcile a captured gateway payment to an unlinked order.”
- “This packet prepares order/payment references and suggested official escalation route.”
- “This is a Test Mode / simulated demonstration.”

### Claims the prototype must never make

- “We can see your PhonePe, Google Pay, NPCI, or bank transaction status live.”
- “We can reverse UPI funds.”
- “We guarantee refund or recovery.”
- “We file NPCI/RBI/bank complaints for you.”
- “We are approved by NPCI/RBI or connected to a bank switch.”
- “A screenshot proves bank settlement.”

## 6. Design implication

The customer has a real grievance-navigation problem. The merchant has a narrower, buildable problem:

> **Before asking the buyer to pay again, use the merchant’s own order/gateway evidence to decide whether retry is safe.**

PayState Bridge starts there. It does not impersonate a regulated grievance platform.
