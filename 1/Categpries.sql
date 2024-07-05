CREATE TABLE categories (
    id SMALLINT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    categoryL1 VARCHAR(255),
    categoryL2 VARCHAR(255),
    categoryL3 VARCHAR(255),
    categoryL4 VARCHAR(255),
    categoryL5 VARCHAR(255),
    categoryL6 VARCHAR(255)
);

CREATE TABLE inventory_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    category_id SMALLINT,
    available_quantity INT NOT NULL,
    record_timestamp DATETIME NOT NULL,
    FOREIGN KEY (category_id) REFERENCES categories(id)
);
