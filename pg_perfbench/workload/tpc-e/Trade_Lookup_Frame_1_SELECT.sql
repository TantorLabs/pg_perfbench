DO $$ DECLARE v_debug_mode BOOLEAN := FALSE;

-- -- Trade-Lookup_Frame-1
v_acct_id BIGINT;

-- input parameters
v_end_trade_dts TIMESTAMP;

-- input parameters
-- v_frame_to_execute                    -- input parameters
-- v_max_acct_id                    -- input parameters
v_max_trades INT := floor(random() * 20) + 1;

-- input parameters
-- v_start_trade_dts                    -- input parameters
-- v_symbol                    -- input parameters
v_trade_id BIGINT [];

-- input parameters
v_is_cash BOOLEAN [];

-- v_frame_executed
-- v_is_market[]
-- v_status
-- v_trade_list[]
v_num_found INT := 0;

v_bid_price DECIMAL(8, 2) [];

v_exec_name VARCHAR(49) [];

v_is_market BOOLEAN [];

v_trade_price DECIMAL(8, 2) [];

settlement_amount DECIMAL(10, 2) [];

settlement_cash_due_date DATE [];

settlement_cash_type VARCHAR(40) [];

v_cash_transaction_amount DECIMAL(10, 2) [];

v_cash_transaction_dts TIMESTAMP [];

v_cash_transaction_name VARCHAR(100) [];

v_trade_history_dts TIMESTAMP [];

v_trade_history_status_id CHAR(4) [];

v_i INT := 1;

rec RECORD;

rec_1_ RECORD;

BEGIN -- -- Trade-Lookup_Frame-1 Pseudo-code: Get trade information for each trade ID in
-- -- the trade_id array
--generate array trade_id
for rec in(
    select
        t_id
    from
        trade
    order by
        random()
    LIMIT
        v_max_trades
) loop v_trade_id = array_append(v_trade_id, rec.t_id);

-- --// Get trade information
-- --// Should only return one row for each trade
for rec_1_ in (
    select
        T_BID_PRICE,
        T_EXEC_NAME,
        T_IS_CASH,
        TT_IS_MRKT,
        T_TRADE_PRICE
    from
        TRADE,
        TRADE_TYPE
    where
        T_ID = rec.t_id
        and T_TT_ID = TT_ID
) loop v_bid_price = array_append(v_bid_price, rec_1_.T_BID_PRICE);

v_exec_name = array_append(v_exec_name, rec_1_.T_EXEC_NAME);

v_is_cash = array_append(v_is_cash, rec_1_.T_IS_CASH);

v_is_market = array_append(v_is_market, rec_1_.TT_IS_MRKT);

v_trade_price = array_append(v_trade_price, rec_1_.T_TRADE_PRICE);

end loop;

-- -- // Get settlement information
-- -- // Should only return one row for each trade
for rec_1_ in (
    select
        SE_AMT,
        SE_CASH_DUE_DATE,
        SE_CASH_TYPE
    from
        SETTLEMENT
    where
        SE_T_ID = rec.t_id
) loop settlement_amount = array_append(settlement_amount, rec_1_.SE_AMT);

settlement_cash_due_date = array_append(
    settlement_cash_due_date,
    rec_1_.SE_CASH_DUE_DATE
);

settlement_cash_type = array_append(settlement_cash_type, rec_1_.SE_CASH_TYPE);

end loop;

-- -- // get cash information if this is a cash transaction
-- -- Should only return one row for each trade that was a cash transaction
if (v_is_cash [v_i]) then for rec_1_ in (
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

if v_debug_mode then RAISE NOTICE ' -- -- Trade-Order_Frame-1: t_id in loop %',
rec.t_id;

end if;

end loop;

--
END $$ LANGUAGE plpgsql;