---
title: Schema
sidebar_label: Schema
description: "Capability input_schema and output_schema: which one Runtime binds on LLM stages, and what the catalogue only documents."
---

# Schema

JSON Schema on a capability is the contract for what goes in and what comes out. Control Plane shows it at `/capabilities/{id}`. Runtime binds `output_schema` on LLM stages (`classify`, `synthesis`, `query_formulation`) through `with_structured_output`. HTTP `none` stages do not bind either schema today.

| Field | Who uses it | When it is real |
| --- | --- | --- |
| `output_schema` | LLM structured output on classify / synthesis / query_formulation | Bound and validated in `agent-runtime/app/graph/llm/schema.py` |
| `input_schema` | HTTP tool request body (later: hop validation) | Catalogue and UI today. Runtime does not validate HTTP against it yet. See [data](/concepts/executing-a-request/run-data) |

For an extraction / classify stage, put the extraction contract on **`output_schema`**, not `input_schema`. The same keywords can live on `input_schema` to document a domain HTTP body.

Seed example: [`extract_fields`](http://localhost:3006/capabilities/extract_fields) (`purchase_refund` classify). Frozen copy: [`capability-extract-fields.json`](/fixtures/capability-extract-fields.json).

## Bindable `output_schema`

The schema must be a **flat object** with a non-empty `properties`. Each property is one of:

- a primitive: `string`, `number`, `integer`, `boolean`
- that primitive plus `null`: `"type": ["string", "null"]`
- a closed `enum` of strings (or numbers / booleans)
- an **array of primitives** (`"items": { "type": "string" }`)

Empty `{ "type": "object" }`, nested objects, arrays of objects, `$ref`, and `oneOf` are **not** bindable. The stage then stays free-form (no field descriptions, no validation).

## Keywords Runtime honors

| Keyword | Where | Effect |
| --- | --- | --- |
| `description` | object and each property | Sent to the model. Write extraction rules here, not labels. |
| `required` | object | Key must be present on the completion. |
| `type` | property | Primitive, `null` union, or `array`. |
| `enum` | property | Closed set. Invalid values fail validation. |
| `minLength` / `maxLength` | string | Rejects `""` (`minLength: 1`) and caps length. |
| `pattern` | string | Regex (use this instead of `format: date`). |
| `minimum` / `maximum` | number / integer | Inclusive bounds. |
| `items` | array | Must be a primitive (and may have its own `enum`). |

`examples`, `title`, `default`, `const`, `format`, `exclusiveMinimum`, `additionalProperties` can sit in catalogue JSON (the UI will show them) but Runtime does not map them onto the Pydantic model.

## Required + null (do not invent)

Put every extraction key in `required`, and use `"type": ["string", "null"]` (or number/null) when the source may not contain the value:

```json
"order_id": {
  "type": ["string", "null"],
  "description": "The order ID provided by the customer, or null if missing."
}
```

The model must **emit the key**. `null` means “not in the notes.” That is stricter than omitting the key, and it stops the model from inventing a value to satisfy `required`.

| Intent | Schema |
| --- | --- |
| Always present, never null | `"type": "string"` and listed in `required` |
| Always emit the key; null if unknown | `"type": ["string", "null"]` and listed in `required` |
| May omit the key entirely | Leave it out of `required` |

Do not put `"null"` in `type` *and* leave the key out of `required` unless omission is what you want. `"null"` in `type` plus `required` is the extraction default.

## Closed sets (`enum`)

Use `enum` for reasons, actions, urgency, currency — anything that must not be free text:

```json
"reason": {
  "type": "string",
  "enum": [
    "damaged_item",
    "wrong_item",
    "changed_mind",
    "billing_dispute",
    "policy_exception",
    "unclear",
    "other"
  ]
}
```

Keep an `unclear` / `other` value so the model has a legal escape. Pair `other` with a nullable `reason_details` string.

## Arrays, booleans, confidence, review

These are bindable when they stay flat:

```json
"missing_information": {
  "type": "array",
  "items": { "type": "string" },
  "description": "Keys that are null or too unclear to extract. Empty array if complete."
},
"evidence_provided": {
  "type": "boolean",
  "description": "Whether the customer provided evidence such as a photo or attachment."
},
"confidence": {
  "type": "number",
  "minimum": 0,
  "maximum": 1,
  "description": "Confidence score from 0 to 1 for the extraction."
},
"human_review_required": { "type": "boolean" },
"human_review_reason": {
  "type": ["string", "null"],
  "description": "Why review is required, or null when human_review_required is false."
}
```

List every one of those keys in `required`. `missing_information` is `[]` when nothing is missing, not `null`.

## Intake extraction (pattern)

Same shape as a return / refund intake classifier. Use this on **`output_schema`** of a classify capability:

```json
{
  "type": "object",
  "description": "Return intake extraction. Always emit every required key. Use null when missing; do not invent.",
  "required": [
    "order_id",
    "item",
    "reason",
    "reason_details",
    "desired_action",
    "evidence_provided",
    "urgency",
    "missing_information",
    "confidence",
    "human_review_required",
    "human_review_reason"
  ],
  "properties": {
    "order_id": {
      "type": ["string", "null"],
      "description": "The order ID provided by the customer, or null if missing."
    },
    "item": {
      "type": ["string", "null"],
      "description": "The item the customer wants to return, or null if missing."
    },
    "reason": {
      "type": "string",
      "enum": [
        "damaged_item",
        "wrong_item",
        "changed_mind",
        "billing_dispute",
        "policy_exception",
        "unclear",
        "other"
      ]
    },
    "reason_details": {
      "type": ["string", "null"],
      "description": "Additional details when reason is other or unclear."
    },
    "desired_action": {
      "type": "string",
      "enum": ["return", "refund", "exchange", "replacement", "unclear"]
    },
    "evidence_provided": {
      "type": "boolean",
      "description": "Whether the customer provided evidence such as a photo or attachment."
    },
    "urgency": {
      "type": "string",
      "enum": ["low", "normal", "high"]
    },
    "missing_information": {
      "type": "array",
      "items": { "type": "string" }
    },
    "confidence": {
      "type": "number",
      "minimum": 0,
      "maximum": 1,
      "description": "Confidence score from 0 to 1 for the extraction."
    },
    "human_review_required": { "type": "boolean" },
    "human_review_reason": { "type": ["string", "null"] }
  }
}
```

`extract_fields` in seed is this pattern applied to a receipt (nullable merchant/amount/date, currency `enum`, `missing_information`, `confidence`, human review).

## Prompt pack vs schema

| Lives in | Role |
| --- | --- |
| `output_schema` | Shape, nullability, enums, bounds |
| classify / synthesis `text` | How to read goal and notes (“use OCR only”) |

Do not duplicate the key list in the prompt when the schema already names them. See [prompts](/concepts/authoring-a-product/prompts).

## What is not built

- Nested objects / arrays of objects on LLM `output_schema` (not bindable).
- Validating HTTP bodies against `input_schema` (dataflow D4a).
- Route `output_schema_id` (pointer only; the capability schema is what binds).
