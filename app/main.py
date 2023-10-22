from typing import List, Union
from uuid import uuid4
from urllib import response
from fastapi.responses import JSONResponse
import firebase_admin
from firebase_admin import credentials, storage
from passlib.context import CryptContext
from fastapi import FastAPI, Response, Depends, File, Body, UploadFile, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, DataError
import logging
import shutil
from datetime import timedelta
from . import models, schemas
from .models import Image
from .database import engine, get_db, SessionLocal
from fastapi.middleware.cors import CORSMiddleware
import os

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

directory = "app/uploaded_images"
if not os.path.exists(directory):
    os.makedirs(directory)


@app.get('/')
def root():
    return {'message': 'Hello world'}


def save_upload_file(upload_file: UploadFile, destination: str):
    try:
        with open(destination, "wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)
    finally:
        upload_file.file.close()


@app.post("/upload/images")
async def upload_images(upload_files: List[UploadFile] = File(...),
                        replace_existing_images: bool = True, db: Session = Depends(get_db)):
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
async def delete_image(response: Response, product_id: int, variant_id: int,
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
        except:
            db.rollback()
            return {"status_code": 500, "message": " Database error"}
    else:
        return {"status_code": 404, "message": "Image URL not found in the product variant"}


def build_company_response(company, db):
    response_data = {
        "status": 200,
        "message": "Company logged in successfully!",
        "data": {
            "companyId": company.company_id if company.company_id is not None else "",
            "company_contact": company.company_contact if company.company_contact is not None else "",
            "company_email": company.company_email if company.company_email is not None else "",
            "company_name": company.company_name if company.company_name is not None else "",
            "role_id": 0000
        }
    }
    company_id = company.company_id
    branches = db.query(models.Branch).filter(models.Branch.company_id == company_id).all()
    employees = db.query(models.Employee).join(models.Branch).filter(models.Branch.company_id == company_id).all()
    response_data['data']['branches'] = [
        {
            'branch_id': branch.branch_id if branch.branch_id is not None else "",
            'branch_email': branch.branch_email if branch.branch_email is not None else "",
            'branch_name': branch.branch_name if branch.branch_name is not None else "",
            'branch_number': branch.branch_number if branch.branch_number is not None else "",
            'branch_address': branch.branch_address if branch.branch_address is not None else "",
        }
        for branch in branches
    ]
    response_data['data']['employees'] = [
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
def signup(response: Response, company_data: schemas.CompanySignUp = Body(...),
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
                "data": {},
            }
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
                "data": {
                    "company_name": new_company.company_name if company.company_name is not None else "",
                    "signup_credentials": signup_credentials,
                    "response_data": response_data
                }
            }
    except Exception as e:
        print(repr(e))
        return {"status": 500, "message": "Internal Server Error", "data": {}}


@app.post('/login')
def login_company(login_credentials: Union[str, int], login_data: schemas.LoginFlow, response: Response,
                  db: Session = Depends(get_db)):
    try:
        user = (
                db.query(models.Companies).filter(models.Companies.company_email == login_credentials).first()
                or
                db.query(models.Companies).filter(models.Companies.company_contact == login_credentials).first()
        )
        if user:
            if pwd_context.verify(login_data.login_password, user.company_password if isinstance(user,
                                                                                                 models.Companies) else user.employee_password):
                if isinstance(user, models.Companies):
                    return build_company_response(user, db)
                else:
                    return build_company_response(user, db)
            else:
                return {"status": 401, "message": "Incorrect password", "data": {}}
        return {"status": 400, "message": "Incorrect password", "data": {}}
    except DataError:
        return {"status": 400, "message": "Invalid login credential", "data": {}}
    except Exception as e:
        print(repr(e))
        return {"status": 500, "message": "Internal Server Error", "data": {}}


@app.get('/welcomescreen')
def signup(response: Response, companyID: str, branchID: int, role_id: int, db: Session = Depends(get_db)):
    try:
        company = db.query(models.Companies).filter(models.Companies.company_id == companyID).first()
        branch = db.query(models.Branch).filter(models.Branch.branch_id == branchID).first()
        response_data = build_company_response(company, db)

        return {
            "status": 200,
            "message": "User Signed Up!",
            "data": {
                "response_data": response_data
            }
        }
    except Exception as e:
        print(repr(e))
        return {"status": 500, "message": "Internal Server Error", "data": {}}


@app.post('/company/details')
def update_company_details(company_id: str, response: Response, request_body: schemas.CompanyUpdateDetails = Body(...),
                           db: Session = Depends(get_db)):
    try:
        company = db.query(models.Companies).filter(models.Companies.company_id == company_id).first()
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
            return {"status_code": 404, "message": "Company not found", "data": {}}

        existing_branch = db.query(models.Branch).filter_by(company_id=company.company_id,
                                                            branch_name=branch_data.branch_name).first()
        if existing_branch:
            return {"status_code": 400, "message": "Branch with the same name already exists", "data": {}}

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


def get_employee_info(employee_id: int, db: Session):
    result = db.query(models.Employee.employee_name, models.Role.role_name, models.Role.role_id) \
        .join(models.Role, models.Employee.employee_id == models.Role.employee_id) \
        .filter(models.Employee.employee_id == employee_id).first()
    return result


@app.post("/branch/employee")
def add_employee(branch_id: int, employee_data: schemas.Employee, role_data: schemas.Role, response: Response,
                 db: Session = Depends(get_db)):
    try:

        employees = db.query(models.Employee).filter_by(branch_id=branch_id).all()
        branch = db.query(models.Branch).filter_by(branch_id=branch_id).first()
        if branch is None:
            return {"status": 404, "message": "Branch not found", "data": {}}

        existing_employee = db.query(models.Employee).filter(
            models.Employee.employee_contact == employee_data.employee_contact).first()
        if existing_employee:
            return {"status": 400, "message": "User already exists", "data": {}}

        existing_user = db.query(models.NewUsers).filter(
            models.NewUsers.user_contact == employee_data.employee_contact).first()
        if existing_user:
            return {"status": 400, "message": "User already exists", "data": {}}

        hashed_password = pwd_context.hash(employee_data.employee_password)
        employee_data.employee_password = hashed_password
        employee_data.branch_id = branch.branch_id
        new_employee = models.Employee(**employee_data.model_dump())
        db.add(new_employee)
        db.commit()

        new_employee_id = new_employee.employee_id
        role_data.role_name = role_data.role_name
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

        return {"status": 200, "message": "New Employee added successfully",
                "data": {"New_employee": employee_data, "role": role_data, "unique_id": unique_id}}
    except IntegrityError as e:
        print(repr(e))
        response.status_code = 500
        return {"status": 500, "message": "Internal Server Error", "data": {}}
    finally:
        db.close()


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


@app.delete("/employee/delete")
def delete_employee(response: Response, empID: int, branchID: int, db: Session = Depends(get_db)):
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


@app.post('/addProduct')
def add_product(branchID: int, userID: int, product_data: schemas.ProductInput, db: Session = Depends(get_db)):
    try:
        branch = db.query(models.Branch).filter(models.Branch.branch_id == branchID)
        user = db.query(models.NewUsers).filter(models.NewUsers.user_uniqueid == userID)
        existing_product = db.query(models.Products).filter(
            models.Products.product_name == product_data.product_name).first()
        if existing_product:
            return JSONResponse(content={"status": 400, "message": "Product already exists!", "data": {}})
        brand = db.query(models.Brand).filter(models.Brand.brand_id == product_data.brand_id).first()
        if not brand:
            return JSONResponse(content={"status": 400, "message": "Brand not found", "data": {}})
        category = db.query(models.Categories).filter(models.Categories.category_id == product_data.category_id).first()
        if not category:
            category = models.Categories(category_id=product_data.category_id)
            db.add(category)
            db.commit()
            db.refresh(category)
        new_product = models.Products(
            product_name=product_data.product_name,
            brand_id=product_data.brand_id,
            category_id=product_data.category_id,
            branch_id=branchID,
            user_id=userID
        )
        db.add(new_product)
        db.commit()
        db.refresh(new_product)
        new_variant = models.ProductVariant(
            variant_cost=product_data.variant_cost,
            measuring_unit=product_data.measuring_unit,
            brand_id=product_data.brand_id,
            discounted_cost=product_data.discounted_cost,
            quantity=product_data.quantity,
            stock=product_data.stock,
            description=product_data.description,
            product_id=new_product.product_id,
            category_id=product_data.category_id,
            barcode_no=product_data.barcode_no,
        )
        db.add(new_variant)
        db.commit()
        product_category = models.CategoryProduct(
            product_id=new_product.product_id,
            category_id=category.category_id,
        )
        db.add(product_category)
        db.commit()
        brand_id = brand.brand_id
        category_id = category.category_id
        return JSONResponse(content={
            "status": 200,
            "message": "New product added successfully!",
            "data": {
                "product_id": new_product.product_id,
                "category_id": category_id,
                "brand_id": brand_id,
                "product_name": new_product.product_name,
                "description": product_data.description,
            }
        })
    except IntegrityError as e:
        if "duplicate key value violates unique constraint" in str(e):
            return JSONResponse(content={"status": 400, "message": "Check the product name and categories", "data": {}})
        else:
            print("Database Error:", str(e))
            raise


@app.get("/company/description")
def fetch_description(response: Response, companyID: str, db: Session = Depends(get_db)):
    try:
        company = db.query(models.Companies).filter(models.Companies.company_id == companyID).first()
        if company:
            company_description = company.company_description if company.company_description is not None else ""
            return {"status": 200, "message": "Company description fetched successfully!", "data": company_description}
        else:
            return {"status": 404, "message": "Company not found!", "data": {}}
    except Exception as e:
        print(repr(e))
        return {"status": 500, "message": "Internal Server Error!", "data": {}}

# @app.post("/user/details")
# def fetch_user_details(response : Response, userID : int,db: Session = Depends(get_db),editUser = schemas.EditUser):
#     try:
#         user = db.query(models.NewUsers).filter(models.NewUsers.user_uniqueid == userID).first()
#         # company = db.query(models.Companies).filter(models.Companies.company_id == companyID).first()
#         # branch = db.query(models.Branch).filter(models.Branch.branch_id == branchID).first()
#         if user:
#             if editUser.user_image is not None:
#                 user.user_image = editUser.user_image
#             if editUser.user_name is not None:
#                 user.user_name = editUser.user_name
#             if editUser.user_contact is not None:
#                 user.user_contact = editUser.user_contact
#             if editUser.user_emailId is not None:
#                 user.user_emailId = editUser.user_emailId
#             db.commit()
#             return {"status": 200, "message": "User details updated successfully", "data": user}
#         else:
#             return {"status": 404, "message": "User not found", "data": {}}
#     except Exception as e:
#         print(repr(e))
#         return {"status": 500, "message": "Internal Server Error", "data": {}}
