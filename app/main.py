import logging
import os
import shutil
from datetime import timedelta
from io import BytesIO
from typing import List, Union
from urllib import response
from uuid import uuid4

import firebase_admin
import pandas as pd
from fastapi import FastAPI, Response, Depends, File, Request, HTTPException, Body, UploadFile, Form, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from firebase_admin import credentials, storage
from passlib.context import CryptContext
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from starlette.responses import FileResponse

from . import models, schemas, database
from .database import engine, get_db
from .models import Image, ProductVariant, Category, Products, Brand, Branch, NewUsers
from .schemas import ProductInput, ProductUpdateInput, BranchUpdate

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
models.Base.metadata.create_all(bind=engine)

app = FastAPI()
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "app/images"

logging.basicConfig(filename='app.log', level=logging.DEBUG)


def save_image_to_db(db, filename, file_path):
    image = Image(filename=filename, file_path=file_path)
    db.add(image)
    db.commit()
    db.refresh(image)
    return image


cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {'storageBucket': 'onecart-6156a.appspot.com',
                                     'databaseURL': 'https://onecart-6156a-default-rtdb.firebaseio.com/'})


@app.get('/')
def root():
    return {'message': 'Hello world'}


directory = "app/uploaded_images"
if not os.path.exists(directory):
    os.makedirs(directory)


