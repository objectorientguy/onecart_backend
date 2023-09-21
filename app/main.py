from typing import List
from contextlib import contextmanager
import bcrypt
from fastapi import FastAPI, Response, Depends, UploadFile, File, Request, HTTPException, Body
from sqlalchemy.orm import Session, joinedload
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

@app.post('/addProducts')
def add_products(products: List[schemas.Product], response: Response, db: Session = Depends(get_db)):
    try:
        new_products = []
        for product in products:
            existing_product = db.query(models.Products).filter(
                models.Products.product_name == product.product_name
            ).first()

            if existing_product:
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


@app.get("/getProductVariants/{product_id}")
def get_product_variants(response: Response, product_id: int, db: Session = Depends(get_db)):
    try:
        feature = db.query(models.FreatureList).all()
        recomended_products = []
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
                    "count": variant.count,
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
                "data": {"product_data": product_data, "feature": feature, "recommended_products":recomended_products}
            }
        else:
            return {
                "status": 404,
                "message": "Product not found",
                "data": {}
            }

    except IntegrityError:
        response.status_code = 200
        return {"status": 204, "message": "Error", "data": {}}


@app.put("/editProduct")
def edit_product(editProduct: schemas.EditProduct,response: Response,product_id: int,db: Session = Depends(get_db)):
    try:
        edit_product = db.query(models.Products).filter( models.Products.product_id == product_id )
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

            # Fetch variants for each product
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
                    "discounted_cost": variant.discounted_cost,
                    "discount": variant.discount,
                    "quantity": variant.quantity,
                    "description": variant.description,
                    "image": variant.image,
                    "ratings": variant.ratings
                }

                product_details_dict["variants"].append(variant_details)

            product_details.append(product_details_dict)

        return {"status": 200, "message": "Products by category fetched", "products": product_details}
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
        return {"status": "400","data": {}}


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


@app.get("/productsSearch/")
def search_products(response: Response, search_term: str, db: Session = Depends(get_db)):
    try:

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

        return {"status": 200, "message": "Products and Brand names fetched", "data": { "Categories": search_categories, "Brands": search_brand, "search_results": search_results}}


    except ValueError as e:
        print(repr(e))
        response.status_code = 400
        return {"status": 400, "message": "Error", "data": {} }
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
            ).filter(models.CategoryProduct.category_id == category.category_id).all()

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
                    # "tags":product.tags,
                    "variants": [],
                }

                product_variants = db.query(models.ProductVariant).filter(models.ProductVariant.product_id == product.product_id).all()
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

        return category_details_with_products
    except Exception as e:
        print(repr(e))
        response.status_code = 500
        return {"status": 500, "message": "Internal Server Error", "data": []}

@app.get("/getAllCategoriesVariants") #for fetch products with category
async def get_all_products_in_categories(response: Response, db: Session = Depends(get_db)):
    try:
        feature = db.query(models.FreatureList).all()
        product_categories = db.query(models.Categories).all()

        recomended_products = []
        category_details_variants = []
        for category in product_categories:
            products = db.query(models.Products).join(models.CategoryProduct,
                models.Products.product_id == models.CategoryProduct.product_id
            ).filter(models.CategoryProduct.category_id == category.category_id).all()

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

                product_variant = db.query(models.ProductVariant).filter(models.ProductVariant.product_id == product.product_id).first()
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

        return {"feature":feature,"category details":category_details_variants,"recomended products":recomended_products}
    except Exception as e:
        print(repr(e))
        response.status_code = 500
        return {"status": 500, "message": "Internal Server Error", "data": []}

@app.get("/homescreen")
def get_categories_and_banners_and_deals(response: Response, db: Session = Depends(get_db)):
    try:
        fetch_categories = db.query(models.Categories).all()
        fetch_shop_banner = db.query(models.Shops).all()
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
                # " products_tags": deal.tags,
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
                "today's deals": shop_deals
            },
        }
    except IntegrityError:
        response.status_code = 200
        return {"status": 204, "message": "Error", "data": {}}

@app.get("/getProductswithCartId/{cart_id}")
def get_cart_items_with_product_ids(response: Response, cart_id: int,customer_contact:int, db: Session = Depends(get_db)):

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

        return {"status": 200, "message": "Cart items fetched", "data": {"cart_items": cart_items_with_product_ids,"item_count": cart_item_count}}
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
def add_to_cart(customer_contact: int, cart_Item: dict = Body(...), db: Session = Depends(get_db)):
    try:
        cart = db.query(models.Cart).filter_by(customer_contact=customer_contact).first()

        if cart is None:
            cart = Cart(customer_contact=customer_contact)
            db.add(cart)
            db.commit()
            db.refresh(cart)

        # cart_id = cart_Item.pop('cart_id', None)

        cart_item = models.CartItem(**cart_Item, cart_id=cart.cart_id)
        db.add(cart_item)
        db.commit()
        db.refresh(cart_item)

        return {"status": 200, "message": "Items Successfully Added to the Cart", "data": cart_item}
    except IntegrityError as e:
                print(repr(e))
                response.status_code = 500
                return {"status": 500, "message": "Error", "data": {}}



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
                "variant": variant
            })

            variant_cost = cart_item.variant.variant_cost
            if variant_id in variant_costs:
                variant_costs[variant_id] += variant_cost
            else:
                variant_costs[variant_id] = variant_cost
            # for variant_id, total_cost in variant_costs.items():
            #     print(f"Variant ID: {variant_id}, Total Cost: {total_cost}")
            total_cost = sum(variant_costs.values())

        return {"status": 200, "message": "Cart items fetched", "data": { "cart_items": cart_items_with_customer_contact, "cart_item_count": len(cart_items), "total_price": total_cost} }
    except IntegrityError as e:
        print(repr(e))
        response.status_code = 500
        return {"status": 500, "message": "Error", "data": {}}

