DO $$ DECLARE v_debug_mode BOOLEAN := FALSE;

v_acct_id BIGINT;

-- --input parameters
v_end_trade_dts TIMESTAMP;

-- --input parameters
v_max_trades INT := floor(random() * 20) + 1;

-- --input parameters
v_start_trade_dts TIMESTAMP;

-- --input parameters
v_bid_price DECIMAL(8, 2) [];

v_exec_name VARCHAR(49) [];

v_is_cash BOOLEAN [];

v_trade_list BIGINT [];

v_trade_price DECIMAL(8, 2) [];

v_settlement_amount DECIMAL(10, 2) [];

v_settlement_cash_due_date DATE [];

v_settlement_cash_type VARCHAR(40) [];

v_cash_transaction_amount DECIMAL(10, 2) [];

v_cash_transaction_dts TIMESTAMP [];

v_cash_transaction_name VARCHAR(100) [];

v_trade_history_dts TIMESTAMP [];

v_trade_history_status_id CHAR(4) [];

v_max_attempts INT;

rec RECORD;

rec_1_ RECORD;

BEGIN ----generate acct_id
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

-- generate dates
v_max_attempts := 10;

LOOP
SELECT
    t_dts INTO v_start_trade_dts
FROM
    TRADE TABLESAMPLE system (5)
WHERE
    random() < 0.01
LIMIT
    1;

v_max_attempts := v_max_attempts - 1;

EXIT
WHEN v_start_trade_dts IS NOT NULL
OR v_max_attempts = 0;

END LOOP;

v_end_trade_dts := v_start_trade_dts + INTERVAL '1 day';

-- -- Trade-Lookup_Frame-2
if v_debug_mode then RAISE NOTICE ' -- -- Trade_Lookup: v_acct_id v_start_trade_dts v_end_trade_dts % % %',
v_acct_id,
v_start_trade_dts,
v_end_trade_dts;

end if;

for rec in (
    select
        T_BID_PRICE,
        T_EXEC_NAME,
        T_IS_CASH,
        T_ID,
        T_TRADE_PRICE
    from
        TRADE
    where
        T_CA_ID = v_acct_id
        and T_DTS >= v_start_trade_dts
        and T_DTS <= v_end_trade_dts
    order by
        T_DTS asc
) loop v_bid_price = array_append(v_bid_price, rec.T_BID_PRICE);

v_exec_name = array_append(v_exec_name, rec.T_EXEC_NAME);

v_is_cash = array_append(v_is_cash, rec.T_IS_CASH);

v_trade_list = array_append(v_trade_list, rec.T_ID);

v_trade_price = array_append(v_trade_price, rec.T_TRADE_PRICE);

for rec_1_ in (
    select
        SE_AMT,
        SE_CASH_DUE_DATE,
        SE_CASH_TYPE
    from
        SETTLEMENT
    where
        SE_T_ID = rec.t_id
) loop v_settlement_amount = array_append(v_settlement_amount, rec_1_.SE_AMT);

v_settlement_cash_due_date = array_append(
    v_settlement_cash_due_date,
    rec_1_.SE_CASH_DUE_DATE
);

v_settlement_cash_type = array_append(v_settlement_cash_type, rec_1_.SE_CASH_TYPE);

end loop;

-- -- // get cash information if this is a cash transaction
-- -- // Should return only one row for each trade that was a cash transaction
if (rec.T_IS_CASH) then for rec_1_ in (
    select
        CT_AMT,
        CT_DTS,
        CT_NAME
    from
        CASH_TRANSACTION
    where
        CT_T_ID = rec.t_id
) loop v_cash_transaction_amount = array_append(v_cash_transaction_amount, rec_1_.CT_AMT);

v_cash_transaction_dts = array_append(v_cash_transaction_dts, rec_1_.CT_DTS);

v_cash_transaction_name = array_append(v_cash_transaction_name, rec_1_.CT_NAME);

end loop;

end if;

for rec_1_ in (
    select
        TH_DTS,
        TH_ST_ID
    from
        TRADE_HISTORY
    where
        TH_T_ID = rec.t_id
    order by
        TH_DTS
    LIMIT
        3
) loop v_trade_history_dts = array_append(v_trade_history_dts, rec_1_.TH_DTS);

v_trade_history_status_id = array_append(v_trade_history_status_id, rec_1_.TH_ST_ID);

end loop;

if v_debug_mode then RAISE NOTICE ' -- -- Trade-Order_Frame-2: t_id in loop %',
rec.t_id;

end if;

end loop;

END $$ LANGUAGE plpgsql;