from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app import schemas, models
from app.database import get_db
router = APIRouter()


@router.get("/barcode/product-name")
def fetch_product_details(barcode_no: int, db: Session = Depends(get_db)):
    try:
        if not barcode_no:
            return {"status": 400, "message": "Invalid barcode!", "data": {}}
        product_variant = db.query(models.ProductVariant).filter(models.ProductVariant.barcode_no == barcode_no).first()
        if not product_variant:
            return {"status": 404, "message": "Variant not found!", "data": {}}
        product_id = product_variant.product_id
        variant_id = product_variant.variant_id
        product = db.query(models.Products).filter(models.Products.product_id == product_id).first()
        if not product:
            return {"status": 404, "message": "Product not found!", "data": {}}
        product_name = product.product_name
        return {"status": 200, "message": "Product details fetched successfully!",
                "data": {"product_name": product_name, "product_id": product_id,
                         "variant_id": variant_id, "barcode": barcode_no}}
    except Exception as e:
        print(repr(e))
        return {"status": 500, "message": "Internal Server Error!", "data": {}}


@router.get("/get/stock-history")
def fetch_stock_history(stock_id: int, db: Session = Depends(get_db)):
    try:
        stock = db.query(models.Stock).filter(models.Stock.stock_id == stock_id).first()
        if not stock:
            return {"status": 404, "message": "Stock Id does not exists!", "data": []}
        stock_history_entries = db.query(models.History).filter(models.History.stock_id == stock_id).all()
        history = []
        for entry in stock_history_entries:
            history_info = {
                "history_id": entry.history_id,
                "supplier": entry.supplier,
                "unit_price": entry.unit_price,
                "shipment_date": entry.shipment_date,
                "expiry_of_product": entry.expiry_of_product,
                "incoming_stock_count": entry.incoming_stock_count
            }
            history.append(history_info)
        return {"status": 200, "message": "History fetched!", "data": history}
    except Exception as e:
        print(repr(e))
        return {"status": 500, "message": "Internal Server Error!", "data": []}


@router.post("/add/stock-history")
def add_new_stock_history(add_stock: schemas.AddStock, stock_id: int, db: Session = Depends(get_db)):
    try:
        stock = db.query(models.Stock).filter(models.Stock.stock_id == stock_id).first()
        if not stock:
            return {"status": 404, "message": "Stock Id does not exists!", "data": {}}
        if stock:
            new_stock_history = models.History(**add_stock.model_dump(), stock_id=stock_id)
            db.add(new_stock_history)
            db.commit()
            db.refresh(new_stock_history)
            return {"status": 200, "message": "Stock History added successfully!", "data": new_stock_history}
    except Exception as e:
        print(repr(e))
        return {"status": 500, "message": "Internal Server Error!", "data": {}}


@router.put("/update/stock-history")
async def update_stock(history_id: int, edit_stock: schemas.UpdateStock, db: Session = Depends(get_db)):
    try:
        history = db.query(models.History).filter(models.History.history_id == history_id)
        history_exists = history.first()
        if not history_exists:
            return {"status": 404, "message": "History Id does not exists!", "data": {}}
        history.update(edit_stock.model_dump(), synchronize_session=False)
        db.commit()
        db.refresh(history_exists)
        return {"status": 200, "message": "History updated successfully!", "data": edit_stock}
    except Exception as e:
        print(repr(e))
        return {"status": 500, "message": "Internal Server Error!", "data": {}}


@router.delete("/delete/stock-history")
async def delete_stock(history_id: int, db: Session = Depends(get_db)):
    try:
        stock_history = db.query(models.History).filter(models.History.history_id == history_id).first()
        if stock_history:
            db.delete(stock_history)
            db.commit()
            return {"status": 200, "message": "Stock History deleted successfully!", "data": {}}
        else:
            return {"status": 404, "message": "Stock History not found!", "data": {}}
    except Exception as e:
        print(repr(e))
        return {"status": 500, "message": "Internal Server Error!", "data": {}}
