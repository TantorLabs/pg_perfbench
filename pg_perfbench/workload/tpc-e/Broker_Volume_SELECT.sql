DO $$ DECLARE v_debug_mode BOOLEAN := FALSE;

v_broker_list VARCHAR(49) [];

--input parameters
v_sector_name VARCHAR(30);

--input parameters
v_broker_name VARCHAR(49) [];

v_list_len INT;

v_volume DECIMAL(10, 2);

rec RECORD;

BEGIN ---generate broker_list as input 
for rec in (
    select
        b_name
    from
        broker
    order by
        random()
    limit
        10
) loop if (v_debug_mode) then RAISE NOTICE 'v_broker_list% ',
rec.b_name;

end if;

v_broker_list = array_append(v_broker_list, rec.b_name);

end loop;

-----
---generate sector_name as input
select
    sc_name into v_sector_name
from
    sector
order by
    random()
limit
    1;

-----
if (v_debug_mode) then RAISE NOTICE 'v_sector_name% ',
v_sector_name;

end if;

PERFORM B_NAME,
SUM(TR_QTY * TR_BID_PRICE)
FROM
    TRADE_REQUEST
    JOIN BROKER ON TR_B_ID = B_ID
    JOIN SECURITY ON TR_S_SYMB = S_SYMB
    JOIN COMPANY ON S_CO_ID = CO_ID
    JOIN INDUSTRY ON CO_IN_ID = IN_ID
    JOIN SECTOR ON SC_ID = IN_SC_ID
WHERE
    B_NAME = ANY(v_broker_list)
    AND SC_NAME = v_sector_name
GROUP BY
    B_NAME
ORDER BY
    2 DESC;

-- Подсчет количества строк в результате
GET DIAGNOSTICS v_list_len = ROW_COUNT;

if (v_debug_mode) then RAISE NOTICE 'v_list_len % ',
v_list_len;

end if;

END $$ LANGUAGE plpgsql;