import pyaudio
# from . import speech  # This assumes the `speech.py` file is in the same directory
import speech_recognition as sr

# def capture_voice_input():
#     recognizer = sr.Recognizer()
#     microphone = sr.Microphone()
#
#     with microphone as source:
#         print("Please say the recipe name...")
#         recognizer.adjust_for_ambient_noise(source)
#         audio = recognizer.listen(source)
#
#     try:
#         recognized_text = recognizer.recognize_google(audio)
#         return recognized_text
#     except sr.UnknownValueError:
#         print("Sorry, I could not understand your voice input.")
#         return None


def capture_voice_input():
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()

    with microphone as source:
        print("Please say the recipe name...")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)

    try:
        recognized_text = recognizer.recognize_google(audio)
        print(recognized_text)
        return recognized_text
    except sr.UnknownValueError:
        print("Sorry, I could not understand your voice input.")
        return None


# @app.post("/voice_input")
# async def get_voice_input():
#     voice_input = capture_voice_input()
#
#     if voice_input:
#         return {"message": "Voice input captured successfully", "voice_text": voice_input}
#     else:
#         return {"message": "Failed to capture voice input"}

butter_chicken_recipe = {
"name": "Butter Chicken",
"description": "A delicious and creamy Indian chicken curry dish",
"ingredients": [
"1 pound boneless, skinless chicken breasts, cut into bite-sized pieces",
"1 tablespoon tandoori masala",
"1/2 teaspoon ground cumin",
"1/4 teaspoon salt",
"1/4 teaspoon black pepper",
"1/4 cup yogurt",
"1 tablespoon lemon juice",
"1 tablespoon butter",
"1 tablespoon oil",
"1 onion, chopped",
"2 cloves garlic, minced",
"1 gingerroot (1-inch piece), minced",
"1 (14.5 ounce) can diced tomatoes",
"1/2 cup heavy cream",
"1/4 cup cilantro, chopped"
],
"steps": [
"In a large bowl, combine the chicken, tandoori masala, cumin, salt, pepper, yogurt, and lemon juice. Mix well and marinate for at least 30 minutes, or up to overnight.",
"Heat the butter and oil in a large skillet over medium heat. Add the chicken and cook until browned on all sides.",
"Add the onion, garlic, and ginger to the skillet and cook until softened, about 5 minutes.",
"Add the diced tomatoes and bring to a boil. Reduce heat to low and simmer for 15 minutes, or until the chicken is cooked through.",
"Stir in the heavy cream and cilantro. Serve with rice or naan bread."
]
}
gajar_ka_halwa_recipe = {
    "name": "Gajar ka Halwa",
    "description": "A delicious and creamy Indian carrot dessert",
    "ingredients": [
        "1 kg carrots, peeled and grated",
        "1 cup milk",
        "1/2 cup sugar",
        "1/4 cup ghee",
        "1/4 cup chopped almonds",
        "1/4 cup chopped cashews",
        "1/4 teaspoon cardamom powder"
    ],
    "steps": [
        "Heat the ghee in a heavy bottomed pan over medium heat. Add the grated carrots and cook until softened, about 10 minutes.",
        "Add the milk and sugar to the pan and bring to a boil. Reduce heat to low and simmer until the carrots are tender and the milk has thickened, about 30 minutes.",
        "Stir in the cardamom powder and nuts. Serve warm or at room temperature."
    ]
}
gulab_jamun_recipe = {
    "name": "Gulab Jamun",
    "description": "A delicious and syrupy Indian dessert",
    "ingredients": [
        "1 cup milk powder",
        "1/4 cup all-purpose flour",
        "1/4 teaspoon baking powder",
        "1/4 teaspoon baking soda",
        "1/4 teaspoon cardamom powder",
        "1/4 cup ghee, melted",
        "1/4 cup sugar",
        "1/4 cup water",
        "1/4 teaspoon saffron threads, soaked in 1 tablespoon of milk",
        "1/4 cup chopped pistachios"
    ],
    "steps": [
        "In a large bowl, combine the milk powder, flour, baking powder, baking soda, and cardamom powder.",
        "Add the melted ghee and mix well.",
        "Add enough water to make a soft dough.",
        "Divide the dough into small balls, about 1 inch in diameter.",
        "Heat the ghee in a deep frying pan over medium heat.",
        "Fry the gulab jamuns in the hot ghee until golden brown, about 10 minutes.",
        "In a separate pan, combine the sugar and water and bring to a boil. Reduce heat to low and simmer for 5 minutes.",
        "Add the fried gulab jamuns and saffron milk to the sugar syrup and simmer for another 5 minutes.",
        "Serve warm or at room temperature, garnished with chopped pistachios."
    ]
}
egg_biryani_recipe = {
    "name": "Egg Biryani",
    "description": "A delicious and flavorful Indian rice dish with eggs",
    "ingredients": [
        "1 cup basmati rice, soaked in water for 30 minutes",
        "1 pound boneless, skinless chicken breasts, cut into bite-sized pieces",
        "1/2 cup chopped onions",
        "1/2 cup chopped tomatoes",
        "1/4 cup chopped cilantro",
        "1/4 teaspoon ground cumin",
        "1/4 teaspoon ground coriander",
        "1/4 teaspoon turmeric powder",
        "1/4 teaspoon red chili powder",
        "1/4 teaspoon garam masala powder",
        "1/4 teaspoon salt",
        "1/4 cup oil",
        "6 hard-boiled eggs, peeled and halved"
    ],
    "steps": [
        "Drain the rice and rinse it well.",
        "Heat the oil in a large pot over medium heat. Add the onions and cook until softened, about 5 minutes.",
        "Add the chicken and cook until browned on all sides.",
        "Add the tomatoes, cilantro, cumin, coriander, turmeric, chili powder, garam masala, and salt. Mix well and cook for 2 minutes.",
        "Add the rice and 4 cups of water to the pot. Bring to a boil, then reduce heat to low and simmer for 20 minutes, or until the rice is cooked through.",
        "Stir in the hard-boiled eggs and cook for another 2 minutes.",
        "Serve hot."
    ]
}
butter_paneer_recipe = {
    "name": "Butter Paneer",
    "description": "A delicious and creamy Indian paneer curry dish",
    "ingredients": [
        "1 pound paneer, cut into cubes",
        "1 tablespoon butter",
        "1 tablespoon oil",
        "1 onion, chopped",
        "2 cloves garlic, minced",
        "1 gingerroot (1-inch piece), minced",
        "1 (14.5 ounce) can diced tomatoes",
        "1/2 cup heavy cream",
        "1/4 cup cilantro, chopped",
        "1/4 teaspoon garam masala powder",
        "1/4 teaspoon turmeric powder",
        "1/4 teaspoon red chili powder",
        "1/4 teaspoon salt"
    ],
    "steps": [
        "Heat the butter and oil in a large skillet over medium heat. Add the onions and cook until softened, about 5 minutes.",
        "Add the garlic and ginger and cook for another minute.",
        "Add the diced tomatoes, heavy cream, cilantro, garam masala, turmeric, chili powder, and salt. Mix well and bring to a boil. Reduce heat to low and simmer for 10 minutes.",
        "Add the paneer cubes and cook for another 2 minutes, or until heated through.",
        "Serve hot."
    ]
}


