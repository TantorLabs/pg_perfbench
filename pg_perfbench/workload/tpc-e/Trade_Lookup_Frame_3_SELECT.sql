DO $$ DECLARE v_debug_mode BOOLEAN := FALSE;

---
v_end_trade_dts TIMESTAMP;

v_max_acct_id INT := floor(random() * 25) + 1;

v_max_trades INT := floor(random() * 20) + 1;

v_start_trade_dts TIMESTAMP;

v_symbol CHAR(15) := '';

v_acct_id BIGINT [];

-- v_cash_transaction_amount
-- v_cash_transaction_dts
-- v_cash_transaction_name
v_exec_name VARCHAR(49) [];

v_is_cash BOOLEAN [];

-- v_num_found
v_price DECIMAL(8, 2) [];

v_quantity INTEGER [];

-- v_settlement_amount
-- v_settlement_cash_due_date
-- v_settlement_cash_type
v_trade_dts TIMESTAMP [];

-- v_trade_history_dts
-- v_trade_history_status_id
v_trade_list BIGINT [];

v_trade_type CHAR(3) [];

v_max_attempts INT;

v_settlement_amount DECIMAL(10, 2) [];

v_settlement_cash_due_date DATE [];

v_settlement_cash_type VARCHAR(40) [];

v_cash_transaction_amount DECIMAL(10, 2) [];

v_cash_transaction_dts TIMESTAMP [];

v_cash_transaction_name VARCHAR(100) [];

v_trade_history_dts TIMESTAMP [];

v_trade_history_status_id CHAR(4) [];

rec RECORD;

rec_1_ RECORD;

BEGIN -- generate dates
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

-- -- generate symbols
v_max_attempts := 10;

----generate v_symbol as input 
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

----
-- -- Trade-Lookup_Frame-3
if v_debug_mode then RAISE NOTICE ' -- -- Trade_Lookup: v_max_acct_id v_max_trades v_start_trade_dts v_end_trade_dts v_symbol % % % % %',
v_max_acct_id,
v_max_trades,
v_start_trade_dts,
v_end_trade_dts,
v_symbol;

end if;

for rec in (
    select
        T_CA_ID,
        T_EXEC_NAME,
        T_IS_CASH,
        T_TRADE_PRICE,
        T_QTY,
        T_DTS,
        T_ID,
        T_TT_ID
    from
        TRADE
    where
        T_S_SYMB = v_symbol
        and T_DTS >= v_start_trade_dts
        and T_DTS <= v_end_trade_dts
    order by
        T_DTS asc
    LIMIT
        v_max_trades
) loop v_acct_id = array_append(v_acct_id, rec.T_CA_ID);

v_exec_name = array_append(v_exec_name, rec.T_EXEC_NAME);

v_is_cash = array_append(v_is_cash, rec.T_IS_CASH);

v_price = array_append(v_price, rec.T_TRADE_PRICE);

v_quantity = array_append(v_quantity, rec.T_QTY);

v_trade_dts = array_append(v_trade_dts, rec.T_DTS);

v_trade_list = array_append(v_trade_list, rec.T_ID);

v_trade_type = array_append(v_trade_type, rec.T_TT_ID);

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

if v_debug_mode then RAISE NOTICE ' -- -- Trade-Order_Frame-3: t_id in loop %',
rec.t_id;

end if;

end loop;

END $$ LANGUAGE plpgsql;