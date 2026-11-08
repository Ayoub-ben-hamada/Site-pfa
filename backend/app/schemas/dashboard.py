from pydantic import BaseModel


class UpdateProductRequest(BaseModel):
    product_id: int


class DashboardTargetResponse(BaseModel):
    variable: str
    temporal: list[dict]
    by_product: list[dict]
    by_gouvernorat: list[dict]
    factors: list[dict]
    plotly_figures: dict
