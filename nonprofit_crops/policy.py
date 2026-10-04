"""Channel policy for nonprofit image records."""

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class AssetKind(str, Enum):
    DONOR_RECEIPT = "donor_receipt"
    VOLUNTEER_REMINDER = "volunteer_reminder"
    CAMPAIGN_REPORT = "campaign_report"


class CropJob(BaseModel):
    model_config = ConfigDict(extra="forbid")

    job_id: str = Field(min_length=1)
    asset_kind: AssetKind
    image: dict[str, str]


class CropTarget(BaseModel):
    name: str
    aspect: str


TARGETS: dict[AssetKind, tuple[CropTarget, ...]] = {
    AssetKind.DONOR_RECEIPT: (
        CropTarget(name="email", aspect="4:5"),
        CropTarget(name="archive", aspect="4:3"),
    ),
    AssetKind.VOLUNTEER_REMINDER: (
        CropTarget(name="mobile", aspect="1:1"),
        CropTarget(name="email_banner", aspect="16:9"),
    ),
    AssetKind.CAMPAIGN_REPORT: (
        CropTarget(name="dashboard", aspect="16:9"),
        CropTarget(name="report", aspect="4:3"),
        CropTarget(name="social", aspect="1:1"),
    ),
}


def targets_for(kind: AssetKind) -> tuple[CropTarget, ...]:
    """Return the ordered output contract for one asset record."""
    return TARGETS[kind]