import json

def fetch_all_recipes():
    # Load all the JSON files from the code
    recipes = []
    for recipe_json in [butter_chicken_recipe, gajar_ka_halwa_recipe, gulab_jamun_recipe, egg_biryani_recipe, butter_paneer_recipe]:
        recipes.append(recipe_json)

    return recipes


def search_recipe(recipes, keyword):
    # Search all the recipes for the given keyword
    found_recipes = []
    for recipe in recipes:
        found_ingredients = [ingredient for ingredient in recipe.get("ingredients", []) if keyword in ingredient]
        found_steps = [step for step in recipe.get("steps", []) if keyword in step]

        if found_ingredients or found_steps:
            found_recipes.append({
                "name": recipe.get("name"),
                "found_ingredients": found_ingredients,
                "found_steps": found_steps,
            })

    return found_recipes

@app.post("/voice_input")
async def get_voice_input(response: Response, db: Session = Depends(get_db)):
    voice_input = capture_voice_input()

    if voice_input:
        recipes = fetch_all_recipes()
        words = voice_input.split()

        found_recipes_set = set()
        found_recipes = []
        matched_recipe_ingredients = []

        for word in words:
            word_found_recipes = search_recipe(recipes, word)
            for recipe in word_found_recipes:
                recipe_name = recipe["name"]
                matched_recipe_ingredients.extend(recipe.get("found_ingredients", []))

                if recipe_name not in found_recipes_set:
                    found_recipes_set.add(recipe_name)
                    found_recipes.append(recipe)
                    # matched_ingredients_set.update(recipe["found_ingredients"])

        # matched_ingredients = list(matched_ingredients_set)

        # matched_recipe_ingredients = []
        # for recipe in found_recipes:
        #     matched_recipe_ingredients.extend(recipe.get("found_ingredients", []))
        unique_matched_recipe_ingredients = set(matched_recipe_ingredients)

        return {
            "data": {
                "voice_input": voice_input,
                "found_recipes": found_recipes,
                # "matched_ingredients": matched_ingredients,
                "matched_recipe_ingredients": unique_matched_recipe_ingredients

            }
        }
    else:
        return {"message": "Failed to capture voice input"}