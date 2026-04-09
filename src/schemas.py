from pydantic import BaseModel, field_validator

IMPORTANT_COLUMNS = frozenset(
    {
        "ГВС (ТЭ на нагрев воды)",
        "Холодное водоснабж.",
        "Водоотведение",
        "Электроснабжение",
        "ХВС повыш.коэф-т",
        "ГВС повыш.коэф-т",
    }
)


class UtilityBillRow(BaseModel):
    service: str
    norm: float
    social_norm: float
    tariff: float
    volume: float
    unit: str
    accrued: float
    recalculation: float
    total: float

    @field_validator("service")
    def validate_service(cls, v: str) -> str:
        return v.strip()


class UtilityBillTotals(BaseModel):
    accrued_sum: float
    recalculation_sum: float
    grand_total: float


class UtilityBillTable(BaseModel):
    rows: list[UtilityBillRow]
    totals: UtilityBillTotals
