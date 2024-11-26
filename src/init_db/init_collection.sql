-- Gacha table creation
CREATE TABLE IF NOT EXISTS Gacha(
        id INTEGER PRIMARY KEY AUTO_INCREMENT,
        name VARCHAR(64) NOT NULL,
        extractionProb FLOAT NOT NULL,
        rarity VARCHAR(32) NOT NULL,
        image VARCHAR(1024) NOT NULL,
        damage INTEGER NOT NULL,
        speed INTEGER NOT NULL,
        critical FLOAT NOT NULL,
        accuracy INTEGER NOT NULL
);

-- Owned table creation
CREATE TABLE IF NOT EXISTS Owned(
        id INTEGER PRIMARY KEY AUTO_INCREMENT,
        user INTEGER NOT NULL,
        gacha INTEGER NOT NULL,
        FOREIGN KEY (gacha) REFERENCES Gacha(id)
);

-- Data load
LOAD DATA INFILE '/var/lib/mysql-files/data_collection.csv'
INTO TABLE Gacha
FIELDS TERMINATED BY ','
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(accuracy, critical, damage, extractionProb, image, name, rarity, speed);