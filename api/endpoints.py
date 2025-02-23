from rapidfuzz import fuzz
from database import get_session, Contractor, ApprovedPermit, Address
from fastapi import APIRouter, HTTPException
from sqlalchemy import and_
from sqlalchemy import distinct
import os
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import exists
from pydantic import BaseModel
import database
import json
from sqlalchemy.orm import class_mapper
from openai import OpenAI
from typing import List, Optional
from sqlalchemy import func

class FuzzyContractor(BaseModel):
    name: str
    score: int

router = APIRouter()
client = OpenAI()

@router.get(
    "/fuzzy-contractor",
    response_model=List[FuzzyContractor],
    summary="Fuzzy Search Contractors",
    description=(
        "Search for a contractor's name using fuzzy search. If the provided contractor_name "
        "has more than 4 characters, a fuzzy search is used based on a threshold (fuzz_ratio). "
        "Otherwise, a simple case-insensitive search is performed. Only the first 10 results are returned."
    ),
)
async def search_contractor(contractor_name: Optional[str] = None, fuzz_ratio: Optional[int] = 75) -> List[FuzzyContractor]:
    """
    Search for a contractor's name using fuzzy search.
    - If 'contractor_name' is provided and its length > 4, uses fuzzy_search_contractors.
    - fuzz_ratio is a number between 0-100. 100 means only return exact results.
    Only the first 10 results are returned.
    """

    if len(contractor_name) > 4:
        # Use fuzzy search if the input length is more than 4 characters
        # fuzzy_search_contractors should return a list of tuples: (Contractor, score)
        results = fuzzy_search_contractors(contractor_name, fuzz_ratio)
        limited_results = results[:10]
        return [
            {
                "name": contractor,
                "score": score
            }
            for contractor, score in limited_results
        ]
    else:
        # For short queries, fallback to a simple ilike search
        with get_session() as session:
            contractors = session.query(Contractor).filter(
                Contractor.name.ilike(f"%{contractor_name}%")
            ).limit(10).all()
            return [
                {
                    "name": contractor.name.title(),
                    "score": 0
                }
                for contractor in contractors
            ]

    raise HTTPException(status_code=400, detail="Must provide either contractor_name or license_id")



@router.get("/detailed-contractor")
async def detailed_contractor(contractor_name: str = None, license_id: str = None):
    with get_session() as session:
        # Build the query based on provided parameters
        query = session.query(Contractor)
        if license_id:
            contractor = query.filter_by(license_id=license_id.lower()).first()
        elif contractor_name:
            contractor = query.filter_by(name=contractor_name.lower()).first()
        else:
            raise HTTPException(status_code=400, detail="Either contractor_name or license_id must be provided")

        if not contractor:
            raise HTTPException(status_code=404, detail="Contractor not found")

        # Retrieve previous works from ApprovedPermit table
        previous_works = (
            session.query(ApprovedPermit)
            .join(Address, ApprovedPermit.project_address_id == Address.id)
            .filter(ApprovedPermit.contractor_name == contractor.name)
            .all()
        )

        total_amount = get_total_project_amount_for_contractor(contractor_name)
        # TODO: include gpt response

        contractor_info = f"'previous_works': {serialize_query_result(previous_works)},\n 'total_amount': {total_amount}"
        gpt_result = gpt_search("{" + contractor_info + "}")

        # Prepare the response
        response = {
            "previous_works": previous_works,
            "total_amount": total_amount,
            "gpt": gpt_result
        }

    return response

def model_to_dict(model_instance):
    """Convert a SQLAlchemy model instance into a dictionary."""
    return {
        column.key: getattr(model_instance, column.key)
        for column in class_mapper(model_instance.__class__).columns
    }

def serialize_query_result(query_result):
    """Convert a list of model instances into a JSON string."""
    data = [model_to_dict(row) for row in query_result]
    return json.dumps(data, default=str)  # default=str handles datetime and other non-serializable objects


def get_total_project_amount_for_contractor(contractor_name: str):
    with get_session() as session:
        total_amount = session.query(
            func.sum(ApprovedPermit.project_amount)
        ).filter(
            ApprovedPermit.contractor_name == contractor_name
        ).scalar()
    return total_amount

def fuzzy_search_contractors(search_query, threshold=75):
    search_query = search_query.lower()
    with get_session() as session:
        # Step 1: Fetch distinct contractor names from ApprovedPermit
        candidates = session.query(
            distinct(ApprovedPermit.contractor_name)
        ).filter(
            ApprovedPermit.contractor_name.ilike(f"%{search_query}%"),
            ApprovedPermit.contractor_name != None
        ).limit(50).all()

        # Step 2: If no candidates found, fallback to all distinct contractor names
        if not candidates:
            candidates = session.query(
                distinct(ApprovedPermit.contractor_name)
            ).filter(
                ApprovedPermit.contractor_name != None
            ).limit(50).all()

        # Step 3: Compute fuzzy match scores and filter by threshold
        results = []
        for (contractor_name,) in candidates:
            score = fuzz.ratio(contractor_name.lower(), search_query)
            if score >= threshold:
                results.append((contractor_name, score))

        # Step 4: Sort results by score (highest first)
        results.sort(key=lambda x: x[1], reverse=True)

    return results



def gpt_search(query):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": "You are a financial and civil advisor for homeowners. You provide advice to homeowners on their selected home improvement contractor. You are given the past history (i.e. past projects) of each contractor (some of the details of which might be trimmed) and their licensing history. Analyze the information you are given and make a short (under 100 words) recommendation on whether on not to hire this home improvement contractor for a home improvement project at my residence. Judge based on contractor's experience, and diversity of skill sets. For example If a contractor pulls multiple permits for different addresses, in a short period of time, you might identify them as high risk since they are over-committing putting in doubt their ability to complete the job."
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"{query}"
                    }
                ]
            }
        ],
        response_format={
            "type": "text"
        },
        temperature=0.5,
        max_completion_tokens=1024,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )

    return response.choices[0].message.content