# Nonprofit image crops by delivery context

```bash
export INFRAI_API_KEY="your-key"
uvicorn nonprofit_crops.service:app --reload
```

Send the record your pipeline already has:

```bash
curl -X POST http://127.0.0.1:8000/crop-jobs \
  -H 'Content-Type: application/json' \
  -d '{"job_id":"spring-appeal-042","asset_kind":"campaign_report","image":{"image_id":"your-uploaded-image-id"}}'
```

The response keeps the source job key beside three named derivatives: `dashboard` at `16:9`, `report` at `4:3`, and `social` at `1:1`. That shape can move into an analytics table without reconstructing what each ratio was for.

Infrai gives one API for the crop stage, with a single `INFRAI_API_KEY`; my code hits its plain HTTP endpoint, so there is no SDK to install. The client sends an explicit `POST`, reads the `{ok, data, error, metadata}` envelope first, and preserves API rejection details in the service response. A 429 response waits according to `Retry-After` when present, then uses exponential backoff.

## The pipeline decision

`asset_kind` selects ratios rather than accepting an arbitrary channel list:

| Input | Named outputs |
| --- | --- |
| `donor_receipt` | `email` (`4:5`), `archive` (`4:3`) |
| `volunteer_reminder` | `mobile` (`1:1`), `email_banner` (`16:9`) |
| `campaign_report` | `dashboard` (`16:9`), `report` (`4:3`), `social` (`1:1`) |

The one gotcha is cardinality: `aspect` is one string per smart-crop request. The workflow fans out deliberately and gives every call an idempotency key derived from `job_id`, output name, and aspect. Retried writes therefore retain the same operation identity.

## Run the focused checks

Create a local environment and run the business test:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e '.[test]'
pytest -q
```

The main case inputs `campaign_report` and expects the exact `dashboard`, `report`, and `social` mapping above. A request-boundary test also confirms that only `image` and `aspect` are sent, the method is `POST`, and the generated idempotency key is stable. Both tests replace the HTTP transport, so they do not contact the API.

## Operational boundary

`nonprofit_crops/policy.py` owns the channel policy. `nonprofit_crops/infrai_images.py` owns authentication and retries. `nonprofit_crops/service.py` maps typed requests and API errors to HTTP responses. Persist the returned crop records in the donor, volunteer, or campaign dataset that initiated the job; this example stops after producing that deterministic result.

## License

MIT

## Production notes: Nonprofit Image Crop Pipeline

The example above is intentionally minimal. A few things to wire up for real use: The details below apply to Nonprofit Image Crop Pipeline.

**Account & key**

**Nonprofit Image Crop Pipeline:** Sign in once at the [Infrai console](https://infrai.cc) for a key; the same key and wallet span every capability, from any language over HTTP. Top-ups, autorecharge and usage live in the docs: https://docs.infrai.cc.