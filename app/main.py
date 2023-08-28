from typing import List
from contextlib import contextmanager
import bcrypt
from fastapi import FastAPI, Response, Depends, UploadFile, File, Request, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from starlette.responses import FileResponse
import logging
from . import models, schemas
from .models import Image
from .database import engine, get_db
from fastapi.middleware.cors import CORSMiddleware
import os

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
                new_user_added = models.UserCompany(  #composite table
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
def add_address( user_contact: int, createAddress: schemas.AddAddress, response: Response, db: Session = Depends(get_db)):
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


# @app.post("/add_to_cart", response_model=schemas.CartResponse)
# def add_to_cart(cart_data: schemas.CartCreate, db: Session = Depends(get_db)):
#     cart = db.query(models.Cart).filter(models.Cart.company_id == cart_data.company_id,
#                                         models.Cart.user_id == cart_data.user_id).first()
#
#     if cart is None:
#         cart = models.Cart(**cart_data.model_dump())
#         db.add(cart)
#         db.commit()
#     else:
#         cart_items = db.query(models.CartItem).filter(cart.id).all()
#         existing_product_ids = set(item.product_id for item in cart_items)
#         for item in cart_data.items:
#             if item.product_id not in existing_product_ids:
#                 new_cart_item = models.CartItem(cart_id=cart.id, product_id=item.product_id)
#                 db.add(new_cart_item)
#
#         db.flush()
#
#     db.commit()
#     db.refresh(cart)
#
#     return cart


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
        print(repr(e))
        response.status_code = 200
        return {"status": 204, "message": "Error", "data": {}}

@contextmanager
def session_scope():
    session = Session(bind=engine)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
@app.post("/create_categories/")
def create_categories():
    try:
        # Create 20 different categories and add them to the database
        categories_to_create = [
            {"category_name": "Fruits & Vegetables", "category_image": "https://oneart.onrender.com/images/Fruit_and_vegetables.jpg"},
            {"category_name": "Dairy & Bakery", "category_image": "https://oneart.onrender.com/images/bakery-dairy.jpg"},
            {"category_name": "Staples", "category_image" : "https://oneart.onrender.com/images/staples.jpg"},
            {"category_name": "Premium Fruits", "category_image" : "https://oneart.onrender.com/images/premium-fruits.jpeg"},
            {"category_name": "Beverages", "category_image" : "https://oneart.onrender.com/images/beverages.jpg"},
            {"category_name": "Personal Care", "category_image": "https://oneart.onrender.com/images/personal-care.png"},
            {"category_name": "Home Care", "category_image": "https://oneart.onrender.com/images/home-care.jpeg"},
            {"category_name": "Mom & Baby Care", "category_image": "https://oneart.onrender.com/images/baby-care.jpg"},
            {"category_name": "Home & Kitchen", "category_image": "https://oneart.onrender.com/images/home-kitchen.jpg"}


        ]

        with session_scope() as session:
            for category_data in categories_to_create:
                category = models.Categories(**category_data)
                session.add(category)
                session.commit()
                session.refresh(category)

        return {"message": "Categories created successfully", "data" : {} }

    except Exception as e:
        print(repr(e))
        raise HTTPException(status_code=500, detail=str(e))

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
def add_product_variants(product_id: int, variants: schemas.ProductVariant, response: Response, db: Session = Depends(get_db)):
    try:
        new_product_variant = models.ProductVariant(**variants.model_dump())
        db.add(new_product_variant)
        db.commit()
        db.refresh(new_product_variant)

        return {"status": "200", "message": "New product variants added successfully!", "data": variants}
    except IntegrityError:
        response.status_code = 200
        return {"status": "404", "message": "Error", "data": {}}


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


@app.get("/getProductVariants/{product_id}")
def get_product_variants(response: Response, product_id: int, db: Session = Depends(get_db)):
    try:
        fetch_variants = db.query(models.ProductVariant).filter(models.ProductVariant.product_id == product_id).all()
        if not fetch_variants:
            return {"status": 204, "message": "No product variants available", "data": {}}

        return {"status": 200, "message": "Product Variants Fetched", "data": fetch_variants}
    except IntegrityError:
        response.status_code = 200
        return {"status": 204, "message": "Error", "data": {}}


@app.put("/editProduct")
def edit_product(editProduct: schemas.EditProduct,response: Response,product_id: int,db: Session = Depends(get_db)):
    try:
        edit_product = db.query(models.Products).filter(
            models.Products.product_id == product_id
        )
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

@app.get("/products/categories/{category_id}")
def get_products_by_category_id(response: Response, category_id: int, db: Session = Depends(get_db)):
    try:
        fetch_category = db.query(models.Categories).filter(models.Categories.category_id == category_id).first()
        if not fetch_category:
            raise HTTPException(status_code=404, detail="Category not found")

        fetch_product_category = db.query(models.Products).filter(models.Products.category_id == category_id).all()
        if not fetch_product_category:
            return {"status": 204, "message": "No product of this category available", "data": {}}

        return {"status": 200, "message": "Product by category Fetched", "category": fetch_category, "data": fetch_product_category}
    except IntegrityError:
        response.status_code = 200
        return {"status": 204, "message": "Error", "data": {}}

@app.post("/carts/")
async def create_cart(cart: schemas.CartSchema, response: Response, db: Session = Depends(get_db)):

    try:
        new_cart = models.Cart(**cart.model_dump())
        db.add(new_cart)
        db.commit()
        db.refresh(new_cart)

        return {"status": "200", "message": "New cart created successfully!", "data": new_cart}
    except IntegrityError:
        response.status_code = 400
        return {"status": "400","data": {}}

@app.post("/carts/Items")
async def create_cart(items: schemas.CartItemSchema, response: Response, db: Session = Depends(get_db)):

    try:
        new_items = models.CartItem(**items.model_dump())
        db.add(new_items)
        db.commit()
        db.refresh(new_items)

        return {"status": "200", "message": "New Items added to the cart successfully!", "data": new_items}
    except IntegrityError:
        response.status_code = 400
        return {"status": "400","data": {}}

@app.get("/getCartItem/{cart_id}")
def get_cart_items_by_cart_id(response: Response, cart_id: int, db: Session = Depends(get_db)):
    try:
        fetch_cart_items = db.query(models.CartItem).filter(models.CartItem.cart_id == cart_id).all()
        if not fetch_cart_items:
            return {"status": 204, "message": "No cart items found", "data": {}}

        return {"status": 200, "message": "Cart items fetched", "data": fetch_cart_items}
    except IntegrityError:
        response.status_code = 200
        return {"status": 204, "message": "Error", "data": {}}


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

@app.post('/deleteCartItem')
def delete_cart_item(id: int, response: Response, db: Session = Depends(get_db)):
    try:
        cartItem = db.query(models.CartItem).get(id)

        if not cartItem:
            raise HTTPException(status_code=404, detail="Cart Item not found")

        db.delete(cartItem)
        db.commit()

        return {"status": "200", "message": "Cart Item deleted successfully!"}
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


@app.get("/productsSearch/")
def search_products(response: Response, search_term: str, db: Session = Depends(get_db)):
    try:

        if not search_term:
            raise ValueError("Search term cannot be empty.")
        for char in search_term:
            if not char.isalnum():
                raise ValueError(f"Search term cannot contain invalid characters: {char}.")

        search_results = db.query(models.Products).filter(
            (models.Products.product_name.ilike(f"%{search_term}%")) |
            (models.Products.brand_name.ilike(f"%{search_term}%"))
        ).all()

        if not search_results:
            return {"status": 204, "message": "No product or brand found", "data": {}}

        return {
            "status": 200,
            "message": "Products and Brand names fetched",
            "data": {
                "search_results": search_results
            }
        }


    except ValueError as e:
        print(repr(e))
        response.status_code = 400
        return {"status": 400, "message": "Error", "data": {} }
    except IntegrityError as e:
        response.status_code = 500
        return {"status": 500, "message": "Error", "data": {}}


@app.get("/getBanners")
def get_all_banners(response: Response, db: Session = Depends(get_db)):
    try:
        fetch_banners = db.query(models.PromotionalBanners).all()
        if not fetch_banners:
            return {"status": 204, "message": "No Banners available please add", "data": {}}

        return {"status": 200, "message": "Banners Fetched", "data": fetch_banners}
    except IntegrityError:
        response.status_code = 200
        return {"status": 204, "message": "Error", "data": {}}

@app.get("/getDeals")
def get_deal_products(response: Response, db: Session = Depends(get_db)):
    try:
        deal_products = db.query(models.Products).filter(models.Products.deal == True).all()
        if not deal_products:
            return {"status": 204, "message": "No deal products available", "data": []}

        return {"status": 200, "message": "Deal products fetched", "data": deal_products}
    except IntegrityError:
        response.status_code = 200
        return {"status": 204, "message": "Error", "data": []}


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


@app.post('/bookOrder')
def add_booking(response: Response, bookOrder: schemas.BookingsCreate, db: Session = Depends(get_db)):
    try:
        new_booking = models.Bookings(**bookOrder.model_dump())
        db.add(new_booking)
        db.commit()
        db.refresh(new_booking)

        return {"status": 200, "message": "Booking order created successfully!", "data": new_booking}
    except IntegrityError:
        response.status_code = 400
        return {"status": 400, "message": "Error creating booking order", "data": {}}


@app.get("/getOrders")
def get_Orders(response: Response, db: Session = Depends(get_db)):
    try:
        orders = db.query(models.Bookings).all()
        if not orders:
            return {"status": 204, "message": "No Booking Orders available", "data": []}

        return {"status": 200, "message": "Booking Orders  fetched", "data": orders}
    except IntegrityError as e:
        print(repr(e))
        response.status_code = 200
        return {"status": 204, "message": "Error", "data": []}


@app.get("/getOrders/{order_id}")
def get_oreders_by_order_id(response: Response, order_id: int, db: Session = Depends(get_db)):
    try:
        fetch_orders_id = db.query(models.Bookings).filter(models.Bookings.order_id == order_id).all()
        if not fetch_orders_id:
            return {"status": 204, "message": "No Booking Orders found", "data": {}}

        return {"status": 200, "message": "Booking Orders fetched", "data": fetch_orders_id}
    except IntegrityError:
        response.status_code = 200
        return {"status": 204, "message": "Error", "data": {}}

@app.get("/getProductswithCartId/{cart_id}")
def get_cart_items_with_product_ids(response: Response, cart_id: int, db: Session = Depends(get_db)):

    try:
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
                "cartItemId": cart_item.cartItemId,
                "product": product,
                "variant": variant
            })

        return {"status": 200, "message": "Cart items fetched", "data": cart_items_with_product_ids}
    except IntegrityError as e:
        print(repr(e))
        response.status_code = 500
        return {"status": 500, "message": "Error", "data": {}}


