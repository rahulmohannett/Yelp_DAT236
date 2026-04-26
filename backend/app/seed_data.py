"""
Synthetic data seeder for Yelp Prototype.
Populates MongoDB with realistic restaurants, users, reviews, and favorites.

Run from inside user-service container:
    docker exec yelp-user-service python -m app.seed_data

Or locally (requires MONGO_URI env):
    cd backend && python -m app.seed_data
"""
import asyncio
import random
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from bson import ObjectId
import os

MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongodb:27017/yelp_db")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ============================================================
# SEED DATA
# ============================================================

RESTAURANTS = [
    {"name": "Pasta Paradise", "cuisine_type": "Italian", "price_range": "$$",
     "city": "San Jose", "state": "CA", "zip_code": "95113",
     "description": "Authentic Italian pasta and pizzas in a cozy setting.",
     "phone": "408-555-0101", "website": "https://pastaparadise.com",
     "amenities": ["Outdoor Seating", "WiFi", "Family-Friendly"]},
    {"name": "Sushi Master", "cuisine_type": "Japanese", "price_range": "$$$",
     "city": "Palo Alto", "state": "CA", "zip_code": "94301",
     "description": "Premium sushi and sashimi by master chefs.",
     "phone": "650-555-0102", "website": "https://sushimaster.com",
     "amenities": ["Reservations", "Full Bar", "Quiet"]},
    {"name": "Taco Fiesta", "cuisine_type": "Mexican", "price_range": "$",
     "city": "San Jose", "state": "CA", "zip_code": "95110",
     "description": "Street tacos, burritos, and margaritas.",
     "phone": "408-555-0103", "website": "https://tacofiesta.com",
     "amenities": ["Outdoor Seating", "Takeout", "Family-Friendly"]},
    {"name": "Green Leaf Cafe", "cuisine_type": "Vegetarian", "price_range": "$$",
     "city": "Berkeley", "state": "CA", "zip_code": "94704",
     "description": "100% plant-based menu with organic ingredients.",
     "phone": "510-555-0104", "website": "https://greenleafcafe.com",
     "amenities": ["Vegan Options", "Gluten-Free Options", "WiFi"]},
    {"name": "The Golden Wok", "cuisine_type": "Chinese", "price_range": "$$",
     "city": "Oakland", "state": "CA", "zip_code": "94607",
     "description": "Szechuan and Cantonese classics with modern twists.",
     "phone": "510-555-0105", "website": "https://goldenwok.com",
     "amenities": ["Delivery", "Takeout", "Large Groups"]},
    {"name": "Bombay Spice", "cuisine_type": "Indian", "price_range": "$$",
     "city": "Sunnyvale", "state": "CA", "zip_code": "94086",
     "description": "North and South Indian cuisine with extensive vegetarian options.",
     "phone": "408-555-0106", "website": "https://bombayspice.com",
     "amenities": ["Vegetarian", "Vegan Options", "Halal", "Large Groups"]},
    {"name": "Candlelight Bistro", "cuisine_type": "French", "price_range": "$$$$",
     "city": "San Francisco", "state": "CA", "zip_code": "94108",
     "description": "Romantic fine dining with classic French dishes.",
     "phone": "415-555-0107", "website": "https://candlelightbistro.com",
     "amenities": ["Romantic", "Reservations", "Full Bar", "Dress Code"]},
    {"name": "Burger Haven", "cuisine_type": "American", "price_range": "$",
     "city": "Mountain View", "state": "CA", "zip_code": "94040",
     "description": "Classic burgers, fries, and shakes since 1985.",
     "phone": "650-555-0108", "website": "https://burgerhaven.com",
     "amenities": ["Takeout", "Casual", "Family-Friendly", "Kid-Friendly"]},
    {"name": "Sakura Ramen", "cuisine_type": "Japanese", "price_range": "$$",
     "city": "San Francisco", "state": "CA", "zip_code": "94102",
     "description": "Authentic Tonkotsu and Shoyu ramen.",
     "phone": "415-555-0109", "website": "https://sakuraramen.com",
     "amenities": ["Casual", "Late Night", "Quick Service"]},
    {"name": "Mediterranean Breeze", "cuisine_type": "Mediterranean", "price_range": "$$",
     "city": "San Jose", "state": "CA", "zip_code": "95128",
     "description": "Greek, Turkish, and Lebanese specialties.",
     "phone": "408-555-0110", "website": "https://medbreeze.com",
     "amenities": ["Vegetarian", "Halal", "Outdoor Seating"]},
    {"name": "Thai Orchid", "cuisine_type": "Thai", "price_range": "$$",
     "city": "San Mateo", "state": "CA", "zip_code": "94401",
     "description": "Traditional Thai flavors with a modern touch.",
     "phone": "650-555-0111", "website": "https://thaiorchid.com",
     "amenities": ["Vegan Options", "Gluten-Free Options", "Takeout"]},
    {"name": "Rooftop Grill", "cuisine_type": "American", "price_range": "$$$",
     "city": "San Francisco", "state": "CA", "zip_code": "94105",
     "description": "Steaks and seafood with panoramic city views.",
     "phone": "415-555-0112", "website": "https://rooftopgrill.com",
     "amenities": ["Romantic", "Outdoor Seating", "Full Bar", "View"]},
]

