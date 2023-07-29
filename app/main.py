from fastapi import FastAPI, Response, Depends, UploadFile, File, Request, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from starlette.responses import FileResponse

from . import models, schemas
from .models import Image
from .database import engine, get_db
import os

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

UPLOAD_DIR = "app/images"


def save_image_to_db(db, name, filename):
    image = Image(name=name, filename=filename)
    db.add(image)
    db.commit()
    db.refresh(image)
    return image


@app.post("/upload")
async def upload_image(name: str, request: Request, file: UploadFile = File(...), db: Session = Depends(get_db)):
    image_data = file.file.read()
    image_path = os.path.join(UPLOAD_DIR, file.filename)

    with open(image_path, "wb") as f:
        f.write(image_data)

    try:
        image_obj = save_image_to_db(db, name, file.filename)
        base_url = request.base_url
        image_url = f"{base_url}images/{file.filename}"
        return {"message": "Image uploaded successfully", "image_id": image_obj.id, "image_url": image_url}
    finally:
        db.close()


@app.get("/images/{filename}")
async def get_image(filename: str):
    image_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(image_path)


@app.get('/')
def root():
    return {'message': 'Hello world'}


@app.post('/userAuthenticate')
def create_user(loginSignupAuth: schemas.UserData, response: Response, db: Session = Depends(get_db),
                companyId=str | None):
    try:
        print(loginSignupAuth.customer_name)
        user_data = db.query(models.User).get(
            loginSignupAuth.customer_contact)

        if not user_data:
            try:
                new_user_data = models.User(
                    **loginSignupAuth.model_dump())
                new_user_data.companies.append(companyId)
                db.add(new_user_data)
                db.commit()
                db.refresh(new_user_data)
                return {"status": 200, "message": "New user successfully created!", "data": new_user_data}
            except IntegrityError:
                response.status_code = 200
                return {"status": 204, "message": "User is not registered please Sing up", "data": {}}

        try:
            k = user_data.companies.index(companyId)
            return {"status": 200, "message": "New user successfully Logged in!", "data": user_data}
        except ValueError:
            return {"status": 204, "message": "User is not registered for this company please Sing up", "data": {}}

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


@app.get('/getUser')
def get_user_details(response: Response, db: Session = Depends(get_db), userId=int, companyId=str):
    try:
        get_user = db.query(models.User).filter(
            models.User.customer_contact == userId).filter(
            models.User.companies.contains(companyId)).all()

        if not get_user:
            response.status_code = 200
            return {"status": 204, "message": "No user found", "data": []}

        return {"status": 200, "message": "success", "data": get_user}
    except IntegrityError:
        response.status_code = 404
        return {"status": 404, "message": "Error", "data": {}}


@app.post('/addAddress')
def add_address(createAddress: schemas.AddAddress, response: Response, db: Session = Depends(get_db)):
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
            models.Addresses.company == companyId).filter(
            models.Addresses.user_contact == userId).all()

        if not user_addresses:
            response.status_code = 200
            return {"status": "200", "message": "No address found", "data": []}

        return {"status": "200", "message": "success", "data": user_addresses}
    except IntegrityError:
        response.status_code = 404
        return {"status": "404", "message": "Error", "data": {}}


@app.put('/editAddress')
def edit_address(editAddress: schemas.Address, response: Response, db: Session = Depends(get_db),
                 addressId=int):
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


@app.post('/addCart')
def add_cart(createCart: schemas.Cart, response: Response, db: Session = Depends(get_db)):
    try:
        add_to_cart = db.query(models.UserCart).filter(models.UserCart.user_contact == createCart.user_contact).filter(
            models.UserCart.company_id == createCart.company_id).first()

        if not add_to_cart:
            try:
                new_cart = models.UserCart(**createCart.model_dump())
                db.add(new_cart)
                db.commit()
                db.refresh(new_cart)
                return {"status": 200, "message": "new cart successfully created!", "data": new_cart}
            except IntegrityError:
                response.status_code = 200
                return {"status": 204, "message": "Error", "data": {}}

        return {"status": 200, "message": "Fetched Cart", "data": add_to_cart}
    except IntegrityError:
        response.status_code = 200
        return {"status": 204, "message": "Error", "data": {}}


@app.get('/getCart')
def get_cart(response: Response, db: Session = Depends(get_db), userId=int, companyId=str):
    try:
        fetch_cart = db.query(models.UserCart).filter(models.UserCart.user_contact == userId).filter(
            models.UserCart.company_id == companyId).first()

        if not fetch_cart:
            return {"status": 204, "message": "Error", "data": {}}

        return {"status": 200, "message": "Fetched Cart", "data": fetch_cart}
    except IntegrityError:
        response.status_code = 200
        return {"status": 204, "message": "Error", "data": {}}


@app.put('/editCart')
def edit_user_cart(editCart: schemas.UpdateCart, response: Response, db: Session = Depends(get_db), cartId=int):
    try:
        edit_cart = db.query(models.UserCart).filter(
            models.UserCart.cart_id == cartId)
        cart_exist = edit_cart.first()
        if not cart_exist:
            response.status_code = 200
            return {"status": 204, "message": "Address doesn't exists", "data": {}}

        edit_cart.update(editCart.model_dump(
            exclude_unset=True), synchronize_session=False)
        db.commit()
        return {"status": "200", "message": "Cart edited!", "data": edit_cart.first()}

    except IntegrityError:
        response.status_code = 404
        return {"status": "404", "message": "Error", "data": {}}


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
