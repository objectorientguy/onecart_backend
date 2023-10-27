import os
from fastapi import APIRouter
from fastapi import Response, Depends, File, Request, Body, UploadFile, Form
from sqlalchemy.orm import Session
from app import schemas, models
from app.database import get_db

router = APIRouter()
UPLOAD_DIR = "app/images"


@router.post("/company/logo")
async def upload_company_logo(request: Request, logo: UploadFile = File(...), company_id: str = Form(...),
                              db: Session = Depends(get_db)):
    try:
        image_data = logo.file.read()
        image_filename = logo.filename
        image_path = os.path.join(UPLOAD_DIR, image_filename)
        with open(image_path, "wb") as f:
            f.write(image_data)
        company = db.query(models.Companies).filter(models.Companies.company_id == company_id).first()
        if company:
            base_url = request.base_url
            logo_url = f"{base_url}images/{image_filename}"
            company.company_logo = logo_url
            db.commit()
            return {"status": 200, "message": "Company logo uploaded successfully", "data": {"logo_url": logo_url}}
        else:
            return {"status": 404, "message": "Company not found", "data": {}}
    except Exception as e:
        print(repr(e))
        return {"status": 500, "message": "Internal Server Error", "data": {}}
    finally:
        db.close()


@router.delete("/company/logo")
async def delete_company_logo(company_id: str, db: Session = Depends(get_db)):
    try:
        company = db.query(models.Companies).filter(models.Companies.company_id == company_id).first()
        if company:
            if company.company_logo:
                image_filename = company.company_logo.split("/")[-1]
                image_path = os.path.join(UPLOAD_DIR, image_filename)
                if os.path.exists(image_path):
                    os.remove(image_path)
                company.company_logo = None
                db.commit()
                return {"status": 200, "message": "Company logo deleted successfully", "data": {}}
            else:
                return {"status": 404, "message": "Company logo not found", "data": {}}
        else:
            return {"status": 404, "message": "Company not found", "data": {}}
    except Exception as e:
        print(repr(e))
        db.rollback()
        return {"status": 500, "message": "Internal Server Error", "data": {}}
    finally:
        db.close()


@router.post('/company/details')
def update_company_details(company_id: str, response: Response, request_body: schemas.CompanyUpdateDetails = Body(...),
                           db: Session = Depends(get_db)):
    try:
        company = db.query(models.Companies).filter(models.Companies.company_id == company_id).first()
        if not company:
            return {"status": 404, "message": "Company not found", "data": {}}
        if company:
            existing_company = db.query(models.Companies).filter(
                models.Companies.company_name == request_body.company_name).first()
            if existing_company and existing_company.company_id != company_id:
                return {"status": 400, "message": "Company name already exists for another company", "data": {}}
            company.company_name = request_body.company_name
            company.company_address = request_body.company_address
            company.company_contact = request_body.company_contact
            company.company_domain = request_body.company_domain
            print(company)
            db.commit()
            return {"status": 200, "message": "Company details added successfully",
                    "data": {"company_details": request_body}}
    except Exception as e:
        print(repr(e))
        response.status_code = 500
        return {"status": 500, "message": "Internal Server Error", "data": {}}