HOURS_TEMPLATE = {
    "Monday": "11:00 AM - 10:00 PM",
    "Tuesday": "11:00 AM - 10:00 PM",
    "Wednesday": "11:00 AM - 10:00 PM",
    "Thursday": "11:00 AM - 10:00 PM",
    "Friday": "11:00 AM - 11:00 PM",
    "Saturday": "10:00 AM - 11:00 PM",
    "Sunday": "10:00 AM - 9:00 PM",
}

CUSTOMERS = [
    {"email": "customer@test.com", "name": "Test Customer", "city": "San Jose"},
    {"email": "alice@test.com", "name": "Alice Johnson", "city": "Palo Alto"},
    {"email": "bob@test.com", "name": "Bob Smith", "city": "San Francisco"},
    {"email": "carol@test.com", "name": "Carol Davis", "city": "Berkeley"},
    {"email": "dave@test.com", "name": "Dave Wilson", "city": "Mountain View"},
    {"email": "emma@test.com", "name": "Emma Chen", "city": "Sunnyvale"},
    {"email": "frank@test.com", "name": "Frank Taylor", "city": "Oakland"},
]

OWNERS = [
    {"email": "owner@test.com", "name": "Test Owner", "city": "San Jose"},
    {"email": "owner2@test.com", "name": "Maria Garcia", "city": "Palo Alto"},
    {"email": "owner3@test.com", "name": "James Kim", "city": "San Francisco"},
]

REVIEW_TEMPLATES = {
    5: ["Amazing food and great service!", "Best {cuisine} in the area!", "Absolutely delicious, highly recommend!",
        "Will definitely be coming back!", "Perfect atmosphere and incredible flavors."],
    4: ["Really enjoyed the meal.", "Solid {cuisine} spot.", "Good food, friendly staff.",
        "Nice place, would recommend.", "Satisfying experience overall."],
    3: ["Decent but not memorable.", "Average {cuisine}, okay service.", "It was fine, nothing special.",
        "Could be better, could be worse.", "Meh, you can find better."],
    2: ["Below expectations.", "Service was slow and food was cold.", "Not worth the price.",
        "Had to wait too long for average food.", "Disappointing experience."],
    1: ["Terrible experience.", "Food was awful and service was worse.", "Would not recommend.",
        "Waste of money.", "Avoid this place."],
}

PREFERENCES_SAMPLES = [
    {"cuisine_preferences": ["Italian", "Mediterranean"], "price_range": "$$",
     "dietary_needs": ["Vegetarian"], "ambiance_preferences": ["Casual", "Family-Friendly"],
     "sort_preference": "rating"},
    {"cuisine_preferences": ["Japanese", "Thai"], "price_range": "$$$",
     "dietary_needs": ["Gluten-Free"], "ambiance_preferences": ["Romantic", "Quiet"],
     "sort_preference": "rating"},
    {"cuisine_preferences": ["Mexican", "American"], "price_range": "$",
     "dietary_needs": [], "ambiance_preferences": ["Casual", "Outdoor"],
     "sort_preference": "popularity"},
    {"cuisine_preferences": ["Indian", "Vegetarian"], "price_range": "$$",
     "dietary_needs": ["Vegan", "Vegetarian"], "ambiance_preferences": ["Family-Friendly"],
     "sort_preference": "price"},
]


