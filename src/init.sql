-- Creazione della tabella Auctions
CREATE TABLE IF NOT EXISTS Auctions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    gacha_id INT NOT NULL,
    seller_id INT NOT NULL,
    starting_price INT NOT NULL,
    current_price INT NOT NULL,
    auction_end TIMESTAMP NOT NULL,
    status ENUM('active', 'closed', 'canceled', 'suspended') DEFAULT 'active'
);

-- Creazione della tabella Bids
CREATE TABLE IF NOT EXISTS Bids (
    id INT AUTO_INCREMENT PRIMARY KEY,
    auction_id INT NOT NULL,
    bidder_id INT NOT NULL,
    bid_amount INT NOT NULL,
    bid_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    refunded BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (auction_id) REFERENCES Auctions(id) ON DELETE CASCADE
);

-- Creazione della tabella AuctionTransactions
CREATE TABLE IF NOT EXISTS AuctionTransactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    auction_id INT NOT NULL,
    buyer_id INT,
    seller_id INT NOT NULL,
    final_price INT NOT NULL,
    transaction_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status ENUM('completed', 'failed') DEFAULT 'completed',
    FOREIGN KEY (auction_id) REFERENCES Auctions(id) ON DELETE CASCADE
);

-- Creazione della tabella UserTransactionHistory
CREATE TABLE IF NOT EXISTS UserTransactionHistory (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    auction_id INT NOT NULL,
    transaction_type ENUM('buy', 'sell', 'refund') NOT NULL,
    amount INT NOT NULL,
    transaction_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (auction_id) REFERENCES Auctions(id) ON DELETE CASCADE
);
