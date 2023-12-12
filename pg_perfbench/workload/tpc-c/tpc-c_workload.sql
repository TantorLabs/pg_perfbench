
\set c_w_id random(1, :scale)
\set c_d_id random(1, 10)
\set c_id random(1, 3000)
\set ol_i_id random(1, 100000)
\set ol_quantity random(1, 10)
\set o_all_local random(0, 1)
\set w_id random(1, :scale)
\set d_id random(1, 10)
\set o_id random(1, 3000)
\set no_o_id random(1, 3000)
\set h_amount random(1, 5000)
\set h_data random(1, 255)
\set o_carrier_id random(1, 10)
\set ol_total random(1, 100)
\set o_c_id random(1, 3000 * :scale)

DO $$
BEGIN
PERFORM c_discount, c_last, c_credit, w_tax
FROM customer, warehouse
WHERE w_id = :w_id AND c_w_id = w_id AND c_d_id = :d_id AND c_id = :c_id;

PERFORM d_tax, d_next_o_id
FROM district
WHERE d_id = :d_id AND d_w_id = :w_id
FOR UPDATE;

PERFORM i_price, i_name, i_data
FROM item
WHERE i_id = :ol_i_id;

PERFORM s_quantity, s_data, s_dist_01, s_dist_02, s_dist_03, s_dist_04, s_dist_05,
       s_dist_06, s_dist_07, s_dist_08, s_dist_09, s_dist_10
FROM stock
WHERE s_i_id = :ol_i_id AND s_w_id = :w_id
FOR UPDATE;

UPDATE stock
SET s_quantity = s_quantity - :ol_quantity
WHERE s_i_id = :ol_i_id AND s_w_id = :w_id;

IF :o_all_local = 0 THEN
    UPDATE district
    SET d_next_o_id = d_next_o_id + 1
    WHERE d_id = :d_id AND d_w_id = :w_id;
ELSE
    UPDATE district
    SET d_next_o_id = d_next_o_id + 1
    WHERE d_id = :d_id AND d_w_id = :w_id;
END IF;
END $$;

INSERT INTO new_order (no_o_id, no_d_id, no_w_id)
VALUES (:o_id, :d_id, :w_id)
ON CONFLICT DO NOTHING;




-- Payment Transaction

BEGIN;
SELECT c_balance, c_first, c_middle, c_last
FROM customer
WHERE c_w_id = :w_id AND c_d_id = :d_id AND c_id = :c_id
FOR UPDATE;

UPDATE customer
SET c_balance = c_balance - :h_amount, c_ytd_payment = c_ytd_payment + :h_amount,
    c_payment_cnt = c_payment_cnt + 1
WHERE c_w_id = :w_id AND c_d_id = :d_id AND c_id = :c_id;

SELECT w_street_1, w_street_2, w_city, w_state, w_zip, w_name
FROM warehouse
WHERE w_id = :w_id;

SELECT d_street_1, d_street_2, d_city, d_state, d_zip, d_name
FROM district
WHERE d_id = :d_id AND d_w_id = :w_id;

INSERT INTO history (h_c_id, h_c_d_id, h_c_w_id, h_d_id, h_w_id, h_date, h_amount, h_data)
VALUES (:c_id, :c_d_id, :c_w_id, :d_id, :w_id, current_timestamp, :h_amount, :h_data);

COMMIT;

-- Order Status Transaction
BEGIN;
SELECT c_balance, c_first, c_middle, c_last
FROM customer
WHERE c_w_id = :w_id AND c_d_id = :d_id AND c_id = :c_id;

SELECT o_id, o_carrier_id, o_entry_d, o_ol_cnt
FROM "order_o"
WHERE o_w_id = :w_id AND o_d_id = :d_id AND o_c_id = :c_id
ORDER BY o_id DESC
LIMIT 1;

SELECT ol_i_id, ol_supply_w_id, ol_quantity, ol_amount, ol_delivery_d
FROM order_line
WHERE ol_w_id = :w_id AND ol_d_id = :d_id AND ol_o_id = :o_id;

COMMIT;

-- Delivery Transaction
BEGIN;
SELECT no_o_id, no_d_id, no_w_id
FROM new_order
WHERE no_d_id = :d_id AND no_w_id = :w_id
ORDER BY no_o_id
LIMIT 1
FOR UPDATE;

DELETE FROM new_order
WHERE no_o_id = :no_o_id AND no_d_id = :d_id AND no_w_id = :w_id;

SELECT o_c_id
FROM "order_o"
WHERE o_id = :no_o_id AND o_d_id = :d_id AND o_w_id = :w_id;

UPDATE "order_o"
SET o_carrier_id = :o_carrier_id
WHERE o_id = :no_o_id AND o_d_id = :d_id AND o_w_id = :w_id;

UPDATE order_line
SET ol_delivery_d = current_timestamp
WHERE ol_o_id = :no_o_id AND ol_d_id = :d_id AND ol_w_id = :w_id;

SELECT SUM(ol_amount) AS ol_total
FROM order_line
WHERE ol_o_id = :no_o_id AND ol_d_id = :d_id AND ol_w_id = :w_id;

UPDATE customer
SET c_balance = c_balance + :ol_total
WHERE c_id = :o_c_id AND c_d_id = :d_id AND c_w_id = :w_id;

COMMIT;

