from contextlib import contextmanager

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app import models
from app.database import engine, get_db, SessionLocal
from app.main import app


@contextmanager
def session_scope():
    session = Session(bind=engine)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()



@app.post("/addShop/")
def create_shop(response: Response, db: Session = Depends(get_db)):
    try:
        shops_data = [
            {
                "shop_name": "Sai Chanduram Bakery",
                "shop_description": "Description 1",
                "shop_image": "image1.jpg",
                "shop_contact": 1234567890,
                "shop_address": "123 Main St",
                "shop_coordinates": "lat: 123, long: 456",
                "shop_mok": "1234-5678-9012",
                "shop_service": "Bakery",
                "is_available": True,
                "company_name": "OneCart",
            },
            {
                "shop_name": "Nagpur Stores",
                "shop_description": "Description 2",
                "shop_image": "image2.jpg",
                "shop_contact": 9876543210,
                "shop_address": "456 Elm St",
                "shop_coordinates": "lat: 789, long: 101",
                "shop_mok": "5678-9012-3456",
                "shop_service": "Grocery",
                "is_available": False,
                "company_name": "OneCart",
            },
            {
                "shop_name": "Kirana King",
                "shop_description": "Description 3",
                "shop_image": "image3.jpg",
                "shop_contact": 5555555555,
                "shop_address": "789 Oak St",
                "shop_coordinates": "lat: 246, long: 789",
                "shop_mok": "9876-5432-1098",
                "shop_service": "Grocery",
                "is_available": True,
                "company_name": "OneCart",
            },
            {
                "shop_name": "Ajit Bakery",
                "shop_description": "Description 4",
                "shop_image": "image4.jpg",
                "shop_contact": 3333333333,
                "shop_address": "101 Pine St",
                "shop_coordinates": "lat: 987, long: 654",
                "shop_mok": "1234-5678-9012",
                "shop_service": "Bakery",
                "is_available": False,
                "company_name": "OneCart",
            },
        ]

        with session_scope() as session:
            for shop_data in shops_data:
                shop = models.Shops(**shop_data)
                session.add(shop)
                session.commit()
                session.refresh(shop)

        return {"message": "shops created successfully", "data": {}}

    except Exception as e:
        print(repr(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/create_categories/")
def create_categories(response: Response, db: Session = Depends(get_db)):
    try:
        # Create 20 different categories and add them to the database
        categories_to_create = [
            {"category_name": "Snacks", "category_image": "https://oneart.onrender.com/images/snack.JPG"},
            {"category_name": "Dairy & Bakery", "category_image": "https://oneart.onrender.com/images/bakery1.JPG"},
            {"category_name": "Staples", "category_image": "https://oneart.onrender.com/images/staples.JPG"},
            {"category_name": "Stationaries", "category_image": "https://oneart.onrender.com/images/stationaries.JPG"},
            {"category_name": "Beverages", "category_image": "https://oneart.onrender.com/images/beverages.JPG"},
            {"category_name": "Personal Care", "category_image": "https://oneart.onrender.com/images/products.JPG"},
            {"category_name": "Home Care", "category_image": "https://oneart.onrender.com/images/home.JPG"},
            {"category_name": "Mom & Baby Care", "category_image": "https://oneart.onrender.com/images/baby.JPG"},
            {"category_name": "Home & Kitchen", "category_image": "https://oneart.onrender.com/images/kitchen.JPG"}

        ]

        with session_scope() as session:
            for category_data in categories_to_create:
                category = models.Categories(**category_data)
                session.add(category)
                session.commit()
                session.refresh(category)

        return {"message": "Categories created successfully", "data": {}}

    except Exception as e:
        print(repr(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/addProducts/")
def add_products(response: Response, db: Session = Depends(get_db)):
    try:
        products_data = [
            {"brand_id": 2, "product_name": "Parachute Coconut Oil", "details": "Premium Coconut Oil"},
            {"brand_id": 13, "product_name": "Santoor Sandal & Turmeric Soap 150 g",
             "details": "Premium bathing soap with haldi"},
            {"brand_id": 1, "product_name": "Pepsi 7up", "details": "Refreshing and tasty"},
            {"brand_id": 1, "product_name": "Amul Lassi", "details": "Refreshing and tasty on a hot day"},
            {"brand_id": 3, "product_name": "Madhur Pure & Hygienic Sugar 5 kg",
             "details": "Packed with the utmost care, Pure and natural product"},
            {"brand_id": 3, "product_name": "Ashirwad Multigrain Atta 5 kg",
             "details": "Made with the choicest grains which provides wholesome nutrition"},
            {"brand_id": 5, "product_name": "MamyPoko Extra Absorb Pants (M) 72 count (7 - 12 kg)",
             "details": "Prevents leakage Keeps baby's skin dry"},
            {"brand_id": 8, "product_name": "Cerelac Baby Cereal with Milk Wheat Apple 6 months (Stage 1) 300 g",
             "details": "Rich in Iron ,Source of vitamins and minerals."},
            {"brand_id": 1, "product_name": "Amul Butter 500 g (Carton)",
             "details": "Smooth and creamy, Easy to spread,Enhances the flavor"},
            {"brand_id": 1, "product_name": "Amul Cow Ghee 1 L (Tin)",
             "details": "Can be consumed directly or can be swapped for oil/butter"},
            {"brand_id": 14, "product_name": "Camel Wax Crayons - 12 Shades (Pack of 10 Pkts)",
             "details": "Camel Wax Crayons - 12 Shades per Pkt (Pack of 10 Pkts)"},
            {"brand_id": 5, "product_name": "Camlin Tri-Mech 3-in-1 Pen Pencil Kit",
             "details": "1 pen pencil (0.7 mm with 5 leads) and 1 pen pencil (0.9mm with 5 leads)"},
            {"brand_id": 7, "product_name": "Parle-G Gold Biscuits 1 kg",
             "details": "Made from the finest quality ingredients"},
            {"brand_id": 8, "product_name": "Maggi 2-Minute Masala Noodles 70 g",
             "details": "Made from the finest quality ingredients"},
            {"brand_id": 9, "product_name": "Pigeon Mini Handy and Compact Chopper with 3 Blades (Green, 400 ml)",
             "details": "3 blade, stainless steel blade"},
            {"brand_id": 10, "product_name": "Vim Lemon Concentrated Dishwash Liquid 250 ml",
             "details": "Non messy and gentle on the skin, Leaves utensils sparkling clean"},
            {"brand_id": 11, "product_name": "HIT Cockroach Killer Spray 200 ml",
             "details": "Instant action, Unique formulation & nozzle design"},
            {"brand_id": 12, "product_name": "Odonil Zipper Rose Air Freshener 10 g",
             "details": "Nature-inspired scents, Lasts up to 30 days"},
        ]

        with session_scope() as session:
            for product_data in products_data:
                product = models.Products(**product_data)
                session.add(product)
                session.commit()
                session.refresh(product)

        return {"message": "Products added successfully", "data": {}}

    except Exception as e:
        print(repr(e))
        raise HTTPException(status_code=500, detail=str(e))


# ... (previous code remains the same)

@app.post("/addVariants/")
def add_products(response: Response, db: Session = Depends(get_db)):
    try:
        products_data = [
            {"variant_cost": 99, "brand_name": "Pepsi", "count": 100, "discounted_cost": 66, "discount": 33,
             "quantity": "2.2 l",
             "description": "Delight your guests with 7Up, it is the perfect drink for any weather.",
             "image": ["https://oneart.onrender.com/images/7up-2-25-l.jpeg","https://oneart.onrender.com/images/7up-2-25-l-back.jpeg","https://oneart.onrender.com/images/7up-2-25-l-legals.jpeg"], "ratings": 4, "product_id": 3},

            {"variant_cost": 40, "brand_name": "Pepsi", "count": 100, "discounted_cost": 30, "discount": 25,
             "quantity": "750 ml",
             "description": "Delight your guests with 7Up, it is the perfect drink for any weather.",
             "image": ["https://oneart.onrender.com/images/7up-750-ml.jpeg"], "ratings": 4, "product_id": 3},

            {"variant_cost": 40, "brand_name": "Pepsi", "count": 100, "discounted_cost": 34, "discount": 15,
             "quantity": "300 ml",
             "description": "Delight your guests with 7Up, it is the perfect drink for any weather.",
             "image": ["https://oneart.onrender.com/images/7up-250-ml-can.jpeg"], "ratings": 4, "product_id": 3},

            {
                "variant_cost": 824,
                "brand_name": "MamyPoko",
                "count": 1000,
                "discounted_cost": 824,
                "discount": 34,
                "quantity": "72 count (7 - 12 kg)",
                "description": "MamyPoko Extra Absorb Pants locks away the wetness and keeps your baby's bottom dry. These pants have faster absorption and prevent leakage keeping your baby's skin dry.",
                "image": ["https://oneart.onrender.com/images/mamypoko-extra-absorb-pants.jpg","https://oneart.onrender.com/images/mamypoko-extra-absorb-pants-b.jpg","https://oneart.onrender.com/images/mamypoko-extra-absorb-pants-d.jpg"],
                "ratings": 0,
                "product_id": 7
            },


        {
                "variant_cost": 90,
                "brand_name": "Amul",
                "count": 1000,
                "discounted_cost": 90,
                "discount": 10,
                "quantity": "250 ml",
                "description": "Amul Lassi is a refreshing milk-based natural drink. It refreshes you immediately with the goodness of nature.",
                "image": ["https://oneart.onrender.com/images/amul-lassi-250-ml-tetra-pak-prod.jpg","https://oneart.onrender.com/images/amul-lassi-250-ml-tetra-info.jpg","https://oneart.onrender.com/images/amul-lassi-250-ml-tetra-pak-lega.jpg"],
                "ratings": 0,
                "product_id": 4},

            {
                "variant_cost": 285,
                "brand_name": "Ashirwad",
                "count": 1000,
                "discounted_cost": 285,
                "discount": 19,
                "quantity": "5 kg",
                "description": "Looking to switch to a healthier flour option? Look no further. Aashirvaad Multigrain Atta provides you and your family with wholesome goodness and health benefits without compromising on taste.",
                "image": ["https://oneart.onrender.com/images/aashirvaad-multigrain-atta-5-kg.jpg","https://oneart.onrender.com/images/aashirvaad-multigrain-atta-5-kg-back.jpg"],
                "ratings": 0,
                "product_id": 6},

            {
                "variant_cost": 645,
                "brand_name": "Amul",
                "count": 1000,
                "discounted_cost": 645,
                "discount": 3,
                "quantity": "1 L",
                "description": "Ghee is a class of clarified butter that originated in ancient India. It is commonly used in Indian cooking.",
                "image": ["https://oneart.onrender.com/images/amul-cow-ghee-1-l-tin-product-f.jpg","https://oneart.onrender.com/images/amul-cow-ghee-1-l-tin-product-b.jpg","https://oneart.onrender.com/images/amul-cow-ghee-1-l-tin-product-s.jpg"],
                "ratings": 0,
                "product_id": 10
            },


            {
                "variant_cost": 260,
                "brand_name": "Cerelac",
                "count": 1000,
                "discounted_cost": 260,
                "discount": 0,
                "quantity": "300 g",
                "description": "Nestle presents Cerelac Baby Cereal with Milk Wheat Apple complementary food for babies from 6 months onwards. Infants have a higher requirement of nutrients, Cerelac Wheat Apple Cereal ensures your growing infant is getting the right nutritional requirements.",
                "image": ["https://oneart.onrender.com/images/cerelac-baby-cereal-with-milk-wh","https://oneart.onrender.com/images/cerelac-baby-cereal-with-milk-wh-b","https://oneart.onrender.com/images/cerelac-baby-cereal-with-milk-wh-s"],
                "ratings": 0,
                "product_id": 8
            },


            {
            "variant_cost": 90, "brand_name": "Amul", "count": 100, "discounted_cost": 84, "discount": 8,
             "quantity": "250 ml",
             "description": "Amul Lassi is a refreshing milk-based natural drink. It refreshes you immediately with the goodness of nature.",
             "image": ["https://oneart.onrender.com/images/amul-lassi-1-l-tetra-pak-product-side.jpeg"], "ratings": 4,
             "product_id": 4},

            {"variant_cost": 14.7, "brand_name": "Amul", "count": 100, "discounted_cost": 14.7, "discount": 0,
             "quantity": "180 ml",
             "description": "Amul Lassi is a refreshing milk-based natural drink. It refreshes you immediately with the goodness of nature.",
             "image": ["https://oneart.onrender.com/images/amul-rose-flavoured-probiotic-la.jpeg"], "ratings": 4,
             "product_id": 4},

            {"variant_cost": 80, "brand_name": "Amul", "count": 100, "discounted_cost": 74, "discount": 8,
             "quantity": "250 ml",
             "description": "Amul Lassi is a refreshing milk-based natural drink. It refreshes you immediately with the goodness of nature.",
             "image": ["https://oneart.onrender.com/images/4_packs-amul-lassi-rose-flavor.jpeg"], "ratings": 4,
             "product_id": 4},

            {
                "variant_cost": 645,
                "brand_name": "Amul",
                "count": 1000,
                "discounted_cost": 645,
                "discount": 3,
                "quantity": "1 L",
                "description": "Ghee is a class of clarified butter that originated in ancient India. It is commonly used in Indian cooking.",
                "image": ["https://oneart.onrender.com/images/amul-cow-ghee-1-l-tin-product-f.jpg"],
                "ratings": 0,
                "product_id": 10
            },


            {
            "variant_cost": 127, "brand_name": "Parachute", "count": 100, "discounted_cost": 99, "discount": 22,
             "quantity": "1 bottle",
             "description": "Tired of dull and frizzy hair? Hair oil plays a vital role in protecting your hair from regular wear and tear. Parachute 100% Pure Coconut Hair Oil gives your hair the much-needed nourishment and protects it from further damage.",
             "image": ["https://oneart.onrender.com/images/parachute-300ml.jpg"], "ratings": 4, "product_id": 1},

            {"variant_cost": 37, "brand_name": "Parachute", "count": 100, "discounted_cost": 34, "discount": 8,
             "quantity": "1 bottle",
             "description": "Tired of dull and frizzy hair? Hair oil plays a vital role in protecting your hair from regular wear and tear. Parachute 100% Pure Coconut Hair Oil gives your hair the much-needed nourishment and protects it from further damage.",
             "image": ["https://oneart.onrender.com/images/parachute-100-ml.jpg"], "ratings": 4, "product_id": 1},

            {
                "variant_cost": 99, "brand_name": "Parachute",
                "count": 800,
                "discounted_cost": 99,
                "discount": 22,
                "quantity": "200 ml",
                "description": "Tired of dull and frizzy hair? Hair oil plays a vital role in protecting your hair from regular wear and tear. Parachute 100% Pure Coconut Hair Oil gives your hair the much-needed nourishment and protects it from further damage.",
                "image": ["https://oneart.onrender.com/images/parachute-product.jpg","https://oneart.onrender.com/images/parachute-200-ml.jpg"],
                "ratings": 0, "product_id": 1
            },

            {
                "variant_cost": 199,
                "brand_name": "Pigeon",
                "count": 1000,
                "discounted_cost": 199,
                "discount": 63,
                "quantity": "400 ml",
                "description": "Pigeon Mini Handy and Compact Chopper with 3 Blades (Green, 400 ml)",
                "image": ["https://oneart.onrender.com/images/pigeon-mini-handy-and-compact-ch.jpg","https://oneart.onrender.com/images/pigeon-mini-handy-and-compact-f.jpg","https://oneart.onrender.com/images/pigeon-mini-handy-and-compact-d.jpg","https://oneart.onrender.com/images/pigeon-mini-handy-and-compact-dt.jpg","https://oneart.onrender.com/images/pigeon-mini-handy-and-compact-dtt.jpg"],
                "ratings": 0,
                "product_id": 15
            },


        {"variant_cost": 499, "brand_name": "Pigeon", "count": 100, "discounted_cost": 249, "discount": 50,
             "quantity": "900 ml",
             "description": "Pigeon Mini Handy and Compact Chopper with 3 Blades (Green, 400 ml)",
             "image": ["https://oneart.onrender.com/images/pigeon-mini-chopper-900-ml.jpg"], "ratings": 4,
             "product_id": 15},

            {"variant_cost": 499, "brand_name": "Pigeon", "count": 100, "discounted_cost": 249, "discount": 50,
             "quantity": "900 ml",
             "description": "Pigeon Mini Handy and Compact Chopper with 3 Blades (Green, 400 ml)",
             "image": ["https://oneart.onrender.com/images/pigeon-mini-chopper-900-ml.jpg"], "ratings": 4,
             "product_id": 15},

            {
                "variant_cost": 46,
                "brand_name": "Vim",
                "count": 1000,
                "discounted_cost": 46,
                "discount": 8,
                "quantity": "250 ml",
                "description": "Vim Lemon Concentrated Dishwash Liquid helps in removing the toughest of grease and stains from utensils easily and conveniently. It eradicates the tough grease and grime from the soiled utensils. It removes residual food odor effectively.",
                "image": ["https://oneart.onrender.com/images/vim-lemon-concentrated-dishwash-f.jpg","https://oneart.onrender.com/images/vim-lemon-concentrated-dishwash.jpg",  "https://oneart.onrender.com/images/vim-lemon-concentrated-dishwash-d.jpg", "https://oneart.onrender.com/images/vim-lemon-concentrated-dishwash-dt.jpg"],
                "ratings": 0,
                "product_id": 16
            },

        {"variant_cost": 20, "brand_name": "Vim", "count": 100, "discounted_cost": 18, "discount": 10,
             "quantity": "140 ml",
             "description": "Vim Lemon Concentrated Dishwash Liquid helps in removing the toughest of grease and stains from utensils easily and conveniently. It eradicates the tough grease and grime from the soiled utensils. It removes residual food odor effectively.",
             "image": ["https://oneart.onrender.com/images/vim-lemon-140ml.jpg"], "ratings": 4, "product_id": 16},

            {"variant_cost": 445, "brand_name": "Vim", "count": 100, "discounted_cost": 413, "discount": 7,
             "quantity": "1.8 liters",
             "description": "Vim Lemon Concentrated Dishwash Liquid helps in removing the toughest of grease and stains from utensils easily and conveniently. It eradicates the tough grease and grime from the soiled utensils. It removes residual food odor effectively.",
             "image": ["https://oneart.onrender.com/images/vim-lemon-1.8l.jpg"], "ratings": 4, "product_id": 16},

            {"variant_cost": 445, "brand_name": "Vim", "count": 100, "discounted_cost": 0, "discount": 0,
             "quantity": "2 liters",
             "description": "Vim Lemon Concentrated Dishwash Liquid helps in removing the toughest of grease and stains from utensils easily and conveniently. It eradicates the tough grease and grime from the soiled utensils. It removes residual food odor effectively.",
             "image": ["https://oneart.onrender.com/images/vim-dishwash-2l.jpg"], "ratings": 4, "product_id": 16},

            {
                "variant_cost": 92,
                "brand_name": "HIT",
                "count": 1000,
                "discounted_cost": 92,
                "discount": 7,
                "quantity": "200 ml",
                "description": "Worried about food getting infected or cockroaches bothering you at night? Then use HIT Cockroach Killer Spray. It is an effective cockroach killer spray.",
                "image": ["https://oneart.onrender.com/images/hit-cockroach-killer-spray-200-m.jpg","https://oneart.onrender.com/images/hit-cockroach-killer-spray-200-f.jpg","https://oneart.onrender.com/images/hit-cockroach-killer-spray-200-b.jpg","https://oneart.onrender.com/images/hit-cockroach-killer-spray-200-d.jpg"],
                "ratings": 0,
                "product_id": 17
            },

            {"variant_cost": 498, "brand_name": "HIT", "count": 100, "discounted_cost": 396, "discount": 20,
             "quantity": "200 ml",
             "description": "Worried about food getting infected or cockroaches bothering you at night? Then use HIT Cockroach Killer Spray. It is an effective cockroach killer spray.",
             "image": ["https://oneart.onrender.com/images/hit-crawling-insect-killer-cockr.jpg"], "ratings": 4,
             "product_id": 17},

            {"variant_cost": 340, "brand_name": "HIT", "count": 100, "discounted_cost": 306, "discount": 10,
             "quantity": "625 ml",
             "description": "Worried about food getting infected or cockroaches bothering you at night? Then use HIT Cockroach Killer Spray. It is an effective cockroach killer spray.",
             "image": ["https://oneart.onrender.com/images/hit-cockroach-killer-spray-625-ml.jpg"], "ratings": 4,
             "product_id": 17},

            {"variant_cost": 225, "brand_name": "HIT", "count": 100, "discounted_cost": 209, "discount": 7,
             "quantity": "400 ml",
             "description": "Worried about food getting infected or cockroaches bothering you at night? Then use HIT Cockroach Killer Spray. It is an effective cockroach killer spray.",
             "image": ["https://oneart.onrender.com/images/hit-cockroach-killer-spray-400-ml.jpg"], "ratings": 4,
             "product_id": 17},

            {
                "variant_cost": 53,
                "brand_name": "Santoor",
                "count": 1000,
                "discounted_cost": 53,
                "discount": 33,
                "quantity": "150 g",
                "description": "Showering and bathing is an everyday routine. Santoor Sandal & Turmeric Soap is required for you to begin your day on a refreshing note.",
                "image": ["https://oneart.onrender.com/images/santoor-sandal-turmeric-soap-150.jpg", "https://oneart.onrender.com/images/santoor-sandal-turmeric-soap-150-f.jpg", "https://oneart.onrender.com/images/santoor-sandal-turmeric-soap-150-d.jpg", "https://oneart.onrender.com/images/santoor-sandal-turmeric-soap-150-t.jpg"],
                "ratings": 0,
                "product_id": 2},

            {"variant_cost": 136, "brand_name": "Santoor", "count": 100, "discounted_cost": 124, "discount": 8,
             "quantity": "400 ml",
             "description": "Showering and bathing is an everyday routine. Santoor Sandal & Turmeric Soap is required for you to begin your day on a refreshing note.",
             "image": ["https://oneart.onrender.com/images/santoor-sandal-turmeric-soap-100.jpg"], "ratings": 4,
             "product_id": 2},

            {"variant_cost": 199, "brand_name": "Santoor", "count": 100, "discounted_cost": 178, "discount": 10,
             "quantity": "400 gms",
             "description": "Showering and bathing is an everyday routine. Santoor Sandal & Turmeric Soap is required for you to begin your day on a refreshing note.",
             "image": ["https://oneart.onrender.com/images/santoor-sandal-almond-milk-soap.jpg"], "ratings": 4,
             "product_id": 2},

            {"variant_cost": 60, "brand_name": "Odonil", "count": 100, "discounted_cost": 55, "discount": 8,
             "quantity": "10 gms",
             "description": "Odonil Zipper Rose Air Freshener has special odour busters that keep bad smell away. It can be used in washrooms, bedrooms, wardrobes, kitchen, shoe racks, etc.",
             "image": ["https://oneart.onrender.com/images/odonil-zipper-joyful-lavender-ai.jpg"], "ratings": 4,
             "product_id": 18},

            {"variant_cost": 60, "brand_name": "Odonil", "count": 100, "discounted_cost": 55, "discount": 8,
             "quantity": "10 gms",
             "description": "Odonil Zipper Rose Air Freshener has special odour busters that keep bad smell away. It can be used in washrooms, bedrooms, wardrobes, kitchen, shoe racks, etc.",
             "image": ["https://oneart.onrender.com/images/odonil-zipper-blissful-citrus-ai.jpg"], "ratings": 4,
             "product_id": 18},

            {"variant_cost": 80, "brand_name": "Odonil", "count": 100, "discounted_cost": 68, "discount": 15,
             "quantity": "10 gms",
             "description": "Odonil Zipper Rose Air Freshener has special odour busters that keep bad smell away. It can be used in washrooms, bedrooms, wardrobes, kitchen, shoe racks, etc.",
             "image": ["https://oneart.onrender.com/images/odonil-jasmine-fantasy-room-fres.jpg"], "ratings": 4,
             "product_id": 18},

            {
                "variant_cost": 285,
                "brand_name": "Ashirwad",
                "count": 1000,
                "discounted_cost": 285,
                "discount": 19,
                "quantity": "5 kg",
                "description": "Looking to switch to a healthier flour option? Look no further. Aashirvaad Multigrain Atta provides you and your family with wholesome goodness and health benefits without compromising on taste.",
                "image": ["https://oneart.onrender.com/images/aashirvaad-multigrain-atta-5-kg.jpg"],
                "ratings": 0,
                "product_id": 6
            },

        {
                "variant_cost": 242,
                "brand_name": "Madhur",
                "count": 1000,
                "discounted_cost": 242,
                "discount": 23,
                "quantity": "5 kg",
                "description": "Madhur Pure and Hygienic Sugar is used in preparing sweetmeats and sweet dishes for your loved ones. It is a must-have product in your kitchen wardrobe",
                "image": ["https://oneart.onrender.com/images/madhur-pure-hygienic-sugar-5-kg.jpg"],
                "ratings": 0,
                "product_id": 5},

            {"variant_cost": 65, "brand_name": "Madhur", "count": 100, "discounted_cost": 52, "discount": 20,
             "quantity": "1 kg",
             "description": "Madhur Pure and Hygienic Sugar is used in preparing sweetmeats and sweet dishes for your loved ones. It is a must-have product in your kitchen wardrobe",
             "image": ["https://oneart.onrender.com/images/madhur-pure-hygienic-sugar-1-kg.jpg"], "ratings": 4,
             "product_id": 5},

            {
                "variant_cost": 116,
                "brand_name": "Parle-G",
                "count": 1000,
                "discounted_cost": 116,
                "discount": 17,
                "quantity": "1 kg",
                "description": "Filled with the goodness of milk and wheat, Parle-G has been a source of all-round nourishment for the nation since decades. They're crispy, they're tasty and they'll leave you craving for more.",
                "image": ["https://oneart.onrender.com/images/parle-g-gold-biscuits-1-kg-produ.jpg"],
                "ratings": 0,
                "product_id": 13
            },


        {"variant_cost": 30, "brand_name": "Parle", "count": 100, "discounted_cost": 27, "discount": 10,
             "quantity": "200 gms",
             "description": "Filled with the goodness of milk and wheat, Parle-G has been a source of all-round nourishment for the nation since decades. They're crispy, they're tasty and they'll leave you craving for more.",
             "image": ["https://oneart.onrender.com/images/parle-g-gold-biscuits-200-g.jpg"], "ratings": 4,
             "product_id": 13},

            {"variant_cost": 75, "brand_name": "Parle", "count": 100, "discounted_cost": 69, "discount": 8,
             "quantity": "500 gms",
             "description": "Filled with the goodness of milk and wheat, Parle-G has been a source of all-round nourishment for the nation since decades. They're crispy, they're tasty and they'll leave you craving for more.",
             "image": ["https://oneart.onrender.com/images/parle-g-gold-biscuits-500-g-prod.jpg"], "ratings": 4,
             "product_id": 13},

            {"variant_cost": 10, "brand_name": "Parle", "count": 100, "discounted_cost": 0, "discount": 0,
             "quantity": "60 gms",
             "description": "Filled with the goodness of milk and wheat, Parle-G has been a source of all-round nourishment for the nation since decades. They're crispy, they're tasty and they'll leave you craving for more.",
             "image": ["https://oneart.onrender.com/images/parle-g-gold-biscuits-1-kg-produ.jpg","https://oneart.onrender.com/images/parle-g-gold-biscuits-1-kg-produ-b.jpg","https://oneart.onrender.com/images/parle-g-gold-biscuits-1-kg-produ-t.jpg"], "ratings": 4,
             "product_id": 13},

            {
                "variant_cost": 13,
                "brand_name": "Maggi",
                "count": 1000,
                "discounted_cost": 13,
                "discount": 7,
                "quantity": "70 g",
                "description": "Maggi 2-Minutes Noodles have been a classic Indian snack for a good few decades now. Nestle brings you another delicious instant food product - Maggi 2-Minute Masala Noodles!",
                "image": ["https://oneart.onrender.com/images/maggi-2-minute-masala-noodles.jpg","https://oneart.onrender.com/images/maggi-2-minute-masala-noodles-b.jpg","https://oneart.onrender.com/images/maggi-2-minute-masala-noodles-f.jpg","https://oneart.onrender.com/images/maggi-2-minute-masala-noodles-d.jpg"],
                "ratings": 0,
                "product_id": 14
            },


        {"variant_cost": 160, "brand_name": "Maggie", "count": 100, "discounted_cost": 128, "discount": 20,
             "quantity": "832 gms",
             "description": "Maggi 2-Minutes Noodles have been a classic Indian snack for a good few decades now. Nestle brings you another delicious instant food product - Maggi 2-Minute Masala Noodles!",
             "image": ["https://oneart.onrender.com/images/maggi-2-minutes-masala-noodles.jpg"], "ratings": 4,
             "product_id": 14},

            {"variant_cost": 28, "brand_name": "Maggie", "count": 100, "discounted_cost": 268, "discount": 7,
             "quantity": "140 gms",
             "description": "Maggi 2-Minutes Noodles have been a classic Indian snack for a good few decades now. Nestle brings you another delicious instant food product - Maggi 2-Minute Masala Noodles!",
             "image": ["https://oneart.onrender.com/images/maggi-2-minute-masala-noodles-14.jpg"], "ratings": 4,
             "product_id": 14},

            {
                "variant_cost": 260,
                "brand_name": "Cerelac",
                "count": 1000,
                "discounted_cost": 260,
                "discount": 0,
                "quantity": "300 g",
                "description": "Nestle presents Cerelac Baby Cereal with Milk Wheat Apple complementary food for babies from 6 months onwards. Infants have a higher requirement of nutrients, Cerelac Wheat Apple Cereal ensures your growing infant is getting the right nutritional requirements.",
                "image": ["https://oneart.onrender.com/images/cerelac-baby-cereal-with-milk-wh","https://oneart.onrender.com/images/cerelac-baby-cereal-with-milk-wh-b","https://oneart.onrender.com/images/cerelac-baby-cereal-with-milk-wh-s"],
                "ratings": 0,
                "product_id": 8
            },
            {
                "variant_cost": 218,
                "brand_name": "Camel",
                "count": 1000,
                "discounted_cost": 218,
                "discount": 45,
                "quantity": "12 Shades per Pkt (Pack of 10 Pkts)",
                "description": "Camel Wax Crayons is the best way to let your child explore their natural desire for coloring.",
                "image": ["https://oneart.onrender.com/images/aashirvaad-multigrain-atta-5-kg.jpg","https://oneart.onrender.com/images/aashirvaad-multigrain-atta-5-kg-back.jpg"],
                "ratings": 0,
                "product_id": 11
            },
            {
                "variant_cost": 47,
                "brand_name": "Camlin",
                "count": 1000,
                "discounted_cost": 47,
                "discount": 20,
                "quantity": "1 pen pencil (0.7 mm with 5 leads) and 1 pen pencil (0.9mm with 5 leads)•1 XL Eraser",
                "description": "Breaking lead of pencil is often an obstacle for every child that is preceded by sharpening again and again and making unnecessary chaos",
                "image": ["https://oneart.onrender.com/images/camlin-tri-mech-3-in-1-pen-penci.jpg","https://oneart.onrender.com/images/camlin-tri-mech-3-in-1-pen-penci-b.jpg"],
                "ratings": 0,
                "product_id": 12
            },
            {
                "variant_cost": 50,
                "brand_name": "Odonil",
                "count": 1000,
                "discounted_cost": 50,
                "discount": 23,
                "quantity": "10 g",
                "description": "Odonil Zipper Rose Air Freshener has special odor busters that keep bad smell away. It can be used in washrooms, bedrooms, wardrobes, kitchen, shoe racks, etc.",
                "image": ["https://oneart.onrender.com/images/odonil-zipper-rose-air-freshener.jpg","https://oneart.onrender.com/images/odonil-zipper-rose-air-freshener-b.jpg","https://oneart.onrender.com/images/odonil-zipper-rose-air-freshener-t.jpg"],
                "ratings": 0,
                "product_id": 18
            }

        ]

        with session_scope() as session:
            for product_data in products_data:
                product = models.ProductVariant(**product_data)
                session.add(product)
                session.commit()
                session.refresh(product)

        return {"message": "Products added successfully", "data":{}}

    except Exception as e:
        print(repr(e))
        raise HTTPException(status_code=500, detail=str(e))

