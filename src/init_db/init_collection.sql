-- Gacha table creation
CREATE TABLE Gacha(
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
CREATE TABLE Owned(
        id INTEGER PRIMARY KEY AUTO_INCREMENT,
        user INTEGER NOT NULL,
        gacha INTEGER NOT NULL,
        FOREIGN KEY (gacha) REFERENCES Gacha(id)
);


LOAD DATA INFILE '/path/to/data.csv'
INTO TABLE my_table
FIELDS TERMINATED BY ',' 
ENCLOSED BY '"' 
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(name, extractionProb, rarity, image, damage, speed, critical, accuracy)