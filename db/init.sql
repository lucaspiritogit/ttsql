CREATE TABLE sales (
    date DATE,
    week_day TEXT,
    hour TEXT,
    ticket_number TEXT,
    waiter TEXT,
    product_name TEXT,
    quantity FLOAT,
    unitary_price NUMERIC,
    total NUMERIC
);

COPY sales(date, week_day, hour, ticket_number, waiter, product_name, quantity, unitary_price, total)
FROM '/seed/data.csv'
WITH (
    FORMAT csv,
    HEADER true
);