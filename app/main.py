from typing import List, Optional, Dict
from contextlib import contextmanager
from uuid import uuid4
from urllib import response
from collections import defaultdict
import bcrypt
import firebase_admin
from firebase_admin import credentials, db, storage
from passlib.context import CryptContext
from fastapi import FastAPI, Response, Depends, File, Request, HTTPException, Body, Path, UploadFile, Form
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from starlette.responses import FileResponse
import logging
from sqlalchemy import select, func, update

from . import models, schemas
from .models import Image, Products, ProductVariant, FavItem, CategoryProduct, Review, Categories
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

cred = credentials.Certificate({
  "type": "service_account",
  "project_id": "onecart-5f6a8",
  "private_key_id": "38c1e579ad08c6f059967f28369307f30b05eb5c",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDC5Bs6pGly2HUZ\niXzinRJNxiQl11bdZ8JgoQPzyqSPFq6IbQePSBs82ntbSjxHf6x4jjYGRD3oBA93\npjyaViU9PlKP7uoLoqVAz22jfyK66OD6f8svtzjXqAYnyi0Q78GbnEoAygFOOiVw\n6D3ka65MCiKiAcjWwbqx9aN9AsTSK+nBZsfrDd9d1MSDofAvmlM3NNDtTJ4Z33TV\nE39CpJfBEcqxkFRDMI4nckOnJ6/WFNC7ec0Ey6zXxgrjibwQ/7sWuTWkYmqbRUyx\nC/9+QR0f+DToOG15AphEJpKngdayFI2rw/OE23Vz1wyKqKhsoEYark92GZnPZc28\nmprFQlZFAgMBAAECggEAH6GPpM0t+zCUEuS8cvhM0fgsgkLIy68NPosrncwgOMQU\n6DoP7cqldxM7zbWHApC/gKKONKarSIauLvx5XhBIw3+jvU4oyOIpQZNZB135WE43\nQ5jttK0faesQsrEO7u6G5Rdw8F9Y5mYsEP70mqf6dkd31wUEoIx5XWxRkFbcdILZ\nAMbJo5+YmRCAunB35OrN5DTRp5ODU6Ab1xxXXwX5AVL8IbaEJdHDX6wA6JKl+9TH\n/x2nOr4scpmprjHnWPWQJkDW4W3LR4fwyghb2bnemKhkON5Bl5wH3CJwKZAEe+x0\nWGbUAdBqD2IBX4+HayR8JGhu0oeFAe55E7dts+PiyQKBgQDosee0S6+kmgKcuCFg\n+1Il/qI/BaBjTNzkfleHnzSqSD6L8b5Yh0OwzxBrtaVh3m1LuZ/I1r41yStlf829\njY86u77ZetWvmydSem8jqUnP9MTEOodjEU/SDgvZpkj1hLBFM5AhCk4yRF0jqj07\ndA/UWgd/sgLnh/Ca5tGkOs83/QKBgQDWaPE5jhgPunZWPyE4UTlvE0+cihBv4/Ef\nKYBDJ0nsom6etSq0nNBrD/ElQJyK9HcOykayZR8SZnEZSkHCphlL05MQqYAaIB2V\nqPKmb6R+1mAVDaMeWSWF2Eg3E4uWIVdmhvzcN3QYzSvBnvbio4xQ4QCmaCkegwmR\niUGY6qU16QKBgFdBdvA9vVRMyBP6W9HhC/HhZPea5YS26tHnqmzZv0bnJkUV1lme\nBz0CuFabW7OyU2uk5IzMMbE7iUFbRkwBDCdrBWrJy904oeskrA5EScBoOWyXwfLd\nKABNchYga5VdNzgL2Mz6702cIwzfpmxn3hOz2sIAf2RQrmF3kj8yKkgFAoGBAMi8\nFWOqKdLH4rSahBKC0P+yF63aAMuQn5VqOGAmr2oxJNnHiYTw75vcoAsdc7IQcErT\ni97HF5EVgbuIrwp6kWJRYfWOi5VqDeio9Qxnp5zsPaZYTyhBlAS8Wdfen6fd7ULb\nDG9sJ3B03gt3NXM4ZUzvarlg+WZMji/ITjbJMAXJAoGBAItWLAgjFNq4Tt6A+9eN\nXmXFB3QmiwyN8HDQNzs6WxpoqhBm52yaD/F+wE8Tp/KswiwqNLjRYNo5XiUk2mj8\nShgS3UyrMK+ZJyb+OCD15G/QdVsPUWB8/6q4B4sdoWvp3qrlj/lfMdQ+d6+JYgcl\nNJCL44NeX0QSptNEMsRKjPPA\n-----END PRIVATE KEY-----\n",
  "client_email": "firebase-adminsdk-1g1po@onecart-5f6a8.iam.gserviceaccount.com",
  "client_id": "108694359227909599503",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-1g1po%40onecart-5f6a8.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
})

firebase_admin.initialize_app(cred, {"sotageBucket": 'gs://onecart-5f6a8.appspot.com'})



@app.get('/')
def root():
    return {'message': 'Hello world'}


# class ImageUploadResponse(BaseModel):
#     image_url: str

@app.post("/upload-image/")
async def upload_image(
    image: UploadFile = File(...),
    product_id: int = Form(...),
    variant_id: int = Form(...),
    db: Session = Depends(get_db),
):
    try:
        # Upload the image to Firebase Storage
        bucket = storage.bucket()
        blob = bucket.blob(f"product_images/{product_id}/{variant_id}/{image.filename}")
        blob.upload_from_string(image.file.read(), content_type=image.content_type)

        # Get the URL of the uploaded image from Firebase
        image_url = blob.public_url

        # Store the image URL in your local database
        product_variant = db.query(models.ProductVariant).filter_by(
            product_id=product_id, variant_id=variant_id
        ).first()

        if product_variant:
            existing_images = product_variant.image or []
            existing_images.append(image_url)
            product_variant.image = existing_images
            db.commit()

        return {"image_url": image_url}

    except Exception as e:
        print(repr(e))
        # Handle any errors that may occur during image upload or database update
        return {"error": str(e)}


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

@app.post("/multipleUpload")
async def upload_image(request: Request, files: List[UploadFile] = File(...), db: Session = Depends(get_db)):
    image_urls = []
    for file in files:
        contents = await file.read()
        filename = file.filename
        file_path = os.path.join(UPLOAD_DIR, filename)

        with open(file_path, "wb") as f:
            f.write(contents)

        image = Image(filename=filename, file_path=file_path)
        try:
            db.add(image)
            db.commit()
            db.refresh(image)
        except Exception as e:
            logging.error(f"Error storing image {filename}: {e}")
            db.rollback()
        finally:
            db.close()
        base_url = request.base_url
        image_url = f"{base_url}images/{file.filename}"
        image_urls.append(image_url)

    return {"status": 200, "message": "Images uploaded successfully", "data": {"image_url": image_urls}}

# @app.post("/product/image")
# async def upload_image(request: Request, product_id: int, variant_id: int,  files: List[UploadFile] = File(...), db: Session = Depends(get_db)):
#     image_urls = []
#     for file in files:
#         contents = await file.read()
#         filename = file.filename
#         file_path = os.path.join(UPLOAD_DIR, filename)
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
#
#         base_url = request.base_url
#         image_url = f"{base_url}images/{file.filename}"
#         image_urls.append(image_url)
#
#     product_variant = db.query(ProductVariant).filter_by(product_id=product_id, variant_id=variant_id).first()
#     if product_variant:
#         existing_images = product_variant.image or []
#         existing_images += image_urls
#         product_variant.image = existing_images
#         db.commit()
#
#     return {"status": 200, "message": "Images uploaded successfully", "data": {"image_urls": image_urls}}

@app.post("/product/image")
async def edit_product_images(
    request: Request,
    product_id: int,
    variant_id: int,
    new_files: List[UploadFile] = File(...),
    remove_images: List[str] = Body(...),
    db: Session = Depends(get_db)
):
    try:
        product_variant = db.query(ProductVariant).filter_by(product_id=product_id, variant_id=variant_id).first()
        if not product_variant:
            return {"status": 404, "message": "Product variant not found"}

        # Remove the specified images
        existing_images = [image for image in product_variant.image if image not in remove_images]

        # Upload new images
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

        # Combine existing and new images
        updated_images = existing_images + new_image_urls

        # Update the product variant with the updated image URLs
        product_variant.image = updated_images
        db.commit()

        return {"status": 200, "message": "Images updated successfully", "data": {"image_urls": updated_images}}
    except Exception as e:
        print(repr(e))
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        db.close()

