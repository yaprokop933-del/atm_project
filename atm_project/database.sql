CREATE DATABASE IF NOT EXISTS atm_db;
USE atm_db;

CREATE TABLE Clients (
    id_client INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20)
);

CREATE TABLE Accounts (
    id_account INT AUTO_INCREMENT PRIMARY KEY,
    id_client INT NOT NULL,
    balance DECIMAL(15,2) DEFAULT 0.00,
    FOREIGN KEY (id_client) REFERENCES Clients(id_client)
);

CREATE TABLE Cards (
    id_card INT AUTO_INCREMENT PRIMARY KEY,
    id_account INT NOT NULL,
    card_number VARCHAR(16) UNIQUE NOT NULL,
    pin_hash VARCHAR(255) NOT NULL,
    status ENUM('active', 'blocked') DEFAULT 'active',
    failed_attempts INT DEFAULT 0,
    FOREIGN KEY (id_account) REFERENCES Accounts(id_account)
);

CREATE TABLE Transactions (
    id_transaction INT AUTO_INCREMENT PRIMARY KEY,
    id_card INT NOT NULL,
    trans_type ENUM('withdraw', 'deposit', 'balance_check') NOT NULL,
    amount DECIMAL(15,2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_card) REFERENCES Cards(id_card)
);