def save_upload_file(upload_file: UploadFile, destination: str):
    try:
        with open(destination, "wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)
    finally:
        upload_file.file.close()


@app.post("/upload/images")
async def upload_images(upload_files: List[UploadFile] = File(...)):
    image_urls = []
    for upload_file in upload_files:
        destination = os.path.join("app", "uploaded_images", upload_file.filename)
        save_upload_file(upload_file, destination)
        bucket = storage.bucket()
        blob = bucket.blob(f"uploaded_images/{upload_file.filename}")
        blob.upload_from_filename(destination)
        image_url = blob.generate_signed_url(method="GET", expiration=timedelta(days=120))
        image_urls.append(image_url)
    response_data = {
        "status": 200,
        "message": "Images uploaded successfully.",
        "data": {"image_urls": image_urls}
    }
    return JSONResponse(content=response_data)


@app.post("/delete_image/")
async def delete_image(product_id: int, variant_id: int,
                       image_info: schemas.ImageDeleteRequest = Body(...), db: Session = Depends(get_db)):
    image_url = image_info.image_url
    product_variant = db.query(models.ProductVariant).filter_by(
        product_id=product_id, variant_id=variant_id
    ).first()
    if not product_variant:
        return {"status_code": 404, "message": "Product variant not found"}
    updated_images = [img for img in product_variant.image if img != image_url]
    if len(product_variant.image) != len(updated_images):
        product_variant.image = updated_images
        try:
            db.commit()
            return {"status": 200, "message": "Image deleted successfully"}
        except Exception:
            db.rollback()
            return {"status": 500, "message": " Database error"}
    else:
        return {"status": 404, "message": "Image URL not found in the product variant"}


@app.post("/upload")
async def upload_image(request: Request, file: UploadFile = File(...), db: Session = Depends(get_db)):
    image_data = file.file.read()
    image_path = os.path.join(UPLOAD_DIR, file.filename)

    with open(image_path, "wb") as f:
        f.write(image_data)

    try:
        image_obj = save_image_to_db(db, file.filename, image_path)
        base_url = request.base_url
        image_url = f"{base_url}images/{file.filename}"
        return {"status": 200, "message": "Image uploaded successfully",
                "data": {"image_id": image_obj.id, "image_url": image_url}}
    finally:
        db.close()


@app.get("/images/{filename}")
async def get_image(filename: str):
    image_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(image_path):
        logging.error(f"Image not found: {filename}")
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(image_path)


# @app.post("/multipleUpload")
# async def upload_image(request: Request, files: List[UploadFile] = File(...), db: Session = Depends(get_db)):
#     image_urls = []
#     for file in files:
#         contents = await file.read()
#         filename = file.filename
#         file_path = os.path.join(UPLOAD_DIR, filename)
#
#         with open(file_path, "wb") as f:
#             f.write(contents)
#
#         image = Image(filename=filename, file_path=file_path)
#         try:
#             db.add(image)
#             db.commit()
#             db.refresh(image)
#         except Exception as e:
#             logging.error(f"Error storing image {filename}: {e}")
#             db.rollback()
#         finally:
#             db.close()
#         base_url = request.base_url
#         image_url = f"{base_url}images/{file.filename}"
#         image_urls.append(image_url)
#
#     return {"status": 200, "message": "Images uploaded successfully", "data": {"image_url": image_urls}}


@app.post("/product/image")
async def edit_product_images(request: Request, product_id: int, variant_id: int,
                              new_files: List[UploadFile] = File(...), db: Session = Depends(get_db)):
    try:
        product_variant = db.query(ProductVariant).filter_by(product_id=product_id, variant_id=variant_id).first()
        if not product_variant:
            return {"status": 404, "message": "Product variant not found"}

        existing_images = [image for image in product_variant.image]
        new_image_urls = []
        for file in new_files:
            contents = await file.read()
            filename = file.filename
            file_path = os.path.join(UPLOAD_DIR, filename)
            with open(file_path, "wb") as f:
                f.write(contents)

            image = Image(filename=filename, file_path=file_path)
            db.add(image)
            db.commit()
            db.refresh(image)
            base_url = request.base_url
            image_url = f"{base_url}images/{file.filename}"
            new_image_urls.append(image_url)

        updated_images = new_image_urls
        product_variant.image = updated_images
        db.commit()
        return {"status": 200, "message": "Images updated successfully", "data": {"image_urls": updated_images}}
    except Exception as e:
        print(repr(e))
        db.rollback()
        return {"status": 200, "message": "Internal Server error", "data": str(e)}
    finally:
        db.close()


# @app.post('/userAuthenticate')
# def create_user(loginSignupAuth: schemas.UserData, response: Response,
#                 db: Session = Depends(get_db), companyName=str):
#     try:
#         user_data = db.query(models.User).get(
#             loginSignupAuth.customer_contact)
#
#         if not user_data:
#             # try:
#             new_user_data = models.User(
#                 **loginSignupAuth.model_dump())
#             new_user_added = models.UserCompany(  # composite table
#                 company_name=companyName,
#                 user_contact=loginSignupAuth.customer_contact)
#             db.add(new_user_data)
#             db.add(new_user_added)
#             db.commit()
#             db.refresh(new_user_data)
#             return {"status": 200, "message": "New user successfully created!", "data": new_user_data}
#         # except IntegrityError:
#         #     response.status_code = 200
#         #     return {"status": 204, "message": "User is not registered please Sing up", "data": {}}
#
#         user_exists = db.query(models.UserCompany).filter(models.UserCompany.company_name == companyName).filter(
#             models.UserCompany.user_contact == loginSignupAuth.customer_contact).first()
#         print(user_exists)
#         if not user_exists:
#             try:
#                 new_user_company = models.UserCompany(
#                     company_name=companyName,
#                     user_contact=loginSignupAuth.customer_contact)
#                 db.add(new_user_company)
#                 db.commit()
#                 db.refresh(new_user_company)
#                 return {"status": 200, "message": "New user successfully Logged in!", "data": user_data}
#             except IntegrityError:
#                 response.status_code = 200
#                 return {"status": "204", "message": "User is not registered for this company please Sing up",
#                         "data": {}}
#
#         return {"status": 200, "message": "New user successfully Logged in for this company!", "data": user_data}
#
#     except IntegrityError as e:
#         print(repr(e))
#         response.status_code = 404
#         return {"status": 404, "message": "Error", "data": {}}
#
# @app.put('/editUser/{userId}')
# def edit_user(userDetail: schemas.EditUserData, response: Response, db: Session = Depends(get_db),
#               userId=int):
#     try:
#         edit_user_details = db.query(models.User).filter(models.User.customer_contact == userId)
#
#         user_exist = edit_user_details.first()
#         if not user_exist:
#             response.status_code = 200
#             return {"status": 204, "message": "User doesn't exists", "data": {}}
#
#         edit_user_details.update(userDetail.model_dump(), synchronize_session=False)
#         db.commit()
#         return {"status": 200, "message": "user edited!", "data": edit_user_details.first()}
#     except IntegrityError as e:
#         print(repr(e))
#         response.status_code = 404
#         return {"status": 404, "message": "Error", "data": {}}
#
#
# @app.post("/addAddress")
# def add_address(user_contact: int, createAddress: schemas.AddAddress, response: Response,
#                 db: Session = Depends(get_db)):
#     try:
#
#         new_address = models.Addresses(**createAddress.model_dump())
#         db.add(new_address)
#         db.commit()
#         db.refresh(new_address)
#
#         return {"status": "200", "message": "New address created!", "data": new_address}
#     except IntegrityError as e:
#         print(repr(e))
#         response.status_code = 404
#         return {"status": "404", "message": "Error", "data": {}}
#
#
# @app.get('/getAllAddresses')
# def get_address(response: Response, db: Session = Depends(get_db), userId=int):
#     try:
#         user_addresses = db.query(models.Addresses).filter(
#             models.Addresses.user_contact == userId).all()
#
#         if not user_addresses:
#             response.status_code = 200
#             return {"status": "200", "message": "No address found", "data": []}
#
#         return {"status": "200", "message": "success", "data": user_addresses}
#     except IntegrityError:
#         response.status_code = 404
#         return {"status": "404", "message": "Error", "data": {}}
#
#
# @app.put('/editAddress')
# def edit_address(editAddress: schemas.EditAddress, response: Response, db: Session = Depends(get_db), addressId=int):
#     try:
#         edit_user_address = db.query(models.Addresses).filter(
#             models.Addresses.address_id == addressId)
#         address_exist = edit_user_address.first()
#         if not address_exist:
#             response.status_code = 200
#             return {"status": 204, "message": "Address doesn't exists", "data": {}}
#
#         edit_user_address.update(editAddress.model_dump(
#             exclude_unset=True), synchronize_session=False)
#         db.commit()
#         return {"status": "200", "message": "address edited!", "data": edit_user_address.first()}
#
#     except IntegrityError as e:
#         print(repr(e))
#         response.status_code = 404
#         return {"status": "404", "message": "Error", "data": {}}
#
#
# @app.delete('/deleteAddress')
# def delete_user_address(response: Response, db: Session = Depends(get_db), addressId=int):
#     try:
#         delete_address = db.query(models.Addresses).filter(
#             models.Addresses.address_id == addressId)
#         address_exist = delete_address.first()
#         if not address_exist:
#             response.status_code = 200
#             return {"status": "204", "message": "Address doesn't exists", "data": {}}
#
#         delete_address.delete(synchronize_session=False)
#         db.commit()
#         return {"status": "200", "message": "Address deleted!"}
#     except IntegrityError:
#         response.status_code = 404
#         return {"status": "404", "message": "Error", "data": {}}
#

def build_company_response(company, db):
    response_data = {
        "companyId": company.company_id if company.company_id is not None else "",
        "company_contact": str(company.company_contact) if company.company_contact is not None else "",
        "company_email": company.company_email if company.company_email is not None else "",
        "company_name": company.company_name if company.company_name is not None else "",
        "role_id": 0000
    }

    company_id = company.company_id
    branches = db.query(models.Branch).filter(models.Branch.company_id == company_id).all()
    employees = db.query(models.Employee).join(models.Branch).filter(models.Branch.company_id == company_id).all()

    response_data['branches'] = [
        {
            'branch_id': branch.branch_id if branch.branch_id is not None else "",
            'branch_email': branch.branch_email if branch.branch_email is not None else "",
            'branch_name': branch.branch_name if branch.branch_name is not None else "",
            'branch_number': branch.branch_number if branch.branch_number is not None else "",
            'branch_address': branch.branch_address if branch.branch_address is not None else "",
        }
        for branch in branches
    ]

    response_data['employees'] = [
        {
            'employeeID': employee.employee_id if employee.employee_id is not None else "",
            'employee_name': employee.employee_name if employee.employee_name is not None else "",
            'employee_contact': employee.employee_contact if employee.employee_contact is not None else "",
            'employee_gender': employee.employee_gender if employee.employee_gender is not None else "",
        }
        for employee in employees
    ]

    return response_data


@app.post('/signup')
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
                "data": {
                    "branches": [],
                    "employees": [],
                    "role_id": 0}}

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
            response_data = build_company_response(company, db)

            return {
                "status": 200,
                "message": "User Signed Up!",
                "data": response_data}

    except Exception as e:
        print(repr(e))
        return {"status": 500, "message": "Internal Server Error", "data": {
            "branches": [],
            "employees": [],
            "role_id": 0}}


