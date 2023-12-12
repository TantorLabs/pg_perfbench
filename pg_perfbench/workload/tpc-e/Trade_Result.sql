DO $$ DECLARE v_debug_mode BOOLEAN := FALSE;

--Trade-Result_Frame-1
v_trade_id BIGINT;

v_max_attempts INTEGER := 10;

v_acct_id BIGINT;

v_type_id CHAR(3);

v_symbol CHAR(15);

v_hs_qty INTEGER;

v_trade_is_cash BOOLEAN;

-- Trade-Result_Frame-2
-- input variables
--   v_acct_id BIGINT;
--   v_hs_qty INTEGER;
v_is_lifo BOOLEAN;

--   v_symbol CHAR(15);
--   v_trade_id INT;
v_trade_price DECIMAL(8, 2);

v_trade_qty INTEGER;

v_type_is_sell BOOLEAN;

v_type_name VARCHAR(12);

v_type_is_mrkt BOOLEAN;

-- output variables
v_broker_id BIGINT;

v_cust_id BIGINT;

--   v_sell_value NUMERIC;
v_tax_status SMALLINT;

v_trade_dts TIMESTAMP;

--    v_trade_price DECIMAL(8,2); 
-- additional declared variables from pseudocode
v_hold_id BIGINT;

v_hold_price DECIMAL(8, 2);

v_hold_qty INT;

v_needed_qty INT;

-- Initialize variables
v_buy_value NUMERIC := 0.0;

v_sell_value NUMERIC := 0.0;

--
hold_rec RECORD;

v_last_trade_id BIGINT;

--   v_max_attempts INT := 10;
-- Trade-Result_Frame-3
v_tax_rates DECIMAL(6, 5);

v_tax_amount INT := 0;

-- Trade-Result_Frame-4
v_comm_rate DECIMAL(5, 2);

v_s_name VARCHAR(70);

v_c_tier SMALLINT;

v_s_ex_id CHAR(6);

-- Trade-Result_Frame-6 
v_cash_type char(40);

v_str_fr_6 VARCHAR(100);

BEGIN -- Генерация trade_dts
v_trade_dts := NOW() :: timestamp;

-- Генерация v_trade_id
LOOP
SELECT
    t_id INTO v_trade_id
FROM
    TRADE TABLESAMPLE SYSTEM (5)
WHERE
    random() < 0.01
LIMIT
    1;

v_max_attempts := v_max_attempts - 1;

EXIT
WHEN v_trade_id IS NOT NULL
OR v_max_attempts = 0;

END LOOP;

--- generate trade price 
v_max_attempts = 10;

LOOP
SELECT
    h_price INTO v_trade_price
FROM
    holding TABLESAMPLE SYSTEM (5)
WHERE
    random() < 0.01
LIMIT
    1;

v_max_attempts := v_max_attempts - 1;

EXIT
WHEN v_trade_id IS NOT NULL
OR v_max_attempts = 0;

END LOOP;

if v_debug_mode then RAISE NOTICE 'v_trade_id %',
v_trade_id;

RAISE NOTICE 'v_trade_price %',
v_trade_price;

end if;

--Trade-Result_Frame-1 Pseudo-code: Get info on the trade and the customer's account
-- 
SELECT
    -- acct_id = T_CA_ID,
    -- type_id = T_TT_ID,
    -- symbol = T_S_SYMB,
    -- trade_qty = T_QTY,
    -- charge = T_CHRG,
    -- is_lifo = T_LIFO,
    -- trade_is_cash = T_IS_CASH
    T_CA_ID,
    T_TT_ID,
    T_S_SYMB,
    T_LIFO,
    T_QTY,
    T_IS_CASH INTO v_acct_id,
    v_type_id,
    v_symbol,
    v_is_lifo,
    v_trade_qty,
    v_trade_is_cash
FROM
    TRADE
WHERE
    T_ID = v_trade_id;

SELECT
    -- type_name = TT_NAME,
    -- type_is_sell = TT_IS_SELL,
    -- type_is_market = TT_IS_MRKT
    TT_NAME,
    TT_IS_SELL,
    TT_IS_MRKT INTO v_type_name,
    v_type_is_sell,
    v_type_is_mrkt
FROM
    TRADE_TYPE
WHERE
    TT_ID = v_type_id;

SELECT
    -- hs_qty = HS_QTY  
    HS_QTY INTO v_hs_qty
