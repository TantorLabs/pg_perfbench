DO $$ DECLARE v_debug_mode BOOLEAN := FALSE;

v_acct_id BIGINT;

--input parameters
v_start_trade_dts TIMESTAMP;

--input parameters
v_holding_history_id BIGINT [];

v_holding_history_trade_id BIGINT [];

-- v_num_trades_found
v_quantity_after INTEGER [];

v_quantity_before INTEGER [];

v_trade_id BIGINT;

v_max_attempts INT;

rec RECORD;

BEGIN --generate acct_id
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

----
if v_debug_mode then RAISE NOTICE ' -- -- Trade_Lookup: v_start_trade_dts v_acct_id   % %',
v_start_trade_dts,
v_acct_id;

end if;

select
    T_ID into v_trade_id
from
    TRADE
where
    T_CA_ID = v_acct_id
    and T_DTS >= v_start_trade_dts
order by
    T_DTS asc
limit
    1;

for rec in (
    select
        HH_H_T_ID,
        HH_T_ID,
        HH_BEFORE_QTY,
        HH_AFTER_QTY
    from
        HOLDING_HISTORY
    where
        HH_H_T_ID in (
            select
                HH_H_T_ID
            from
                HOLDING_HISTORY
            where
                HH_T_ID = v_trade_id
        )
    limit
        20
) loop v_holding_history_id = array_append(v_holding_history_id, rec.HH_H_T_ID);

v_holding_history_trade_id = array_append(v_holding_history_trade_id, rec.HH_T_ID);

v_quantity_before = array_append(v_quantity_before, rec.HH_BEFORE_QTY);

v_quantity_after = array_append(v_quantity_after, rec.HH_AFTER_QTY);

end loop;

END $$ LANGUAGE plpgsql;