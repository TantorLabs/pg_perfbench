DO $$ DECLARE stock_list REFCURSOR;

v_debug_mode BOOLEAN := FALSE;

v_acct_id BIGINT := 43000000886;

v_cust_id BIGINT;

v_ending_co_id BIGINT;

v_industry_name VARCHAR(50);

v_start_date DATE;

v_starting_co_id BIGINT;

-- v_pct_change DECIMAL(8,2); 
v_case_c INT := floor(random() * 3) + 1;

---  1 - cust_id; 2 - industry_name; 3 - acct_id; 
v_old_mkt_cap DECIMAL(20, 2) := 0.0;

v_new_mkt_cap DECIMAL(20, 2) := 0.0;

v_pct_change DECIMAL(20, 2) := 0.0;

v_symbol CHAR(15) := '';

v_max_attempts INT;

---
v_new_price DECIMAL(8, 2);

v_s_num_out BIGINT;

v_old_price DECIMAL(8, 2);

BEGIN --generate start_dte as input 
select
    dm_date into v_start_date
from
    daily_market
order by
    random()
limit
    1;

if v_debug_mode then RAISE NOTICE 'v_start_date %',
v_start_date;

end if;

-------
if (v_case_c = 1) then -- generate cust_id as input 
SELECT
    co_id INTO v_cust_id
FROM
    COMPANY
order by
    random()
LIMIT
    1;

----------
if v_debug_mode then RAISE NOTICE 'v_case_c v_cust_id : % %',
v_case_c,
v_cust_id;

end if;

----------
OPEN stock_list FOR
SELECT
    WI_S_SYMB
FROM
    WATCH_ITEM,
    WATCH_LIST
WHERE
    WI_WL_ID = WL_ID
    AND WL_C_ID = v_cust_id;

ELSEIF (v_case_c = 2) then -- generate v_starting_co_id as input 
SELECT
    co_id INTO v_starting_co_id
FROM
    COMPANY
order by
    random()
LIMIT
    1;

----------
-- generate v_ending_co_id as input 
SELECT
    co_id INTO v_ending_co_id
FROM
    COMPANY
where
    co_id > v_starting_co_id
order by
    random()
LIMIT
    1;

----------
-- generate industry_name as input 
SELECT
    IN_NAME INTO v_industry_name
FROM
    INDUSTRY
order by
    random()
LIMIT
    1;

---------- 
if v_debug_mode then RAISE NOTICE 'v_case_c v_industry_name v_starting_co_id v_ending_co_id  : % % % %',
v_case_c,
v_industry_name,
v_starting_co_id,
v_ending_co_id;

end if;

OPEN stock_list FOR
SELECT
    S_SYMB
FROM
    INDUSTRY,
    COMPANY,
    SECURITY
WHERE
    IN_NAME = v_industry_name
    AND CO_IN_ID = IN_ID
    AND CO_ID BETWEEN v_starting_co_id
    AND v_ending_co_id
    AND S_CO_ID = CO_ID;

ELSEIF (v_case_c = 3) then -- generate ca_id as input --todo
-- SELECT
--     ca_id INTO v_acct_id
-- FROM
--     CUSTOMER_ACCOUNT
-- order by
--     random()
-- LIMIT
--     1;
-- v_max_attempts := 10; 
-- LOOP
-- SELECT
--     ca_id INTO v_acct_id
-- FROM
--     CUSTOMER_ACCOUNT TABLESAMPLE system (5)
-- WHERE
--     random() < 0.01
-- LIMIT
--     1;
-- v_max_attempts := v_max_attempts - 1;
-- EXIT WHEN v_acct_id IS NOT NULL OR v_max_attempts = 0;
-- END LOOP;
-----------
if v_debug_mode then RAISE NOTICE 'v_case_c v_acct_id : % % ',
v_case_c,
v_acct_id;

end if;

OPEN stock_list FOR
SELECT
    HS_S_SYMB
FROM
    HOLDING_SUMMARY
WHERE
    HS_CA_ID = v_acct_id;

end if;

v_old_mkt_cap = 0.0;

v_new_mkt_cap = 0.0;

v_pct_change = 0.0;

-- OPEN stock_list;
LOOP FETCH stock_list INTO v_symbol;

EXIT
WHEN NOT FOUND;

if v_debug_mode then RAISE NOTICE 'v_symbol : %',
v_symbol;

end if;

select
    LT_PRICE into v_new_price
from
    last_trade
where
    lt_s_symb = v_symbol;

select
    S_NUM_OUT into v_s_num_out
from
    security
where
    s_symb = v_symbol;

select
    DM_CLOSE into v_old_price
from
    daily_market
where
    dm_s_symb = v_symbol
    and dm_date = v_start_date;

if v_debug_mode then RAISE NOTICE 'v_new_price v_s_num_out v_old_price: % % %',
v_new_price,
v_s_num_out,
v_old_price;

end if;

v_old_mkt_cap := v_old_mkt_cap + v_s_num_out * v_old_price;

v_new_mkt_cap := v_new_mkt_cap + v_s_num_out * v_new_price;

END LOOP;

if (v_old_mkt_cap != 0) then v_pct_change = 100 * (v_new_mkt_cap / v_old_mkt_cap - 1);

else v_pct_change = 0.0;

end if;

CLOSE stock_list;

END $$ LANGUAGE plpgsql;