@app.post('/login')
async def login(login_credentials: Union[str, int], login_data: schemas.LoginFlow, db: Session = Depends(get_db)):
    try:
        if login_credentials.isdigit():
            company_contact = int(login_credentials)
            company = db.query(models.Companies).filter(
                models.Companies.company_contact == company_contact
            ).first()
        else:
            company_email = login_credentials
            company = db.query(models.Companies).filter(
                models.Companies.company_email == company_email
            ).first()

        if not company:
            return {
                "status": 404,
                "message": "User not found",
                "data": {
                    "branches": [],
                    "employees": [], "role_id": 0
                }}

        if pwd_context.verify(login_data.login_password, company.company_password if company else ""):
            response_data = build_company_response(company, db)
            return {"status": 200, "message": "Login successful", "data": response_data}
        else:
            return {"status": 401, "message": "Incorrect password", "data": {
                "branches": [],
                "employees": [],
                "role_id": 0
            }}
    except Exception as e:
        print(repr(e))
        return {"status": 500, "message": "Internal Server Error", "data": {
            "branches": [],
            "employees": [], "role_id": 0}}


@app.get('/welcomescreen')
def signup(companyID: str, branchID: int, role_id: int, db: Session = Depends(get_db)):
    try:
        company = db.query(models.Companies).filter(models.Companies.company_id == companyID).first()
        branch = db.query(models.Branch).filter(models.Branch.branch_id == branchID).first()
        response_data = build_company_response(company, db)

        return {
            "status": 200,
            "message": "User Signed Up!",
            "data": response_data

        }
    except Exception as e:
        print(repr(e))
        return {"status": 500, "message": "Internal Server Error", "data": {
            "branches": [],
            "employees": [],
            "role_id": 0}}


