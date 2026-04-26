from pydantic import BaseModel


class ParseRequest(BaseModel):
    file_url: str
    file_name: str = "document.pdf"
    document_type_hint: str | None = None
    include_enrichment: bool = False
    cross_check_balances: bool = True
    # Context for enrichment (only used when include_enrichment=True)
    business_name: str | None = None
    industry: str | None = None


class ClassifyRequest(BaseModel):
    file_url: str
    file_name: str = "document.pdf"
