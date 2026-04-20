-- Yelp Prototype Database Schema

CREATE DATABASE IF NOT EXISTS yelp_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE yelp_db;

-- Users table
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    role ENUM('customer', 'owner') NOT NULL DEFAULT 'customer',
    phone VARCHAR(20),
    about_me TEXT,
    city VARCHAR(100),
    country VARCHAR(100),
    state VARCHAR(50),
    languages JSON,
    gender VARCHAR(50),
    profile_picture VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_email (email),
    INDEX idx_role (role)
);

-- User preferences for AI recommendations
CREATE TABLE user_preferences (
    user_id INT PRIMARY KEY,
    cuisine_preferences JSON,
    price_range VARCHAR(10),
    dietary_needs JSON,
    location VARCHAR(255),
    ambiance_preferences JSON,
    sort_preference VARCHAR(50),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Restaurants
CREATE TABLE restaurants (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    cuisine_type VARCHAR(100),
    price_range VARCHAR(10),
    address VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(50),
    zip_code VARCHAR(20),
    phone VARCHAR(20),
    website VARCHAR(255),
    hours JSON,
    amenities JSON,
    view_count INT NOT NULL DEFAULT 0,
    owner_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_cuisine (cuisine_type),
    INDEX idx_city (city),
    INDEX idx_price (price_range),
    INDEX idx_owner (owner_id)
);

-- Restaurant photos
CREATE TABLE restaurant_photos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    restaurant_id INT NOT NULL,
    photo_url VARCHAR(500) NOT NULL,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (restaurant_id) REFERENCES restaurants(id) ON DELETE CASCADE,
    INDEX idx_restaurant (restaurant_id)
);

-- Reviews
CREATE TABLE reviews (
    id INT AUTO_INCREMENT PRIMARY KEY,
    restaurant_id INT NOT NULL,
    user_id INT NOT NULL,
    rating INT NOT NULL CHECK (rating >= 1 AND rating <= 5),
    review_text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (restaurant_id) REFERENCES restaurants(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_restaurant (restaurant_id),
    INDEX idx_user (user_id),
    INDEX idx_rating (rating)
);

-- Review photos
CREATE TABLE review_photos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    review_id INT NOT NULL,
    photo_url VARCHAR(500) NOT NULL,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (review_id) REFERENCES reviews(id) ON DELETE CASCADE,
    INDEX idx_review (review_id)
);

-- Favorites
CREATE TABLE favorites (
    user_id INT NOT NULL,
    restaurant_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, restaurant_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (restaurant_id) REFERENCES restaurants(id) ON DELETE CASCADE
);

-- Restaurant claims
CREATE TABLE restaurant_claims (
    id INT AUTO_INCREMENT PRIMARY KEY,
    restaurant_id INT NOT NULL,
    owner_id INT NOT NULL,
    status ENUM('pending', 'approved', 'rejected') NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (restaurant_id) REFERENCES restaurants(id) ON DELETE CASCADE,
    FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_status (status),
    INDEX idx_owner (owner_id)
);

-- Chat conversations
CREATE TABLE chat_conversations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    title VARCHAR(255) NOT NULL DEFAULT 'New conversation',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user (user_id)
);

-- Chat messages
CREATE TABLE chat_messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    conversation_id INT NOT NULL,
    role ENUM('user', 'assistant') NOT NULL,
    content TEXT NOT NULL,
    recommendations JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES chat_conversations(id) ON DELETE CASCADE,
    INDEX idx_conversation (conversation_id)
);

-- ============================================================
-- Sample data (password = "password" hashed with bcrypt)
-- ============================================================

INSERT INTO users (email, password_hash, name, role, city, state, country) VALUES
('customer@test.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqNk5rHVqK', 'Test Customer', 'customer', 'San Francisco', 'CA', 'USA'),
('owner@test.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqNk5rHVqK', 'Test Owner', 'owner', 'San Francisco', 'CA', 'USA');

INSERT INTO user_preferences (user_id, cuisine_preferences, price_range, dietary_needs, location, ambiance_preferences, sort_preference) VALUES
(1, '["Italian", "Japanese"]', '$$', '["vegetarian"]', 'San Francisco', '["casual", "romantic"]', 'rating');