FROM
    HOLDING_SUMMARY
WHERE
    HS_CA_ID = v_acct_id
    AND HS_S_SYMB = v_symbol;

IF (v_hs_qty is NULL) THEN v_hs_qty := 0;

END IF;

-- -- -- Trade-Result_Frame-2 Pseudo-code: Update the customer's holdings for buy or sell
v_needed_qty := v_trade_qty;

select
    CA_B_ID,
    CA_C_ID,
    CA_TAX_ST INTO v_broker_id,
    v_cust_id,
    v_tax_status
from
    CUSTOMER_ACCOUNT
where
    CA_ID = v_acct_id;

if (v_type_is_sell) then if (v_hs_qty = 0) then
INSERT INTO
    HOLDING_SUMMARY (HS_CA_ID, HS_S_SYMB, HS_QTY)
VALUES
    (v_acct_id, v_symbol, - v_trade_qty);

else if (v_hs_qty != v_trade_qty) then
update
    holding_summary
set
    HS_QTY = v_hs_qty - v_trade_qty
where
    HS_CA_ID = v_acct_id
    and hs_s_symb = v_symbol;

end if;

end if;

if v_debug_mode then RAISE NOTICE 'hs_qty %',
v_hs_qty;

RAISE NOTICE 'v_is_lifo %',
v_is_lifo;

RAISE NOTICE 'v_acct_id %',
v_acct_id;

RAISE NOTICE 'h_s_symb %',
v_symbol;

end if;

-- -- //sell trade
-- -- //  First look for existing holdings, H_QTY > 0 --todo
if (v_hs_qty > 0) then for hold_rec in (
    SELECT
        h_t_id,
        h_qty,
        h_price
    FROM
        holding
    WHERE
        h_ca_id = v_acct_id
        AND h_s_symb = v_symbol
    ORDER BY
        CASE
            WHEN v_is_lifo THEN h_dts
        END DESC,
        h_dts ASC
) LOOP v_hold_id := hold_rec.h_t_id;

v_hold_qty := hold_rec.h_qty;

v_hold_price := hold_rec.h_price;

if v_debug_mode then RAISE NOTICE 'v_hold_id %',
v_hold_id;

end if;

IF v_hold_qty > v_needed_qty THEN -- Selling part of holdings
INSERT INTO
    holding_history (hh_h_t_id, hh_t_id, hh_before_qty, hh_after_qty)
VALUES
    (
        v_hold_id,
        v_trade_id,
        v_hold_qty,
        v_hold_qty - v_needed_qty
    ) ON CONFLICT (HH_H_T_ID, HH_T_ID) DO NOTHING;

UPDATE
    holding
SET
    h_qty = h_qty - v_needed_qty
WHERE
    h_t_id = hold_rec.h_t_id;

v_buy_value := v_buy_value + v_needed_qty * v_hold_price;

v_sell_value := v_sell_value + v_needed_qty * v_trade_price;

v_needed_qty := 0;

ELSE -- Selling all holdings
INSERT INTO
    holding_history (hh_h_t_id, hh_t_id, hh_before_qty, hh_after_qty)
VALUES
    (v_hold_id, v_trade_id, v_hold_qty, 0) ON CONFLICT (HH_H_T_ID, HH_T_ID) DO NOTHING;

DELETE FROM
    holding
WHERE
    h_t_id = v_hold_id;

v_buy_value := v_buy_value + v_hold_qty * v_hold_price;

v_sell_value := v_sell_value + v_hold_qty * v_trade_price;

v_needed_qty := v_needed_qty - v_hold_qty;

END IF;

END LOOP;

end if;

if v_debug_mode then RAISE NOTICE 'v_hold_id %',
v_hold_id;

end if;

-- // Sell Short:
-- // If needed_qty > 0 then customer has sold all existing
-- // holdings and customer is selling short. A new HOLDING
-- // record will be created with H_QTY set to the negative
-- // number of needed shares.
IF v_needed_qty > 0
and v_hold_id != NULL THEN
INSERT INTO
    holding_history (hh_h_t_id, hh_t_id, hh_before_qty, hh_after_qty)
VALUES
    (v_hold_id, v_trade_id, 0, - v_needed_qty);

---todo
INSERT INTO
    holding (h_t_id, h_ca_id, h_s_symb, h_dts, h_price, h_qty)
