DO $$ DECLARE v_debug_mode BOOLEAN := FALSE;

-- Trade-Order_Frame-1
v_acct_id BIGINT;

--input parameters
v_acct_name VARCHAR(50) [];

v_broker_id BIGINT [];

v_broker_name VARCHAR(49);

v_cust_f_name VARCHAR(20);

v_cust_id BIGINT;

v_cust_l_name VARCHAR(25);

v_cust_tier SMALLINT;

v_num_found INT = 0;

v_tax_id VARCHAR(20);

v_tax_status SMALLINT;

-----
rec_1_ RECORD;

v_ap_acl CHAR(4);

-- Trade-Order_Frame-2
-- v_acct_id BIGINT;
v_exec_f_name VARCHAR(20);

v_exec_l_name VARCHAR(20);

v_exec_tax_id VARCHAR(20);

-- Trade-Order_Frame-3
v_is_lifo BOOLEAN;

--- input parameters
v_issue CHAR(6);

--- input parameters
v_st_pending_id TEXT := 'Pending';

--- input parameters
v_st_submitted_id TEXT := 'Submitted';

--- input parameters
-- v_tax_status INTEGER := floor(random()*4);    --- input parameters
v_trade_qty INTEGER := floor(random() * 50) + 1;

--- input parameters
v_trade_type_id CHAR(3) := '';

--- input parameters
v_type_is_margin BOOLEAN;

--- input parameters
v_co_name VARCHAR(60);

--- input parameters
v_requested_price DECIMAL(8, 2);

--- input parameters
v_symbol CHAR(15) := '';

--- input parameters
v_buy_value DECIMAL(8, 2);

v_charge_amount DECIMAL(10, 2);

v_comm_rate DECIMAL(5, 2);

v_acct_assets DECIMAL(12, 2);

v_s_name VARCHAR(70) := '';

v_sell_value DECIMAL(8, 2);

v_status_id TEXT := '';

v_tax_amount DECIMAL(8, 2);

v_type_is_market BOOLEAN;

v_type_is_sell BOOLEAN;

v_market_price DECIMAL(8, 2);

v_hold_price DECIMAL(8, 2);

v_hold_qty INT;

v_needed_qty INT;

v_hs_qty INT;

-----
v_co_id BIGINT;

v_exch_id CHAR(6);

v_tax_rates DECIMAL(6, 5);

v_max_attempts int;

v_acct_bal DECIMAL(12, 2);

v_hold_assets DECIMAL(8, 2);

-- -- Trade-Order_Frame-4
v_now_dts TIMESTAMP;

v_trade_id BIGINT;

v_is_cash BOOLEAN;

v_exec_name VARCHAR(49);

v_comm_amount DECIMAL(10, 2) := random() * 2 + floor(random() * 90);

v_broker_id_v BIGINT;

BEGIN --generate v_acct_id 
v_max_attempts := 10;

LOOP
SELECT
    ca_id INTO v_acct_id
FROM
    CUSTOMER_ACCOUNT TABLESAMPLE system (5)
WHERE
    random() < 0.01
LIMIT
    1;

v_max_attempts := v_max_attempts - 1;

EXIT
WHEN v_acct_id IS NOT NULL
OR v_max_attempts = 0;

END LOOP;

if (v_acct_id is NULL) then
SELECT
    ca_id INTO v_acct_id
FROM
    CUSTOMER_ACCOUNT
order by
    random()
LIMIT
    1;

end if;

-- Trade-Order_Frame-1 Pseudo-code: Get customer, customer account, and broker
-- information
for rec_1_ in (
    select
        CA_NAME,
        CA_B_ID,
        CA_C_ID,
        CA_TAX_ST
    from
        CUSTOMER_ACCOUNT
    where
        CA_ID = v_acct_id
) loop v_acct_name = array_append(v_acct_name, rec_1_.CA_NAME);

v_broker_id = array_append(v_broker_id, rec_1_.CA_B_ID);

