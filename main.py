import json
import re
import os
from typing import Optional
from fastapi import FastAPI, HTTPException, Depends, Header, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# ── App setup ────────────────────────────────────────────────
security = HTTPBearer()
app = FastAPI(
    title="Global Loyalty & Rewards Registry",
    description="""
A structured reference API for the global travel and lifestyle rewards ecosystem.
Covers airlines, hotels, car rental, credit cards, cruise, and rail.

**Designed for agentic AI consumption.** Every field is strictly typed and described.
Null values are always returned explicitly — never omitted.

## Authentication
Pass your API key in the Authorization header:
`Authorization: Bearer YOUR_API_KEY`
    """,
    version="1.0.0",
    contact={"name": "Global Loyalty & Rewards Registry"}
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Load data at startup ──────────────────────────────────────
with open("programs.json", encoding="utf-8") as f:
    PROGRAMS: list[dict] = json.load(f)

PROGRAMS_BY_SLUG: dict[str, dict] = {p["slug"]: p for p in PROGRAMS}

# ── Auth ──────────────────────────────────────────────────────
API_KEY = os.getenv("API_KEY")

def verify_api_key(auth: HTTPAuthorizationCredentials = Depends(security)):
    if auth.credentials != API_KEY:
        raise HTTPException(
            status_code=401, 
            detail="Invalid API key"
        )
    return auth.credentials

# ── Response models ───────────────────────────────────────────
class LoyaltyProgram(BaseModel):
    slug: str = Field(description="Unique lowercase identifier. Use this as a stable reference key.")
    program_name: str = Field(description="Official name of the loyalty program (e.g. 'MileagePlus', 'Bonvoy')")
    brand_name: str = Field(description="Parent company or group operating the program (e.g. 'United Airlines', 'Marriott International')")
    sub_brands: Optional[list[str]] = Field(description="For hotel programs: list of hotel brands where points can be earned. Null for all other categories.")
    category: str = Field(description="Top-level category: Airline, Hotel, Car, Credit, Cruise, or Rail")
    sub_category: str = Field(description="Sub-type within category (e.g. 'Full Service', 'Low Cost', 'Rental', 'Card')")
    currency_name: str = Field(description="Name of the loyalty currency (e.g. 'Miles', 'Points', 'Avios')")
    iata_icao_code: Optional[list[str]] = Field(description="IATA 2-letter codes for participating carriers. Array because some programs cover multiple airlines. Null for non-airline programs.")
    gds_code: Optional[str] = Field(description="GDS chain code used to identify this program in booking systems. Null for airlines.")
    member_number_regex: Optional[str] = Field(description="Regular expression to validate a member number format.")
    member_number_example: Optional[str] = Field(description="A valid example member number format hint.")
    tiers: Optional[list[str]] = Field(description="Status tiers in ascending order. Index 0 is the lowest/entry tier.")
    program_url: Optional[str] = Field(description="URL to the program overview page.")
    enrollment_url: Optional[str] = Field(description="URL to enroll or create a new account.")
    last_verified: Optional[str] = Field(description="ISO date when this record was last manually verified (YYYY-MM-DD).")
    alliance: Optional[str] = Field(description="Formal alliance (e.g. 'Star Alliance'). Null for non-airline programs.")
    active: bool = Field(description="True if this program is currently operating.")

class ProgramList(BaseModel):
    count: int = Field(description="Total number of programs returned")
    programs: list[LoyaltyProgram]

class ValidationResult(BaseModel):
    valid: bool = Field(description="True if the member number matches the expected format")
    slug: str = Field(description="The program slug validated against")
    program_name: str = Field(description="The full name of the program")
    member_number: str = Field(description="The member number submitted")
    member_number_example: Optional[str] = Field(description="A valid example format to guide the user.")

# ── Endpoints ─────────────────────────────────────────────────
@app.get("/", tags=["Health"])
def root():
    """Health check and API metadata."""
    return {
        "name": "Global Loyalty & Rewards Registry",
        "version": "1.0.0",
        "status": "operational",
        "total_programs": len(PROGRAMS),
        "docs": "/docs",
        "openapi": "/openapi.json"
    }


@app.get("/programs", response_model=ProgramList, tags=["Programs"],
    summary="List all loyalty programs",
    description="Returns all active loyalty programs. Filter by category (Airline, Hotel, etc.) to narrow results.")
def list_programs(
    category: Optional[str] = Query(None, description="Filter by category: Airline, Hotel, Car, Credit, Cruise, Rail"),
    active_only: bool = Query(True, description="Only returns active programs when true"),
    _: str = Depends(verify_api_key)
):
    results = PROGRAMS

    if active_only:
        results = [p for p in results if p.get("active") is True]

    if category:
        category_clean = category.strip().title()
        results = [p for p in results if p.get("category", "").title() == category_clean]
        if not results:
            raise HTTPException(
                status_code=404,
                detail=f"No programs found for category '{category}'."
            )

    return {"count": len(results), "programs": results}


@app.get("/programs/{slug}", response_model=LoyaltyProgram, tags=["Programs"],
    summary="Get a single loyalty program by slug")
def get_program(
    slug: str,
    _: str = Depends(verify_api_key)
):
    program = PROGRAMS_BY_SLUG.get(slug.lower().strip())

    if not program:
        close = [s for s in PROGRAMS_BY_SLUG.keys() if slug.replace("_", "") in s.replace("_", "")][:3]
        detail = f"No program found with slug '{slug}'."
        if close:
            detail += f" Did you mean: {', '.join(close)}?"
        raise HTTPException(status_code=404, detail=detail)

    return program


@app.post("/programs/validate", response_model=ValidationResult, tags=["Validation"],
    summary="Validate a member number format")
def validate_member_number(
    slug: str = Query(..., description="The program slug"),
    member_number: str = Query(..., description="The number to validate"),
    _: str = Depends(verify_api_key)
):
    program = PROGRAMS_BY_SLUG.get(slug.lower().strip())

    if not program:
        raise HTTPException(status_code=404, detail=f"No program found with slug '{slug}'")

    regex = program.get("member_number_regex")

    # If no regex is available, we assume true but return the example for reference
    if not regex or regex in ("Null", "Passport", "Mobile Number", "email address", ""):
        return ValidationResult(
            valid=True,
            slug=slug,
            program_name=program["program_name"],
            member_number=member_number,
            member_number_example=program.get("member_number_example")
        )

    is_valid = bool(re.fullmatch(regex, member_number.strip()))

    return ValidationResult(
        valid=is_valid,
        slug=slug,
        program_name=program["program_name"],
        member_number=member_number,
        member_number_example=program.get("member_number_example")
    )