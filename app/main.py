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
def create_user(loginSignupAuth: schemas.UserData, response: Response, db: Session = Depends(get_db)):
    try:
        user_data = db.query(models.User).get(
            loginSignupAuth.customer_contact)

        if not user_data:
            try:
                new_user_data = models.User(
                    **loginSignupAuth.model_dump())
                db.add(new_user_data)
                db.commit()
                db.refresh(new_user_data)
                return {"status": 200, "message": "New user successfully created!", "data": new_user_data}
            except IntegrityError as err:
                response.status_code = 200
                return {"status": 204, "message": "User is not registered please Sing up", "data": {}}

        return {"status": 200, "message": "New user successfully Logged in!", "data": user_data}
    except IntegrityError as err:
        response.status_code = 404
        return {"status": 404, "message": "Error", "data": {}}


@app.put('/editUser')
def edit_user(userDetail: schemas.UserData, response: Response, db: Session = Depends(get_db),
              userId=str | None):
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
    except IntegrityError as err:
        response.status_code = 404
        return {"status": 404, "message": "Error", "data": {}}


@app.get('/getUser')
def get_user_details(response: Response, db: Session = Depends(get_db), userId=int | None):
    try:

        get_user = db.query(models.User).filter(
            models.User.customer_contact == userId).all()

        if not get_user:
            response.status_code = 200
            return {"status": 204, "message": "No user found", "data": []}

        return {"status": 200, "message": "success", "data": get_user}
    except IntegrityError as err:
        response.status_code = 404
        return {"status": 404, "message": "Error", "data": {}}