v_cust_id := rec_1_.CA_C_ID;

v_tax_status := rec_1_.CA_TAX_ST;

v_num_found := v_num_found + 1;

end loop;

select
    C_F_NAME,
    C_L_NAME,
    C_TIER,
    C_TAX_ID into v_cust_f_name,
    v_cust_l_name,
    v_cust_tier,
    v_tax_id
from
    CUSTOMER
where
    C_ID = v_cust_id;

if v_debug_mode then RAISE NOTICE ' -- -- Trade-Order_Frame-1: ';

RAISE NOTICE 'v_cust_id %',
v_cust_id;

end if;

select
    B_NAME into v_broker_name
from
    BROKER
where
    B_ID = ANY(v_broker_id);

if v_debug_mode then RAISE NOTICE 'v_broker_name %',
v_broker_name;

end if;

-- Trade-Order_Frame-2 Pseudo-code : Check executor's permission
---generate v_acct_id 
v_max_attempts := 10;

LOOP
SELECT
    ca_id INTO v_acct_id
FROM
    CUSTOMER_ACCOUNT TABLESAMPLE system (5)
WHERE
    random() < 0.01
LIMIT
    1;

v_max_attempts := v_max_attempts - 1;

EXIT
WHEN v_acct_id IS NOT NULL
OR v_max_attempts = 0;

END LOOP;

-- -- generate  v_exec_f_name v_exec_l_name v_exec_tax_id
select
    ap_f_name into v_exec_f_name
from
    account_permission
order by
    random()
limit
    1;

select
    ap_l_name into v_exec_l_name
from
    account_permission
where
    ap_f_name = v_exec_f_name
order by
    random()
limit
    1;

select
    ap_tax_id into v_exec_tax_id
from
    account_permission
where
    ap_f_name = v_exec_f_name
    and ap_l_name = v_exec_l_name
order by
    random()
limit
    1;

if (v_debug_mode) then RAISE NOTICE 'Trade-Order_Frame-2 v_exec_f_name v_exec_l_name v_exec_tax_id % % % ',
v_exec_f_name,
v_exec_l_name,
v_exec_tax_id;

end if;

--------
select
    AP_ACL into v_ap_acl
from
    ACCOUNT_PERMISSION
where
    AP_CA_ID = v_acct_id
    and AP_F_NAME = v_exec_f_name
    and AP_L_NAME = v_exec_l_name
    and AP_TAX_ID = v_exec_tax_id;

if v_debug_mode then RAISE NOTICE ' Trade-Order_Frame-2: ';

RAISE NOTICE 'v_acct_id v_cust_f_name v_cust_l_name v_tax_id % % % %',
v_acct_id,
v_cust_f_name,
v_cust_l_name,
v_tax_id;

end if;

-- -- -- Trade-Order_Frame-3 Pseudo-code: Estimate overall effects of the trade
---- generate random trade_type_id as input  
v_max_attempts := 10;

LOOP
SELECT
    tt_id INTO v_trade_type_id
FROM
    trade_type
order by
    random()
LIMIT
    1;

v_max_attempts := v_max_attempts - 1;

EXIT
WHEN v_trade_type_id != ''
OR v_max_attempts = 0;

END LOOP;

----random value determination between variables v_issue and v_symbol
v_max_attempts := 10;

if(floor(random() * 2) = 1) then ----generate v_symbol as input 
LOOP
SELECT
    s_symb INTO v_symbol
FROM
    SECURITY TABLESAMPLE system (5)
WHERE
    random() < 0.01
LIMIT
    1;

v_max_attempts := v_max_attempts - 1;

EXIT
WHEN v_symbol != ''
OR v_max_attempts = 0;

END LOOP;

else ----generate issue as input 
LOOP
SELECT
    s_issue INTO v_issue
FROM
    SECURITY TABLESAMPLE system (5)
WHERE
    random() < 0.01
