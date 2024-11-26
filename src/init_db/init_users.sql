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
VALUES ('admin1', 'b6b8e7fb8dbf898fa873a633315436f2', 'f3289aa25ed8cca41d0f6eb7813ed3fcb2bcc54f45756771a7fa549728d3542d');

LOAD DATA INFILE '/var/lib/mysql-files/users.csv'
INTO TABLE users
FIELDS TERMINATED BY ',' 
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(username, salt, password, in_game_currency);