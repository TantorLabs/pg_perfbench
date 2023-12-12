DO $$ DECLARE request_list REFCURSOR;

v_debug_mode BOOLEAN := FALSE;

v_price_quote DECIMAL(8, 2) [];

--input parameters
v_status_submitted CHAR(4);

--input parameters
v_symbol CHAR(15) [];

--input parameters
v_trade_qty INTEGER [];

--input parameters
v_type_limit_buy CHAR(3);

--input parameters
v_type_limit_sell CHAR(3);

--input parameters
v_type_stop_loss CHAR(3);

--input parameters
-- v_num_updated
-- v_send_len
v_max_feed_len INT := 20;

v_rows_updated INT := 0;

----
v_now_dts TIMESTAMP;

v_req_trade_id BIGINT;

v_req_price_quote DECIMAL(8, 2);

v_req_trade_type CHAR(3);

v_req_trade_qty INTEGER;

-- v_rows_updated INTEGER;
v_rows_sent int := 0;

-- v_now_dts TIMESTAMP;
v_iter INT;

rec RECORD;

BEGIN --- generate v_symbol as input 
for rec in (
    select
        LT_S_SYMB
    from
        LAST_TRADE
    order by
        random()
    limit
        v_max_feed_len
) loop if v_debug_mode then RAISE NOTICE 'symbol %',
rec.LT_S_SYMB;

end if;

v_symbol = array_append(v_symbol, rec.LT_S_SYMB);

end loop;

---generate price_quote  
for rec in (
    select
        LT_PRICE
    from
        LAST_TRADE
    order by
        random()
    limit
        v_max_feed_len
) loop if v_debug_mode then RAISE NOTICE 'v_price_quote[i] %',
rec.LT_PRICE;

end if;

v_price_quote = array_append(v_price_quote, rec.LT_PRICE);

end loop;

---generate v_status_submitted
select
    T_ST_ID into v_status_submitted
from
    TRADE
order by
    random()
limit
    1;

if v_debug_mode then RAISE NOTICE 'v_status_submitted %',
v_status_submitted;

end if;

----
---generate v_trade_qty
for rec in (
    select
        t_qty
    from
        TRADE
    order by
        random()
    limit
        v_max_feed_len
) loop if v_debug_mode then RAISE NOTICE 'v_trade_qty[i] %',
rec.t_qty;

end if;

v_trade_qty = array_append(v_trade_qty, rec.t_qty);

end loop;

----
---generate v_type_limit_buy v_type_limit_sell v_type_stop_loss
select
    tr_tt_id into v_type_limit_buy
from
    trade_request
order by
    random()
limit
    1;

select
    tr_tt_id into v_type_limit_sell
from
    trade_request
order by
    random()
limit
    1;

select
    tr_tt_id into v_type_stop_loss
from
    trade_request
order by
    random()
limit
    1;

if v_debug_mode then RAISE NOTICE 'v_type_limit_buy v_type_limit_sell v_type_stop_loss  % % %',
v_type_limit_buy,
v_type_limit_sell,
v_type_stop_loss;

end if;

----
v_now_dts = NOW() :: timestamp;

v_iter := 0;

LOOP
UPDATE
    last_trade
set
    LT_PRICE = v_price_quote [v_iter],
    LT_VOL = LT_VOL + v_trade_qty [v_iter],
    LT_DTS = v_now_dts
where
    lt_s_symb = v_symbol [v_iter];

-- rows_updated = rows_updated + row_count
OPEN request_list FOR
select
    TR_T_ID,
    TR_BID_PRICE,
    TR_TT_ID,
    TR_QTY
from
    TRADE_REQUEST
where
    TR_S_SYMB = v_symbol [v_iter]
    and (
        (
            TR_TT_ID = v_type_stop_loss
            and TR_BID_PRICE >= v_price_quote [v_iter]
        )
        or (
            TR_TT_ID = v_type_limit_sell
            and TR_BID_PRICE <= v_price_quote [v_iter]
        )
        or (
            TR_TT_ID = v_type_limit_buy
            and TR_BID_PRICE >= v_price_quote [v_iter]
        )
    );

LOOP FETCH request_list INTO v_req_trade_id,
v_req_price_quote,
v_req_trade_type,
v_req_trade_qty;

EXIT
WHEN NOT FOUND;

if v_debug_mode then RAISE NOTICE 'v_req_trade_id, v_req_price_quote, v_req_trade_type, v_req_trade_qty  % % % %',
v_req_trade_id,
v_req_price_quote,
v_req_trade_type,
v_req_trade_qty;

end if;

update
    TRADE
set
    T_DTS = v_now_dts,
    T_ST_ID = v_status_submitted
where
    T_ID = v_req_trade_id;

delete from
    TRADE_REQUEST
where
    tr_t_id = v_req_trade_id;

insert into
    TRADE_HISTORY
values
    (
        TH_T_ID = v_req_trade_id,
        TH_DTS = v_now_dts,
        TH_ST_ID = v_status_submitted
    );

-- v_TradeRequestBuffer[rows_sent].symbol = symbol[i];
-- v_TradeRequestBuffer[rows_sent].trade_id = req_trade_id;
-- v_TradeRequestBuffer[rows_sent].price_quote = req_price_quote;
-- v_TradeRequestBuffer[rows_sent].trade_qty = req_trade_qty;
-- v_TradeRequestBuffer[rows_sent].trade_type = req_trade_type;
-- v_rows_sent := v_rows_sent + 1;
end loop;

CLOSE request_list;

EXIT
WHEN v_iter <= v_max_feed_len;

v_iter := v_iter + 1;

END LOOP;

END $$ LANGUAGE plpgsql;