LIMIT
    1;

v_max_attempts := v_max_attempts - 1;

EXIT
WHEN v_issue != ''
OR v_max_attempts = 0;

END LOOP;

end if;

----generate co_name as input 
v_max_attempts := 10;

LOOP
SELECT
    co_name INTO v_co_name
FROM
    company TABLESAMPLE system (5)
WHERE
    random() < 0.01
LIMIT
    1;

v_max_attempts := v_max_attempts - 1;

EXIT
WHEN v_co_name IS NOT NULL
OR v_max_attempts = 0;

END LOOP;

----
if v_debug_mode then RAISE NOTICE ' -- -- Trade-Order_Frame-3: ';

RAISE NOTICE 'v_co_name %',
v_co_name;

end if;

---generate type_is_margin as input
v_type_is_margin := random() >= 0.5;

if (v_symbol = '') then --// Get information on the security
select
    CO_ID into v_co_id
from
    Company
where
    CO_NAME = v_co_name;

select
    S_EX_ID,
    S_NAME,
    S_SYMB into v_exch_id,
    v_s_name,
    v_symbol
from
    SECURITY
where
    S_CO_ID = v_co_id
    and S_ISSUE = v_issue;

if v_debug_mode then RAISE NOTICE 'v_issue %',
v_issue;

RAISE NOTICE 'v_exch_id v_s_name v_symbol % % %',
v_exch_id,
v_s_name,
v_symbol;

end if;

else
select
    S_CO_ID,
    S_EX_ID,
    S_NAME into v_co_id,
    v_exch_id,
    v_s_name
from
    SECURITY
where
    S_SYMB LIKE v_symbol;

select
    co_name into v_co_name
from
    company
where
    co_id = v_co_id;

if v_debug_mode then RAISE NOTICE 'v_symbol %',
v_symbol;

RAISE NOTICE 'v_exch_id v_s_name v_symbol % % %',
v_exch_id,
v_s_name,
v_symbol;

end if;

end if;

---- // Get current pricing information for the security
select
    LT_PRICE into v_market_price
from
    last_trade
where
    LT_S_SYMB = v_symbol;

---- // Set trade characteristics based on the type of trade.    
select
    TT_IS_MRKT,
    TT_IS_SELL into v_type_is_market,
    v_type_is_sell
from
    TRADE_TYPE
where
    TT_ID = v_trade_type_id;

---- // If this is a limit-order, then the requested_price was passed in to the frame,
if(v_type_is_market) then v_requested_price = v_market_price;

end if;

-- --// Local frame variables used when estimating impact of this trade on
-- --// any current holdings of the same security.
v_buy_value := 0.0;

v_sell_value := 0.0;

v_needed_qty := v_trade_qty;

select
    HS_QTY into v_hs_qty
from
    HOLDING_SUMMARY
where
    HS_CA_ID = v_acct_id
    and HS_S_SYMB = v_symbol;

if (v_hs_qty is NULL) then v_hs_qty := 0;

end if;

if (v_type_is_sell) then if (v_hs_qty > 0) then for rec_1_ in (
    select
        H_QTY,
        H_PRICE
    from
        HOLDING
    where
        H_CA_ID = v_acct_id
        and H_S_SYMB = v_symbol
    ORDER BY
        CASE
            WHEN v_is_lifo THEN h_dts
        END DESC,
        h_dts ASC
) loop v_hold_qty := rec_1_.H_QTY;

v_hold_price := rec_1_.H_PRICE;

if (v_hold_qty > v_needed_qty) then v_buy_value := v_buy_value + v_needed_qty * v_hold_price;

v_sell_value := v_sell_value + v_needed_qty * v_requested_price;

v_needed_qty := 0;

else -- // All of this holding would be sold as a result of this trade.
v_buy_value := v_buy_value + v_hold_qty * v_hold_price;

v_sell_value := v_sell_value + v_hold_qty * v_requested_price;

