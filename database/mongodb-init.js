// MongoDB initialization script for Yelp prototype
// Run on MongoDB startup to create collections and indexes

// Switch to yelp_db database
db = db.getSiblingDB('yelp_db');

// ============================================================
// CREATE COLLECTIONS
// ============================================================

// Users collection
db.createCollection("users", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["email", "password_hash", "role"],
      properties: {
        _id: { bsonType: "objectId" },
        email: { bsonType: "string" },
        password_hash: { bsonType: "string" },
        name: { bsonType: "string" },
        role: { enum: ["customer", "owner"] },
        phone: { bsonType: "string" },
        about_me: { bsonType: "string" },
        city: { bsonType: "string" },
        country: { bsonType: "string" },
        state: { bsonType: "string" },
        languages: { bsonType: "array" },
        gender: { bsonType: "string" },
        profile_picture: { bsonType: "string" },
        created_at: { bsonType: "date" },
        updated_at: { bsonType: "date" }
      }
    }
  }
});

// Restaurants collection
db.createCollection("restaurants", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["name", "cuisine_type"],
      properties: {
        _id: { bsonType: "objectId" },
        name: { bsonType: "string" },
        description: { bsonType: "string" },
        cuisine_type: { bsonType: "string" },
        price_range: { enum: ["$", "$$", "$$$", "$$$$"] },
        address: { bsonType: "string" },
        city: { bsonType: "string" },
        state: { bsonType: "string" },
        zip_code: { bsonType: "string" },
        phone: { bsonType: "string" },
        website: { bsonType: "string" },
        hours: { bsonType: "object" },
        amenities: { bsonType: "array" },
        view_count: { bsonType: "int" },
        owner_id: { bsonType: "objectId" },
        photos: { bsonType: "array" },
        created_at: { bsonType: "date" },
        updated_at: { bsonType: "date" }
      }
    }
  }
});

// Reviews collection
db.createCollection("reviews", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["restaurant_id", "user_id", "rating"],
      properties: {
        _id: { bsonType: "objectId" },
        restaurant_id: { bsonType: "objectId" },
        user_id: { bsonType: "objectId" },
        rating: { bsonType: "int", minimum: 1, maximum: 5 },
        review_text: { bsonType: "string" },
        photos: { bsonType: "array" },
        created_at: { bsonType: "date" },
        updated_at: { bsonType: "date" }
      }
    }
  }
});

// User preferences collection
db.createCollection("user_preferences", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      properties: {
        _id: { bsonType: "objectId" },
        user_id: { bsonType: "objectId" },
        cuisine_preferences: { bsonType: "array" },
        price_range: { bsonType: "array" },
        dietary_needs: { bsonType: "array" },
        location: { bsonType: "string" },
        ambiance_preferences: { bsonType: "array" },
        sort_preference: { enum: ["rating", "distance", "popularity", "price"] },
        updated_at: { bsonType: "date" }
      }
    }
  }
});

// Favorites collection
db.createCollection("favorites");

// Restaurant claims collection
db.createCollection("restaurant_claims", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      properties: {
        _id: { bsonType: "objectId" },
        restaurant_id: { bsonType: "objectId" },
        owner_id: { bsonType: "objectId" },
        status: { enum: ["pending", "approved", "rejected"] },
        created_at: { bsonType: "date" }
      }
    }
  }
});

// Chat conversations collection
db.createCollection("chat_conversations", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      properties: {
        _id: { bsonType: "objectId" },
        user_id: { bsonType: "objectId" },
        title: { bsonType: "string" },
        created_at: { bsonType: "date" },
        updated_at: { bsonType: "date" }
      }
    }
  }
});

// Chat messages collection
db.createCollection("chat_messages", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      properties: {
        _id: { bsonType: "objectId" },
        conversation_id: { bsonType: "objectId" },
        role: { enum: ["user", "assistant"] },
        content: { bsonType: "string" },
        recommendations: { bsonType: "array" },
        created_at: { bsonType: "date" }
      }
    }
  }
});

// Sessions collection (with TTL)
db.createCollection("sessions");

// ============================================================
// CREATE INDEXES
// ============================================================

// Users indexes
db.users.createIndex({ "email": 1 }, { unique: true });
db.users.createIndex({ "role": 1 });
db.users.createIndex({ "created_at": 1 });

// Restaurants indexes
db.restaurants.createIndex({ "name": 1 });
db.restaurants.createIndex({ "city": 1 });
db.restaurants.createIndex({ "cuisine_type": 1 });
db.restaurants.createIndex({ "owner_id": 1 });
db.restaurants.createIndex({ "created_at": 1 });

// Reviews indexes
db.reviews.createIndex({ "restaurant_id": 1 });
db.reviews.createIndex({ "user_id": 1 });
db.reviews.createIndex({ "rating": 1 });
db.reviews.createIndex({ "created_at": 1 });
db.reviews.createIndex({ "restaurant_id": 1, "created_at": -1 });

// User preferences indexes
db.user_preferences.createIndex({ "user_id": 1 }, { unique: true });

// Favorites indexes
db.favorites.createIndex({ "user_id": 1 });
db.favorites.createIndex({ "restaurant_id": 1 });
db.favorites.createIndex({ "user_id": 1, "restaurant_id": 1 }, { unique: true });

// Restaurant claims indexes
db.restaurant_claims.createIndex({ "restaurant_id": 1 });
db.restaurant_claims.createIndex({ "owner_id": 1 });
db.restaurant_claims.createIndex({ "status": 1 });

// Chat indexes
db.chat_conversations.createIndex({ "user_id": 1 });
db.chat_conversations.createIndex({ "created_at": 1 });

db.chat_messages.createIndex({ "conversation_id": 1 });
db.chat_messages.createIndex({ "created_at": 1 });
db.chat_messages.createIndex({ "conversation_id": 1, "created_at": -1 });

// Sessions indexes (TTL: 7 days = 604800 seconds)
// Note: expireAfterSeconds: 0 means MongoDB will use the expiry field directly
db.sessions.createIndex({ "expires_at": 1 }, { expireAfterSeconds: 0 });
db.sessions.createIndex({ "user_id": 1 });

// ============================================================
// DONE
// ============================================================
print("MongoDB initialized successfully!");
print("Collections created: users, restaurants, reviews, user_preferences, favorites, restaurant_claims, chat_conversations, chat_messages, sessions");
print("Indexes created on all collections");