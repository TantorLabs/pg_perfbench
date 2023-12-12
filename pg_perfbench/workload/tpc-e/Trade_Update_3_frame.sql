DO $$ DECLARE v_debug_mode BOOLEAN := FALSE;

v_symbol CHAR(15);

--input parameters
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
---------------
v_acct_id_arr BIGINT [];

v_exec_name_arr VARCHAR(49) [];

v_is_cash_arr BOOLEAN [];

v_price_arr DECIMAL(8, 2) [];

v_quantity_arr INTEGER [];

v_s_name_arr VARCHAR(70) [];

v_trade_dts_arr TIMESTAMP [];

v_trade_list_arr BIGINT [];

v_trade_type_arr CHAR(3) [];

v_type_name_arr VARCHAR(12) [];

---------------
rec_1_ RECORD;

---------------
v_num_found INTEGER := 0;

v_num_updated INTEGER := 0;

---------------
v_ct_name VARCHAR(100);

BEGIN -- -- generate input parameters 
-- --generate start_trade_dts as input 
SELECT
    t_dts INTO v_start_trade_dts
from
    trade
order by
    random()
limit
    1;

-- --generate end_trade_dts as input
v_end_trade_dts := v_start_trade_dts + ((floor(random() * 2) + 1) || ' days') :: INTERVAL;

-- --generate symbol as input
SELECT
    t_s_symb INTO v_symbol
from
    trade
order by
    random()
limit
    1;

-- --
for rec_1_ in (
    select
        T_CA_ID,
        --acct_id
        T_EXEC_NAME,
        --exec_name
        T_IS_CASH,
        --is_cash
        T_TRADE_PRICE,
        --price
        T_QTY,
        --quantity
        S_NAME,
        --s_name
        T_DTS,
        --trade_dts
        T_ID,
        --trade_list
        T_TT_ID,
        --trade_type
        TT_NAME --type_name
    from
        TRADE,
        TRADE_TYPE,
        SECURITY
    where
        T_S_SYMB = v_symbol
        and T_DTS BETWEEN v_start_trade_dts
        and v_end_trade_dts
        and TT_ID = T_TT_ID
        and S_SYMB = T_S_SYMB
    order by
        T_DTS ASC
) LOOP -- --// Get settlement information
-- --// Will return only one row for each trade
PERFORM -- settlement_amount[i] = SE_AMT,
-- settlement_cash_due_date[i] = SE_CASH_DUE_DATE,
-- settlement_cash_type[i] = SE_CASH_TYPE
SE_AMT,
SE_CASH_DUE_DATE,
SE_CASH_TYPE
from
    SETTLEMENT
where
    SE_T_ID = rec_1_.T_ID;

--  --// get cash information if this is a cash transaction
--  --// Will return only one row for each trade that was a cash transaction
if(rec_1_.T_IS_CASH) then if (v_num_updated < v_max_updates) then
select
    CT_NAME into v_ct_name
from
    CASH_TRANSACTION
where
    CT_T_ID = rec_1_.T_ID;

if (position('shares of' in v_ct_name) > 0) then v_ct_name := rec_1_.TT_NAME || ' ' || rec_1_.T_QTY || ' Shares of ' || rec_1_.s_name;

ELSE v_ct_name := rec_1_.TT_NAME || ' ' || rec_1_.T_QTY || ' shares of ' || rec_1_.s_name;

end if;

update
    CASH_TRANSACTION
set
    CT_NAME = v_ct_name
where
    CT_T_ID = rec_1_.T_ID;

v_num_updated := v_num_updated + 1;

end if;

PERFORM -- cash_transaction_amount[i] = CT_AMT,
-- cash_transaction_dts[i] = CT_DTS
-- cash_transaction_name[i] = CT_NAME
CT_AMT,
CT_DTS,
CT_NAME
from
    CASH_TRANSACTION
where
    CT_T_ID = rec_1_.T_ID;

end if;

PERFORM -- trade_history_dts[i][] = TH_DTS,
-- trade_history_status_id[i][] = TH_ST_ID
TH_DTS,
TH_ST_ID
from
    TRADE_HISTORY
where
    TH_T_ID = rec_1_.T_ID
order by
    TH_DTS asc;

END LOOP;

END $$ LANGUAGE plpgsql;