DO $$ DECLARE v_debug_mode BOOLEAN := FALSE;

v_acct_id BIGINT;

--input parameters
v_start_trade_dts TIMESTAMP;

--input parameters
v_end_trade_dts TIMESTAMP;

--input parameters
v_max_trades INT := floor(random() * 20) + 1;

--input parameters
v_max_updates INT := floor(random() * 20) + 1;

--input parameters
---pseudo-code declares vars
v_i INT;

--- used variables
v_bid_price_arr DECIMAL(8, 2) [];

v_exec_name_arr VARCHAR(49) [];

v_is_cash_arr BOOLEAN [];

v_trade_list_arr BIGINT [];

--t_id
v_trade_price_arr DECIMAL(8, 2) [];

v_num_found INT := 0;

v_num_updated INT := 0;

v_cash_type VARCHAR(40);

---
rec_1_ RECORD;

-----
v_max_attempts INT := 10;

BEGIN --generate acct_id from Customer accounts
-- generate acct_id as input 
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

IF(v_acct_id = NULL) THEN
SELECT
    ca_id INTO v_acct_id
FROM
    CUSTOMER_ACCOUNT
order by
    random()
LIMIT
    1;

END IF;

--
--generate start_trade_dts as input 
SELECT
    t_dts INTO v_start_trade_dts
from
    trade
where
    t_ca_id = v_acct_id
order by
    random()
limit
    1;

--generate end_trade_dts as input
v_end_trade_dts := v_start_trade_dts + ((floor(random() * 2) + 1) || ' days') :: INTERVAL;

--
if (v_debug_mode) then RAISE NOTICE 'v_acct_id, v_start_trade_dts, v_end_trade_dts % % %',
v_acct_id,
v_start_trade_dts,
v_end_trade_dts;

end if;

-- //Get trade information 
-- //Will return between 0 and max_trades rows
for rec_1_ IN(
    SELECT
        T_BID_PRICE,
        T_EXEC_NAME,
        T_IS_CASH,
        T_ID,
        T_TRADE_PRICE
    FROM
        TRADE
    WHERE
        T_CA_ID = v_acct_id
        AND T_DTS BETWEEN v_start_trade_dts
        AND v_end_trade_dts
    ORDER BY
        T_DTS ASC
    LIMIT
        v_max_trades
) LOOP v_bid_price_arr = array_append(v_bid_price_arr, rec_1_.T_BID_PRICE);

v_exec_name_arr = array_append(v_exec_name_arr, rec_1_.T_EXEC_NAME);

v_is_cash_arr = array_append(v_is_cash_arr, rec_1_.T_IS_CASH);

v_trade_list_arr = array_append(v_trade_list_arr, rec_1_.T_ID);

v_trade_price_arr = array_append(v_trade_price_arr, rec_1_.T_TRADE_PRICE);

v_num_found := v_num_found + 1;

-- -- // Get extra information for each trade in the trade list
if (v_num_updated < v_max_updates) then
select
    se_cash_type into v_cash_type
from
    SETTLEMENT
where
    SE_T_ID = rec_1_.T_ID;

if (rec_1_.T_IS_CASH) then IF v_cash_type = 'Cash Account' THEN v_cash_type := 'Cash';

ELSE v_cash_type := 'Cash Account';

END IF;

else IF v_cash_type = 'Margin Account' THEN v_cash_type := 'Margin';

ELSE v_cash_type := 'Margin Account';

END IF;

end if;

update
    settlement
set
    se_cash_type = v_cash_type
where
    se_t_id = rec_1_.T_ID;

v_num_updated := v_num_updated + 1;

end if;

-- --// Get settlement information
-- --// Will return only one row for each trade
PERFORM -- settlement_amount[i] = SE_AMT,   --todo, while perform
-- settlement_cash_due_date[i] = SE_CASH_DUE_DATE,  --todo, while perform
-- settlement_cash_type[i] = SE_CASH_TYPE   --todo, while perform
SE_AMT,
SE_CASH_DUE_DATE,
SE_CASH_TYPE
from
    SETTLEMENT
where
    SE_T_ID = rec_1_.T_ID;

-- -- // get cash information if this is a cash transaction
-- -- // Should return only one row for each trade that was a cash transaction
if (rec_1_.T_IS_CASH) then PERFORM -- cash_transaction_amount[i] = CT_AMT, --todo, while perform
-- cash_transaction_dts[i] = CT_DTS --todo, while perform
-- cash_transaction_name[i] = CT_NAME --todo, while perform
CT_AMT,
CT_DTS,
CT_NAME
from
    CASH_TRANSACTION
where
    CT_T_ID = rec_1_.T_ID;

end if;

-- -- // read trade_history for the trades
-- -- // Will return 2 or 3 rows per trade
PERFORM -- trade_history_dts[i][] = TH_DTS,--todo, while perform
-- trade_history_status_id[i][] = TH_ST_ID--todo, while perform
TH_DTS,
TH_ST_ID
from
    TRADE_HISTORY
where
    TH_T_ID = rec_1_.T_ID
order by
    TH_DTS;

END LOOP;

END $$ LANGUAGE plpgsql;