@app.post('/userAuthenticate')
def create_user(loginSignupAuth: schemas.UserData, response: Response,
                db: Session = Depends(get_db), companyName=str):
    try:
        user_data = db.query(models.User).get(
            loginSignupAuth.customer_contact)

        if not user_data:
            # try:
            new_user_data = models.User(
                **loginSignupAuth.model_dump())
            new_user_added = models.UserCompany(  # composite table
                company_name=companyName,
                user_contact=loginSignupAuth.customer_contact)
            db.add(new_user_data)
            db.add(new_user_added)
            db.commit()
            db.refresh(new_user_data)
            return {"status": 200, "message": "New user successfully created!", "data": new_user_data}
        # except IntegrityError:
        #     response.status_code = 200
        #     return {"status": 204, "message": "User is not registered please Sing up", "data": {}}

        user_exists = db.query(models.UserCompany).filter(models.UserCompany.company_name == companyName).filter(
            models.UserCompany.user_contact == loginSignupAuth.customer_contact).first()
        print(user_exists)
        if not user_exists:
            try:
                new_user_company = models.UserCompany(
                    company_name=companyName,
                    user_contact=loginSignupAuth.customer_contact)
                db.add(new_user_company)
                db.commit()
                db.refresh(new_user_company)
                return {"status": 200, "message": "New user successfully Logged in!", "data": user_data}
            except IntegrityError:
                response.status_code = 200
                return {"status": "204", "message": "User is not registered for this company please Sing up",
                        "data": {}}

        return {"status": 200, "message": "New user successfully Logged in for this company!", "data": user_data}

    except IntegrityError as e:
        print(repr(e))
        response.status_code = 404
        return {"status": 404, "message": "Error", "data": {}}

@app.put('/editUser/{userId}')
def edit_user(userDetail: schemas.EditUserData, response: Response, db: Session = Depends(get_db),
              userId=int):
    try:
        edit_user_details = db.query(models.User).filter(models.User.customer_contact == userId)

        user_exist = edit_user_details.first()
        if not user_exist:
            response.status_code = 200
            return {"status": 204, "message": "User doesn't exists", "data": {}}

        edit_user_details.update(userDetail.model_dump(), synchronize_session=False)
        db.commit()
        return {"status": 200, "message": "user edited!", "data": edit_user_details.first()}
    except IntegrityError as e:
        print(repr(e))
        response.status_code = 404
        return {"status": 404, "message": "Error", "data": {}}


@app.post("/addAddress")
def add_address(user_contact: int, createAddress: schemas.AddAddress, response: Response,
                db: Session = Depends(get_db)):
    try:

        new_address = models.Addresses(**createAddress.model_dump())
        db.add(new_address)
        db.commit()
        db.refresh(new_address)

        return {"status": "200", "message": "New address created!", "data": new_address}
    except IntegrityError as e:
        print(repr(e))
        response.status_code = 404
        return {"status": "404", "message": "Error", "data": {}}


@app.get('/getAllAddresses')
def get_address(response: Response, db: Session = Depends(get_db), userId=int):
    try:
        user_addresses = db.query(models.Addresses).filter(
            models.Addresses.user_contact == userId).all()

        if not user_addresses:
            response.status_code = 200
            return {"status": "200", "message": "No address found", "data": []}

        return {"status": "200", "message": "success", "data": user_addresses}
    except IntegrityError:
        response.status_code = 404
        return {"status": "404", "message": "Error", "data": {}}


@app.put('/editAddress')
def edit_address(editAddress: schemas.EditAddress, response: Response, db: Session = Depends(get_db), addressId=int):
    try:
        edit_user_address = db.query(models.Addresses).filter(
            models.Addresses.address_id == addressId)
        address_exist = edit_user_address.first()
        if not address_exist:
            response.status_code = 200
            return {"status": 204, "message": "Address doesn't exists", "data": {}}

        edit_user_address.update(editAddress.model_dump(
            exclude_unset=True), synchronize_session=False)
        db.commit()
        return {"status": "200", "message": "address edited!", "data": edit_user_address.first()}

    except IntegrityError as e:
        print(repr(e))
        response.status_code = 404
        return {"status": "404", "message": "Error", "data": {}}


@app.delete('/deleteAddress')
def delete_user_address(response: Response, db: Session = Depends(get_db), addressId=int):
    try:
        delete_address = db.query(models.Addresses).filter(
            models.Addresses.address_id == addressId)
        address_exist = delete_address.first()
        if not address_exist:
            response.status_code = 200
            return {"status": "204", "message": "Address doesn't exists", "data": {}}

        delete_address.delete(synchronize_session=False)
        db.commit()
        return {"status": "200", "message": "Address deleted!"}
    except IntegrityError:
        response.status_code = 404
        return {"status": "404", "message": "Error", "data": {}}


# @app.post('/signupCompany')
# def add_companies(addCompany: schemas.CompanySignUp, response: Response, db: Session = Depends(get_db)):
#     try:
#         existing_company = db.query(models.Companies).filter(
#             models.Companies.company_email == addCompany.company_email).first()
#         if existing_company:
#             return {"status": 200, "message": "Company Signup Completed. Please fill in company details.",
#                     "data": existing_company}
#
#         salt = bcrypt.gensalt()
#         password = bcrypt.hashpw(addCompany.company_password.encode('utf-8'), salt)
#         new_company = models.Companies(**addCompany.model_dump())
#         new_company.password = password.decode('utf-8')
#         db.add(new_company)
#         db.commit()
#         db.refresh(new_company)
#
#         return {"status": 200, "message": "Company Signed Up!", "data": new_company}
#     except Exception as e:
#         print(repr(e))
#         response.status_code = 500
#         return {"status": 500, "message": "Internal Server Error", "data": {}}

# @app.post('/signupCompany')
# def add_companies(addCompany: schemas.CompanySignUp, response: Response, db: Session = Depends(get_db)):
#     try:
#         existing_company = db.query(models.Companies).filter(
#             models.Companies.company_email == addCompany.company_email).first()
#         if existing_company:
#             return {"status": 200, "message": "Company Signup Completed. Please fill in company details.",
#                     "data": existing_company}
#
#         hashed_password = pwd_context.hash(addCompany.company_password)
#         user.password = hashed_password
#         salt = bcrypt.gensalt()
#         password = bcrypt.hashpw(addCompany.company_password.encode('utf-8'), salt)  # Removed .encode('utf-8')
#         new_company = models.Companies(**addCompany.model_dump())
#         new_company.password = password.decode('utf-8')
#         db.add(new_company)
#         db.commit()
#         db.refresh(new_company)
#
#         return {"status": 200, "message": "Company Signed Up!", "data": new_company}
#     except Exception as e:
#         print(repr(e))
#         response.status_code = 500
#         return {"status": 500, "message": "Internal Server Error", "data": {}}

@app.post('/signupcompany')
async def add_companies(addCompany: schemas.CompanySignUp, response: Response, db: Session = Depends(get_db)):
    try:
        existing_company = db.query(models.Companies).filter(
            models.Companies.company_email == addCompany.company_email).first()
        if existing_company:
            return {"status": 400, "message":"Company already exists", "data": {}}

        hashed_password = pwd_context.hash(addCompany.company_password)

        company_id = uuid4().hex

        new_company = models.Companies(
            company_id=company_id,
            company_email=addCompany.company_email,
            company_password=hashed_password
        )

        db.add(new_company)
        db.commit()
        db.refresh(new_company)

        return {"status": 200, "message": "Company Signed Up!", "data": {
            "company_id": new_company.company_id,
            "company_email": new_company.company_email,
        }}
    except Exception as e:
        print(repr(e))
        response.status_code = 500
        return {"status": 500, "message": "Internal Server Error", "data": {}}

# def create_company_from_signup(signup_data: schemas.CompanySignUp):
#     salt = bcrypt.gensalt()
#     hashed_password = bcrypt.hashpw(signup_data.company_password.encode(), salt)
#
#     return Companies(
#         company_name=signup_data.company_name,
#         company_password=hashed_password.decode(),
#         company_email=signup_data.company_email,
#     )

# @app.post('/signupCompany')
# def add_companies(addCompany: schemas.CompanySignUp, response: Response, db: Session = Depends(get_db)):
#     try:
#         existing_company = db.query(models.Companies).filter(models.Companies.company_email == addCompany.company_email).first()
#         if existing_company:
#             return {"status": 200, "message": "Company Signup Completed. Please fill in company details.",
#                     "data": existing_company}
#
#         new_company = create_company_from_signup(addCompany)
#         db.add(new_company)
#         db.commit()
#         db.refresh(new_company)
#
#         return {"status": 200, "message": "Company Signed Up!", "data": new_company}
#     except Exception as e:
#         print(repr(e))
#         response.status_code = 500
#         return {"status": 500, "message": "Internal Server Error", "data": {}}
@app.post('/logincompany')
def login_company(login_data: schemas.CompanyLogin, response: Response, db: Session = Depends(get_db)):
    try:
        company = db.query(models.Companies).filter(models.Companies.company_email == login_data.company_email).first()

        if company:
            if pwd_context.verify(login_data.company_password, company.company_password):
                return {"status": 200, "message": "Company logged in successfully!", "data":  {
            "company_id": company.company_id,
            "company_email": company.company_email,
        }}
            else:
                return {"status": 401, "message": "Incorrect password", "data": {}}
        else:
            return {"status": 404, "message": "Company not found", "data": {}}
    except Exception as e:
        print(repr(e))
        response.status_code = 500
        return {"status": 500, "message": "Internal Server Error", "data": {}}
@app.post("/company/logo")
async def upload_company_logo(request: Request, logo: UploadFile = File(...), company_id: str = Form(...),  db: Session = Depends(get_db)):
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
            company.company_logo = logo_url  # Store the full image URL in the database
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
        return{"status" : 500, "message": "Internal Server Error","data": {}}
    finally:
        db.close()

