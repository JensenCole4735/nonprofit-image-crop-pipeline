"""FastAPI boundary for nonprofit crop jobs."""

from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .infrai_images import InfraiError, InfraiImageClient
from .policy import CropJob, targets_for


class CropOutput(BaseModel):
    name: str
    aspect: str
    result: dict[str, Any]


class CropJobResult(BaseModel):
    job_id: str
    asset_kind: str
    crops: list[CropOutput]


def execute_crop_job(job: CropJob, client: InfraiImageClient) -> CropJobResult:
    crops = [
        CropOutput(
            name=target.name,
            aspect=target.aspect,
            result=client.smart_crop(
                job.image,
                target.aspect,
                job_id=job.job_id,
                output_name=target.name,
            ),
        )
        for target in targets_for(job.asset_kind)
    ]
    return CropJobResult(job_id=job.job_id, asset_kind=job.asset_kind.value, crops=crops)


app = FastAPI(title="Nonprofit crop pipeline")


@app.post("/crop-jobs", response_model=CropJobResult)
def create_crop_job(job: CropJob) -> CropJobResult:
    client = InfraiImageClient()
    try:
        return execute_crop_job(job, client)
    except InfraiError as error:
        caller_status = error.status_code if 400 <= error.status_code < 500 else 502
        raise HTTPException(
            status_code=caller_status,
            detail={"code": error.code, "error": error.detail},
        ) from error
    finally:
        client.close()