VALUES
    (
        v_trade_id,
        v_acct_id,
        v_symbol,
        v_trade_dts,
        v_trade_price,
        - v_needed_qty
    );

ELSE IF v_hs_qty = v_trade_qty THEN
DELETE FROM
    holding_summary
WHERE
    hs_ca_id = v_acct_id
    AND hs_s_symb = v_symbol;

END IF;

END IF;

else --// The trade is a BUY !v_type_is_sell
if v_debug_mode then RAISE NOTICE 'The trade is a BUY';

end if;

if (v_hs_qty = 0) then --// no prior holdings exist, but one will be inserted
insert into
    HOLDING_SUMMARY (
        HS_CA_ID,
        HS_S_SYMB,
        HS_QTY
    )
values
    (
        v_acct_id,
        v_symbol,
        v_trade_qty
    );

else --// hs_qty != 0
if (- v_hs_qty != v_trade_qty) then
update
    HOLDING_SUMMARY
set
    HS_QTY = hs_qty + v_trade_qty
where
    HS_CA_ID = v_acct_id
    and HS_S_SYMB = v_symbol;

end if;

end if;

--     -- -- // Short Cover:
--     -- -- // First look for existing negative holdings, H_QTY < 0,
--     -- -- // which indicates a previous short sell. The buy trade
--     -- -- // will cover the short sell.
if (v_hs_qty < 0) then FOR hold_rec IN (
    SELECT
        *
    FROM
        holding
    WHERE
        h_ca_id = v_acct_id
        AND h_s_symb = v_symbol
    ORDER BY
        CASE
            WHEN v_is_lifo THEN h_dts
        END DESC,
        h_dts ASC
) LOOP v_hold_id := hold_rec.h_t_id;

v_hold_qty := hold_rec.h_qty;

v_hold_price := hold_rec.h_price;

IF v_hold_qty + v_needed_qty < 0 THEN -- покупка части короткой позиции
INSERT INTO
    holding_history (
        HH_H_T_ID,
        HH_T_ID,
        HH_BEFORE_QTY,
        HH_AFTER_QTY
    )
VALUES
    (
        v_hold_id,
        --- // H_T_ID original trade
        v_trade_id,
        --- // T_ID current trade
        v_hold_qty,
        --- // H_QTY now
        v_hold_qty + v_needed_qty --// H_QTY after update
    ) ON CONFLICT (HH_H_T_ID, HH_T_ID) DO NOTHING;

UPDATE
    holding
SET
    h_qty = h_qty + v_needed_qty
WHERE
    h_t_id = v_hold_id;

-- расчет стоимостей
v_sell_value := v_sell_value + v_needed_qty * v_hold_price;

v_buy_value := v_buy_value + v_needed_qty * v_trade_price;

v_needed_qty := 0;

ELSE -- покупка всей короткой позиции
INSERT INTO
    holding_history (
        HH_H_T_ID,
        HH_T_ID,
        HH_BEFORE_QTY,
        HH_AFTER_QTY
    )
VALUES
    (
        v_hold_id,
        --// H_T_ID original trade
        v_trade_id,
        --- // T_ID current trade
        v_hold_qty,
        --- // H_QTY now
        0 ---// H_QTY after delete
    ) ON CONFLICT (HH_H_T_ID, HH_T_ID) DO NOTHING;

DELETE FROM
    holding
WHERE
    h_t_id = v_hold_id;

-- расчет стоимостей
v_hold_qty := - v_hold_qty;

v_sell_value := v_sell_value + abs(v_hold_qty) * v_hold_price;

v_buy_value := v_buy_value + abs(v_hold_qty) * v_trade_price;

v_needed_qty := v_needed_qty - abs(hold_rec.h_qty);

END IF;

END LOOP;

if v_debug_mode then RAISE NOTICE ' -- -- // Short Cover: ';

RAISE NOTICE 'v_sell_value v_buy_value v_needed_qty % % %',
v_sell_value,
v_buy_value,
v_needed_qty;

end if;

end if;

---/v_hs_qty < 0  
-- -- -- if !v_type_is_sell
if (
    v_needed_qty > 0
    and v_hold_id != NULL
) then
insert into
    holding_history(
        HH_H_T_ID,
        HH_T_ID,
        HH_BEFORE_QTY,
        HH_AFTER_QTY
    )