@app.put('/company/details')
def update_company_details(company_id: str, response: Response,request_body: schemas.CompanyUpdateDetails = Body(...), db: Session = Depends(get_db)):
    try:
        company = db.query(models.Companies).filter(models.Companies.company_id == company_id).first()
        if company:
            company.company_name = request_body.company_name
            company.company_domain = request_body.company_domain
            company.company_logo = request_body.company_logo
            company.services = request_body.services
            company.company_contact = request_body.company_contact
            company.company_address = request_body.company_address
            company.white_labelled = request_body.white_labelled
            print(company)
            db.commit()

            return {"status": 200, "message": "Company details added successfully", "data": {"company_details": request_body}}
    except Exception as e:
        print(repr(e))
        response.status_code = 500
        return {"status": 500, "message": "Internal Server Error", "data": {}}

@app.post("/branch/{company_id}")
def add_branch(company_id: str, branch_data: schemas.Branch, db: Session = Depends(get_db)):
    try:
        company = db.query(models.Companies).filter_by(company_id=company_id).first()
        if company is None:
            return {"status_code": 404, "message": "Company not found", "data": {}}

        existing_branch = db.query(models.Branch).filter_by(company_name=company.company_name,
                                                            branch_name=branch_data.branch_name).first()
        if existing_branch:
            return {"status_code": 400, "message": "Branch with the same name already exists", "data": {}}

        branch_data.company_name = company.company_name
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

@app.post("/branch/employee/{branch_id}")
def add_employee(branch_id: int, employee_data: schemas.Employee, role_data: schemas.Role, response: Response,
                 db: Session = Depends(get_db)):
    try:
        branch = db.query(models.Branch).filter_by(branch_id=branch_id).first()
        employees = db.query(models.Employee).filter_by(branch_id=branch_id).all()
        roles = db.query(models.Role).first()

        if branch is None:
            return {"status": 404, "message": "Branch not found", "data": {}}

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

        employee_list = []

        response_data = {
            "address": branch.branch_address,
            "employee_count": len(employees),
            "employees": employee_list
        }

        for emp in employees:
            employee_list.append({
                "employee_name": emp.employee_name,
                "roles": role_data.role_name
            })

        db.refresh(new_employee)
        return {"status": 200, "message": "New Employee added successfully",
                "data": {"New_employee": new_employee, "Existing_employee": response_data}}
    except IntegrityError as e:
        print(repr(e))
        response.status_code = 500
        return {"status": 500, "message": "Internal Server Error", "data": {}}
    finally:
        db.close()

# @app.post("/branch/employee/{branch_id}")
# def add_employee(branch_id:int, employee_data: schemas.Employee, role_data: schemas.Role,response:Response, db: Session = Depends(get_db)):
#     try:
#         branch = db.query(models.Branch).filter_by(branch_id=branch_id).first()
#         employees = db.query(models.Employee).filter_by(branch_id=branch_id).all()
#         role = db.query(models.Role).first()
#         if branch is None:
#             return {"status": 404, "message":"Branch not found"}
#         employee_count = len(employees)
#         response_data = {
#             "role": role.role_name,
#             "branch_name": branch.branch_name,
#             "employee_count": employee_count,
#             "employees": [{"employee_name": emp.employee_name} for emp in employees]
#         }
#
#         employee_data.branch_id = branch.branch_id
#         new_employee = models.Employee(**employee_data.model_dump())
#         db.add(new_employee)
#         db.commit()
#
#         employees.employee_id = employees.employee_id
#         new_role_name = models.Role(**role_data.model_dump())
#         db.add(new_role_name)
#         db.commit()
#
#         db.refresh(new_employee)
#         return {"status": 200, "message": "New Employee added successfully", "data": {"New_employee": new_employee, "Existing_employee": response_data}}
#     except IntegrityError as e:
#         print(repr(e))
#         response.status_code = 500
#         return {"status": 500, "message": "Internal Server Error", "data": {}}
#     finally:
#         db.close()

# @app.post("/branch/employee/{branch_id}")
# def add_employee(branch_id:int, employee_data: schemas.Employee, response:Response, db: Session = Depends(get_db)):
#     try:
#         branch = db.query(models.Branch).filter_by(branch_id=branch_id).first()
#         employees = db.query(models.Employee).filter_by(branch_id=branch_id).all()
#
#         if branch is None:
#             return {"status": 404, "message":"Branch not found"}
#         employee_count = len(employees)
#         response_data = {
#             "branch_name": branch.branch_name,
#             "employee_count": employee_count,
#             "employees": [{"employee_name": emp.employee_name} for emp in employees]
#         }
#         employee_data.branch_id = branch.branch_id
#         new_employee = models.Employee(**employee_data.model_dump())
#         db.add(new_employee)
#         db.commit()
#
#         db.refresh(new_employee)
#         return {"status": 200, "message": "New Employee added successfully", "data": {"New_employee": new_employee, "Existing_employee": response_data}}
#     except IntegrityError as e:
#         print(repr(e))
#         response.status_code = 500
#         return {"status": 500, "message": "Internal Server Error", "data": {}}
#     finally:
#         db.close()


# @app.post('/loginCompany')
# def login_company(login_data: schemas.Companies, response: Response, db: Session = Depends(get_db)):
#     try:
#         company = db.query(models.Companies).filter(models.Companies.company_email == login_data.company_email).first()
#
#         if company:
#             stored_hashed_password = company.company_password.encode()
#             if bcrypt.checkpw(login_data.company_password.encode(), stored_hashed_password):
#                 return {"status": 200, "message": "Company logged in successfully!", "data": company}
#             else:
#                 return {"status": 401, "message": "Incorrect password", "data": {}}
#         else:
#             return {"status": 404, "message": "Company not found", "data": {}}
#     except Exception as e:
#         print(repr(e))
#         response.status_code = 500
#         return {"status": 500, "message": "Internal Server Error", "data": {}}

@app.post('/addCategory')
def add_categories(addCategory: schemas.Category, response: Response, db: Session = Depends(get_db)):
    try:
        new_category = models.Categories(**addCategory.model_dump())
        db.add(new_category)
        db.commit()
        db.refresh(new_category)

        return {"status": "200", "message": "New category added successfully!", "data": new_category}
    except IntegrityError:
        response.status_code = 200
        return {"status": "404", "message": "Error", "data": {}}


@app.put('/editCategory')
def edit_categories(editCategory: schemas.EditCategory, response: Response, db: Session = Depends(get_db),
                    categoryId=int):
    try:
        edit_category = db.query(models.Categories).filter(
            models.Categories.category_id == categoryId)
        category_exist = edit_category.first()
        if not category_exist:
            response.status_code = 200
            return {"status": 204, "message": "User doesn't exists", "data": {}}

        edit_category.update(editCategory.model_dump(exclude_unset=True), synchronize_session=False)
        db.commit()
        return {"status": 200, "message": "Category edited!", "data": edit_category.first()}

    except IntegrityError:
        response.status_code = 200
        return {"status": "404", "message": "Error", "data": {}}


@app.get('/getCategories')
def get_categories(response: Response, db: Session = Depends(get_db)):
    try:
        fetch_categories = db.query(models.Categories).all()

        if not fetch_categories:
            return {"status": 204, "message": "No categories available please add", "data": {}}

        return {"status": 200, "message": "Categories Fetched", "data": fetch_categories}
    except IntegrityError:
        print(repr(e))
        response.status_code = 200
        return {"status": 204, "message": "Error", "data": {}}


@app.post('/addProducts')
def add_products(products: List[schemas.Product], response: Response, db: Session = Depends(get_db)):
    try:
        new_products = []
        for product in products:
            existing_product = db.query(models.Products).filter(
                models.Products.product_name == product.product_name
            ).first()

            if existing_product:
                return {"status": "200", "message": "Product already exists!", "data": {}}
                continue

            new_product = models.Products(**product.model_dump())
            db.add(new_product)
            new_products.append(new_product)

        db.commit()
        for product in new_products:
            db.refresh(product)

        return {"status": "200", "message": "New products added successfully!", "data": new_products}
    except IntegrityError as e:
        if "duplicate key value violates unique constraint" in str(e):
            response.status_code = 400
            return {"status": "400", "message": "check the company and categories", "data": {}}
        else:
            raise


