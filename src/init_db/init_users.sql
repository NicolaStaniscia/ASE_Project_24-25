CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(25) NOT NULL,
    salt VARCHAR(32) NOT NULL,
    password VARCHAR(64) NOT NULL,
    in_game_currency INT DEFAULT 0,
    last_access TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE users_admin (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(25) NOT NULL,
    salt VARCHAR(32) NOT NULL,
    password VARCHAR(64) NOT NULL,
    currency INT DEFAULT 0
);

CREATE TABLE payments (
    transaction_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    amount_spent INT NOT NULL,
    in_game_currency_purchased INT NOT NULL,
    transaction_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
    ON DELETE CASCADE
);

INSERT INTO users_admin (username, salt, password)
VALUES ('admin1', 'bfe17296dc5434254a21b50d760380f9', '5c79cb4de0c0eb1f5be3581b0aeeb8a8a0bb1e0fd68597d972a365f1d3af1534');

LOAD DATA INFILE './users.csv'
INTO TABLE users
FIELDS TERMINATED BY ',' 
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(username, salt, password, in_game_currency);