@app.post("/company/logo")
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
        response.status_code = 500
        return {"status": 500, "message": "Internal Server Error", "data": {}}
    finally:
        db.close()


@app.delete("/company/logo")
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


@app.post('/company/details')
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


@app.post("/branch")
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
        response.status_code = 500
        return {"status": 500, "message": "Internal Server Error", "data": {}}
    finally:
        db.close()


@app.post("/branch/employee")
def add_employee(branch_id: int, employee_data: schemas.Employee, role_data: schemas.Role,
                 db: Session = Depends(get_db)):
    try:
        branch = db.query(models.Branch).filter_by(branch_id=branch_id).first()
        if branch is None:
            return {"status": 404, "message": "Branch not found",
                    "data": {"New_employee": {}, "role": {}, "unique_id": 0}}

        hashed_password = pwd_context.hash(employee_data.employee_password)
        employee_data.employee_password = hashed_password
        employee_data.branch_id = branch.branch_id
        new_employee = models.Employee(**employee_data.model_dump())
        db.add(new_employee)
        db.commit()
        new_employee_id = new_employee.employee_id
        new_role_name = models.Role(**role_data.model_dump())
        new_role_name.employee_id = new_employee_id
        db.add(new_role_name)
        db.commit()
        new_user = models.NewUsers(
            user_contact=employee_data.employee_contact,
            user_password=employee_data.employee_password,
            user_name=employee_data.employee_name
        )
        db.add(new_user)
        db.commit()
        unique_id = new_user.user_uniqueid
        employee_id = new_employee.employee_id if new_employee.employee_id is not None else ""
        role_id = new_role_name.role_id if new_role_name.role_id is not None else ""
        response_data = {
            "status": 200,
            "message": "New Employee added successfully",
            "data": {
                "New_employee": {
                    key: value for key, value in employee_data.model_dump().items() if value is not None
                },
                "role": {
                    key: value for key, value in role_data.model_dump().items() if value is not None
                },
                "unique_id": unique_id,
                "employee_id": employee_id,
                "role_id": role_id
            }
        }
        return response_data
    except IntegrityError as e:
        print(repr(e))
        return {"status": 500, "message": "Internal Server Error",
                "data": {"New_employee": {}, "role": {}, "unique_id": 0}}
    finally:
        db.close()


def get_employee_info(employee_id: int, db: Session):
    result = db.query(models.Employee.employee_name, models.Role.role_name, models.Role.role_id) \
        .join(models.Role, models.Employee.employee_id == models.Role.employee_id) \
        .filter(models.Employee.employee_id == employee_id).first()
    return (result)


@app.get("/branch/employee/details")
def get_employee_details(branch_id: int, db: Session = Depends(get_db)):
    try:
        employees = db.query(models.Employee).filter_by(branch_id=branch_id).all()
        response_data = {
            "employee_count": len(employees),
            "employees": []
        }
        for employee in employees:
            employee_info = get_employee_info(employee.employee_id, db)
            if employee_info:
                employee_name, role_name, role_id = employee_info
                response_data["employees"].append({
                    "employee_id": employee.employee_id,
                    "employee_name": employee_name,
                    "employee_gender": employee.employee_gender,
                    "employee_contact": employee.employee_contact,
                    "role_name": role_name,
                    "role_key": role_id
                })

        return {"status": 200, "message": "Employee details retrieved successfully", "data": response_data}

    except Exception as e:
        print(repr(e))
        return {"status": 500, "message": "Internal Server Error", "data": {}}


@app.delete("/employee/delete")
def delete_employee(empID: int, branchID: int, db: Session = Depends(get_db)):
    try:
        employee = db.query(models.Employee).filter(models.Employee.employee_id == empID)
        employee_exist = employee.first()
        if not employee_exist:
            return {"status": 404, "message": "Employee doesn't exists", "data": {}}

        branch = db.query(models.Branch).filter(models.Branch.branch_id == branchID)
        branch_exist = branch.first()
        if not branch_exist:
            return {"status": 404, "message": "Branch doesn't exists", "data": {}}

        employee.delete(synchronize_session=False)
        db.commit()
        return {"status": 200, "message": "Employee deleted!", "data": {}}
    except IntegrityError:
        return {"status": 500, "message": "Error", "data": {}}