async def seed():
    print(f"🔌 Connecting to MongoDB at {MONGO_URI}")
    client = AsyncIOMotorClient(MONGO_URI)
    db = client.yelp_db

    # Nuke existing data for a clean seed
    print("🗑️  Dropping existing collections...")
    for col in ["users", "user_preferences", "restaurants", "reviews",
                "favorites", "restaurant_claims", "chat_conversations",
                "chat_messages", "sessions"]:
        await db[col].drop()

    now = datetime.utcnow()

    # ========== USERS ==========
    print("👤 Creating users...")
    password_hash = pwd_context.hash("password")

    customer_ids = []
    for c in CUSTOMERS:
        result = await db.users.insert_one({
            **c,
            "password_hash": password_hash,
            "role": "customer",
            "created_at": now - timedelta(days=random.randint(1, 90)),
            "updated_at": now,
        })
        customer_ids.append(result.inserted_id)
    print(f"   {len(customer_ids)} customers created")

    owner_ids = []
    for o in OWNERS:
        result = await db.users.insert_one({
            **o,
            "password_hash": password_hash,
            "role": "owner",
            "created_at": now - timedelta(days=random.randint(1, 90)),
            "updated_at": now,
        })
        owner_ids.append(result.inserted_id)
    print(f"   {len(owner_ids)} owners created")

    # ========== USER PREFERENCES ==========
    print("⚙️  Creating user preferences...")
    for uid in customer_ids[:4]:  # first 4 customers get preferences
        pref = random.choice(PREFERENCES_SAMPLES).copy()
        pref["user_id"] = uid
        pref["updated_at"] = now
        await db.user_preferences.insert_one(pref)
    print(f"   4 preference records created")

    # ========== RESTAURANTS ==========
    print("🍽️  Creating restaurants...")
    restaurant_ids = []
    for i, r in enumerate(RESTAURANTS):
        owner_id = owner_ids[i % len(owner_ids)]
        result = await db.restaurants.insert_one({
            **r,
            "hours": HOURS_TEMPLATE.copy(),
            "photos": [],
            "owner_id": owner_id,
            "view_count": random.randint(50, 500),
            "average_rating": 0.0,
            "review_count": 0,
            "created_at": now - timedelta(days=random.randint(10, 180)),
            "updated_at": now,
        })
        restaurant_ids.append(result.inserted_id)
    print(f"   {len(restaurant_ids)} restaurants created")

    # ========== REVIEWS ==========
    print("⭐ Creating reviews...")
    review_count = 0
    for rest_id in restaurant_ids:
        # Each restaurant gets 3-10 reviews
        n = random.randint(3, 10)
        reviewers = random.sample(customer_ids, min(n, len(customer_ids)))
        restaurant_doc = await db.restaurants.find_one({"_id": rest_id})
        cuisine = restaurant_doc["cuisine_type"]

        ratings = []
        for reviewer_id in reviewers:
            # Skew ratings toward 4-5
            rating = random.choices([5, 4, 3, 2, 1], weights=[40, 35, 15, 7, 3])[0]
            text_template = random.choice(REVIEW_TEMPLATES[rating])
            review_text = text_template.replace("{cuisine}", cuisine)

            await db.reviews.insert_one({
                "restaurant_id": rest_id,
                "user_id": reviewer_id,
                "rating": rating,
                "review_text": review_text,
                "photos": [],
                "created_at": now - timedelta(days=random.randint(1, 60)),
                "updated_at": now - timedelta(days=random.randint(0, 30)),
            })
            ratings.append(rating)
            review_count += 1

        # Update restaurant's average + count
        avg = sum(ratings) / len(ratings) if ratings else 0
        await db.restaurants.update_one(
            {"_id": rest_id},
            {"$set": {"average_rating": round(avg, 1), "review_count": len(ratings)}}
        )
    print(f"   {review_count} reviews created")

    # ========== FAVORITES ==========
    print("❤️  Creating favorites...")
    fav_count = 0
    for uid in customer_ids:
        # Each customer favorites 2-4 random restaurants
        favs = random.sample(restaurant_ids, random.randint(2, 4))
        for rest_id in favs:
            await db.favorites.insert_one({
                "user_id": uid,
                "restaurant_id": rest_id,
                "created_at": now - timedelta(days=random.randint(1, 30)),
            })
            fav_count += 1
    print(f"   {fav_count} favorites created")

    # ========== RESTAURANT CLAIMS ==========
    print("📋 Creating restaurant claims...")
    # 2 approved claims from owners
    for i in range(2):
        await db.restaurant_claims.insert_one({
            "restaurant_id": restaurant_ids[i],
            "owner_id": owner_ids[i % len(owner_ids)],
            "status": "approved",
            "created_at": now - timedelta(days=random.randint(5, 60)),
        })
    print(f"   2 claims created")

    # ========== SUMMARY ==========
    print("\n" + "=" * 50)
    print("✅ SEED COMPLETE")
    print("=" * 50)
    print(f"Users:        {len(customer_ids)} customers + {len(owner_ids)} owners")
    print(f"Restaurants:  {len(restaurant_ids)}")
    print(f"Reviews:      {review_count}")
    print(f"Favorites:    {fav_count}")
    print(f"Preferences:  4")
    print(f"Claims:       2")
    print("\n📧 Login credentials (all password: 'password'):")
    print(f"   Customers: {', '.join(c['email'] for c in CUSTOMERS)}")
    print(f"   Owners:    {', '.join(o['email'] for o in OWNERS)}")
    print("=" * 50)

    client.close()


if __name__ == "__main__":
    asyncio.run(seed())