@app.get("/checkoutScreen/{cart_id}")
def get_cart_item_count_with_price_and_discount_sum(response: Response, cart_id: int, db: Session = Depends(get_db)):

    try:
        fetch_cart_items = db.query(models.CartItem).filter(models.CartItem.cart_id == cart_id).all()
        if not fetch_cart_items:
            return {"status": 404, "message": "No cart items found", "data": {}}

        cart_item_count = 0
        cart_total = 0
        discount_sum = 0
        coupon_applied = None
        delivery_charges = 40.50

        if models.Cart.coupon_id:
            applied_coupon = db.query(models.Coupon).filter(models.Coupon.coupon_id == models.Cart.coupon_id).first()
            if applied_coupon:
                coupon_applied = applied_coupon.coupon_name

        for cart_item in fetch_cart_items:
            product_id = cart_item.product_id
            variant_id = cart_item.variant_id

            product = db.query(models.Products).filter(models.Products.product_id == product_id).first()
            variant = db.query(models.ProductVariant).filter(models.ProductVariant.variant_id == variant_id).first()

            if variant:
                price = variant.variant_price
                discount_amount = variant.discounted_cost
            else:
                price = product.price
                discount_amount = product.discounted_cost

            discount_sum += variant.discounted_cost * cart_item.item_count
            discount_sum += product.discounted_cost * cart_item.item_count

            cart_item_count += cart_item.item_count
            cart_total += price * cart_item.item_count

        total_bill = cart_total - discount_sum + delivery_charges

        discount_sum = cart_total - discount_sum

        return {"status": 200, "message": "CHECKOUT SCREEN fetched", "data": {"cart_item_count": cart_item_count, "cart_total": cart_total, "discount_sum": discount_sum, "coupon_applied": coupon_applied, "delivery_charges": delivery_charges, "total_bill": total_bill}}
    except IntegrityError as e:
        print(repr(e))
        response.status_code = 500
        return {"status": 500, "message": "Error", "data": {}}