@app.put("/branch/employee")
def edit_employee(response: Response, branch_id: int, employee_id: int, request_body: schemas.EditEmployee = Body(...),
                  db: Session = Depends(get_db)):
    try:

        employee = db.query(models.Employee).filter(models.Employee.employee_id == employee_id).first()
        if employee is None:
            return {"status": 404, "message": "Employee not found", "data": {}}
        branch = db.query(models.Branch).filter(models.Branch.branch_id == branch_id).first()
        if branch is None:
            return {"status": 404, "message": "Branch not found", "data": {}}
        role = db.query(models.Role).filter(models.Role.employee_id == employee_id).first()

        if request_body.role_name is not None and role:
            role.role_name = request_body.role_name
        if request_body.employee_name is not None:
            employee.employee_name = request_body.employee_name
        if request_body.employee_contact is not None:
            employee.employee_contact = request_body.employee_contact
        if request_body.employee_gender is not None:
            employee.employee_gender = request_body.employee_gender

        db.commit()
        return {"status": 200, "message": "Employee edited successfully", "data": request_body}
    except Exception as e:
        print(repr(e))
        return {"status": 500, "message": "Internal Server Error", "data": {}}
    finally:
        db.close()


@app.get("/productByCategories")
def get_product_by_categories(db: Session = Depends(get_db)):
    try:
        response_data = []
        categories = db.query(Category).all()

        for category in categories:
            category_data = {
                "category_id": category.category_id,
                "category_name": category.category_name,
                "products": []
            }

            products = db.query(Products).filter(Products.category_id == category.category_id).all()

            for product in products:
                brand = db.query(Brand).filter(Brand.brand_id == product.brand_id).first()
                product_data = {
                    "product_id": product.product_id,
                    "product_name": product.product_name,
                    "brand_name": brand.brand_name,
                    "variants": []
                }

                variants = db.query(ProductVariant).filter(ProductVariant.product_id == product.product_id).all()

                for variant in variants:
                    variant_data = {
                        "variant_id": variant.variant_id,
                        "variant_cost": variant.variant_cost,
                        "quantity": variant.quantity,
                        "discounted_cost": variant.discounted_cost,
                        "discount": variant.discount,
                        "stock": variant.stock,
                        "description": variant.description,
                        "image": variant.image,
                        "ratings": variant.ratings,
                        "measuring_unit": variant.measuring_unit,
                        "barcode_no": variant.barcode_no
                    }

                    product_data["variants"].append(variant_data)

                category_data["products"].append(product_data)

            response_data.append(category_data)
        return {
            "status": 200,
            "message": "Variants fetched successfully for all categories!",
            "data": response_data
        }

    except Exception as e:
        print(repr(e))
        return {"status": 500, "message": "Internal Server Error", "data": {}}


@app.post('/addProduct')
def add_product(product_data: ProductInput, db: Session = Depends(get_db)):
    try:
        existing_product = db.query(Products).filter(
            Products.product_name == product_data.product_name).first()

        if existing_product:
            return {"status": 400, "message": "Product already exists!", "data": {}}

        brand = db.query(Brand).filter(
            Brand.brand_name == product_data.brand_name).first()

        if not brand:
            return {"status": 204, "message": "Brand not found", "data": {}}

        category = db.query(Category).filter(
            Category.category_name == product_data.category_name).first()

        if not category:
            category = Category(category_name=product_data.category_name)
            db.add(category)
            db.commit()
            db.refresh(category)

        barcode_no = product_data.barcode_no if product_data.barcode_no is not None else ""

        user = db.query(NewUsers).filter(
            NewUsers.user_uniqueid == product_data.user_id).first()

        if not user:
            return {"status": 204, "message": "User not found", "data": {}}

        branch = db.query(Branch).filter(
            Branch.branch_id == product_data.branch_id).first()

        if not branch:
            return {"status": 204, "message": "Branch not found", "data": {}}

        new_product = Products(
            product_name=product_data.product_name,
            brand_id=brand.brand_id,
            category_id=category.category_id
        )

        db.add(new_product)
        db.commit()
        db.refresh(new_product)

        new_variant = ProductVariant(
            variant_cost=product_data.variant_cost,
            measuring_unit=product_data.measuring_unit,
            brand_name=product_data.brand_name,
            discounted_cost=product_data.discounted_cost,
            quantity=product_data.quantity,
            image=product_data.image,
            stock=product_data.stock,
            description=product_data.description,
            product=new_product,
            branch_id=product_data.branch_id,
            user_id=product_data.user_id,

        )
        db.add(new_variant)


        default_variant = ProductVariant(
            variant_cost=product_data.variant_cost,
            measuring_unit=product_data.measuring_unit,
            brand_name=product_data.brand_name,
            quantity=product_data.quantity,
            stock=0,
            description="",
            product=new_product,
            branch_id=product_data.branch_id,
            user_id=product_data.user_id
        )

        db.add(default_variant)

        db.commit()

        brand_name = brand.brand_name
        category_name = category.category_name

        return {
            "status": 200,
            "message": "New product added successfully!",
            "data": {
                "product_id": new_product.product_id,
                "product_name": new_product.product_name,
                "description": product_data.description,
                "category_name": category_name,
                "brand": brand_name
            }
        }
    except IntegrityError as e:
        if "duplicate key value violates unique constraint" in str(e):
            return {"status": 400, "message": "Check the product name or categories or barcode no", "data": {}}
        else:
            print("Database Error:", str(e))
            raise



