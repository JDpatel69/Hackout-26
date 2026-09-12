from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import RoleInvestor
from app.database import get_db
from app.models import CarbonProject, Investment, Transaction, User
from app.schemas import (
    CarbonProjectOut,
    InvestRequest,
    InvestmentOut,
    PortfolioSummaryOut,
    TransactionOut,
)
from app.services.notification_service import notify
from app.utils.ids import new_id, now
from app.utils.mappers import investment_out, portfolio_summary, project_out, transaction_out

router = APIRouter(prefix="/investor", tags=["investor"])


@router.get("/projects", response_model=List[CarbonProjectOut])
def get_projects(
    region: Optional[str] = None,
    riskTier: Optional[str] = None,
    minROI: Optional[float] = None,
    user: User = Depends(RoleInvestor),
    db: Session = Depends(get_db),
) -> List[CarbonProjectOut]:
    q = db.query(CarbonProject)
    if region:
        q = q.filter(CarbonProject.region.ilike(f"%{region}%"))
    projects = q.order_by(CarbonProject.verified_at.desc()).all()
    out = []
    for p in projects:
        if minROI is not None and p.expected_roi_percent < minROI:
            continue
        if riskTier and (p.risk or {}).get("tier") != riskTier:
            continue
        out.append(project_out(p))
    return out


@router.get("/projects/{project_id}", response_model=CarbonProjectOut)
def get_project(
    project_id: str,
    user: User = Depends(RoleInvestor),
    db: Session = Depends(get_db),
) -> CarbonProjectOut:
    p = db.get(CarbonProject, project_id)
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    return project_out(p)


@router.get("/projects/{project_id}/roi")
def calculate_roi(
    project_id: str,
    amount: float = Query(..., gt=0),
    user: User = Depends(RoleInvestor),
    db: Session = Depends(get_db),
) -> dict:
    p = db.get(CarbonProject, project_id)
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    credits = round(amount / p.price_per_credit, 4)
    expected_return = round(amount * (1 + p.expected_roi_percent / 100.0), 2)
    return {
        "projectId": project_id,
        "amount": amount,
        "credits": credits,
        "expectedValue": expected_return,
        "roiPercent": p.expected_roi_percent,
    }


@router.get("/projects/{project_id}/risk")
def calculate_risk(
    project_id: str,
    user: User = Depends(RoleInvestor),
    db: Session = Depends(get_db),
) -> dict:
    p = db.get(CarbonProject, project_id)
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    return p.risk or {}


@router.post("/projects/{project_id}/invest", response_model=InvestmentOut, status_code=201)
def invest(
    project_id: str,
    body: InvestRequest,
    user: User = Depends(RoleInvestor),
    db: Session = Depends(get_db),
) -> InvestmentOut:
    p = db.get(CarbonProject, project_id)
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    credits = round(body.amount / p.price_per_credit, 4)
    if credits > p.total_credits_available:
        raise HTTPException(status_code=400, detail="Not enough credits available")
    p.total_credits_available = round(p.total_credits_available - credits, 4)
    inv = Investment(
        id=new_id(),
        investor_id=user.id,
        project_id=p.id,
        amount_invested=body.amount,
        credits_purchased=credits,
        invested_at=now(),
        status="active",
        current_value=round(body.amount * (1 + p.expected_roi_percent / 200.0), 2),
        return_percent=round(p.expected_roi_percent / 2.0, 2),
    )
    tx = Transaction(
        id=new_id(),
        investor_id=user.id,
        type="investment",
        amount=body.amount,
        related_project_id=p.id,
        date=now(),
        status="completed",
    )
    db.add(inv)
    db.add(tx)
    notify(
        db,
        user.id,
        "investment",
        "Investment confirmed",
        f"You invested ${body.amount:,.2f} in {p.title} ({credits} credits).",
        link_to="/investor/portfolio",
    )
    db.commit()
    db.refresh(inv)
    return investment_out(inv)


@router.get("/portfolio", response_model=PortfolioSummaryOut)
def portfolio(
    user: User = Depends(RoleInvestor),
    db: Session = Depends(get_db),
) -> PortfolioSummaryOut:
    invs = db.query(Investment).filter(Investment.investor_id == user.id).all()
    return portfolio_summary(invs)


@router.get("/investments", response_model=List[InvestmentOut])
def investments(
    user: User = Depends(RoleInvestor),
    db: Session = Depends(get_db),
) -> List[InvestmentOut]:
    invs = (
        db.query(Investment)
        .filter(Investment.investor_id == user.id)
        .order_by(Investment.invested_at.desc())
        .all()
    )
    return [investment_out(i) for i in invs]


@router.get("/transactions", response_model=List[TransactionOut])
def transactions(
    user: User = Depends(RoleInvestor),
    db: Session = Depends(get_db),
) -> List[TransactionOut]:
    rows = (
        db.query(Transaction)
        .filter(Transaction.investor_id == user.id)
        .order_by(Transaction.date.desc())
        .all()
    )
    return [transaction_out(t) for t in rows]
