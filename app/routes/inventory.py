from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app import schemas, models
from app.database import get_db

router = APIRouter()


@router.post("/add/stock")
def add_new_stock(add_stock: schemas.Stock, product_id: int, variant_id: int, barcode_no: int,
                  db: Session = Depends(get_db)):
    try:
        product = db.query(models.Products).filter(models.Products.product_id == product_id).first()
        product_variant = db.query(models.ProductVariant).filter(
            models.ProductVariant.variant_id == variant_id,
            models.ProductVariant.barcode_no == barcode_no).first()
        if product and product_variant:
            new_stock = models.Stock(**add_stock.model_dump(),
                                     product_id=product_id, variant_id=variant_id, barcode_no=barcode_no)
            db.add(new_stock)
            product_variant.stock += new_stock.stock_order_count
            db.commit()
            db.refresh(new_stock)
            return {"status": 200, "message": "Stock added successfully!", "data": new_stock}
        else:
            return {"status": 404, "message": "Product, product variant, or stock not found!", "data": {}}
    except Exception as e:
        print(repr(e))
        return {"status": 500, "message": "Internal Server Error!", "data": {}}


@router.put("/update/stock")
async def update_stock(product_id: int, variant_id: int, barcode_no: int, edit_stock: schemas.UpdateStock,
                       db: Session = Depends(get_db)):
    try:
        product_variant = db.query(models.ProductVariant).filter(
            models.ProductVariant.variant_id == variant_id,
            models.ProductVariant.product_id == product_id,
            models.ProductVariant.barcode_no == barcode_no
        ).first()
        if product_variant:
            stock = db.query(models.Stock).filter(
                models.Stock.product_id == product_id,
                models.Stock.variant_id == variant_id,
                models.Stock.barcode_no == barcode_no
            ).first()
            if stock:
                stock.stock_order_count = edit_stock.stock_order_count
                db.commit()
                return {"status": 200, "message": "Stock updated successfully!",
                        "data": {"stock_id": stock.stock_id, "updated_stock": stock.stock_order_count}}
            else:
                return {"status": 404, "message": "Stock not found for the given product variant!", "data": {}}
        else:
            return {"status": 404, "message": "Product variant not found!", "data": {}}
    except Exception as e:
        print(repr(e))
        return {"status": 500, "message": "Internal Server Error!", "data": {}}


@router.delete("/delete/stock")
async def delete_stock(stock_id: int, db: Session = Depends(get_db)):
    try:
        stock = db.query(models.Stock).filter(models.Stock.stock_id == stock_id).first()
        if stock:
            db.delete(stock)
            db.commit()
            return {"status": 200, "message": "Stock deleted successfully!", "data": {}}
        else:
            return {"status": 404, "message": "Stock not found!", "data": {}}
    except Exception as e:
        print(repr(e))
        return {"status": 500, "message": "Internal Server Error!", "data": {}}


@router.get("/get/stock")
def get_all_stock(db: Session = Depends(get_db)):
    stock_items = db.query(models.Stock).all()
    stock_list = []
    for stock in stock_items:
        stock_dict = {
            "stock_id": stock.stock_id,
            "stock_order_count": stock.stock_order_count,
            "seller": stock.seller,
            "barcode_no": stock.barcode_no,
            "product_id": stock.product_id,
            "variant_id": stock.variant_id,
            "date_of_shipment": stock.date_of_shipment,
            "expiry_date": stock.expiry_date
        }
        stock_list.append(stock_dict)
    return {"status": 200, "message": "Stock items retrieved successfully", "data": stock_list}
