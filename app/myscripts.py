# from app import models, database
# from .database import SessionLocal
# from .models import Categories
#
# def create_categories():
#     # Create 20 different categories and add them to the database
#     categories_to_create = [
#         {"category_name": "Electronics", "category_image": "electronics.jpg"},
#         {"category_name": "Clothing", "category_image": "clothing.jpg"},
#         # Add more categories here...
#     ]
#
#     session = SessionLocal()
#     for category_data in categories_to_create:
#         category = models.Categories(**category_data)
#         session.add(category)
#         session.commit()
#         session.refresh(category)
#
#     session.close()
#
#
# if __name__ == "__main__":
#     create_categories()