@app.post('/addProductVariant/{product_id}')
def add_product_variant(product_id: int, product_data: ProductUpdateInput, db: Session = Depends(get_db)):
    try:
        existing_product_variant = db.query(models.ProductVariant).filter(
            models.ProductVariant.product_id == product_id
        ).first()

        if not existing_product_variant:
            return {"status": 204, "message": "Product variant not found", "data": {}}

        product = existing_product_variant.product

        new_variant = models.ProductVariant(
            variant_cost=product_data.variant_cost,
            brand_name=existing_product_variant.brand_name,
            branch_id=existing_product_variant.branch_id,
            user_id=existing_product_variant.user_id,
            discounted_cost=product_data.discounted_cost,
            stock=product_data.stock,
            quantity=product_data.quantity,
            measuring_unit=product_data.measuring_unit,
            description=existing_product_variant.description,
            product=product,
            barcode_no=product_data.barcode_no,
            image=product_data.image,
        )
        db.add(new_variant)
        db.commit()

        return {"status": 200, "message": "Product variant added successfully"}
    except Exception as e:
        return {"status": 500, "message": "Internal Server Error", "error": str(e)}


@app.put('/editProductVariant')
def edit_product_variant(variant_data: schemas.ProductEdit, db: Session = Depends(get_db)):
    try:
        existing_variant = db.query(models.ProductVariant).filter(
            models.ProductVariant.variant_id == variant_data.variant_id,
            models.ProductVariant.product_id == variant_data.product_id,
            models.ProductVariant.branch_id == variant_data.branch_id,
            models.ProductVariant.user_id == variant_data.user_id).first()

        if not existing_variant:
            return {"status": 204, "detail": "Product variant not found", "data": {}}

        # Update the fields based on the provided data
        for field, value in variant_data.dict().items():
            if value is not None:
                setattr(existing_variant, field, value)

        db.commit()

        return {"status": 200, "message": "Product variant edited successfully!"}
    except IntegrityError as e:
        if "duplicate key value violates unique constraint" in str(e):
            return {"status": 400, "message": "Check the variant details", "data": {}}
        else:
            return {"status": 500, "message": "Internal Server Error", "error": str(e)}


@app.get('/getProductVariant')
def get_product_variant(variant_id: int, db: Session = Depends(get_db)):
    try:
        product_variant = db.query(models.ProductVariant).filter(
            models.ProductVariant.variant_id == variant_id).first()

        if not product_variant:
            return {"status": 204, "message": "product variant not found", "data": {}}

        product = product_variant.product
        category = product_variant.category

        product_input = schemas.ProductInput(
            product_name=product.product_name,
            brand_name=product_variant.brand_name,
            description=product_variant.description,
            category_name=category.category_name,
            image=product_variant.image,
            variant_cost=product_variant.variant_cost,
            discounted_cost=product_variant.discounted_cost,
            stock=product_variant.stock,
            quantity=product_variant.quantity,
            measuring_unit=product_variant.measuring_unit,
            barcode_no=product_variant.barcode_no,
            user_id=product_variant.user_id,
            branch_id=product_variant.branch_id)

        return {
            "status": 200,
            "message": "Product variant details retrieved successfully",
            "data": product_input
        }
    except Exception as e:
        return {"status": 500, "message": "Internal Server Error", "data": str(e)}


