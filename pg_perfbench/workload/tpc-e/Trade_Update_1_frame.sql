DO $$ DECLARE v_debug_mode BOOLEAN := FALSE;

v_max_trades INT := floor(random() * 20) + 1;

--input parameters
v_max_updates INT;

--input parameters, <= v_max_trades
v_trade_id_arr BIGINT [];

-- input parameters, size - v_max_trades
rec RECORD;

--todo
rec_1_ RECORD;

--todo
v_ex_name CHAR(49);

------------------------
v_num_updated INT := 0;

v_num_trades INT := 0;

-- idx for external cycle on v_max_trades
v_num_found INT := 0;

------------------------
v_bid_price_arr DECIMAL(8, 2) [];

v_exec_name_arr VARCHAR(49) [];

v_is_cash_arr BOOLEAN [];

v_is_market_arr BOOLEAN [];

v_trade_price_arr DECIMAL(8, 2) [];

BEGIN v_max_updates := floor(random() * (v_max_trades - 1)) + 1;

-- Trade-Update_Frame-1
FOR rec IN(
    SELECT
        t_id
    FROM
        TRADE
    order by
        random()
    LIMIT
        v_max_trades
) LOOP -- v_trade_id_arr := array_append(v_trade_id_arr, rec.T_ID);
v_num_trades := v_num_trades + 1;

IF (v_debug_mode) THEN RAISE NOTICE 'loop on v_max_trades %',
v_max_trades;

END IF;

IF (v_num_updated < v_max_updates) THEN
SELECT
    t_exec_name INTO v_ex_name
FROM
    TRADE
WHERE
    T_ID = rec.T_ID;

IF (v_ex_name LIKE '% X %') THEN v_ex_name := REPLACE (v_ex_name, ' X ', ' ');

ELSE v_ex_name := REPLACE (v_ex_name, '  ', ' X ');

END IF;

UPDATE
    TRADE
SET
    t_exec_name = v_ex_name
WHERE
    T_ID = rec.T_ID;

v_num_updated := v_num_updated + 1;

--todo
IF (v_debug_mode) THEN RAISE NOTICE 'loop on v_max_updates %',
v_num_updated;

END IF;

END IF;

---- // Will only return one row for each trade
for rec_1_ IN(
    SELECT
        T_BID_PRICE,
        T_EXEC_NAME,
        T_IS_CASH,
        TT_IS_MRKT,
        T_TRADE_PRICE
    FROM
        TRADE,
        TRADE_TYPE
    WHERE
        T_ID = rec.T_ID
        AND T_TT_ID = TT_ID
) LOOP v_bid_price_arr = array_append(v_bid_price_arr, rec_1_.T_BID_PRICE);

v_exec_name_arr = array_append(v_exec_name_arr, rec_1_.T_EXEC_NAME);

v_is_cash_arr = array_append(v_is_cash_arr, rec_1_.T_IS_CASH);

v_is_market_arr = array_append(v_is_market_arr, rec_1_.TT_IS_MRKT);

v_trade_price_arr = array_append(v_trade_price_arr, rec_1_.T_TRADE_PRICE);

END LOOP;

-- --// Get settlement information
-- --// Will only return one row for each trade
PERFORM -- settlement_amount[i] = SE_AMT,
-- settlement_cash_due_date[i] = SE_CASH_DUE_DATE,
-- settlement_cash_type[i] = SE_CASH_TYPE
SE_AMT,
SE_CASH_DUE_DATE,
SE_CASH_TYPE
from
    SETTLEMENT
where
    SE_T_ID = rec.T_ID;

-- --// get cash information if this is a cash transaction
-- --// Will only return one row for each trade that was a cash transaction
-- --todo
IF (v_is_cash_arr [v_num_trades]) THEN PERFORM CT_AMT,
CT_DTS,
CT_NAME
FROM
    CASH_TRANSACTION
where
    CT_T_ID = rec.t_id;

END IF;

-- --// read trade_history for the trades
-- --// Will return 2 or 3 rows per trade
PERFORM -- trade_history_dts[i][] = TH_DTS,
-- trade_history_status_id[i][] = TH_ST_ID 
TH_DTS,
TH_ST_ID
from
    trade_history
WHERE
    TH_T_ID = rec.T_ID
ORDER BY
    TH_DTS
LIMIT
    3;

END LOOP;

--commit transaction
IF (v_debug_mode) THEN RAISE NOTICE 'random num %',
v_max_trades;

END IF;

END $$ LANGUAGE plpgsql;