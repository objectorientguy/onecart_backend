from fastapi import APIRouter, Depends
from fastapi.openapi.models import Response
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app import schemas, models
from app.database import get_db

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@router.post("/addBranch")
def add_branch(company_id: str, branch_data: schemas.Branch, db: Session = Depends(get_db)):
    try:
        company = db.query(models.Companies).filter_by(company_id=company_id).first()
        if company is None:
            return {"status": 404, "message": "Company not found", "data": {}}

        existing_branch = db.query(models.Branch).filter_by(company_id=company.company_id,
                                                            branch_name=branch_data.branch_name).first()
        if existing_branch:
            return {"status": 400, "message": "Branch with the same name already exists", "data": {}}

        branch_data.company_id = company.company_id
        new_branch = models.Branch(**branch_data.model_dump())
        db.add(new_branch)
        db.commit()
        db.refresh(new_branch)

        return {"status": 200, "message": "Branch added successfully", "data": new_branch}
    except IntegrityError as e:
        print(repr(e))
        Response.status_code = 500
        return {"status": 500, "message": "Internal Server Error", "data": {}}
    finally:
        db.close()


@router.get("/getAllBranches")
async def get_branches(companyId: str, db: Session = Depends(get_db)):
    try:
        branches = db.query(models.Branch).filter(models.Branch.company_id == companyId).all()
        if not branches:
            return {"status": 204, "message": "No branches found", "data": []}

        serialized_branches = [{"branch_id": branch.branch_id,
                                "branch_name": branch.branch_name,
                                "branch_address": branch.branch_address,
                                "branch_email": branch.branch_email,
                                "branch_number": branch.branch_number}
                               for branch in branches]

        return {"status": 200, "message": "All branches fetched!", "data": serialized_branches}
    except Exception as e:
        print(repr(e))
        Response.status_code = 500
        return {"status": "500", "message": "Internal Server Error", "data": str(e)}


@router.put("/editBranch")
async def edit_branch(branch_data: schemas.BranchUpdate, branch_id: int, db: Session = Depends(get_db)):
    try:
        branch = db.query(models.Branch).filter(models.Branch.branch_id == branch_id)
        branch_exist = branch.first()
        if not branch_exist:
            Response.status_code = 404
            return {"status": 404, "message": "Branch not found", "data": {}}

        branch.update(branch_data.model_dump(), synchronize_session=False)
        db.commit()

        return {"status": 200, "message": "Branch updated successfully", "data": {}}
    except Exception as e:
        print(repr(e))
        return {"status": 500, "message": "Internal Server Error", "data": str(e)}


@router.delete("/deleteBranch")
async def delete_branch(branch_id: int, db: Session = Depends(get_db)):
    try:
        branch = db.query(models.Branch).filter(models.Branch.branch_id == branch_id)
        branch_exist = branch.first()
        if not branch_exist:
            return {"status": 204, "message": "Branch Not Found", "data": {}}
        branch.delete(synchronize_session=False)
        db.commit()

        return {"status": 200, "message": "Branch deleted successfully", "data": {}}
    except Exception as e:
        print(repr(e))
        return {"status": 500, "message": "Internal Server Error", "data": str(e)}