@app.post('/addProductVariants/{product_id}')
def add_product_variants(product_id: int, variants: List[schemas.ProductVariant], response: Response,
                         db: Session = Depends(get_db)):
    try:

        product = db.query(models.Products).filter(models.Products.product_id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        # Create and add each product variant to the database
        new_variants = []
        for variant in variants:
            new_product_variant = models.ProductVariant(**variant.model_dump())
            db.add(new_product_variant)
            new_variants.append(new_product_variant)

        db.commit()
        for variant in new_variants:
            db.refresh(variant)

        return {"status": "200", "message": "New product variants added successfully!", "data": variants}
    except IntegrityError as e:
        print(repr(e))
        response.status_code = 400
        return {"status": "400", "message": "Error", "data": {}}


@app.get("/getProducts")
def get_all_products(response: Response, db: Session = Depends(get_db)):
    try:
        fetch_products = db.query(models.Products).all()
        if not fetch_products:
            return {"status": 204, "message": "No products available please add", "data": {}}

        return {"status": 200, "message": "Products Fetched", "data": fetch_products}
    except IntegrityError:
        response.status_code = 200
        return {"status": 204, "message": "Error", "data": {}}


@app.get("/products/{product_id}")
def get_product_by_product_id(response: Response, product_id: int, db: Session = Depends(get_db)):
    try:
        fetch_product = db.query(models.Products).filter(models.Products.product_id == product_id).first()
        if not fetch_product:
            return {"status": 204, "message": "Product not found", "data": {}}

        return {"status": 200, "message": "Product fetched", "data": fetch_product}
    except IntegrityError:
        response.status_code = 200
        return {"status": 204, "message": "Error", "data": {}}


@app.get("/getProductVariants")
def get_product_variants(
        response: Response,
        user_id: int,
        product_id: Optional[int] = None,
        variant_id: Optional[int] = None,
        db: Session = Depends(get_db)
):
    try:
        count_query = db.query(func.count('*')).select_from(models.CartItem)
        total_count = count_query.scalar()
        cart = db.query(models.Cart).filter_by(customer_contact=user_id).first()

        if cart:
            cart_items_query = (
                db.query(models.CartItem)
                .filter_by(cart_id=cart.cart_id)
                .options(joinedload(models.CartItem.variant))
            )

            if product_id:
                cart_items_query = cart_items_query.filter_by(product_id=product_id)
            if variant_id:
                cart_items_query = cart_items_query.filter_by(variant_id=variant_id)

            cart_items = cart_items_query.all()

        variant_counts = defaultdict(int)

        for cart_item in cart_items:
            variant_id = cart_item.variant_id
            count = cart_item.count
            variant_counts[variant_id] += count

        feature = db.query(models.FreatureList).all()
        recommended_products = [
            {"variant_id": 9, "variant_cost": 90.0, "count": 100, "cart_item_quantity_count":1,"brand_name": "Amul", "discounted_cost": 84.0,
             "discount": 8, "quantity": "250 ml",
             "description": "Amul Lassi is a refreshing milk-based natural drink. It refreshes you immediately with the goodness of nature.",
             "image": [
                 "https://oneart.onrender.com/images/amul-lassi-1-l-tetra-pak-product-side.jpeg"
             ],
             "ratings": 4
             },
            {
                "variant_id": 10, "variant_cost": 14.7, "count": 100, "cart_item_quantity_count":1,"brand_name": "Amul", "discounted_cost": 14.7,
                "discount": 0, "quantity": "180 ml",
                "description": "Amul Lassi is a refreshing milk-based natural drink. It refreshes you immediately with the goodness of nature.",
                "image": [
                    "https://oneart.onrender.com/images/amul-rose-flavoured-probiotic-la.jpeg"
                ],
                "ratings": 4
            }]
        product = db.query(models.Products).filter(models.Products.product_id == product_id).first()

        if product:
            product_data = {
                "product_id": product.product_id,
                "product_name": product.product_name,
                "details": product.details,
                "variants": []
            }

            product_variants = db.query(models.ProductVariant).filter(
                models.ProductVariant.product_id == product_id).all()

            for variant in product_variants:
                variant_details = {
                    "variant_id": variant.variant_id,
                    "variant_cost": variant.variant_cost,
                    "count":variant.count,
                    "cart_item_quantity_count": variant_counts.get(variant.variant_id, 0),
                    "brand_name": variant.brand_name,
                    "discounted_cost": variant.discounted_cost,
                    "discount": variant.discount,
                    "quantity": variant.quantity,
                    "description": variant.description,
                    "image": variant.image,
                    "ratings": variant.ratings
                }

                product_data["variants"].append(variant_details)

            return {
                "status": 200,
                "message": "Product and its variants fetched successfully",
                "data": {
                    "product_data": product_data,
                    "feature": feature,
                    "recommended_products": recommended_products,
                    "cart_item_count": total_count,
                }
            }
        else:
            return {"status": 404, "message": "Product not found", "data": {}}

    except IntegrityError:
        response.status_code = 200
        return {"status": 204, "message": "Error", "data": {}}


@app.put("/editProduct")
def edit_product(editProduct: schemas.EditProduct, response: Response, product_id: int, db: Session = Depends(get_db)):
    try:
        edit_product = db.query(models.Products).filter(models.Products.product_id == product_id)
        product_exist = edit_product.first()
        if not product_exist:
            response.status_code = 404
            return {"status": 404, "message": "Product doesn't exist", "data": {}}

        edit_product.update(editProduct.model_dump(exclude_unset=True), synchronize_session=False)
        db.commit()
        return {"status": 200, "message": "Product edited!", "data": edit_product.first()}

    except IntegrityError:
        response.status_code = 400
        return {"status": 400, "message": "Error", "data": {}}


@app.get("/products/categories/{customer_contact}/{category_id}")
def get_products_by_category_id(response: Response, category_id: int, customer_contact: int, product_id: Optional[int] = None,  variant_id: Optional[int] = None, db: Session = Depends(get_db)):
    try:

        cart = db.query(models.Cart).filter_by(customer_contact=customer_contact).first()

        if cart:
            cart_items_query = (
                db.query(models.CartItem)
                .filter_by(cart_id=cart.cart_id)
                .options(joinedload(models.CartItem.variant))
            )

            if product_id:
                cart_items_query = cart_items_query.filter_by(product_id=product_id)
            if variant_id:
                cart_items_query = cart_items_query.filter_by(variant_id=variant_id)

            cart_items = cart_items_query.all()

        variant_counts = defaultdict(int)

        for cart_item in cart_items:
            variant_id = cart_item.variant_id
            count = cart_item.count
            variant_counts[variant_id] += count

        count_query = db.query(func.count('*')).select_from(models.CartItem)
        total_count = count_query.scalar()

        product_details = []
        products_in_category = (
            db.query(models.Products)
            .join(models.CategoryProduct, models.Products.product_id == models.CategoryProduct.product_id)
            .filter(models.CategoryProduct.category_id == category_id)
            .all()
        )

        for product in products_in_category:
            product_details_dict = {
                "product_id": product.product_id,
                "product_name": product.product_name,
                "details": product.details,
                "variants": [],
            }

            variants = (
                db.query(models.ProductVariant)
                .filter(models.ProductVariant.product_id == product.product_id)
                .all()
            )

            for variant in variants:
                variant_details = {
                    "variant_id": variant.variant_id,
                    "variant_cost": variant.variant_cost,
                    "count": variant.count,
                    "brand_name": variant.brand_name,
                    "cart_item_quantity_count": variant_counts.get(variant_id, 0),
                    "discounted_cost": variant.discounted_cost,
                    "discount": variant.discount,
                    "quantity": variant.quantity,
                    "description": variant.description,
                    "image": variant.image,
                    "ratings": variant.ratings
                }

                product_details_dict["variants"].append(variant_details)

            product_details.append(product_details_dict)

        return {"status": 200, "message": "Products by category fetched", "products": product_details, "cart_item_count": total_count}
    except IntegrityError as e:
        print(repr(e))
        response.status_code = 200
        return {"status": 204, "message": "Error", "data": {}}


@app.post("/carts")
async def create_cart(cart: schemas.CartSchema, response: Response, db: Session = Depends(get_db)):
    try:
        new_cart = models.Cart(**cart.model_dump())
        db.add(new_cart)
        db.commit()
        db.refresh(new_cart)

        return {"status": "200", "message": "New cart created successfully!", "data": new_cart}
    except IntegrityError as e:
        print(repr(e))
        response.status_code = 400
        return {"status": "400", "data": {}}


@app.post('/deleteCart')
def delete_cart(id: int, response: Response, db: Session = Depends(get_db)):
    try:
        cart = db.query(models.Cart).get(id)

        if not cart:
            raise HTTPException(status_code=404, detail="Cart not found")

        db.delete(cart)
        db.commit()

        return {"status": "200", "message": "Cart deleted successfully!"}
    except Exception as e:
        print(repr(e))
        response.status_code = 500
        return {"status": "500", "message": "Internal server error"}


@app.post('/deleteMultipleProduct')
def delete_multiple_products(product_ids: List[int], response: Response, db: Session = Depends(get_db)):
    if not product_ids:
        raise HTTPException(status_code=400, detail="Please provide a list of product IDs")

    try:
        products = db.query(models.Products).filter(models.Products.product_id.in_(product_ids))

        if not products:
            raise HTTPException(status_code=404, detail="Products not found")

        for product in products:
            db.delete(product)
        db.commit()

        return {"status": "200", "message": "Products deleted successfully!"}
    except Exception as e:
        response.status_code = 500
        return {"status": "500", "message": "Internal server error"}


@app.get("/productsSearch/{customer_contact}")
def search_products(response: Response, search_term: str, customer_contact: int,product_id: Optional[int] = None,  variant_id: Optional[int] = None, db: Session = Depends(get_db)):
    try:

        cart = db.query(models.Cart).filter_by(customer_contact=customer_contact).first()

        if cart:
            cart_items_query = (
                db.query(models.CartItem)
                .filter_by(cart_id=cart.cart_id)
                .options(joinedload(models.CartItem.variant))
            )

            if product_id:
                cart_items_query = cart_items_query.filter_by(product_id=product_id)
            if variant_id:
                cart_items_query = cart_items_query.filter_by(variant_id=variant_id)

            cart_items = cart_items_query.all()

        variant_counts = defaultdict(int)

        for cart_item in cart_items:
            variant_id = cart_item.variant_id
            count = cart_item.count
            variant_counts[variant_id] += count

        count_query = db.query(func.count('*')).select_from(models.CartItem)
        total_count = count_query.scalar()

        for char in search_term:
            if not char.isalnum():
                raise ValueError(f"Search term cannot contain invalid characters: {char}.")

        search_categories = db.query(models.Categories).filter(
            (models.Categories.category_name.ilike(f"%{search_term}%"))).all()
        search_brand = db.query(models.Brand).filter(
            (models.Brand.brand_name.ilike(f"%{search_term}%"))).all()
        search_results = db.query(models.Products).filter(
            (models.Products.product_name.ilike(f"%{search_term}%"))).all()

        if not search_results:
            return {"status": 204, "message": "No product or brand found", "data": {}}

        return {"status": 200, "message": "Products and Brand names fetched",
                "data": {"Categories": search_categories, "Brands": search_brand, "search_results": search_results, "cart_item_count": total_count}}


    except ValueError as e:
        print(repr(e))
        response.status_code = 400
        return {"status": 400, "message": "Error", "data": {}}
    except IntegrityError as e:
        response.status_code = 500
        return {"status": 500, "message": "Error", "data": {}}


@app.get("/getCategoriesAndBannersAndDeals")
def get_categories_and_banners_and_deals(response: Response, db: Session = Depends(get_db)):
    try:
        fetch_categories = db.query(models.Categories).all()
        fetch_banners = db.query(models.PromotionalBanners).all()
        deal_products = db.query(models.Products).filter(models.Products.deal == True).all()

        if not fetch_categories or not fetch_banners or not deal_products:
            return {"status": 204, "message": "No data available", "data": {}}

        return {
            "status": 200,
            "message": "Categories, banners, and deals fetched",
            "data": {
                "categories": fetch_categories,
                "banners": fetch_banners,
                "deals": deal_products,
            },
        }
    except IntegrityError:
        response.status_code = 200
        return {"status": 204, "message": "Error", "data": {}}


@app.get("/getAllCategoriesProducts")
async def get_all_products_in_categories(response: Response, db: Session = Depends(get_db)):
    try:
        product_categories = db.query(models.Categories).all()

        category_details_with_products = []
        for category in product_categories:
            products = db.query(models.Products).join(models.CategoryProduct,
                                                      models.Products.product_id == models.CategoryProduct.product_id
                                                      ).filter(
                models.CategoryProduct.category_id == category.category_id).all()

            category_details = {
                "category_id": category.category_id,
                "category_name": category.category_name,
                "category_image": category.category_image,
                "products": [],
            }
            for product in products:
                product_details = {
                    "product_id": product.product_id,
                    "product_name": product.product_name,
                    "details": product.details,
                    "variants": [],
                }

                product_variants = db.query(models.ProductVariant).filter(
                    models.ProductVariant.product_id == product.product_id).all()
                for variant in product_variants:
                    variant_details = {
                        "variant_id": variant.variant_id,
                        "variant_cost": variant.variant_cost,
                        "count": variant.count,
                        "brand_name": variant.brand_name,
                        "discounted_cost": variant.discounted_cost,
                        "discount": variant.discount,
                        "quantity": variant.quantity,
                        "description": variant.description,
                        "image": variant.image,
                        "ratings": variant.ratings
                    }

                    product_details["variants"].append(variant_details)
                category_details["products"].append(product_details)
            category_details_with_products.append(category_details)

        return {"status": 200 , "message": "response fetched successfully","data": category_details_with_products}
    except Exception as e:
        print(repr(e))
        response.status_code = 500
        return {"status": 500, "message": "Internal Server Error", "data": []}


@app.get("/getAllCategoriesVariants")  # for fetch products with category
async def get_all_products_in_categories(response: Response, db: Session = Depends(get_db)):
    try:
        feature = db.query(models.FreatureList).all()
        product_categories = db.query(models.Categories).all()

        recomended_products = []
        category_details_variants = []
        for category in product_categories:
            products = db.query(models.Products).join(models.CategoryProduct,
                                                      models.Products.product_id == models.CategoryProduct.product_id
                                                      ).filter(
                models.CategoryProduct.category_id == category.category_id).all()

            category_details = {
                "category_id": category.category_id,
                "category_name": category.category_name,
                "category_image": category.category_image,
                "products": [],
            }
            for product in products:
                product_details = {
                    "product_id": product.product_id,
                    "product_name": product.product_name,
                    "details": product.details,
                    "variants": [],
                }

                product_variant = db.query(models.ProductVariant).filter(
                    models.ProductVariant.product_id == product.product_id).first()
                if product_variant:
                    variant_details = {
                        "variant_id": product_variant.variant_id,
                        "variant_cost": product_variant.variant_cost,
                        "count": product_variant.count,
                        "brand_name": product_variant.brand_name,
                        "discounted_cost": product_variant.discounted_cost,
                        "discount": product_variant.discount,
                        "quantity": product_variant.quantity,
                        "description": product_variant.description,
                        "image": product_variant.image,
                        "ratings": product_variant.ratings
                    }

                    product_details["variants"].append(variant_details)
                category_details["products"].append(product_details)
            category_details_variants.append(category_details)

        return {"feature": feature, "category details": category_details_variants,
                "recomended products": recomended_products}
    except Exception as e:
        print(repr(e))
        response.status_code = 500
        return {"status": 500, "message": "Internal Server Error", "data": []}
@app.get("/homescreen")
def get_categories_and_banners_and_deals(customer_contact:int, response: Response ,product_id: Optional[int] = None,  variant_id: Optional[int] = None, db: Session = Depends(get_db)):
    try:
        fetch_categories = db.query(models.Categories).all()
        fetch_shop_banner = db.query(models.Shops).all()
        fetch_deals = db.query(models.Products).limit(3).all()

        cart = db.query(models.Cart).filter_by(customer_contact=customer_contact).first()

        if cart:
            cart_items_query = (
                db.query(models.CartItem)
                .filter_by(cart_id=cart.cart_id)
                .options(joinedload(models.CartItem.variant))
            )

            if product_id:
                cart_items_query = cart_items_query.filter_by(product_id=product_id)
            if variant_id:
                cart_items_query = cart_items_query.filter_by(variant_id=variant_id)

            cart_items = cart_items_query.all()

        variant_counts = defaultdict(int)

        for cart_item in cart_items:
            variant_id = cart_item.variant_id
            count = cart_item.count
            variant_counts[variant_id] += count

        count_query = db.query(func.count('*')).select_from(models.CartItem)
        total_count = count_query.scalar()
        fetch_deals = db.query(models.Products).limit(3).all()

        shop_deals = []
        shop_details = []
        for shop in fetch_shop_banner:
            shop_images = {
                "shop_id": shop.shop_id,
                "shop_name": shop.shop_name,
                "shop_image": shop.shop_image
            }
            shop_details.append(shop_images)

        for deal in fetch_deals:
            deal_products = {
                "product_id": deal.product_id,
                "product_name": deal.product_name,
                "details": deal.details,
                "variants": [],
            }

            product_variant = db.query(models.ProductVariant).filter(
                models.ProductVariant.product_id == deal.product_id).first()
            if product_variant:
                variant_details = {
                    "variant_id": product_variant.variant_id,
                    "variant_cost": product_variant.variant_cost,
                    "count": product_variant.count,
                    "brand_name": product_variant.brand_name,
                    "cart_item_quantity_count": variant_counts.get(product_variant.variant_id, 0),
                    "discounted_cost": product_variant.discounted_cost,
                    "discount": product_variant.discount,
                    "quantity": product_variant.quantity,
                    "description": product_variant.description,
                    "image": product_variant.image,
                    "ratings": product_variant.ratings
                }

                deal_products["variants"].append(variant_details)

            shop_deals.append(deal_products)

        return {
            "status": 200,
            "message": "Categories, banners, and deals fetched",
            "data": {
                "categories": fetch_categories,
                "popular shops": shop_details,
                "today's deals": shop_deals,
                "cart_item_count": total_count
            }
        }
    except IntegrityError:
        response.status_code = 200
        return {"status": 204, "message": "Error", "data": {}}

@app.get("/getProductswithCartId/{cart_id}")
def get_cart_items_with_product_ids(response: Response, cart_id: int, customer_contact: int,
                                    db: Session = Depends(get_db)):
    try:
        cart = db.query(models.Cart).filter_by(customer_contact=customer_contact).first()
        if cart:
            cart_items = (
                db.query(models.CartItem, models.ProductVariant.variant_cost)
                .join(models.ProductVariant, models.CartItem.variant_id == models.ProductVariant.variant_id)
                .filter(models.CartItem.cart_id == cart.cart_id)
                .all()
            )

        fetch_cart_items = db.query(models.CartItem).filter(models.CartItem.cart_id == cart_id).all()
        if not fetch_cart_items:
            return {"status": 404, "message": "No cart items found", "data": {}}

        cart_items_with_product_ids = []

        for cart_item in fetch_cart_items:
            product_id = cart_item.product_id
            variant_id = cart_item.variant_id

            product = db.query(models.Products).filter(models.Products.product_id == product_id).first()
            variant = db.query(models.ProductVariant).filter(models.ProductVariant.variant_id == variant_id).first()

            cart_items_with_product_ids.append({
                "cartItemId": cart_item.cartItem_id,
                "product": product,
                "variant": variant
            })
            cart_item_count = len(cart_items)

        return {"status": 200, "message": "Cart items fetched",
                "data": {"cart_items": cart_items_with_product_ids, "item_count": cart_item_count}}
    except IntegrityError as e:
        print(repr(e))
        response.status_code = 500
        return {"status": 500, "message": "Error", "data": {}}


# @app.post("/add_to_cart/")
# def add_to_cart(cart_item: schemas.CartItem, cart_id: int,response: Response,db: Session = Depends(get_db)):
#     try:
#
#         # user_cart = (db.query(models.Cart).options(joinedload(models.CartItem)).join(models.CartItem)
#         #              ).filter(models.Cart.customer_contact == user_contact)
#
#         product_variant = db.query(models.ProductVariant).filter_by(variant_id=cart_item.variant_id).first()
#         if not product_variant:
#             raise HTTPException(status_code=404, detail="Product variant not found")
#
#
#
#
#         new_cart_item = models.CartItem(**cart_item.model_dump())
#
#         db.add(new_cart_item)
#         db.commit()
#         db.refresh(new_cart_item)
#
#         return {"status": 200, "message": "Items Successfully Added to the Cart", "data": new_cart_item}
#     except IntegrityError as e:
#         print(repr(e))
#         response.status_code = 500
#         return {"status": 500, "message": "Error", "data": {}}

@app.post("/add_to_cart")
def add_to_cart(response: Response, user_contact: int,product_id: Optional[int] = None,  variant_id: Optional[int] = None, cart_Item: dict = Body(...), db: Session = Depends(get_db)):
    try:
        product_id = cart_Item["product_id"]

        cart = db.query(models.Cart).filter_by(customer_contact=user_contact).first()

        if cart is None:
            cart = models.Cart(customer_contact=user_contact)
            db.add(cart)
            db.commit()
            db.refresh(cart)

        existing_cart_item = db.query(models.CartItem).filter_by(cart_id=cart.cart_id, variant_id=cart_Item.get("variant_id")).first()

        if existing_cart_item:
            return {"status": 200, "message": "Product already exists!", "data":{}}

        else:
            variant_id = cart_Item["variant_id"]
            count = 1 if "count" not in cart_Item else cart_Item["count"]
            cart_item = models.CartItem(cart_id=cart.cart_id, variant_id=variant_id, count=count, product_id=product_id)
            db.add(cart_item)
            db.commit()
            db.refresh(cart_item)

        if cart:
            cart_items_query = (
                db.query(models.CartItem)
                .filter_by(cart_id=cart.cart_id)
                .options(joinedload(models.CartItem.variant)))

            if product_id:
                cart_items_query = cart_items_query.filter_by(product_id=product_id)
            if variant_id:
                cart_items_query = cart_items_query.filter_by(variant_id=variant_id)

            cart_items = cart_items_query.all()

        variant_counts = defaultdict(int)

        for cart_item in cart_items:
            variant_id = cart_item.variant_id
            count = cart_item.count
            variant_counts[variant_id] += count

        count_query = db.query(func.count('*')).select_from(models.CartItem)
        total_count = count_query.scalar()

        return {"status": 200, "message": "Items Successfully Added to the Cart", "data": {"cart_data": cart_item, "cart_item_quantity_count": variant_counts.get(variant_id, 0) ,"cart_item_count": total_count}}
    except IntegrityError as e:
        print(repr(e))
        response.status_code = 500
        return {"status": 500, "message": "Error", "data": {}}


@app.put("/increment_cart_item_count")
def increment_cart_item_count( response: Response, user_contact: int, product_id: int, variant_id: int,
                              db: Session = Depends(get_db)):
    try:
        cart = db.query(models.Cart).filter_by(customer_contact=user_contact).first()
        if cart is None:
            raise HTTPException(status_code=404, detail="Cart not found for the given customer contact")

        cart_item = db.query(models.CartItem).filter_by(cart_id=cart.cart_id, product_id=product_id, variant_id=variant_id).first()
        if cart_item is None:
            raise HTTPException(status_code=404, detail="Cart Item not found")

        cart_item.count += 1
        db.commit()

        if cart:
            cart_items_query = (
                db.query(models.CartItem)
                .filter_by(cart_id=cart.cart_id)
                .options(joinedload(models.CartItem.variant)))

            if product_id:
                cart_items_query = cart_items_query.filter_by(product_id=product_id)
            if variant_id:
                cart_items_query = cart_items_query.filter_by(variant_id=variant_id)

            cart_items = cart_items_query.all()

        variant_counts = defaultdict(int)

        for cart_item in cart_items:
            variant_id = cart_item.variant_id
            count = cart_item.count
            variant_counts[variant_id] += count

        count_query = db.query(func.count('*')).select_from(models.CartItem)
        total_count = count_query.scalar()


        return {
            "status": 200,
            "message": "Cart Item count incremented successfully",
            "data": {
                "cart_data": cart_item,
                "cart_item_quantity_count": variant_counts.get(variant_id, 0),
                "cart_item_count": total_count
            }


        }

    except IntegrityError as e:
        print(repr(e))
        db.rollback()
        response.status_code = 500
        return {"status": 500, "message": "Error", "data": {}}


@app.put("/decrement_cart_item_count")
def decrement_cart_item_count(response: Response, user_contact: int, product_id: int, variant_id: int,
                              db: Session = Depends(get_db)):
    try:
        cart = db.query(models.Cart).filter_by(customer_contact=user_contact).first()
        if cart is None:
            raise HTTPException(status_code=404, detail="Cart not found for the given customer contact")

        cart_item = db.query(models.CartItem).filter_by(cart_id=cart.cart_id, product_id=product_id, variant_id=variant_id).first()
        if cart_item is None:
            raise HTTPException(status_code=404, detail="Cart Item not found")

        if cart_item.count > 0:
            cart_item.count -= 1
            db.commit()
        else:
            raise HTTPException(status_code=400, detail="Count cannot be less than zero")

        if cart:
            cart_items_query = (
                db.query(models.CartItem)
                .filter_by(cart_id=cart.cart_id)
                .options(joinedload(models.CartItem.variant)))

            if product_id:
                cart_items_query = cart_items_query.filter_by(product_id=product_id)
            if variant_id:
                cart_items_query = cart_items_query.filter_by(variant_id=variant_id)

            cart_items = cart_items_query.all()

        variant_counts = defaultdict(int)

        for cart_item in cart_items:
            variant_id = cart_item.variant_id
            count = cart_item.count
            variant_counts[variant_id] += count

        count_query = db.query(func.count('*')).select_from(models.CartItem)
        total_count = count_query.scalar()
        return {
                "status": 200, "message": "Cart Item count decremented successfully",
                "data": {
                "cart_data": cart_item,
                "cart_item_quantity_count": variant_counts.get(variant_id, 0),
                "cart_item_count": total_count
                }}
    except IntegrityError as e:
        db.rollback()
        response.status_code = 500
        return {"status": 500, "message": "Error", "data": {}}

@app.delete("/truncate_cart_items/{cart_id}")
def truncate_cart_items(cart_id: int, db: Session = Depends(get_db)):
    try:
        cart = db.query(models.Cart).filter_by(cart_id=cart_id).first()
        if cart is None:
            return{"status": 404, "message": "Cart not found"}

        db.query(models.CartItem).filter_by(cart_id=cart_id).delete(synchronize_session=False)
        db.commit()

        return {"status": 200, "message": "Cart items truncated successfully"}
    except Exception as e:
        db.rollback()
        print(repr(e))
        return {"status":500, "message": "Internal server error"}

@app.delete("/delete_cart_item")
def delete_cart_item(response: Response, user_contact: int, product_id: int, variant_id: int, db: Session = Depends(get_db)):
    try:
        cart = db.query(models.Cart).filter_by(customer_contact=user_contact).first()
        if cart is None:
            return {"status": 404, "message": "Cart not found"}

        cart_item = db.query(models.CartItem).filter_by(cart_id=cart.cart_id, product_id=product_id, variant_id=variant_id).first()
        if cart_item is None:
            return {"status": 404, "message": "Cart Item not found"}

        db.delete(cart_item)
        db.commit()

        if cart:
            cart_items_query = (
                db.query(models.CartItem)
                .filter_by(cart_id=cart.cart_id)
                .options(joinedload(models.CartItem.variant)))

            if product_id:
                cart_items_query = cart_items_query.filter_by(product_id=product_id)
            if variant_id:
                cart_items_query = cart_items_query.filter_by(variant_id=variant_id)

            cart_items = cart_items_query.all()

        variant_counts = defaultdict(int)

        for cart_item in cart_items:
            variant_id = cart_item.variant_id
            count = cart_item.count
            variant_counts[variant_id] += count

        count_query = db.query(func.count('*')).select_from(models.CartItem)
        total_count = count_query.scalar()
        return {
                "status": 200, "message": "Cart Item deleted successfully",
                "data": {
                "cart_data": cart_item,
                "cart_item_quantity_count": variant_counts.get(variant_id, 0),
                "cart_item_count": total_count
                }}

    except Exception as e:
        db.rollback()
        print(repr(e))
        return {"status": 500, "message": "Internal Server Error"}


# @app.post('/bookOrder')
# def add_bookings(bookOrder: schemas.Bookings, response: Response, db: Session = Depends(get_db)):
#     try:
#         new_booking = models.Bookings(**bookOrder.model_dump())
#         db.add(new_booking)
#         db.commit()
#         db.refresh(new_booking)
#
#         return {"status": "200", "message": "New booking successful!", "data": new_booking}
#     except IntegrityError:
#         response.status_code = 200
#         return {"status": "404", "message": "Error", "data": {}}


# @app.post('/bookOrder/')
# def add_booking(response: Response, bookOrder: schemas.BookingsCreate, db: Session = Depends(get_db)):
#     try:
#         new_booking = models.Bookings(**bookOrder.model_dump())
#
#         # Fetch the products from the cart associated with the provided cart_id
#         cart = db.query(models.Cart).filter(models.Cart.cart_id == bookOrder.cart_id).first()
#         if cart:
#             new_booking.products = cart.products
#
#             cart.products = []
#
#         db.add(new_booking)
#         db.commit()
#         db.refresh(new_booking)
#
#         return {"status": 200, "message": "Booking order created successfully!", "data": new_booking}
#     except IntegrityError:
#         response.status_code = 400
#         return {"status": 400, "message": "Error creating booking order", "data": {}}

# @app.get("/getOrders")
# def get_Orders(response: Response, db: Session = Depends(get_db)):
#     try:
#         orders = db.query(models.Bookings).all()
#         if not orders:
#             return {"status": 204, "message": "No Booking Orders available", "data": []}
#
#         return {"status": 200, "message": "Booking Orders  fetched", "data": orders}
#     except IntegrityError as e:
#         print(repr(e))
#         response.status_code = 200
#         return {"status": 204, "message": "Error", "data": []}
#
#
# @app.get("/getOrders/{order_id}")
# def get_oreders_by_order_id(response: Response, order_id: int, db: Session = Depends(get_db)):
#     try:
#         fetch_orders_id = db.query(models.Bookings).filter(models.Bookings.order_id == order_id).all()
#         if not fetch_orders_id:
#             return {"status": 204, "message": "No Booking Orders found", "data": {}}
#
#         return {"status": 200, "message": "Booking Orders fetched", "data": fetch_orders_id}
#     except IntegrityError:
#         response.status_code = 200
#         return {"status": 204, "message": "Error", "data": {}}

# @app.get("/checkoutScreen/{cart_id}")
# def get_cart_item_count_with_price_and_discount_sum(response: Response, cart_id: int, db: Session = Depends(get_db)):
#
#     try:
#         fetch_cart_items = db.query(models.Cart).filter(models.Cart.cart_id == cart_id).all()
#         if not fetch_cart_items:
#             return {"status": 404, "message": "No cart items found", "data": {}}
#
#         cart_item_count = 0
#         cart_total = 0
#         discount_sum = 0
#         coupon_applied = None
#         delivery_charges = 40.50
#         total_bill = 0
#
#         if models.Cart.coupon_id:
#             applied_coupon = db.query(models.Coupon).filter(models.Coupon.coupon_id == models.Cart.coupon_id).first()
#             if applied_coupon:
#                 coupon_applied = applied_coupon.coupon_name
#         #
#         # for cart_item in fetch_cart_items:
#         #     product_id = cart_item.product_id
#         #     variant_id = cart_item.variant_id
#         #
#         #     product = db.query(models.Products).filter(models.Products.product_id == product_id).first()
#         #     variant = db.query(models.ProductVariant).filter(models.ProductVariant.variant_id == variant_id).first()
#         #
#         #     if variant:
#         #         price = variant.variant_price
#         #         discount_amount = variant.discounted_cost
#         #     else:
#         #         price = product.price
#         #         discount_amount = product.discounted_cost
#         #
#         #     discount_sum += variant.discounted_cost * cart_item.item_count
#         #     discount_sum += product.discounted_cost * cart_item.item_count
#         #
#         #     cart_item_count += cart_item.item_count
#         #     cart_total += price * cart_item.item_count
#         #
#         # total_bill = cart_total - discount_sum + delivery_charges
#         #
#         # discount_sum = cart_total - discount_sum
#
#         return {"status": 200, "message": "CHECKOUT SCREEN fetched", "data": {"cart_item_count": cart_item_count, "cart_total": cart_total, "discount_sum": discount_sum, "coupon_applied": coupon_applied, "delivery_charges": delivery_charges, "total_bill": total_bill}}
#     except IntegrityError as e:
#         print(repr(e))
#         response.status_code = 500
#         return {"status": 500, "message": "Error", "data": {}}

@app.get("/your_cart/{customer_contact}")
def get_your_cart(response: Response, customer_contact: int, db: Session = Depends(get_db)):
    try:
        cart = db.query(models.Cart).filter_by(customer_contact=customer_contact).first()
        if cart:
            cart_items = (
                db.query(models.CartItem)
                .filter_by(cart_id=cart.cart_id)
                .options(joinedload(models.CartItem.variant))
                .all()
            )

        cart_items_with_customer_contact = []
        total_cost = 0.0
        variant_costs = {}

        for cart_item in cart_items:
            product_id = cart_item.product_id
            variant_id = cart_item.variant_id

            product = db.query(models.Products).filter(models.Products.product_id == product_id).first()
            variant = db.query(models.ProductVariant).filter(models.ProductVariant.variant_id == variant_id).first()

            cart_items_with_customer_contact.append({
                "cartItemId": cart_item.cartItem_id,
                "product": product,
                "variant": variant,
                "total_item_count_variant": cart_item.count
            })

            variant_cost = cart_item.variant.variant_cost

            variant_cost_total = variant_cost * cart_item.count

            if variant_id in variant_costs:
                variant_costs[variant_id] += variant_cost
            else:
                variant_costs[variant_id] = variant_cost
            # for variant_id, total_cost in variant_costs.items():
            #     print(f"Variant ID: {variant_id}, Total Cost: {total_cost}")
            # total_cost = sum(variant_cost_total.values())
            total_cost += variant_cost_total


        return {"status": 200, "message": "Cart items fetched",
                "data": {"cart_items": cart_items_with_customer_contact, "cart_item_count": len(cart_items),
                         "total_price": total_cost}}
    except IntegrityError as e:
        print(repr(e))
        response.status_code = 500
        return {"status": 500, "message": "Error", "data": {}}


@app.post('/bookOrder')
def add_booking(
        response: Response,
        bookOrder: schemas.Bookings,
        db: Session = Depends(get_db)
):
    try:
        import uuid
        import time

        def generate_new_order_number():
            return str(uuid.uuid4())

        def generate_new_invoice_number():
            return str(int(time.time()))

        order_number = generate_new_order_number()
        invoice_number = generate_new_invoice_number()

        new_booking = models.Bookings(
            user_name=bookOrder.user_name,
            order_date=bookOrder.order_date,
            product_total=bookOrder.product_total,
            order_amount=bookOrder.order_amount,
            delivery_fees=bookOrder.delivery_fees,
            invoice_amount=bookOrder.invoice_amount,
            order_number=order_number,
            invoice_number=invoice_number,
            products=bookOrder.products,
        )

        db.add(new_booking)
        db.commit()
        db.refresh(new_booking)

        return {"status": 200, "message": "Booking order created successfully!", "data": new_booking}
    except IntegrityError as e:
        db.rollback()
        response.status_code = 400
        return {"status": 400, "message": "Error creating booking order - IntegrityError", "data": {}}
    except Exception as e:
        db.rollback()
        response.status_code = 500
        return {"status": 500, "message": "Internal server error", "data": {}}


# @app.get("/getOrder/{order_id}")
# def get_order_by_id(order_id: int = Path(..., title="Order ID"), db: Session = Depends(get_db)):
#     try:
#         order = db.query(models.Bookings).filter(models.Bookings.order_id == order_id).first()
#
#         if not order:
#             response.status_code = 404
#             return {"status": 404, "message": "Booking Order not found", "data": None}


#
#     return {"status": 200, "message": "Booking Order fetched", "data": order}
# except IntegrityError as e:
#     print(repr(e))
#     response.status_code = 500
#     return {"status": 500, "message": "Internal server error", "data": None}


# @app.post('/reorder/{order_id}', response_model=schemas.Bookings)
# def reorder_booking(
#     order_id: int,c
#     response: Response,
#     db: Session = Depends(get_db)
# ):
#     try:
#         # Check if the original booking exists
#         original_booking = db.query(models.Bookings).filter(models.Bookings.order_id == order_id).first()
#         if not original_booking:
#             raise HTTPException(status_code=404, detail="Original booking not found")
#
#         # Create a new booking by copying data from the original booking
#         new_booking_data = original_booking.__dict__
#         del new_booking_data['_sa_instance_state']  # Remove SQLAlchemy internal state
#
#         import uuid
#         import time
#
#         def generate_new_order_number():
#             # Generate a unique order number (e.g., using UUID)
#             return str(uuid.uuid4())
#
#         def generate_new_invoice_number():
#             # Generate a unique invoice number using Unix timestamp
#             return str(int(time.time()))
#
#         # Set new values for the copied data (e.g., update the order_number, invoice_number, etc.)
#         new_booking_data['order_id'] = None  # Generate a new order_id
#         new_booking_data['order_number'] = generate_new_order_number()
#         new_booking_data['invoice_number'] = generate_new_invoice_number()
#
#         # Create and add the new booking to the database
#         new_booking = models.Bookings(**new_booking_data)
#         db.add(new_booking)
#         db.commit()
#         db.refresh(new_booking)
#
#         return new_booking
#     except Exception as e:
#         db.rollback()
#         response.status_code = 500
#         return {"status": 500, "message": "Internal server error", "data": {}}

@app.get("/orderdetails")
def get_tracking_by_booking_id(booking_id: int, db: Session = Depends(get_db)):
    try:
        order = db.query(models.Bookings).filter(models.Bookings.order_id == booking_id).first()
        tracking = db.query(models.TrackingStage).filter(models.TrackingStage.booking_id == booking_id).first()

        product_list = []

        if order:
            products = order.products
        # tracking_data = {
        #     key: getattr(tracking, key)
        #     for key in ["ordered", "under_process", "shipped", "delivered"]
        # }

        return {"status": 200, "message": "Tracking Stage fetched",
                "data": {"tracking_data": tracking, "order": order, "products": products}}
    except Exception as e:
        print(repr(e))
        response.status_code = 500
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/orderlist")
def get_tracking_by_booking_id(customer_contact: int, db: Session = Depends(get_db)):
    try:
        orders = db.query(models.Bookings).filter(models.Bookings.user_contact == customer_contact).all()
        # category = []
        # item_count = []
        if orders:
            order_list = []

            for order in orders:
                order_details = {
                    "order_id": order.order_id,
                    "order_status": order.order_status,
                    "image": order.image_status
                }
                order_details["category"] = "groceries"
                order_details["item_count"] = 10

                order_list.append(order_details)

            return {"status": 200, "message": "Orders fetched", "data": {"orders": order_list}}
        else:
            return {"status": 404, "message": "No orders found for the specified customer_contact"}

    except Exception as e:
        print(repr(e))
        response.status_code = 500
        raise HTTPException(status_code=500, detail="Internal server error")


# @app.get("/get_all_favitem")
# def get_customer_favorites(response: Response, user_id: int, db: Session = Depends(get_db)):
#     try:
#         fav_items = db.query(models.FavItem).filter_by(user_id=user_id).all()
#         if not fav_items:
#             raise HTTPException(status_code=404, detail="Favorite items not found")
#         results = []
#         for fav_item in fav_items:
#             product = db.query(models.Products).filter_by(product_id=fav_item.product_id).first()
#             variant = db.query(models.ProductVariant).filter_by(variant_id=fav_item.variant_id).first()
#             category_product = db.query(models.CategoryProduct).filter_by(product_id=product.product_id).first()
#             category = None
#             if category_product:
#                 category_id = category_product.category_id
#                 category = db.query(models.Categories).filter_by(category_id=category_id).first()
#             item_data = {
#                 "category_id": category.category_id if category else None,
#                 "category_name": category.category_name if category else None,
#                 "fav_items": [
#                     {
#                         "fav_item_id": fav_item.fav_item_id,
#                         "product_id": product.product_id,
#                         "product_name": product.product_name,
#                         "variant_id": variant.variant_id,
#                         "variant_cost": variant.variant_cost,
#                         "discounted_cost": variant.discounted_cost,
#                         "discount": variant.discount,
#                         "quantity": variant.quantity,
#                         "image": variant.image}
#                 ]
#             }
#             results.append(item_data)
#
#         return {"status": 200, "message": "Customer's favorite items retrieved successfully", "data": results}
#     except Exception as e:
#         print(repr(e))
#         response.status_code = 500
#         return {"status": 500, "message": "Internal server error", "data": {}}



@app.delete("/favitem/")
def remove_favorite_item(user_id: int, product_id: int, variant_id: int, db: Session = Depends(get_db)):
    try:
        # Query the database to retrieve the favorite item by user_id, product_id, and variant_id
        item = db.query(models.FavItem).filter_by(
            user_id=user_id,
            product_id=product_id,
            variant_id=variant_id
        ).first()

        if item is None:
            raise HTTPException(status_code=400, detail="Favorite item doesn't exist")

        # Delete the item from the wishlist
        db.delete(item)
        db.commit()

        return {"status": 200, "message": "Favorite item removed successfully", "data": {}}

    except HTTPException as e:
        return {"status": e.status_code, "message": str(e.detail), "data": {}}
    except Exception as e:
        print(repr(e))
        return {"status": 500, "message": "Internal server error", "data": {}}


@app.post("/favitem")
def add_to_wishlist(fav_item: schemas.FavItem, user_id: int, response: Response, db: Session = Depends(get_db)):
    try:
        existing_item = db.query(models.FavItem).filter_by(user_id=user_id, product_id=fav_item.product_id).first()

        if existing_item:
            response.status_code = 400
            return {"status": 400, "message": "Item already exists in wishlist", "data": {}}

        new_item = models.FavItem(**fav_item.model_dump())
        db.add(new_item)
        db.commit()
        db.refresh(new_item)

        return {"status": 200, "message": "Item added to wishlist successfully", "data": new_item}

    except IntegrityError as e:
        print(repr(e))
        response.status_code = 500
        return {"status": 500, "message": "Internal server error", "data": {}}

@app.post("/addReview")
async def new_review(product_id: int, user_id: int, response: Response, review: schemas.Review,
                     db: Session = Depends(get_db)):
    try:
        new_review = models.Review(**review.model_dump())
        new_review.product_id = product_id
        new_review.user_id = user_id
        db.add(new_review)
        db.commit()
        db.refresh(new_review)

        return {"status": "200", "message": "New review created!", "data": new_review}
    except IntegrityError as e:
        print(repr(e))
        response.status_code = 404
        return {"status": 404, "message": "Error", "data": {}}

@app.delete("/delete_review")
def delete_review( user_id: int, product_id: int, db: Session = Depends(get_db)):
    try:
        review = db.query(models.Review).filter_by( user_id=user_id, product_id=product_id).first()
        if review is None:
            return {"status": 404, "message": "Review not found", "data": {}}

        db.delete(review)
        db.commit()
        return {"status": 200, "message": "Review deleted successfully"}
    except Exception as e:
        db.rollback()
        print(repr(e))
        return {"status": 500, "message": "Internal server error", "data": {}}
@app.get("/getReview")
async def get_review(product_id: int, response: Response, db: Session = Depends(get_db)):
    try:
        # reviews = db.query(models.Review).filter_by(product_id=product_id).order_by(
        #     models.Review.review_id.desc()).all()
        reviews = (
            db.query(models.Review)
            .filter_by(product_id=product_id)
            .order_by(models.Review.review_id.desc())
            .join(models.User, models.Review.user_id == models.User.customer_contact)
            .all()
        )
        review_data = []
        for review in reviews:
            customer_name = review.customer.customer_name if review.customer else None
            profile_image = review.customer.profile_image if review.customer else None
            review_data.append({
                "review_id": review.review_id,
                "product_id": review.product_id,
                "user_id": review.user_id,
                "rating": review.rating,
                "review_text": review.review_text,
                "customer_name": customer_name,
                "profile_image": profile_image
            })

        return {"status": 200, "message": "Product review fetched!", "data": review_data}
    except Exception as e:
        print(repr(e))
        response.status_code = 500
        return {"status": 500, "message": "Internal Server Error", "data": {}}

@app.get("/get_Categories_Id_name")
async def get_categories(response: Response, db: Session = Depends(get_db)):
    try:
        categories = db.query(models.Categories).all()
        if not categories:
            return {"status": 204, "message": "No categories found", "data": []}

        serialized_categories = [
            {
                "category_id": category.category_id,
                "category_name": category.category_name,
            }
            for category in categories
        ]

        return {"status": 200, "message": "All categories fetched!", "data": serialized_categories}
    except Exception as e:
        print(repr(e))
        response.status_code = 500
        return {"status": "500", "message": "Internal Server Error", "data": {}}

@app.get("/getall_favitem/")
def get_customer_favorites(
        response: Response,
        user_id: int,
        db: Session = Depends(get_db)
):
    try:
        cart = db.query(models.Cart).filter_by(customer_contact=user_id).first()
        fav_items = db.query(FavItem).filter_by(user_id=user_id).all()

        if not fav_items:
            return {
                "status": 404,
                "message": "Favorite items not found for the user",
                "data": []
            }

        # Create a list to store all favorite items
        all_fav_items = []
        variant_counts = defaultdict(int)  # Move this outside the loop

        for fav_item in fav_items:
            product = db.query(Products).filter_by(product_id=fav_item.product_id).first()
            variant = db.query(ProductVariant).filter_by(variant_id=fav_item.variant_id).first()

            # Fetch category information for the product
            category_products = db.query(CategoryProduct).filter_by(product_id=product.product_id).all()

            # Initialize a variable to store category_id
            category_id = None

            for category_product in category_products:
                category = db.query(Categories).filter_by(category_id=category_product.category_id).first()
                if category:
                    category_id = category.category_id
                    break  # Stop after finding the first category

            # Fetch the count from CartItem for the current item
            cart_item = db.query(models.CartItem).filter_by(cart_id=cart.cart_id, product_id=fav_item.product_id,
                                                            variant_id=fav_item.variant_id).first()
            count = cart_item.count if cart_item else 0

            # Add the favorite item to the list with category_id
            item_data = {
                "fav_item_id": fav_item.fav_item_id,
                "product_id": product.product_id,
                "product_name": product.product_name,
                "image": variant.image,
                "brand": variant.brand_name,
                "variant_cost": variant.variant_cost,
                "discounted_cost": variant.discounted_cost,
                "discount": variant.discount,
                "quantity": variant.quantity,
                "variant_id": variant.variant_id,
                "category_id": category_id,
                "count": count,
                "cart_item_quantity_count": variant_counts.get(variant.variant_id, 0)
            }

            all_fav_items.append(item_data)

        count_query = db.query(func.count('*')).select_from(models.CartItem)
        total_count = count_query.scalar()

        response_data = {
            "status": 200,
            "message": "Customer's favorite items retrieved successfully",
            "data": all_fav_items,
            "cart_item_count": total_count
        }

        return response_data
    except Exception as e:
        print(repr(e))
        response.status_code = 500
        return {"status": 500, "message": "Internal server error", "data": []}