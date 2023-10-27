from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app import models, schemas
from app.database import engine, get_db
from app.models import Category, Products, ProductVariant, Brand, Order, Payment
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
def get_product_by_categories(branch_id=int, db: Session = Depends(get_db), response_model=schemas.GetBilling):
    try:
        branches = db.query(models.Branch).filter(models.Branch.branch_id == branch_id).all()
        if not branches:
            return {"status": 404, "message": "No branches found", "data": []}
        response_data = products_by_categories(branch_id, db)
        return {"status": 200, "message": "Variants fetched successfully for all categories!", "data": response_data}
    except Exception as e:
        print(repr(e))
        return {"status": 500, "message": "Internal Server Error", "data": []}


@router.get("/product/variants")
def get_product_variants(product_id: int, db: Session = Depends(get_db)):
    try:
        product = db.query(models.Products).filter(models.Products.product_id == product_id).first()
        if not product:
            return {"status": 204, "message": "Product not found", "data": {}}
        variants = db.query(models.ProductVariant).filter(models.ProductVariant.product_id == product_id).all()
        if not variants:
            return {"status": 204, "message": "No variants found for the specified product", "data": {}}
        serialized_variants = []
        for variant in variants:
            serialized_variants.append({
                "variant_id": variant.variant_id,
                "variant_cost": variant.variant_cost,
                "unit": variant.measuring_unit,
                "image": variant.image,
                "quantity": variant.quantity})
        response_data = {
            "product_id": product.product_id, "product_name": product.product_name,  "variants": serialized_variants}
        return {"status": 200, "message": "Product variants fetched successfully!", "data": response_data}
    except Exception as e:
        return {"status": 500, "message": "Internal Server Error", "data": str(e)}

@router.post("/orders/")
async def create_order(order: schemas.OrderCreate, db: Session = Depends(get_db)):
    try:
        product_details = []

        for product_data in order.product_list:
            product_id = product_data.get("product_id")
            variant_id = product_data.get("variant_id")
            item_count = product_data.get("item_count")

            product_variant = db.query(ProductVariant).filter(
                ProductVariant.product_id == product_id,
                ProductVariant.variant_id == variant_id
            ).first()

            if product_variant:
                if product_variant.stock is not None and product_variant.stock >= item_count:
                    product_variant.stock -= item_count
                else:
                    return {"status": 400, "message": f"Product with ID {product_id} is out of stock", "data": {}}
            else:
                return {"status": 400, "message": f"Product ID {product_id} with variant ID {variant_id} is not found",
                        "data": {}}

            variant_cost = product_variant.variant_cost if hasattr(product_variant, 'variant_cost') else 0.0

            product_variant_data = {
                "product_id": product_id,
                "variant_id": variant_id,
                "item_count": item_count,
                "variant_cost": variant_cost,
            }

            product_details_db = db.query(Products.product_name, ProductVariant.measuring_unit,
                                          ProductVariant.discount, ProductVariant.discounted_cost,
                                          ProductVariant.image). \
                join(ProductVariant, Products.product_id == ProductVariant.product_id). \
                filter(Products.product_id == product_id, ProductVariant.variant_id == variant_id).first()

            if product_details_db:
                product_variant_data.update({
                    "product_name": product_details_db.product_name,
                    "measuring_unit": product_details_db.measuring_unit,
                    "discounted_cost": product_details_db.discounted_cost,
                })

            product_details.append(product_variant_data)

        total_order = sum(product["variant_cost"] * product["item_count"] for product in product_details)

        db_order = Order(
            order_no=order.order_no,
            customer_contact=order.customer_contact,
            product_list=product_details,
            total_order=total_order,
            gst_charges=order.gst_charges,
            additional_charges=order.additional_charges,
            to_pay=order.to_pay,
        )

        db.add(db_order)
        db.commit()
        db.refresh(db_order)

        payment_type = order.payment_type
        if payment_type:
            payment_info = Payment(order_id=db_order.order_id, payment_type=payment_type)
            db.add(payment_info)
            db.commit()

        response_data = {
            "order_no": order.order_no,
            "product_list": product_details,
            "total_order": total_order,
            "gst_charges": order.gst_charges,
            "additional_charges": order.additional_charges,
            "to_pay": order.to_pay,
            "payment_type": payment_type,
        }

        return {"status": 200, "message": "Order created successfully", "data": response_data}
    except HTTPException as e:
        db.rollback()
        raise e
    except IntegrityError as e:
        return {"status": 400, "message": "Error creating order", "data": {}}
    except NoResultFound as e:
        return {"status": 400, "message": "Product or variant not found", "data": {}}
    except Exception as e:
        return {"status": 500, "message": "Internal Server Error", "error": str(e)}
    finally:
        db.close()