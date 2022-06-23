
CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT NOT NULL, hash TEXT NOT NULL, UNIQUE(username));
CREATE TABLE items (id INTEGER PRIMARY KEY, item TEXT NOT NULL, unit TEXT NOT NULL, category TEXT, UNIQUE(item));

CREATE TABLE purchase (id INTEGER PRIMARY KEY, item_id INTEGER NOT NULL, purchase_date DATE, best_before DATE, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (item_id) REFERENCES items(id));

CREATE TABLE item_quantity (id INTEGER PRIMARY KEY, purchase_id INTEGER, quantity NUMERIC, FOREIGN KEY (purchase_id) REFERENCES purchase(id));
CREATE TABLE recipes (id INTEGER PRIMARY KEY, name TEXT NOT NULL, count INTEGER NOT NULL, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE ingredients (id INTEGER PRIMARY KEY, item_id INTEGER, quantity NUMERIC, recipe_id INTEGER, FOREIGN KEY (item_id) REFERENCES items(id), FOREIGN KEY (recipe_id) REFERENCES recipe(id));



SELECT , SUM(quantity)
FROM purchase p
JOIN item_quantity iq ON p.id = iq.purchase_id
JOIN items i ON p.item_id = i.id
GROUP BY i.id WHERE