from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app import schemas, models
from app.database import get_db
router = APIRouter()


@router.get("/stock/barcode")
def fetch_product_details(barcode_no: int, db: Session = Depends(get_db)):
    try:
        stock = db.query(models.Stock).filter(models.Stock.barcode_no == barcode_no).first()
        if not stock:
            return {"status": 404, "message": "Variant not found!", "data": {}}

        variant = db.query(models.ProductVariant).filter(models.ProductVariant.variant_id == stock.variant_id).first()
        product = db.query(models.Products).filter(models.Products.product_id == stock.product_id).first()
        stock_data = {
            "stock_id": stock.stock_id,
            "product_id": stock.product_id,
            "product_name": product.product_name,
            "product_image": variant.image,
            "stock": variant.stock,
            "qt_unit": str(variant.quantity) + " " + variant.measuring_unit,
            "selling_price": variant.discounted_cost,
            "variant_id": stock.variant_id,
            "current_stock_count": stock.current_stock_count,
            "barcode_no": stock.barcode_no,
            "reorder_stock_at": stock.reorder_stock_at if stock.reorder_stock_at else 0,
            "perishable": stock.perishable if stock.perishable else ""
        }
        return {"status": 200, "message": "Product details fetched successfully!",
                "data": stock_data}
    except Exception as e:
        print(repr(e))
        return {"status": 500, "message": "Internal Server Error!", "data": {}}


@router.get("/stock")
def fetch_stock(db: Session = Depends(get_db)):
    try:
        stock = db.query(models.Stock).all()
        if not stock:
            return {"status": 404, "message": "No stock data found"}
        stock_data = []
        for item in stock:
            variant = db.query(models.ProductVariant).filter(models.ProductVariant.variant_id == item.variant_id).first()
            product = db.query(models.Products).filter(models.Products.product_id == item.product_id).first()
            if product is not None:  # Check if product is not None
                product_name = product.product_name
            if variant is not None:  # Check if variant is not None
                product_image = variant.image
                selling_price = variant.discounted_cost
                qt_unit = str(variant.quantity) + " " + variant.measuring_unit
                stock_quantity = variant.stock if variant.stock is not None else 0
            stock_data.append({
                "stock_id": item.stock_id,
                "product_id": item.product_id,
                "product_name": product_name,
                "product_image": product_image,
                "stock": stock_quantity,
                "qt_unit": qt_unit,
                "selling_price": selling_price,
                "variant_id": item.variant_id,
                "current_stock_count": item.current_stock_count,
                "barcode_no": item.barcode_no,
                "reorder_stock_at": item.reorder_stock_at if item.reorder_stock_at else 0,
                "perishable": item.perishable if item.perishable else ""
            })
        return {"status": 200, "message": "Stock data retrieved successfully", "data": stock_data}
    except Exception as e:
        print(repr(e))
        return {"status": 500, "message": "Internal Server Error", "data": {}}


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