v_needed_qty := v_needed_qty - v_hold_qty;

end if;

end loop;

end if;

else --(!type_is_sell)
-- -- // This is a buy transaction, so estimate the impact to any currently held
if (v_hs_qty < 0) then for rec_1_ in (
    select
        H_QTY,
        H_PRICE
    from
        HOLDING
    where
        H_CA_ID = v_acct_id
        and H_S_SYMB = v_symbol
    ORDER BY
        CASE
            WHEN v_is_lifo THEN h_dts
        END DESC,
        h_dts ASC
) loop v_hold_qty := rec_1_.H_QTY;

v_hold_price := rec_1_.H_PRICE;

if (v_hold_qty + v_needed_qty < 0) then v_buy_value := v_buy_value + v_needed_qty * v_hold_price;

v_sell_value := v_sell_value + v_needed_qty * v_requested_price;

v_needed_qty := 0;

else -- // All of this holding would be sold as a result of this trade.
v_hold_qty := - v_hold_qty;

v_buy_value := v_buy_value + v_hold_qty * v_hold_price;

v_sell_value := v_sell_value + v_hold_qty * v_requested_price;

v_needed_qty := v_needed_qty - v_hold_qty;

end if;

end loop;

end if;

end if;

if v_debug_mode then RAISE NOTICE 'v_buy_value v_sell_value v_needed_qty % % %',
v_buy_value,
v_sell_value,
v_needed_qty;

end if;

v_tax_amount = 0.0;

-- --// Estimate any capital gains tax that would be incurred as a result of this
-- --// transaction.
if (
    (v_sell_value > v_buy_value)
    and (
        (v_tax_status = 1)
        or (v_tax_status = 2)
    )
) then
select
    sum(TX_RATE) into v_tax_rates
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

v_tax_amount := (v_sell_value - v_buy_value) * v_tax_rates;

end if;

-- -- // Get administrative fees (e.g. trading charge, commision rate)
select
    CR_RATE into v_comm_rate
from
    COMMISSION_RATE
where
    CR_C_TIER = v_cust_tier
    and CR_TT_ID = v_trade_type_id
    and CR_EX_ID = v_exch_id
    and CR_FROM_QTY <= v_trade_qty
    and CR_TO_QTY >= v_trade_qty;

select
    CH_CHRG into v_charge_amount
from
    CHARGE
where
    CH_C_TIER = v_cust_tier
    and CH_TT_ID = v_trade_type_id;

-- -- // Compute assets on margin trades
v_acct_bal = 0.0;

if(v_type_is_margin) then
select
    CA_BAL into v_acct_bal
from
    CUSTOMER_ACCOUNT
where
    ca_id = v_acct_id;

-- // Should return 0 or 1 row
select
    sum(HS_QTY * LT_PRICE) into v_hold_assets
from
    HOLDING_SUMMARY,
    LAST_TRADE
where
    HS_CA_ID = v_acct_id
    and LT_S_SYMB = HS_S_SYMB;

end if;

if v_debug_mode then RAISE NOTICE 'v_hold_assets %',
v_hold_assets;

end if;

if (v_hold_assets is NULL) then
/* account currently has no holdings */
v_acct_assets := v_acct_bal;

else v_acct_assets := v_hold_assets + v_acct_bal;

end if;

-- -- // Set the status for this trade
if (v_type_is_market) then v_status_id := 'CMPT';

--v_st_submitted_id; --todo
else v_status_id := 'CMPT';

--v_st_pending_id; --todo
end if;

if v_debug_mode then RAISE NOTICE 'v_status_id %',
v_status_id;

end if;

-- --Pseudo-code: Record the trade request by making all
-- -- related updates
--generate broker_id as input 
v_max_attempts := 10;

LOOP
SELECT
    B_ID INTO v_broker_id_v
FROM
    broker
ORDER BY
    random()
LIMIT
    1;

v_max_attempts := v_max_attempts - 1;

