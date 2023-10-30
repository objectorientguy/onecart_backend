from fastapi import Response, Depends, Query, APIRouter
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app import models, schemas
from app.database import get_db
from app.schemas import ProductInput
router = APIRouter()


@router.post('/addProduct')
def add_product(product_data: ProductInput, db: Session = Depends(get_db)):
    try:
        brand = db.query(models.Brand).filter(models.Brand.brand_name == product_data.brand_name).first()
        if not brand:
            return {"status": 400, "message": "Brand Not Found", "data": {}}

        category = db.query(models.Category).filter(models.Category.category_name == product_data.category_name).first()
        if not category:
            category = models.Category(category_name=product_data.category_name)
            db.add(category)
            db.commit()
            db.refresh(category)

        existing_product = db.query(models.Products).filter(models.Products.product_name == product_data.product_name).first()
        if existing_product:
            return {"status": 400, "message": "Product With same name already exist", "data": {}}

        existing_variant = db.query(models.ProductVariant).filter(models.ProductVariant.barcode_no == product_data.barcode_no).first()
        if existing_variant:
            return {"status": 400, "message": "Product With same barcode number already exist", "data": {}}

        new_product = models.Products(
            product_name=product_data.product_name,
            brand_id=brand.brand_id,
            category_id=category.category_id
        )
        db.add(new_product)
        db.commit()
        db.refresh(new_product)

        new_variant = models.ProductVariant(
            variant_cost=product_data.variant_cost,
            measuring_unit=product_data.measuring_unit,
            brand_name=product_data.brand_name,
            discounted_cost=product_data.discounted_cost,
            quantity=product_data.quantity,
            image=product_data.image,
            stock=product_data.stock,
            description=product_data.description,
            product_id=new_product.product_id,
            branch_id=product_data.branch_id,
            is_published=product_data.is_published,
            barcode_no=product_data.barcode_no
        )
        db.add(new_variant)
        db.commit()

        db.add(new_variant)
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
        return {"status": 500, "message": "Internal Server Error", "data": {}}

@router.post('/addProductVariant')
def add_product_variant(product_id: int, product_data: schemas.ProductVariant, db: Session = Depends(get_db)):
    try:
        existing_product_variant = db.query(models.ProductVariant).filter(
            models.ProductVariant.product_id == product_id).first()
        if not existing_product_variant:
            return {"status": 204, "message": "Product Variant Not found", "data": {}}
        product = db.query(models.Products).filter(models.Products.product_id == product_id).first()
        if not product:
            return {"status": 204, "message": "Product Not found", "data": {}}
        new_variant = models.ProductVariant(
            variant_cost=product_data.variant_cost,
            brand_name=existing_product_variant.brand_name,
            branch_id=existing_product_variant.branch_id,
            discounted_cost=product_data.discounted_cost,
            stock=product_data.stock,
            quantity=product_data.quantity,
            measuring_unit=product_data.measuring_unit,
            description=existing_product_variant.description,
            product_id=product_id,
            barcode_no=product_data.barcode_no,
            image=product_data.image,
            is_published=product_data.is_published
        )
        db.add(new_variant)
        db.commit()
        return {"status": 200, "message": "Product variant added successfully", "data": {}}
    except Exception as e:
        return {"status": 500, "message": "Internal Server Error", "error": str(e)}


@router.put('/editProductVariant')
def edit_product_variant(variant_id: int, variant_data: schemas.ProductEdit, db: Session = Depends(get_db)):
    try:
        existing_variant = db.query(models.ProductVariant).filter(
            models.ProductVariant.variant_id == variant_id,
            models.ProductVariant.branch_id == variant_data.branch_id).first()
        if not existing_variant:
            return {"status": 204, "detail": "Product variant not found", "data": {}}
        for field, value in variant_data.model_dump().items():
            if value is not None:
                setattr(existing_variant, field, value)
        db.commit()
        return {"status": 200, "message": "Product variant edited successfully!"}
    except IntegrityError as e:
        if "duplicate key value violates unique constraint" in str(e):
            return {"status": 400, "message": "Check the variant details", "data": {}}
        else:
            return {"status": 500, "message": "Internal Server Error", "error": str(e)}


@router.get('/getProductVariant')
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


@router.delete('/deleteProduct')
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


@router.delete('/deleteProductVariant')
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


