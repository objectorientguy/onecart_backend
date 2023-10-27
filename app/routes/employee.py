from fastapi import APIRouter, Depends, Body
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from app import schemas, models
from app.database import get_db
router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@router.post("/branch/employee")
def add_employee(branch_id: int, employee_data: schemas.AddEmployee, db: Session = Depends(get_db)):
    try:
        branch = db.query(models.Branch).filter(models.Branch.branch_id == branch_id).first()
        if branch is None:
            return {"status_code": 404, "message": "Branch not found", "data": {}}

        hashed_password = pwd_context.hash(employee_data.employee_password)
        employee_data.employee_password = hashed_password

        new_employee = models.Employee(branch_id=branch_id, **employee_data.model_dump(exclude={'role_name'}))
        db.add(new_employee)
        db.flush()

        new_role = models.Role(role_name=employee_data.role_name)
        new_role.employee = new_employee
        db.add(new_role)

        new_user = models.NewUsers(
            user_contact=employee_data.employee_contact,
            user_password=employee_data.employee_password,
            user_name=employee_data.employee_name
        )
        db.add(new_user)
        db.commit()
        response_data = {"status": 200, "message": "New Employee added successfully", "data": {}}
        return response_data
    except Exception as e:
        print(repr(e))
        return {"status_code": 500, "message": "Internal Server Error", "data": {}}


def get_employee_info(employee_id: int, db: Session):
    result = db.query(models.Employee.employee_name, models.Role.role_name, models.Role.role_id) \
        .join(models.Role, models.Employee.employee_id == models.Role.employee_id) \
        .filter(models.Employee.employee_id == employee_id).first()
    return(result)


@router.get("/branch/employee/details")
def get_employee_details(branch_id: int, db: Session = Depends(get_db)):
    try:
        employees = db.query(models.Employee).filter_by(branch_id=branch_id).all()
        response_data = {
            "employee_count": len(employees),
            "employees": []
        }
        for employee in employees:
            employee_info = get_employee_info(employee.employee_id, db)
            if employee_info:
                employee_name, role_name, role_id = employee_info
                response_data["employees"].append({
                    "employee_id": employee.employee_id,
                    "employee_name": employee_name,
                    "employee_gender": employee.employee_gender,
                    "employee_contact": employee.employee_contact,
                    "role_name": role_name,
                    "role_key": role_id
                })

        return {"status": 200, "message": "Employee details retrieved successfully", "data": response_data}

    except Exception as e:
        print(repr(e))
        return {"status": 500, "message": "Internal Server Error", "data": {}}


@router.delete("/employee/delete")
def delete_employee(empID: int, branchID: int, db: Session = Depends(get_db)):
    try:
        employee = db.query(models.Employee).filter(models.Employee.employee_id == empID)
        employee_exist = employee.first()
        if not employee_exist:
            return {"status": 404, "message": "Employee doesn't exists", "data": {}}

        branch = db.query(models.Branch).filter(models.Branch.branch_id == branchID)
        branch_exist = branch.first()
        if not branch_exist:
            return {"status": 404, "message": "Branch doesn't exists", "data": {}}

        employee.delete(synchronize_session=False)
        db.commit()
        return {"status": 200, "message": "Employee deleted!", "data": {}}
    except Exception as e:
        print(repr(e))
        return {"status": 500, "message": "Error", "data": {}}


@router.put("/branch/employee")
def edit_employee(branch_id: int, employee_id: int, request_body: schemas.EditEmployee = Body(...),
                  db: Session = Depends(get_db)):
    try:

        employee = db.query(models.Employee).filter(models.Employee.employee_id == employee_id).first()
        if employee is None:
            return {"status": 404, "message": "Employee not found", "data": {}}
        branch = db.query(models.Branch).filter(models.Branch.branch_id == branch_id).first()
        if branch is None:
            return {"status": 404, "message": "Branch not found", "data": {}}
        role = db.query(models.Role).filter(models.Role.employee_id == employee_id).first()

        if request_body.role_name is not None and role:
            role.role_name = request_body.role_name
        if request_body.employee_name is not None:
            employee.employee_name = request_body.employee_name
        if request_body.employee_contact is not None:
            employee.employee_contact = request_body.employee_contact
        if request_body.employee_gender is not None:
            employee.employee_gender = request_body.employee_gender

        db.commit()
        return {"status": 200, "message": "Employee edited successfully", "data": request_body}
    except Exception as e:
        print(repr(e))
        return {"status": 500, "message": "Internal Server Error", "data": {}}
    finally:
        db.close()

