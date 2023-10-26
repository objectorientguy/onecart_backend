from fastapi import APIRouter, Depends
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from app import schemas, models
from app.database import get_db

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@router.get("/company/description")
def fetch_description(company_id: str, db: Session = Depends(get_db)):
    try:
        company = db.query(models.Companies).filter(models.Companies.company_id == company_id).first()
        if company:
            company_description = company.company_description if company.company_description is not None else ""
            return {"status": 200, "message": "Company description fetched successfully!", "data": company_description}
        else:
            return {"status": 404, "message": "Company not found!", "data": {}}
    except Exception as e:
        print(repr(e))
        return {"status": 500, "message": "Internal Server Error!", "data": {}}


@router.post("/user/details")
def fetch_user_details(userid: int, edit_user: schemas.EditUser, db: Session = Depends(get_db)):
    try:
        user = db.query(models.NewUsers).filter(models.NewUsers.user_uniqueid == userid).first()
        if user:
            if edit_user.user_image is not None:
                user.user_image = edit_user.user_image
            if edit_user.user_name is not None:
                user.user_name = edit_user.user_name
            if edit_user.user_contact is not None:
                user.user_contact = edit_user.user_contact
            if edit_user.user_emailId is not None:
                user.user_emailId = edit_user.user_emailId
            db.commit()
            return {"status": 200, "message": "User details updated successfully", "data": edit_user}
        else:
            return {"status": 404, "message": "User not found", "data": {}}
    except Exception as e:
        print(repr(e))
        return {"status": 500, "message": "Internal Server Error!", "data": {}}


def get_password_hash(password: str):
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


@router.put("/change-password")
async def change_password(userid: int, password_data: schemas.ChangePassword, db: Session = Depends(get_db)):
    try:
        user = db.query(models.NewUsers).filter(models.NewUsers.user_uniqueid == userid).first()
        if not user:
            return {"status": 404, "message": "User not found", "data": {}}
        if not verify_password(password_data.current_password, user.user_password):
            return{"status_code": 400, "message": "Current password is incorrect"}
        if password_data.new_password != password_data.confirm_password:
            return{"status_code": 400, "message": "New password and confirm password do not match"}
        user.user_password = get_password_hash(password_data.new_password)
        db.commit()
        return {"message": "Password changed successfully"}
    except Exception as e:
        print(repr(e))
        return {"status": 500, "message": "Internal Server Error!", "data": {}}