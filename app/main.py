from typing import List

import bcrypt
from fastapi import FastAPI, Response, Depends, UploadFile, File, Request, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from starlette.responses import FileResponse

from . import models, schemas
from .models import Image
from .database import engine, get_db,SessionLocal
import os

models.Base.metadata.reflect(bind=engine)

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

UPLOAD_DIR = "app/images"


def save_image_to_db(db, filename, file_path):
    image = Image(filename=filename, file_path=file_path)
    db.add(image)
    db.commit()
    db.refresh(image)
    return image


@app.get('/')
def root():
    return {'message': 'Hello world'}


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
        finally:
            db.close()
        base_url = request.base_url
        image_url = f"{base_url}images/{file.filename}"
        image_urls.append(image_url)

    return {"status": 200, "message": "Images uploaded successfully", "data": {"image_url": image_urls}}


@app.post('/userAuthenticate')
def create_user(loginSignupAuth: schemas.UserData, response: Response,
                db: Session = Depends(get_db), companyId=str):
    try:
        user_data = db.query(models.User).get(
            loginSignupAuth.customer_contact)

        if not user_data:
            try:
                new_user_data = models.User(
                    **loginSignupAuth.model_dump())
                new_user_added = models.UserCompany(
                    company_id=companyId,
                    user_contact=loginSignupAuth.customer_contact)
                db.add(new_user_data)
                db.add(new_user_added)
                db.commit()
                db.refresh(new_user_data)
                return {"status": 200, "message": "New user successfully created!", "data": new_user_data}
            except IntegrityError:
                response.status_code = 200
                return {"status": 204, "message": "User is not registered please Sing up", "data": {}}

        user_exists = db.query(models.UserCompany).filter(models.UserCompany.company_id == companyId).filter(
            models.UserCompany.user_contact == loginSignupAuth.customer_contact).first()
        print(user_exists)
        if not user_exists:
            try:
                new_user_company = models.UserCompany(
                    company_id=companyId,
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

    except IntegrityError:
        response.status_code = 404
        return {"status": 404, "message": "Error", "data": {}}


@app.put('/editUser')
def edit_user(userDetail: schemas.UserData, response: Response, db: Session = Depends(get_db),
              userId=int):
    try:
        edit_user_details = db.query(models.User).filter(
            models.User.customer_contact == userId)
        user_exist = edit_user_details.first()
        if not user_exist:
            response.status_code = 200
            return {"status": 204, "message": "User doesn't exists", "data": {}}

        edit_user_details.update(userDetail.model_dump(), synchronize_session=False)
        db.commit()
        return {"status": 200, "message": "user edited!", "data": edit_user_details.first()}
    except IntegrityError:
        response.status_code = 404
        return {"status": 404, "message": "Error", "data": {}}


@app.post('/addAddress')
def add_address(createAddress: schemas.Address, response: Response, db: Session = Depends(get_db)):
    try:
        new_address = models.Addresses(**createAddress.model_dump())
        db.add(new_address)
        db.commit()
        db.refresh(new_address)
        return {"status": "200", "message": "New address created!", "data": new_address}
    except IntegrityError:
        response.status_code = 404
        return {"status": "404", "message": "Error", "data": {}}


@app.get('/getAllAddresses')
def get_address(response: Response, db: Session = Depends(get_db), userId=int, companyId=str):
    try:
        user_addresses = db.query(models.Addresses).filter(
            models.Addresses.company_id == companyId).filter(
            models.Addresses.user_contact == userId).all()

        if not user_addresses:
            response.status_code = 200
            return {"status": "200", "message": "No address found", "data": []}

        return {"status": "200", "message": "success", "data": user_addresses}
    except IntegrityError:
        response.status_code = 404
        return {"status": "404", "message": "Error", "data": {}}


@app.put('/editAddress')
def edit_address(editAddress: schemas.Address, response: Response, db: Session = Depends(get_db), addressId=int):
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

    except IntegrityError:
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
        return {"status": "200", "message": "Address deleted!", "data": {}}
    except IntegrityError:
        response.status_code = 404
        return {"status": "404", "message": "Error", "data": {}}


@app.post("/add_to_cart", response_model=schemas.CartResponse)
def add_to_cart(cart_data: schemas.CartCreate, db: Session = Depends(get_db)):
    cart = db.query(models.Cart).filter(models.Cart.company_id == cart_data.company_id,
                                        models.Cart.user_id == cart_data.user_id).first()

    if cart is None:
        cart = models.Cart(**cart_data.model_dump())
        db.add(cart)
        db.commit()
    else:
        cart_items = db.query(models.CartItem).filter(cart.id).all()
        existing_product_ids = set(item.product_id for item in cart_items)
        for item in cart_data.items:
            if item.product_id not in existing_product_ids:
                new_cart_item = models.CartItem(cart_id=cart.id, product_id=item.product_id)
                db.add(new_cart_item)

        db.flush()

    db.commit()
    db.refresh(cart)

    return cart


@app.post('/bookOrder')
def add_bookings(bookOrder: schemas.Bookings, response: Response, db: Session = Depends(get_db)):
    try:
        new_booking = models.Bookings(**bookOrder.model_dump())
        db.add(new_booking)
        db.commit()
        db.refresh(new_booking)

        return {"status": "200", "message": "New booking successful!", "data": new_booking}
    except IntegrityError:
        response.status_code = 200
        return {"status": "404", "message": "Error", "data": {}}


@app.post('/signupCompany')
def add_companies(addCompany: schemas.Companies, response: Response, db: Session = Depends(get_db)):
    try:
        salt = bcrypt.gensalt()
        password = bcrypt.hashpw(addCompany.password.encode('utf-8'), salt)
        new_company = models.Companies(**addCompany.model_dump())
        new_company.password = password.decode('utf-8')
        db.add(new_company)
        db.commit()
        db.refresh(new_company)

        return {"status": "200", "message": "New company added successfully!", "data": new_company}
    except IntegrityError:
        response.status_code = 200
        return {"status": "404", "message": "Error", "data": {}}


@app.post("/companyLogin")
def company_login(loginCompany: schemas.CompanyLogin, db: Session = Depends(get_db)):
    company_exists = db.query(models.Companies).filter(models.Companies.email == loginCompany.email).first()
    if company_exists:
        correct_password = bcrypt.checkpw(loginCompany.password.encode('utf-8'),
                                          company_exists.password.encode('utf-8'))
        if correct_password:
            return {"status": "200", "message": "New company logged in!", "data": company_exists}

        return {"status": "204", "message": "Incorrect password!", "data": company_exists}

    return {"status": "204", "message": "Company not registered, Please sign up!", "data": {}}


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
                # Check if the company ID and categories match
                return {"status": "200", "message": "Product already exists!"}
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
def add_product_variants(product_id: int, variants: List[schemas.ProductVariant], response: Response, db: Session = Depends(get_db)):
    try:
        if not isinstance(product_id, int):
            raise HTTPException(status_code=400, detail="Product ID must be an integer")
        if not isinstance(variants, list):
            raise HTTPException(status_code=400, detail="Variants must be a list of ProductVariant objects")

        product = db.query(models.Products).filter(models.Products.product_id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        new_variants = []
        for variant in variants:
            existing_variant = db.query(models.ProductVariant).filter(
                models.ProductVariant.variant_price == variant.variant_price,
                models.ProductVariant.variant_quantity == variant.variant_quantity,
                models.ProductVariant.product_id == product_id,
            ).first()

            if existing_variant:
                return {"status": "200", "message": "Variants already exists!"}

                continue

            new_variant = models.ProductVariant(
                variant_price=variant.variant_price,
                variant_quantity=variant.variant_quantity,
                product_id=product_id,
            )
            db.add(new_variant)
            new_variants.append(new_variant)

        db.commit()

        return {"status": "200", "message": "New variants added successfully!"}
    except IntegrityError as e:
        if "duplicate key value violates unique constraint" in str(e):
            response.status_code = 400
            return {"status": "400", "message": "error"}
        else:
            raise
