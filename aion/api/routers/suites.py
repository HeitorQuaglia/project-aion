"""Suites router — in-memory CRUD for Suite objects."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from aion.api.dependencies import get_suites
from aion.api.schemas import SuiteCreate
from aion.domain.models import Suite

router = APIRouter(tags=["suites"])


@router.post("", response_model=Suite, status_code=201)
def create_suite(
    body: SuiteCreate,
    suites: Annotated[dict[str, Suite], Depends(get_suites)],
) -> Suite:
    """Register a new suite.

    Args:
        body: Suite definition.
        suites: Injected in-memory registry.

    Raises:
        HTTPException: 409 if a suite with the same ``id`` already exists.
    """
    if body.id in suites:
        raise HTTPException(status_code=409, detail=f"Suite '{body.id}' already exists.")
    suite = Suite(
        id=body.id,
        name=body.name,
        description=body.description,
        scenarios=body.scenarios,
    )
    suites[body.id] = suite
    return suite


@router.get("", response_model=list[Suite])
def list_suites(
    suites: Annotated[dict[str, Suite], Depends(get_suites)],
) -> list[Suite]:
    """Return all registered suites."""
    return list(suites.values())


@router.get("/{suite_id}", response_model=Suite)
def get_suite(
    suite_id: str,
    suites: Annotated[dict[str, Suite], Depends(get_suites)],
) -> Suite:
    """Return a single suite by id.

    Raises:
        HTTPException: 404 if the suite does not exist.
    """
    suite = suites.get(suite_id)
    if suite is None:
        raise HTTPException(status_code=404, detail=f"Suite '{suite_id}' not found.")
    return suite
