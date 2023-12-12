--definition of tables
CREATE TABLE warehouse (
    w_id INT PRIMARY KEY,
    w_name TEXT,
    w_street_1 TEXT,
    w_street_2 TEXT,
    w_city TEXT,
    w_state TEXT,
    w_zip TEXT,
    w_tax FLOAT,
    w_ytd FLOAT
);

CREATE TABLE district (
    d_id INT,
    d_w_id INT,
    d_name TEXT,
    d_street_1 TEXT,
    d_street_2 TEXT,
    d_city TEXT,
    d_state TEXT,
    d_zip TEXT,
    d_tax FLOAT,
    d_ytd FLOAT,
    d_next_o_id INT,
    PRIMARY KEY (d_id, d_w_id)
);

CREATE TABLE customer (
    c_id INT,
    c_d_id INT,
    c_w_id INT,
    c_first TEXT,
    c_middle TEXT,
    c_last TEXT,
    c_street_1 TEXT,
    c_street_2 TEXT,
    c_city TEXT,
    c_state TEXT,
    c_zip TEXT,
    c_phone TEXT,
    c_since TIMESTAMP,
    c_credit TEXT,
    c_credit_lim FLOAT,
    c_discount FLOAT,
    c_balance FLOAT,
    c_ytd_payment FLOAT,
    c_payment_cnt INT,
    c_delivery_cnt INT,
    c_data TEXT,
    PRIMARY KEY (c_id, c_d_id, c_w_id)
);

CREATE TABLE history (
    h_c_id INT,
    h_c_d_id INT,
    h_c_w_id INT,
    h_d_id INT,
    h_w_id INT,
    h_date TIMESTAMP,
    h_amount FLOAT,
    h_data TEXT
);

CREATE TABLE order_o (
    o_id INT,
    o_d_id INT,
    o_w_id INT,
    o_c_id INT,
    o_entry_d TIMESTAMP,
    o_carrier_id INT,
    o_ol_cnt INT,
    o_all_local INT,
    PRIMARY KEY (o_id, o_d_id, o_w_id)
);

CREATE TABLE new_order (
    no_o_id INT,
    no_d_id INT,
    no_w_id INT,
    PRIMARY KEY (no_o_id, no_d_id, no_w_id)
);

CREATE TABLE item (
    i_id INT PRIMARY KEY,
    i_im_id INT,
    i_name TEXT,
    i_price FLOAT,
    i_data TEXT
);

CREATE TABLE stock (
    s_i_id INT,
    s_w_id INT,
    s_quantity INT,
    s_dist_01 TEXT,
    s_dist_02 TEXT,
    s_dist_03 TEXT,
    s_dist_04 TEXT,
    s_dist_05 TEXT,
    s_dist_06 TEXT,
    s_dist_07 TEXT,
    s_dist_08 TEXT,
    s_dist_09 TEXT,
    s_dist_10 TEXT,
    s_ytd INT,
    s_order_cnt INT,
    s_remote_cnt INT,
    s_data TEXT,
    PRIMARY KEY (s_i_id, s_w_id)
);

CREATE TABLE order_line (
    ol_o_id INT NOT NULL,
    ol_d_id INT NOT NULL,
    ol_w_id INT NOT NULL,
    ol_number INT NOT NULL,
    ol_i_id INT NOT NULL,
    ol_supply_w_id INT NOT NULL,
    ol_delivery_d TIMESTAMPTZ,
    ol_quantity INT NOT NULL,
    ol_amount NUMERIC(6,2) NOT NULL,
    ol_dist_info VARCHAR(24) NOT NULL,
    PRIMARY KEY (ol_o_id, ol_d_id, ol_w_id, ol_number)
);

--indexes


CREATE INDEX idx_customer ON customer (c_w_id, c_d_id, c_last, c_first);
CREATE INDEX idx_customer_last ON customer (c_last, c_first, c_w_id, c_d_id);
CREATE INDEX idx_district ON district (d_w_id, d_id);
CREATE INDEX idx_history ON history (h_c_id, h_c_d_id, h_c_w_id);
CREATE INDEX idx_new_order ON new_order (no_w_id, no_d_id, no_o_id);
CREATE INDEX idx_order ON "order_o" (o_w_id, o_d_id, o_c_id);
CREATE INDEX idx_stock ON stock (s_w_id, s_i_id);
CREATE INDEX idx_warehouse ON warehouse (w_id);
CREATE INDEX order_line_fk ON order_line (ol_o_id, ol_d_id, ol_w_id);






--procedures

CREATE OR REPLACE FUNCTION get_new_order_id(IN w_id INT, IN d_id INT)
    RETURNS INT AS $$
    DECLARE
        next_o_id INT;
    BEGIN
        UPDATE district
        SET d_next_o_id = d_next_o_id + 1
        WHERE d_w_id = w_id AND d_id = d_id
        RETURNING d_next_o_id INTO next_o_id;
        RETURN next_o_id;
    END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION get_customer_balance(
    IN w_id INT, IN d_id INT, IN c_id INT,
    OUT c_balance FLOAT, OUT c_first TEXT, OUT c_middle TEXT, OUT c_last TEXT)
AS $$
BEGIN
    SELECT c_balance, c_first, c_middle, c_last
    INTO STRICT c_balance, c_first, c_middle, c_last
    FROM customer
    WHERE c_w_id = w_id AND c_d_id = d_id AND c_id = c_id;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION make_payment(
    IN w_id INT, IN d_id INT, IN c_id INT, IN payment FLOAT)
    RETURNS VOID AS $$
BEGIN
    UPDATE customer
    SET c_balance = c_balance - payment, c_ytd_payment = c_ytd_payment + payment,
        c_payment_cnt = c_payment_cnt + 1
    WHERE c_w_id = w_id AND c_d_id = d_id AND c_id = c_id;
    -- RETURN ;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION create_new_order(
    IN o_w_id INT, IN o_d_id INT, IN o_c_id INT, IN o_ol_cnt INT,
    IN o_all_local INT, OUT o_id INT, OUT o_entry_d TIMESTAMP)
AS $$
DECLARE
    new_order_id INT;
BEGIN
    SELECT get_new_order_id(o_w_id, o_d_id) INTO STRICT new_order_id;

    UPDATE district
    SET d_next_o_id = new_order_id
    WHERE d_w_id = o_w_id AND d_id = o_d_id;

    INSERT INTO "order_o" (o_id, o_d_id, o_w_id, o_c_id, o_entry_d, o_ol_cnt, o_all_local)
    VALUES (new_order_id, o_d_id, o_w_id, o_c_id, current_timestamp, o_ol_cnt, o_all_local);

    o_id := new_order_id;
    o_entry_d := current_timestamp;
END;
$$ LANGUAGE plpgsql;
