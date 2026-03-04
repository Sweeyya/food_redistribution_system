USE food_redistribution;
CREATE TABLE Food_Provider (
	provider_id INT AUTO_INCREMENT PRIMARY KEY,
	name VARCHAR(50) NOT NULL,
	provider_type VARCHAR(50) NOT NULL,
	contact_email VARCHAR(100) NOT NULL,
	phone_number VARCHAR(20),
	city VARCHAR(60),
	zip_code VARCHAR(10)
);
CREATE TABLE recipient_organization (
  org_id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  org_type VARCHAR(50) NOT NULL,
  contact_email VARCHAR(100),
  phone_number VARCHAR(20),
  city VARCHAR(60),
  zip_code VARCHAR(10),
  capacity_limit INT
);
CREATE TABLE food_item (
  item_id INT AUTO_INCREMENT PRIMARY KEY,
  item_name VARCHAR(100) NOT NULL,
  category VARCHAR(50),
  storage_type VARCHAR(30),
  is_perishable BOOLEAN
);
CREATE TABLE surplus_listing (
  listing_id INT AUTO_INCREMENT PRIMARY KEY,
  provider_id INT NOT NULL,
  post_date DATE NOT NULL,
  expiration_date DATE NOT NULL,
  total_quantity DECIMAL(10,2),
  status VARCHAR(20) NOT NULL,
  FOREIGN KEY (provider_id) REFERENCES Food_Provider(provider_id)
);
USE food_redistribution;
CREATE TABLE Food_Provider (
	provider_id INT AUTO_INCREMENT PRIMARY KEY,
	name VARCHAR(50) NOT NULL,
	provider_type VARCHAR(50) NOT NULL,
	contact_email VARCHAR(100) NOT NULL,
	phone_number VARCHAR(20),
	city VARCHAR(60),
	zip_code VARCHAR(10)
);
CREATE TABLE recipient_organization (
  org_id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  org_type VARCHAR(50) NOT NULL,
  contact_email VARCHAR(100),
  phone_number VARCHAR(20),
  city VARCHAR(60),
  zip_code VARCHAR(10),
  capacity_limit INT
);
CREATE TABLE food_item (
  item_id INT AUTO_INCREMENT PRIMARY KEY,
  item_name VARCHAR(100) NOT NULL,
  category VARCHAR(50),
  storage_type VARCHAR(30),
  is_perishable BOOLEAN
);
CREATE TABLE listing_item (
  listing_id INT NOT NULL,
  item_id INT NOT NULL,
  quantity DECIMAL(10,2) NOT NULL,
  PRIMARY KEY (listing_id, item_id),
  FOREIGN KEY (listing_id) REFERENCES surplus_listing(listing_id),
  FOREIGN KEY (item_id) REFERENCES food_item(item_id)
);
CREATE TABLE request (
  request_id INT AUTO_INCREMENT PRIMARY KEY,
  listing_id INT NOT NULL,
  org_id INT NOT NULL,
  request_date DATE NOT NULL,
  requested_quantity DECIMAL(10,2),
  status VARCHAR(20) NOT NULL,
  FOREIGN KEY (listing_id) REFERENCES surplus_listing(listing_id),
  FOREIGN KEY (org_id) REFERENCES recipient_organization(org_id)
);
CREATE TABLE pickup (
  pickup_id INT AUTO_INCREMENT PRIMARY KEY,
  request_id INT NOT NULL,
  pickup_date DATE,
  pickup_time TIME,
  pickup_status VARCHAR(20) NOT NULL,
  confirmed_quantity DECIMAL(10,2),
  FOREIGN KEY (request_id) REFERENCES request(request_id)
);