@router.get("/getAllCategories")
async def get_categories(response: Response, db: Session = Depends(get_db)):
    try:
        categories = db.query(models.Category).all()
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


@router.get('/productVariantDetails')
def get_product_variant_details(
        product_id: int = Query(..., title="Product ID", description="ID of the product"),
        variant_id: int = Query(..., title="Variant ID", description="ID of the product variant"),
        db: Session = Depends(get_db)):
    try:
        product = db.query(models.Products).filter(models.Products.product_id == product_id).first()
        if not product:
            return {"status": 204, "message": "Product Not Found", "data": {}}
        variant = db.query(models.ProductVariant).filter(
            models.ProductVariant.product_id == product_id,
            models.ProductVariant.variant_id == variant_id).first()
        if not variant:
            return {"status": 204, "message": "Product Not Found", "data": {}}
        if not variant.is_published:
            return {"status": 204, "message": "Product Variant is not Published", "data": {}}
        category = product.category
        category_name = category.category_name
        response_data = {
            "status": 200,
            "message": "Product variant details fetched successfully",
            "data": {
                "product_id": product.product_id,
                "product_name": product.product_name,
                "variant_id": variant.variant_id,
                "variant_cost": variant.variant_cost,
                "brand_name": variant.brand_name,
                "quantity": variant.quantity,
                "discounted_cost": variant.discounted_cost,
                "stock": variant.stock,
                "description": variant.description,
                "image": variant.image,
                "measuring_unit": variant.measuring_unit,
                "category_name": category_name,
            }
        }
        return response_data
    except Exception as e:
        print(repr(e))
        return {"status": 500, "message": "Internal Server Error", "data": {}}


@router.get("/productsByCategory")
def get_products_by_categories(db: Session = Depends(get_db)):
    try:

        category_names = (
            db.query(models.Category.category_name)
            .join(models.Products, models.Products.category_id == models.Category.category_id)
            .join(models.ProductVariant, models.ProductVariant.product_id == models.Products.product_id)
            .filter(models.ProductVariant.is_published.is_(True))
            .distinct()
            .all()
        )
        response_data = []
        for category_name in category_names:
            category_name = category_name[0]
            products = (
                db.query(models.Products)
                .join(models.ProductVariant, models.Products.product_id == models.ProductVariant.product_id)
                .filter(
                    models.Category.category_name == category_name,
                    models.ProductVariant.is_published.is_(True)).all())
            if products:
                serialized_products = []
                for product in products:
                    product_variants = (
                        db.query(models.ProductVariant)
                        .filter(
                            models.ProductVariant.product_id == product.product_id,
                            models.ProductVariant.is_published.is_(True)).all())
                    if product_variants:
                        serialized_variants = []
                        for variant in product_variants:
                            variant_images = variant.image if variant.image else []
                            serialized_variants.append({
                                "product_id": product.product_id,
                                "product_name": product.product_name,
                                "variant_id": variant.variant_id,
                                "image": variant_images,
                            })
                        serialized_products.append({
                            "product_id": product.product_id,
                            "product_name": product.product_name,
                            "variants": serialized_variants,
                        })
                category_data = {"category_name": category_name, "products": serialized_products}
                response_data.append(category_data)
        if not response_data:
            return {"status": 204, "message": "No products found for any category", "data": []}
        return {"status": 200,
                "message": "Products fetched successfully for all categories with is_published = true",
                "data": response_data}
    except Exception as e:
        print(repr(e))
        return {"status": 500, "message": "Internal Server Error", "data": str(e)}


@router.put('/editProduct')
def edit_product(product_data: schemas.ProductUpdate, product_id: int = Query(...), db: Session = Depends(get_db)):
    try:
        existing_product = db.query(models.Products).filter(
            models.Products.product_id == product_id).first()
        if not existing_product:
            return {"status": 204, "message": "Product not found", "data": {}}
        for field, value in product_data.model_dump().items():
            if value is not None:
                setattr(existing_product, field, value)
        db.query(models.ProductVariant).filter(
            models.ProductVariant.product_id == product_id
        ).update({"description": product_data.description})
        db.commit()
        return {"status": 200, "message": "Product edited successfully", "data": {}}
    except IntegrityError as e:
        if "duplicate key value violates unique constraint" in str(e):
            return {"status": 400, "message": "Check the product details", "data": {}}
        else:
            return {"status": 500, "message": "Internal Server Error", "error": str(e)}