INSERT INTO restaurants (name, description, cuisine_type, price_range, address, city, state, zip_code, phone, hours, amenities, owner_id) VALUES
('Pasta Paradise', 'Authentic Italian cuisine with homemade pasta and wood-fired pizzas', 'Italian', '$$', '123 Main St', 'San Francisco', 'CA', '94102', '415-555-0100',
 '{"Monday": "11:00 AM - 10:00 PM", "Tuesday": "11:00 AM - 10:00 PM", "Wednesday": "11:00 AM - 10:00 PM", "Thursday": "11:00 AM - 10:00 PM", "Friday": "11:00 AM - 11:00 PM", "Saturday": "10:00 AM - 11:00 PM", "Sunday": "10:00 AM - 9:00 PM"}',
 '["family-friendly", "outdoor seating", "wifi"]', 2),

('Sushi Master', 'Fresh sushi and Japanese specialties with an omakase counter', 'Japanese', '$$$', '456 Market St', 'San Francisco', 'CA', '94103', '415-555-0200',
 '{"Monday": "12:00 PM - 10:00 PM", "Tuesday": "12:00 PM - 10:00 PM", "Wednesday": "12:00 PM - 10:00 PM", "Thursday": "12:00 PM - 10:00 PM", "Friday": "12:00 PM - 11:00 PM", "Saturday": "12:00 PM - 11:00 PM", "Sunday": "Closed"}',
 '["quiet", "upscale", "romantic"]', 2),

('Taco Fiesta', 'Authentic Mexican street food and handmade tortillas', 'Mexican', '$', '789 Mission St', 'San Francisco', 'CA', '94104', '415-555-0300',
 '{"Monday": "10:00 AM - 9:00 PM", "Tuesday": "10:00 AM - 9:00 PM", "Wednesday": "10:00 AM - 9:00 PM", "Thursday": "10:00 AM - 9:00 PM", "Friday": "10:00 AM - 10:00 PM", "Saturday": "9:00 AM - 10:00 PM", "Sunday": "9:00 AM - 8:00 PM"}',
 '["casual", "family-friendly", "outdoor seating"]', NULL),

('Green Leaf Cafe', 'Farm-to-table vegetarian and vegan cuisine', 'Vegetarian', '$$', '321 Valencia St', 'San Francisco', 'CA', '94110', '415-555-0400',
 '{"Monday": "8:00 AM - 8:00 PM", "Tuesday": "8:00 AM - 8:00 PM", "Wednesday": "8:00 AM - 8:00 PM", "Thursday": "8:00 AM - 8:00 PM", "Friday": "8:00 AM - 9:00 PM", "Saturday": "9:00 AM - 9:00 PM", "Sunday": "9:00 AM - 7:00 PM"}',
 '["casual", "wifi", "outdoor seating"]', NULL),

('The Golden Wok', 'Traditional Chinese dishes with a modern twist', 'Chinese', '$$', '555 Clement St', 'San Francisco', 'CA', '94118', '415-555-0500',
 '{"Monday": "11:00 AM - 9:30 PM", "Tuesday": "11:00 AM - 9:30 PM", "Wednesday": "11:00 AM - 9:30 PM", "Thursday": "11:00 AM - 9:30 PM", "Friday": "11:00 AM - 10:30 PM", "Saturday": "11:00 AM - 10:30 PM", "Sunday": "11:00 AM - 9:00 PM"}',
 '["family-friendly", "quiet"]', NULL),

('Bombay Spice', 'Authentic Indian cuisine with tandoori specialties', 'Indian', '$$', '888 Geary St', 'San Francisco', 'CA', '94109', '415-555-0600',
 '{"Monday": "11:30 AM - 10:00 PM", "Tuesday": "11:30 AM - 10:00 PM", "Wednesday": "11:30 AM - 10:00 PM", "Thursday": "11:30 AM - 10:00 PM", "Friday": "11:30 AM - 11:00 PM", "Saturday": "12:00 PM - 11:00 PM", "Sunday": "12:00 PM - 9:30 PM"}',
 '["casual", "family-friendly"]', NULL);

INSERT INTO reviews (restaurant_id, user_id, rating, review_text) VALUES
(1, 1, 5, 'Amazing pasta! The carbonara was perfect. Will definitely come back.'),
(2, 1, 5, 'Best sushi in the city! The omakase was outstanding.'),
(3, 1, 4, 'Great tacos and friendly atmosphere. Very affordable.'),
(4, 1, 4, 'Loved the vegan options. The mushroom risotto was incredible.'),
(5, 1, 3, 'Good Chinese food but a bit slow on service.');
