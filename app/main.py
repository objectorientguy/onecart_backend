import logging
import os
import shutil
from datetime import timedelta
from io import BytesIO
from typing import List
import firebase_admin
import pandas as pd
from fastapi import FastAPI, Response, Depends, File, Request, HTTPException, Body, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from firebase_admin import credentials, storage
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from starlette.responses import FileResponse

from . import models, schemas
from .database import engine, get_db
from .models import Image, ProductVariant
from .routes import on_boarding, inventory, profile, branches, products, employee, billing_system, company

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
models.Base.metadata.create_all(bind=engine)

app = FastAPI()
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"])

app.include_router(on_boarding.router)
app.include_router(inventory.router)
app.include_router(profile.router)
app.include_router(branches.router)
app.include_router(products.router)
app.include_router(company.router)
app.include_router(billing_system.router)
app.include_router(employee.router)

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
        return {"status": 404, "message": "Product variant not found"}
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
        return {"status": 500, "detail": str(e)}

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


# @app.get("/productsByCategories")
# def get_products_by_categories(db: Session = Depends(get_db)):
#     try:
#
#         category_names = (
#             db.query(Category.category_name)
#             .join(Products, Products.category_id == Category.category_id)
#             .join(ProductVariant, ProductVariant.product_id == Products.product_id)
#             .filter(ProductVariant.is_published.is_(True))
#             .distinct()
#             .all()
#         )
#
#         if not category_names:
#             return {"status": 204, "message": "No categories found with published products", "data": []}
#
#         response_data = []
#
#         for category_name in category_names:
#             category_name = category_name[0]
#
#             products = (
#                 db.query(Products)
#                 .join(ProductVariant, Products.product_id == ProductVariant.product_id)
#                 .filter(
#                     Category.category_name == category_name,
#                     ProductVariant.is_published.is_(True)
#                 )
#                 .all()
#             )
#
#             if products:
#                 serialized_products = []
#
#                 for product in products:
#                     product_variant = (
#                         db.query(ProductVariant)
#                         .filter(
#                             ProductVariant.product_id == product.product_id,
#                             ProductVariant.is_published.is_(True)
#                         )
#                         .order_by(ProductVariant.variant_id)
#                         .first()
#                     )
#
#                     if product_variant:
#                         serialized_products.append({
#                             "product_id": product.product_id,
#                             "product_name": product.product_name,
#                             "variant_id": product_variant.variant_id,
#                             "image": product_variant.image,
#                         })
#
#                 category_data = {"category_name": category_name, "products": serialized_products}
#                 response_data.append(category_data)
#
#         if not response_data:
#             return {"status": 204, "message": "No products found for any category", "data": []}
#
#         return {
#             "status": 200,
#             "message": "Products fetched successfully for all categories with is_published = true",
#             "data": response_data
#         }
#
#     except Exception as e:
#         print(repr(e))
#         return {"status": 500, "message": "Internal Server Error", "data": {}}


# @app.get('/productVariants')
# def get_product_variants(
#         product_id: int = Query(..., title="Product ID", description="ID of the product to retrieve variants for",
#                                 ge=1),
#         db: Session = Depends(get_db)
# ):
#     try:
#         product = db.query(models.Products).filter(models.Products.product_id == product_id).first()
#
#         if not product:
#             return {"status": 200, "message": "Product Not Found", "data": {}}
#
#         variants = db.query(models.ProductVariant).filter(
#             models.ProductVariant.product_id == product_id,
#             models.ProductVariant.is_published.is_(True)
#         ).all()
#
#         response_data = {
#             "status": 200,
#             "message": "Product variants fetched successfully",
#             "data": [
#                 {
#                     "image": variant.image,
#                     "product_name": product.product_name,
#                     "quantity": variant.quantity,
#                     "price": variant.variant_cost,
#                     "unit": variant.measuring_unit
#                 }
#                 for variant in variants
#             ]
#         }
#
#         return response_data
#     except Exception as e:
#         print(repr(e))
#         return {"status": 500, "message": "Internal Server Error", "data": {}}


# @app.put('/editProductVariant/')
# def edit_product_variant(variant_data: schemas.ProductEdit,
#                          variant_id: int = Query(..., description="The ID of the product variant to edit."),
#                          db: Session = Depends(get_db)):
#     try:
#         existing_variant = db.query(models.ProductVariant).filter(
#             models.ProductVariant.variant_id == variant_id).first()
#
#         if not existing_variant:
#             return {"status": 204, "message": "Product variant not found", "data": {}}
#
#         # Update the fields based on the provided data
#         for field, value in variant_data.dict().items():
#             if value is not None:
#                 setattr(existing_variant, field, value)
#
#         db.commit()
#
#         return {"status": 200, "message": "Product variant edited successfully", "data": {}}
#     except IntegrityError as e:
#         if "duplicate key value violates unique constraint" in str(e):
#             return {"status": 400, "message": "Check the variant details", "data": {}}
#         else:
#             return {"status": 500, "message": "Internal Server Error", "error": str(e)}


# @app.put('/editProduct')
# def edit_product(product_data: schemas.ProductEdit,product_id: int = Query(..., description="The ID of the product to edit"), db: Session = Depends(get_db)):
#     try:
#         existing_product = db.query(models.Products).filter(
#             models.Products.product_id == product_id).first()
#
#         if not existing_product:
#             return {"status": 204, "message": "Product not found", "data": {}}
#
#         # Update the fields based on the provided data
#         for field, value in product_data.dict().items():
#             if value is not None:
#                 setattr(existing_product, field, value)
#
#         db.commit()
#
#         return {"status": 200, "message": "Product edited successfully", "data": {}}
#     except IntegrityError as e:
#         if "duplicate key value violates unique constraint" in str(e):
#             return {"status": 400, "message": "Check the product details", "data": {}}
#         else:
#             return {"status": 500, "message": "Internal Server Error", "error": str(e)}
