from typing import Union
from uuid import uuid4

from fastapi import APIRouter, Depends, Body, Query
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app import schemas, models
from app.database import get_db
from app.models import Category, Products, ProductVariant

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def welcome_api_product(branchId, db):
    categories = db.query(Category).all()

    for category in categories:
        products = db.query(Products).filter(Products.category_id == category.category_id).all()

        for product in products:
            variants = db.query(ProductVariant).filter(ProductVariant.product_id == product.product_id).filter(
                ProductVariant.branch_id == branchId).all()

            if variants:
                return True
            else:
                return False


def login_signup_response(company, db):
    response_data = {
        "companyId": company.company_id if company.company_id is not None else "",
        "company_contact": str(company.company_contact) if company.company_contact is not None else "",
        "company_email": company.company_email if company.company_email is not None else "",
        "company_name": company.company_name if company.company_name is not None else "",
        "role_id": 0000,
        "branches": []
    }

    products_available = False
    company_id = company.company_id
    branches = db.query(models.Branch).filter(models.Branch.company_id == company_id).all()
    for branch in branches:
        categories = db.query(Category).all()

        for category in categories:
            products = db.query(Products).filter(Products.category_id == category.category_id).all()

            for product in products:
                variants = db.query(ProductVariant).filter(
                    ProductVariant.product_id == product.product_id).filter(
                    ProductVariant.branch_id == branch.branch_id).all()

                if variants:
                    products_available = True
                else:
                    products_available = False
            response_data['branches'] = [
                {
                    'branch_id': branch.branch_id if branch.branch_id is not None else "",
                    'branch_email': branch.branch_email if branch.branch_email is not None else "",
                    'branch_name': branch.branch_name if branch.branch_name is not None else "",
                    'branch_number': branch.branch_number if branch.branch_number is not None else "",
                    'branch_address': branch.branch_address if branch.branch_address is not None else "",
                    "products_available": products_available
                }

            ]
    return response_data


@router.post('/signup')
def signup(company_data: schemas.CompanySignUp = Body(...),
           signup_credentials: Union[str, int] = Query(...), db: Session = Depends(get_db)):
    try:
        if signup_credentials.isdigit():
            company_data.company_contact = int(signup_credentials)
            company_exists = db.query(models.Companies).filter(
                (models.Companies.company_contact == signup_credentials)).first()
        else:
            company_data.company_email = signup_credentials
            company_exists = db.query(models.Companies).filter(
                (models.Companies.company_email == signup_credentials)).first()

        if company_exists:
            return {
                "status": 409,
                "message": "Company already exists",
                "data": {"branches": [], "role_id": 0}}

        else:
            hashed_password = pwd_context.hash(company_data.company_password)
            company_id = uuid4().hex
            new_company = models.Companies(
                company_id=company_id,
                company_email=company_data.company_email,
                company_contact=company_data.company_contact,
                company_password=hashed_password
            )
            new_user = models.NewUsers(
                user_contact=company_data.company_contact,
                user_emailId=company_data.company_email,
                user_password=company_data.company_password
            )
            db.add(new_company)
            db.add(new_user)
            db.commit()

            company = db.query(models.Companies).filter(models.Companies.company_id == company_id).first()
            response_data = login_signup_response(company, db)

            return {
                "status": 200,
                "message": "User Signed Up!",
                "data": response_data}

    except Exception as e:
        print(repr(e))
        return {"status": 500, "message": "Internal Server Error", "data": {"branches": [], "role_id": 0}}


@router.post('/login')
async def login(login_credentials: Union[str, int], login_data: schemas.LoginFlow, db: Session = Depends(get_db)):
    try:
        if login_credentials.isdigit():
            company_contact = int(login_credentials)
            company = db.query(models.Companies).filter(
                models.Companies.company_contact == company_contact).first()
        else:
            company_email = login_credentials
            company = db.query(models.Companies).filter(
                models.Companies.company_email == company_email).first()

        if not company:
            return {
                "status": 404,
                "message": "User not found",
                "data": {"branches": [], "role_id": 0}}

        if pwd_context.verify(login_data.login_password, company.company_password if company else ""):
            response_data = login_signup_response(company, db)
            return {"status": 200, "message": "Login successful", "data": response_data}
        else:
            return {"status": 401, "message": "Incorrect password", "data": {"branches": [], "role_id": 0}}
    except Exception as e:
        print(repr(e))
        return {"status": 500, "message": "Internal Server Error", "data": {"branches": [], "role_id": 0}}


@router.get('/welcome')
def signup(companyId: str, branchId: int, role_id: int, db: Session = Depends(get_db)):
    try:
        response_data = {}
        products_available = False
        company = db.query(models.Companies).filter(models.Companies.company_id == companyId).first()
        if company:
            branch = db.query(models.Branch).filter(models.Branch.branch_id == branchId).filter(models.Branch.company_id == companyId).first()
            if branch:

                categories = db.query(Category).all()
                for category in categories:
                    products = db.query(Products).filter(Products.category_id == category.category_id).all()

                    for product in products:
                        variants = db.query(ProductVariant).filter(
                            ProductVariant.product_id == product.product_id).filter(
                            ProductVariant.branch_id == branch.branch_id).all()

                        if variants:
                            products_available = True
                        else:
                            products_available = False
                response_data['branches'] = {
                    'branch_id': branch.branch_id if branch.branch_id is not None else "",
                    'branch_email': branch.branch_email if branch.branch_email is not None else "",
                    'branch_name': branch.branch_name if branch.branch_name is not None else "",
                    'branch_number': branch.branch_number if branch.branch_number is not None else "",
                    'branch_address': branch.branch_address if branch.branch_address is not None else "",
                    "products_available": products_available
                }

                return {"status": 200,
                        "message": "Welcome API success",
                        "data": response_data}

            else:
                return {"status": 404, "message": "Branch does NOT exist",
                        "data": {"branches": {}, "role_id": role_id}}

        return {"status": 404, "message": "Comapny does NOT exist", "data": {"branches": {}, "role_id": role_id}}

    except Exception as e:
        print(repr(e))
    return {"status": 500, "message": "Internal Server Error", "data": {"branches": {}, "role_id": role_id}}
