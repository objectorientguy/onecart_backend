from fastapi import FastAPI, Response, Depends
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from . import models, schemas
from .database import engine, get_db

models.Base.metadata.create_all(bind=engine)

app = FastAPI()


@app.get('/')
def root():
    return {'message': 'Hello world'}


@app.post('/userAuthenticate')
def create_user(loginSignupAuth: schemas.UserData, response: Response,
                db: Session = Depends(get_db), companyId=str):
    try:
        user_data = db.query(models.User).get(
            loginSignupAuth.customer_contact)

        if not user_data:
            try:
                new_user_data = models.User(
                    **loginSignupAuth.model_dump())
                print(loginSignupAuth)
                new_user_added = models.UserCompany(
                    company_id=companyId,
                    user_contact=loginSignupAuth.customer_contact)
                db.add(new_user_data)
                db.add(new_user_added)
                db.commit()
                db.refresh(new_user_data)
                return {"status": 200, "message": "New user successfully created!", "data": new_user_data}
            except IntegrityError:
                response.status_code = 200
                return {"status": 204, "message": "User is not registered please Sing up", "data": {}}

        user_exists = db.query(models.UserCompany).filter(models.UserCompany.company_id == companyId).filter(
            models.UserCompany.user_contact == loginSignupAuth.customer_contact).first()
        print(user_exists)
        if not user_exists:
            try:
                new_user_company = models.UserCompany(
                    company_id=companyId,
                    user_contact=loginSignupAuth.customer_contact)
                db.add(new_user_company)
                db.commit()
                db.refresh(new_user_company)
                return {"status": 200, "message": "New user successfully Logged in!", "data": user_data}
            except IntegrityError:
                response.status_code = 200
                return {"status": "204", "message": "User is not registered for this company please Sing up", "data": {}}

        return {"status": 200, "message": "New user successfully Logged in for this company!", "data": user_data}

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
            models.Addresses.company_id == companyId).filter(
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


@app.post('/addCompany')
def add_companies(addCompany: schemas.Bookings, response: Response, db: Session = Depends(get_db)):
    try:
        new_company = models.Bookings(**addCompany.model_dump())
        db.add(new_company)
        db.commit()
        db.refresh(new_company)

        return {"status": "200", "message": "New company added successfully!", "data": new_company}
    except IntegrityError:
        response.status_code = 200
        return {"status": "404", "message": "Error", "data": {}}


@app.post('/addCategory')
def add_categories(addCategory: schemas.Category, response: Response, db: Session = Depends(get_db)):
    try:
        new_category = models.Bookings(**addCategory.model_dump())
        db.add(new_category)
        db.commit()
        db.refresh(new_category)

        return {"status": "200", "message": "New category added successfully!", "data": new_category}
    except IntegrityError:
        response.status_code = 200
        return {"status": "404", "message": "Error", "data": {}}


@app.post('/addProducts')
def add_products(addProduct: schemas.Product, response: Response, db: Session = Depends(get_db)):
    try:
        new_product = models.Bookings(**addProduct.model_dump())
        db.add(new_product)
        db.commit()
        db.refresh(new_product)

        return {"status": "200", "message": "New product added successfully!", "data": new_product}
    except IntegrityError:
        response.status_code = 200
        return {"status": "404", "message": "Error", "data": {}}
