from typing import List
import psycopg2
import bcrypt
from app import models
from fastapi import FastAPI, Response, Depends, UploadFile, File, Request, HTTPException, Query, Form
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from starlette.responses import FileResponse
from psycopg2.extras import RealDictCursor
from . import models, schemas, database
from .models import Image,Bookings,Companies
from .models import Companies as CompaniesModel
from .schemas import ReviewFeedback,Companies
from .database import engine, get_db, Base
from .database import SessionLocal
import os

import time
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
def add_products(addProduct: schemas.Product, response: Response, db: Session = Depends(get_db)):
    try:
        new_product = models.Products(**addProduct.model_dump())
        db.add(new_product)
        db.commit()
        db.refresh(new_product)

        return {"status": "200", "message": "New product added successfully!", "data": new_product}
    except IntegrityError:
        response.status_code = 200
        return {"status": "404", "message": "Error", "data": {}}

@app.get('/booking_history/')
def get_booking_history(
    response: Response,
    booking_id: str = Query(..., alias='booking_id'),
    db: Session = Depends(get_db)):
    try:
        # Check if the booking history record exists
        booking_data = db.query(models.Bookings).get(booking_id)
        if not booking_data:
            response.status_code = 404
            return {"status": 404, "message": "Booking history not found", "data": {}}

        return {"status": 200, "message": "Booking history retrieved successfully", "data": booking_data}
    except IntegrityError as err:
        response.status_code = 500
        return {"status": 500, "message": "Error retrieving booking history", "data": {}}

@app.delete("/cancel_booking/")
def cancel_booking(response: Response, booking_id: int = Query(..., alias='booking_id'), db: Session = Depends(get_db)):
    try:
        # Check if the booking exists
        booking = db.query(Bookings).filter(Bookings.booking_id == booking_id).first()
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")

        return {"status": 200, "message": "Booking canceled successfully", "data": {}}
    except Exception as e:
        response.status_code = 500
        return {"status": 500, "message": "Error canceling booking", "data": {}}

#favourite item
@app.get("/favorite_item/")
def get_favorite_item_by_user_contact(response: Response, user_contact: int = Query(..., alias='user_contact'),
                                      db: Session = Depends(get_db)):
    try:
        # Check if the user exists
        user_data = db.query(models.User).get(user_contact)
        if not user_data:
            response.status_code = 404
            return {"status": 404, "message": "User not found", "data": {}}

        # Retrieve the favorite item records by user_contact
        favorite_item_data = db.query(models.FavoriteItem).filter_by(user_contact=user_contact).all()
        if not favorite_item_data:
            response.status_code = 404
            return {"status": 404, "message": "Favorite item not found", "data": {}}

        # Create a list to store the favorite item data
        favorite_items = []
        for item in favorite_item_data:
            favorite_items.append({
                "id": item.item_id,
                "item_name": item.item_name,
                "user_contact": item.user_contact
            })

        return {"status": 200, "message": "Favorite item retrieved successfully", "data": favorite_items}
    except IntegrityError as err:
        response.status_code = 500
        return {"status": 500, "message": "Error retrieving favorite item", "data": {}}



#Add favorite items
@app.post("/favorite_item/")
def add_favorite_item(response: Response, favorite_item_data: schemas.FavoriteItem, db: Session = Depends(get_db)):
    try:
        # Check if the user exists
        user_data = db.query(models.User).get(favorite_item_data.user_contact)
        if not user_data:
            response.status_code = 404
            return {"status": 404, "message": "User not found", "data": {}}

        # Create a new favorite item
        new_favorite_item = models.FavoriteItem(
            item_id=favorite_item_data.item_id,
            user_contact=favorite_item_data.user_contact,
            item_name=favorite_item_data.item_name
        )

        db.add(new_favorite_item)
        db.commit()
        db.refresh(new_favorite_item)

        # Access the exact id value of the newly added FavoriteItem
        new_favorite_item_id = new_favorite_item.item_id

        return {
            "status": 200,
            "message": "Favorite item added successfully",
            "data": [{"item_id": new_favorite_item_id, "item_name": favorite_item_data.item_name, "user_contact": favorite_item_data.user_contact}]
        }
    except Exception as e:
        response.status_code = 500
        return {"status": 500, "message": "Error adding favorite item", "data": {}}