values
    (
        v_hold_id,
        -- // T_ID current is original trade
        v_trade_id,
        --//* T_ID current trade
        0,
        --// H_QTY before
        v_needed_qty -- // H_QTY after insert
    );

insert into
    HOLDING (
        H_T_ID,
        H_CA_ID,
        H_S_SYMB,
        H_DTS,
        H_PRICE,
        H_QTY
    )
values
    (
        v_trade_id,
        --// H_T_ID
        v_acct_id,
        --// H_CA_ID
        v_symbol,
        --// H_S_SYMB
        v_trade_dts,
        --// H_DTS
        v_trade_price,
        --// H_PRICE
        v_needed_qty --// H_QTY
    );

else if(- v_hs_qty = v_trade_qty) then
delete from
    HOLDING_SUMMARY
where
    HS_CA_ID = v_acct_id
    and HS_S_SYMB = v_symbol;

end if;

end if;

END IF;

--- -- -- Trade-Result_Frame-3 Pseudo-code: Compute and record the tax liability
select
    SUM(TX_RATE) into v_tax_rates
from
    TAXRATE
where
    TX_ID in (
        select
            CX_TX_ID
        from
            CUSTOMER_TAXRATE
        where
            CX_C_ID = v_cust_id
    );

v_tax_amount = (v_sell_value - v_buy_value) * v_tax_rates;

-- UPDATE TRADE 
-- SET T_TAX = v_tax_amount
-- WHERE T_ID = v_trade_id;
-- -- Trade-Result_Frame-4 Pseudo-code: Compute and record the broker's commission
SELECT
    S_EX_ID,
    --todo 
    S_NAME INTO v_s_ex_id,
    v_s_name
FROM
    SECURITY
where
    S_SYMB = v_symbol;

select
    C_TIER into v_c_tier
from
    CUSTOMER
where
    C_ID = v_cust_id;

-- -- // Only want 1 commission rate row
select
    cr_rate into v_comm_rate
from
    commission_rate
where
    CR_C_TIER = v_c_tier
    and CR_TT_ID = v_type_id
    and CR_EX_ID = v_s_ex_id
    and CR_FROM_QTY <= v_trade_qty
    and CR_FROM_QTY >= v_trade_qty;

-- Trade-Result_Frame-5 Pseudo-code: Record the trade result and the broker's
-- commission
-- update
-- TRADE
-- set
--     T_COMM = v_comm_amount,
--     T_DTS = v_trade_dts,
--     T_ST_ID = v_st_completed_id,
--     T_TRADE_PRICE = v_trade_price
-- where
-- T_ID = trade_id;
-- insert into
-- TRADE_HISTORY (
-- TH_T_ID,
-- TH_DTS,
-- TH_ST_ID
-- )
-- values (
-- trade_id,
-- trade_dts,
-- st_completed_id
-- )
-- update
-- BROKER
-- set
-- B_COMM_TOTAL = B_COMM_TOTAL + comm_amount,
-- B_NUM_TRADES = B_NUM_TRADES + 1
-- where
-- B_ID = broker_id
-- -- Trade-Result_Frame-6 Pseudo-code: Settle the trade
if (v_trade_is_cash) then v_cash_type = 'Cash Account';

else v_cash_type = 'Margin';

end if;

-- insert into --todo
--     SETTLEMENT (
--     SE_T_ID,
--     SE_CASH_TYPE,
--     SE_CASH_DUE_DATE,
--     SE_AMT
--     )
--     values (
--     v_trade_id,
--     v_cash_type,
--     -- due_date,
--     -- se_amount
--     0, 
--     0
--     );
if (v_trade_is_cash) then
update
    CUSTOMER_ACCOUNT
set
    CA_BAL = CA_BAL + 5 --se_amount
where
    CA_ID = v_acct_id;

v_str_fr_6 := v_type_name || ' ' || v_trade_qty || ' shares of ' || v_s_name;

insert into
    CASH_TRANSACTION (
        CT_DTS,
        CT_T_ID,
        CT_AMT,
        CT_NAME
    )
values
    (
        v_trade_dts,
        v_trade_id,
        0,
        -- v_se_amount,
        v_str_fr_6
    ) ON CONFLICT(CT_T_ID) DO NOTHING;

end if;

perform CA_BAL
from
    CUSTOMER_ACCOUNT
where
    CA_ID = v_acct_id;

END $$ LANGUAGE plpgsql;