@app.get("/productVariants")
def get_product_variants(product_id: int, db: Session = Depends(get_db)):
    try:
        product = db.query(models.Products).filter(models.Products.product_id == product_id).first()

        if not product:
            return {"status": 204, "message": "Product not found", "data": {}}

        variants = (
            db.query(models.ProductVariant)
            .filter(models.ProductVariant.product_id == product_id).all())

        if not variants:
            return {"status": 204, "message": "No variants found for the specified product", "data": {}}

        serialized_variants = []

        for variant in variants:
            serialized_variants.append({
                "variant_cost": variant.variant_cost,
                "unit": variant.measuring_unit,
                "image": variant.image,
                "quantity": variant.quantity})

        response_data = {"product_name": product.product_name, "variants": serialized_variants}

        return {
            "status": 200,
            "message": "Product variants fetched successfully!",
            "data": response_data
        }
    except Exception as e:
        return {"status": 500, "message": "Internal Server Error", "data": str(e)}


# @app.post("/orders/")
# async def create_order(order: OrderCreate):
#     db = SessionLocal()
#     try:
#         product_details = []
#
#         for product_data in order.product_list:
#             product_id = product_data.get("product_id")
#             variant_id = product_data.get("variant_id")
#             item_count = product_data.get("item_count")
#
#             product_variant = db.query(ProductVariant).filter(
#                 ProductVariant.product_id == product_id,
#                 ProductVariant.variant_id == variant_id
#             ).first()
#
#             if product_variant:
#                 if product_variant.stock is not None and product_variant.stock >= item_count:
#                     product_variant.stock -= item_count
#                 else:
#                     return {"status": 400, "message": f"Product with ID {product_id} is out of stock", "data": {}}
#             else:
#                 return {"status": 400, "message": f"Product ID {product_id} with variant ID {variant_id} is not found",
#                         "data": {}}
#
#             variant_cost = product_variant.variant_cost if hasattr(product_variant, 'variant_cost') else 0.0
#
#             product_variant_data = {
#                 "product_id": product_id,
#                 "variant_id": variant_id,
#                 "item_count": item_count,
#                 "variant_cost": variant_cost,
#             }
#
#             product_details_db = db.query(Products.product_name, ProductVariant.measuring_unit,
#                                           ProductVariant.discount, ProductVariant.discounted_cost,
#                                           ProductVariant.image). \
#                 join(ProductVariant, Products.product_id == ProductVariant.product_id). \
#                 filter(Products.product_id == product_id, ProductVariant.variant_id == variant_id).first()
#
#             if product_details_db:
#                 product_variant_data.update({
#                     "product_name": product_details_db.product_name,
#                     "measuring_unit": product_details_db.measuring_unit,
#                     "discounted_cost": product_details_db.discounted_cost,
#                 })
#
#             product_details.append(product_variant_data)
#
#         total_order = sum(product["variant_cost"] * product["item_count"] for product in product_details)
#
#         db_order = Order(
#             order_no=order.order_no,
#             customer_contact=order.customer_contact,
#             product_list=product_details,
#             total_order=total_order,
#             gst_charges=order.gst_charges,
#             additional_charges=order.additional_charges,
#             to_pay=order.to_pay,
#         )
#
#         db.add(db_order)
#         db.commit()
#         db.refresh(db_order)
#
#         payment_type = order.payment_type
#         if payment_type:
#             payment_info = Payment(order_id=db_order.order_id, payment_type=payment_type)
#             db.add(payment_info)
#             db.commit()
#
#         response_data = {
#             "order_no": order.order_no,
#             "product_list": product_details,
#             "total_order": total_order,
#             "gst_charges": order.gst_charges,
#             "additional_charges": order.additional_charges,
#             "to_pay": order.to_pay,
#             "payment_type": payment_type,
#         }
#
#         return {"status": 200, "message": "Order created successfully", "data": response_data}
#     except HTTPException as e:
#         db.rollback()
#         raise e
#     except IntegrityError as e:
#         return {"status": 400, "message": "Error creating order", "data": {}}
#     except NoResultFound as e:
#         return {"status": 400, "message": "Product or variant not found", "data": {}}
#     except Exception as e:
#         return {"status": 500, "message": "Internal Server Error", "error": str(e)}
#     finally:
#         db.close()


TABLE_NAME = "product_variants"


@app.post("/upload_products_excel/")
async def upload_products_excel(
        response: Response,
        file: UploadFile = File(...),
        db: Session = Depends(get_db),
):
    # Read the Excel file from the uploaded file
    data = await file.read()
    df = pd.read_excel(BytesIO(data))

    # Define the database engine
    # engine = create_engine(DATABASE_URL)

    # Append the data to the database, avoiding duplicates
    try:
        df.to_sql(TABLE_NAME, engine, if_exists="append", index=False)
        return {"message": "Products uploaded from Excel successfully"}
    except Exception as e:
        response.status_code = 500
        return {"status_code": 500, "detail": str(e)}


