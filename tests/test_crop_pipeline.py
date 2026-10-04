import hashlib

import httpx

from nonprofit_crops.infrai_images import InfraiImageClient
from nonprofit_crops.policy import AssetKind, CropJob
from nonprofit_crops.service import execute_crop_job


class RecordingCropClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, str, str]] = []

    def smart_crop(
        self, image: dict[str, str], aspect: str, *, job_id: str, output_name: str
    ) -> dict[str, str]:
        self.calls.append((image, aspect, job_id, output_name))
        return {"crop_id": f"crop-{output_name}"}


def test_campaign_report_fans_out_to_reporting_channels() -> None:
    client = RecordingCropClient()
    job = CropJob(
        job_id="campaign-42",
        asset_kind=AssetKind.CAMPAIGN_REPORT,
        image={"image_id": "image-record-9"},
    )

    result = execute_crop_job(job, client)  # type: ignore[arg-type]

    assert [(crop.name, crop.aspect) for crop in result.crops] == [
        ("dashboard", "16:9"),
        ("report", "4:3"),
        ("social", "1:1"),
    ]
    assert [call[1] for call in client.calls] == ["16:9", "4:3", "1:1"]


def test_smart_crop_request_has_exact_body_and_stable_operation_key() -> None:
    requests: list[httpx.Request] = []

    def respond(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json={"ok": True, "data": {"crop_id": "crop-1"}, "metadata": {}})

    client = InfraiImageClient(api_key="test-key", transport=httpx.MockTransport(respond))
    try:
        result = client.smart_crop(
            {"image_id": "image-record-9"}, "1:1", job_id="campaign-42", output_name="social"
        )
    finally:
        client.close()

    request = requests[0]
    expected_key = hashlib.sha256(b"campaign-42:social:1:1").hexdigest()
    assert request.method == "POST"
    assert request.url.path == "/v1/image/smart_crop"
    assert request.headers["Idempotency-Key"] == expected_key
    assert request.headers["Authorization"] == "Bearer test-key"
    assert request.read() == b'{"image":{"image_id":"image-record-9"},"aspect":"1:1"}'
    assert result == {"crop_id": "crop-1"}