EXIT
WHEN v_broker_id_v IS NOT NULL
OR v_max_attempts = 0;

END LOOP;

--generate exec_name as input 
v_max_attempts := 10;

LOOP
SELECT
    T_EXEC_NAME INTO v_exec_name
FROM
    TRADE TABLESAMPLE system (5)
WHERE
    random() < 0.01
LIMIT
    1;

v_max_attempts := v_max_attempts - 1;

EXIT
WHEN v_exec_name != ''
OR v_max_attempts = 0;

END LOOP;

---generate 
select
    LT_PRICE into v_requested_price
from
    LAST_TRADE
order by
    random()
LIMIT
    1;

-----
v_now_dts := NOW() :: timestamp;

v_is_cash := CASE
    WHEN random() < 0.5 THEN FALSE
    ELSE TRUE
END;

v_is_lifo := CASE
    WHEN random() < 0.5 THEN FALSE
    ELSE TRUE
END;

-- Generate a new t_id using the seq_trade_id sequence
SELECT
    NEXTVAL('seq_trade_id') INTO v_trade_id;

-- -- // Record trade information in TRADE table.
insert into
    TRADE (
        T_ID,
        T_DTS,
        T_ST_ID,
        T_TT_ID,
        T_IS_CASH,
        T_S_SYMB,
        T_QTY,
        T_BID_PRICE,
        T_CA_ID,
        T_EXEC_NAME,
        T_TRADE_PRICE,
        T_CHRG,
        T_COMM,
        T_TAX,
        T_LIFO
    )
values
    (
        v_trade_id,
        ---// T_ID --todo
        v_now_dts,
        -- // T_DTS
        v_status_id,
        -- // T_ST_ID
        v_trade_type_id,
        -- // T_TT_ID
        v_is_cash,
        -- // T_IS_CASH
        v_symbol,
        -- // T_S_SYMB
        v_trade_qty,
        -- // T_QTY
        v_requested_price,
        -- // T_BID_PRICE
        v_acct_id,
        -- // T_CA_ID
        v_exec_name,
        -- // T_EXEC_NAME
        NULL,
        -- // T_TRADE_PRICE
        v_charge_amount,
        --// T_CHRG
        v_comm_amount,
        --// T_COMM
        0,
        -- // T_TAX
        v_is_lifo --// T_LIFO
    );

if v_debug_mode then RAISE NOTICE 'v_trade_id %',
v_trade_id;

end if;

if(v_type_is_market = FALSE) then
insert into
    trade_request(
        TR_T_ID,
        TR_TT_ID,
        TR_S_SYMB,
        TR_QTY,
        TR_BID_PRICE,
        TR_B_ID
    )
values
(
        v_trade_id,
        --// TR_T-ID
        v_trade_type_id,
        --// TR_TT_ID
        v_symbol,
        --// TR_S_SYMB
        v_trade_qty,
        --// TR_QTY
        v_requested_price,
        --// TR_BID_PRICE
        v_broker_id_v
    );

end if;

-- -- // Record trade information in TRADE_HISTORY table.
insert into
    TRADE_HISTORY (TH_T_ID, TH_DTS, TH_ST_ID)
values
    (
        v_trade_id,
        -- // TH_T_ID
        v_now_dts,
        -- // TH_DTS
        v_status_id --// TH_ST_ID
    );

-- -- Trade-Order_Frame-5 Pseudo-code: Rollback database transaction
-- rollback transaction
-- -- Trade-Order Frame 6
-- commit transaction
EXCEPTION
WHEN NOT_NULL_VIOLATION THEN -- Intentionally ignoring the NOT NULL violation
if v_debug_mode then
    RAISE NOTICE 'column with value NULL ';
end if;

WHEN OTHERS THEN RAISE NOTICE 'An unspecified error occurred: %',
SQLERRM;

-- Additional handling code here
END $$ LANGUAGE plpgsql;