#
# @app.get("/get_all_orders", response_model=OrderList)
# def get_all_orders(db: Session = Depends(get_db)):
#     try:
#         orders = db.query(Order).all()
#
#         if not orders:
#             return JSONResponse(content={"status": "204", "message": "No orders found", "data": []})
#
#         serialized_orders = [
#             {
#                 "order_id": order.order_id,
#                 "order_no": order.order_no,
#                 "product_list": order.product_list,
#                 "total_order": order.total_order,
#                 "gst_charges": order.gst_charges,
#                 "additional_charges": order.additional_charges,
#                 "to_pay": order.to_pay
#             }
#             for order in orders
#         ]
#
#         return JSONResponse(
#             content={"status": 200, "message": "Orders fetched successfully", "data": serialized_orders})
#     except Exception as e:
#         return JSONResponse(content={"status": 500, "message": "Internal Server Error", "data": str(e)})


@app.delete('/deleteProduct')
def delete_product_by_id(product_id: int = Query(None, description="Product ID to delete"),
                         db: Session = Depends(get_db)):
    try:
        if product_id is None:
            return {"status": 400, "message": "product_id is required", "data": {}}

        product = db.query(models.Products).filter(models.Products.product_id == product_id).first()

        if not product:
            return {"status": 204, "message": "Product not found", "data": {}}

        db.query(models.Products).filter(models.Products.product_id == product_id).delete()
        db.commit()

        return {"status": 200, "message": "Product deleted successfully", "data": {}}
    except Exception as e:
        return {"status": 500, "message": "Internal Server Error", "error": str(e)}


@app.delete('/deleteProductVariant')
def delete_product_variant(product_id: int, variant_id: int, db: Session = Depends(get_db)):
    try:
        variant = db.query(models.ProductVariant).filter(
            models.ProductVariant.product_id == product_id,
            models.ProductVariant.variant_id == variant_id).first()

        if not variant:
            return {"status": 204, "message": "product not found", "data": {}}

        db.query(models.ProductVariant).filter(
            models.ProductVariant.product_id == product_id,
            models.ProductVariant.variant_id == variant_id).delete()
        db.commit()

        return {"status": 200, "message": "Product variant deleted successfully", "data": {}}
    except Exception as e:
        return {"status": 500, "message": "Internal Server Error", "error": str(e)}


@app.get("/getAllBranches")
async def get_branches(db: Session = Depends(get_db)):
    try:
        branches = db.query(models.Branch).all()
        if not branches:
            return {"status": 204, "message": "No branches found", "data": []}

        serialized_branches = [
            {"branch_id": branch.branch_id,
             "branch_name": branch.branch_name,
             "branch_address": branch.branch_address,
             "branch_email": branch.branch_email,
             "branch_number": branch.branch_number}
            for branch in branches
        ]

        return {"status": 200, "message": "All branches fetched!", "data": serialized_branches}
    except Exception as e:
        print(repr(e))
        Response.status_code = 500
        return {"status": "500", "message": "Internal Server Error", "data": str(e)}



@app.put("/editBranch/")
async def edit_branch(
        branch_data: schemas.BranchUpdate,
        branch_id: int = Query(..., title="Branch ID", description="The ID of the branch to edit", gt=0),
        db: Session = Depends(get_db)
):
    try:
        branch = db.query(models.Branch).filter(models.Branch.branch_id == branch_id).first()
        if not branch:
            return {"status": 204, "message": "Branch not found", "data": {}}

        if branch_data.branch_name:
            branch.branch_name = branch_data.branch_name
        if branch_data.branch_address:
            branch.branch_address = branch_data.branch_address
        if branch_data.branch_email:
            branch.branch_email = branch_data.branch_email
        if branch_data.branch_number:
            branch.branch_number = branch_data.branch_number

        db.commit()
        db.refresh(branch)

        return {"status": 200, "message": "Branch updated successfully", "data": {}}
    except Exception as e:
        print(repr(e))
        return {"status": 500, "message": "Internal Server Error", "data": str(e)}


@app.delete("/deleteBranch/")
async def delete_branch(
        branch_id: int = Query(..., title="Branch ID", description="The ID of the branch to delete", gt=0),
        db: Session = Depends(database.get_db)
):
    try:
        branch = db.query(models.Branch).filter(models.Branch.branch_id == branch_id).first()
        if not branch:
            return {"status": 204, "message": "Branch Not Found", "data": {}}
        db.delete(branch)
        db.commit()

        return {"status": 200, "message": "Branch deleted successfully", "data": {}}
    except Exception as e:
        print(repr(e))
        return {"status": 500, "message": "Internal Server Error", "data": str(e)}