#remove fav item/items
@app.delete("/remove_item/")
def remove_favorite_item(response: Response,item_id: int = Query(..., alias='item_id'),  db: Session = Depends(get_db)):
    try:
        # Check if the favorite item exists
        favorite_item = db.query(models.FavoriteItem).filter(models.FavoriteItem.item_id == item_id).first()
        if not favorite_item:
            raise HTTPException(status_code=404, detail="Favorite item not found")

        # Delete the favorite item
        db.delete(favorite_item)
        db.commit()

        return {"status": 200, "message": "Favorite item removed successfully", "data": {}}
    except Exception as e:
        response.status_code = 500
        return {"status": 500, "message": "Error removing favorite item", "data": {}}


@app.post("/bookings/")
def add_review_feedback(review_feedback: ReviewFeedback,
    booking_id: int = Query(..., description="Booking ID"),

    db: Session = Depends(get_db)
):
    # Retrieve the booking from the database
    booking = db.query(models.Bookings).get(booking_id)

    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    # Update the review and feedback fields if provided
    if review_feedback.review is not None:
        booking.review = review_feedback.review

    if review_feedback.feedback is not None:
        booking.feedback = review_feedback.feedback

    db.commit()

    updated_data = {
        "review": booking.review,
        "feedback": booking.feedback
    }

    return {"status": 200, "message": "Review and feedback added successfully", "data": updated_data}


#get company
@app.get("/get_company/")
def get_company(company_id: int = Query(..., description="Company ID"), db: Session = Depends(get_db)):
    def get_company_by_id(db: Session, company_id: int):
        return db.query(models.Companies).filter(models.Companies.company_id == company_id).first()

    company = get_company_by_id(db, company_id)
    if company is None:
        raise HTTPException(status_code=404, detail="Company not found")
    return {"status": 200, "message": "Company retrieved successfully", "data": company}


#edit company
@app.put("/edit_company/")
def edit_company(
    company_update: dict,
    company_id: int = Query(..., description="Company ID"),
    db: Session = Depends(database.get_db)
):
    # Retrieve the company from the database
    db_company = db.query(models.Companies).filter(models.Companies.company_id == company_id).first()

    if db_company is None:
        raise HTTPException(status_code=404, detail="Company not found")

    # Update company fields with new values
    for field, value in company_update.items():
        if hasattr(db_company, field) and value is not None:
            setattr(db_company, field, value)

    db.commit()
    db.refresh(db_company)

    return {"status": 200, "message": "Company updated successfully", "data": db_company}

#delete company
@app.delete("/delete_company/")
def delete_company(
    company_id: int = Query(..., description="Company ID"),
    db: Session = Depends(database.get_db)
):
    # Retrieve the company from the database
    db_company = db.query(models.Companies).filter(models.Companies.company_id == company_id).first()

    if db_company is None:
        raise HTTPException(status_code=404, detail="Company not found")

    # Delete the company
    db.delete(db_company)
    db.commit()

    return {"status": 200, "message": "Company deleted successfully", "data": {}}

@app.post("/add_company/")
def add_company(
    company_data: dict,
    db: Session = Depends(database.get_db)
):
    company_name = company_data.get("company_name")

    # Check if a company with the same name already exists
    existing_company = db.query(models.Companies).filter(models.Companies.company_name == company_name).first()

    if existing_company:
        return {"status": 400, "message": "Company already exists", "data": existing_company}

    # Create a new instance of the Companies model and populate its fields
    new_company = models.Companies(**company_data)

    # Add the new company to the database
    db.add(new_company)
    db.commit()
    db.refresh(new_company)

    return {"status": 200, "message": "Company added successfully", "data": new_company}

#book_order

@app.post('/book_order')
def add_booking(response: Response, bookOrder: schemas.BookingsCreate, db: Session = Depends(get_db)):
    try:
        new_booking = models.Bookings(**bookOrder.dict())
        db.add(new_booking)
        db.commit()
        db.refresh(new_booking)

        return {"status": 200, "message": "Booking order created successfully!", "data": new_booking}
    except IntegrityError:
        response.status_code = 400
        return {"status": 400, "message": "Error creating booking order", "data": {}}


# Today deal products
@app.get("/today_deal_products/")
def today_deal_products(
    product_id: int,
    db: Session = Depends(database.get_db)
):
    try:
        # Retrieve the list of products with today_deal=True and matching product_id
        products = db.query(models.Products).filter(
            models.Products.product_id == product_id,
            models.Products.today_deal == True
        ).all()

        if not products:
            return {"status": 200, "message": "Product not in today's deal list", "data": {}}

        # Create a list of dictionaries with selected fields for each product
        selected_products = [
            {
                "product_id": product.product_id,
                "product_name": product.product_name,
                "image": product.image,
                "cost": product.cost,
                "discounted_cost": product.discounted_cost
            }
            for product in products
        ]

        return {"status": 200, "message": "This product is in today's deal", "data": selected_products}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error retrieving today's deal products")