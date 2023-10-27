from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app import models
from app.database import engine, get_db
from app.models import Category, Products, ProductVariant, Brand
models.Base.metadata.create_all(bind=engine)

router = APIRouter()


def products_by_categories(branch_id, db):
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
            variants = db.query(ProductVariant).filter(ProductVariant.product_id == product.product_id).filter(
                ProductVariant.branch_id == branch_id).all()
            if variants:
                product_data = {
                    "product_id": product.product_id,
                    "product_name": product.product_name,
                    "brand_name": brand.brand_name,
                    "variants": []
                }
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
    return response_data


@router.get("/product/categories")
def get_product_by_categories(branch_id=int, db: Session = Depends(get_db)):
    try:
        branches = db.query(models.Branch).filter(models.Branch.branch_id == branch_id).all()
        if not branches:
            return {"status": 404, "message": "No branches found", "data": []}
        response_data = products_by_categories(branch_id, db)
        return {
            "status": 200,
            "message": "Variants fetched successfully for all categories!",
            "data": response_data}
    except Exception as e:
        print(repr(e))
        return {"status": 500, "message": "Internal Server Error", "data": []}


@router.get("/productVariants")
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
