DO $$ DECLARE -- Customer-Position_Frame-1
v_cust_id BIGINT := NULL;

v_debug_mode BOOLEAN := FALSE;

v_tax_id VARCHAR(20); --input parameters


v_acct_id_arr BIGINT [];

v_cash_bal_arr DECIMAL(12, 2) [];

v_assest_total_arr INT [];

v_acct_len INT;

v_hist_len INT;

-- Customer-Position_Frame-1
v_acct_id BIGINT; --input parameters

rec RECORD;

BEGIN ---generate tax_id as input
SELECT
    c_tax_id INTO v_tax_id
FROM
    customer
order by
    random()
LIMIT
    1;

if(v_debug_mode) then RAISE NOTICE 'v_tax_id %',
v_tax_id;

end if;

if(v_cust_id is NULL) then
select
    C_ID into v_cust_id
from
    CUSTOMER
where
    C_TAX_ID = v_tax_id
limit
    1;

end if;

if(v_debug_mode) then RAISE NOTICE 'v_cust_id %',
v_cust_id;

end if;

PERFORM C_ST_ID,
C_L_NAME,
C_F_NAME,
C_M_NAME,
C_GNDR,
C_TIER,
C_DOB,
C_AD_ID,
C_CTRY_1,
C_AREA_1,
C_LOCAL_1,
C_EXT_1,
C_CTRY_2,
C_AREA_2,
C_LOCAL_2,
C_EXT_2,
C_CTRY_3,
C_AREA_3,
C_LOCAL_3,
C_EXT_3,
C_EMAIL_1,
C_EMAIL_2
FROM
    CUSTOMER
WHERE
    C_ID = v_cust_id;

-- Get customer's total assets
-- SELECT COUNT(*) 
-- INTO v_acct_len
-- FROM (
--     SELECT CA_ID, CA_BAL, COALESCE(SUM(HS_QTY * LT_PRICE), 0) AS assets_total
--     -- INTO v_acct_id_arr, v_cash_bal_arr, v_assest_total_arr
--     FROM CUSTOMER_ACCOUNT 
--     LEFT JOIN HOLDING_SUMMARY ON HS_CA_ID = CA_ID,
--     LAST_TRADE
--     WHERE CA_C_ID = v_cust_id AND LT_S_SYMB = HS_S_SYMB
--     GROUP BY CA_ID, CA_BAL
--     ORDER BY assets_total ASC
--     LIMIT 10
-- ) AS foo; 
FOR rec IN (
    SELECT
        CA_ID,
        CA_BAL,
        COALESCE(SUM(HS_QTY * LT_PRICE), 0) AS assets_total
    FROM
        CUSTOMER_ACCOUNT
        LEFT JOIN HOLDING_SUMMARY ON HS_CA_ID = CA_ID
        INNER JOIN LAST_TRADE ON LT_S_SYMB = HS_S_SYMB
    WHERE
        CA_C_ID = v_cust_id
    GROUP BY
        CA_ID,
        CA_BAL
    ORDER BY
        assets_total ASC
    LIMIT
        10
) LOOP v_acct_id_arr := array_append(v_acct_id_arr, rec.CA_ID);

v_cash_bal_arr := array_append(v_cash_bal_arr, rec.CA_BAL);

v_assest_total_arr := array_append(v_assest_total_arr, rec.assets_total);

if (v_debug_mode) then RAISE NOTICE ' Customer-Position_Frame-1v_acct_id_arr v_cash_bal_arr v_assest_total_arr  % % %',
rec.CA_ID,
rec.CA_BAL,
rec.assets_total;

end if;

END LOOP;

SELECT
    COUNT(*) INTO v_acct_len
FROM
    unnest(v_acct_id_arr);

if (v_debug_mode) then RAISE NOTICE 'Customers total assets %',
v_acct_len;

end if;

-- Start of Customer-Position_Frame-2
--generate acct_id
select
    ca_id into v_acct_id
from
    customer_account
order by
    random()
limit
    1;

if (v_debug_mode) then RAISE NOTICE 'v_acct_id %',
v_acct_id;

end if;

------
IF (v_acct_len >= 1) THEN
SELECT
    COUNT(*) INTO v_hist_len
FROM
    (
        SELECT
            TRADE.t_id,
            TRADE.t_s_symb,
            TRADE.t_qty,
            STATUS_TYPE.st_name,
            TRADE_HISTORY.th_dts
        FROM
            (
                SELECT
                    T_ID AS ID
                FROM
                    TRADE
                WHERE
                    T_CA_ID = ANY(v_acct_id_arr)
                ORDER BY
                    T_DTS DESC
                limit
                    10
            ) AS T,
            TRADE,
            TRADE_HISTORY,
            STATUS_TYPE
        WHERE
            TRADE.T_ID = T.ID
            AND TRADE_HISTORY.TH_T_ID = TRADE.T_ID
            AND STATUS_TYPE.ST_ID = TRADE_HISTORY.TH_ST_ID
        ORDER BY
            TRADE_HISTORY.TH_DTS DESC
        LIMIT
            30
    ) AS foo_1;

if (v_debug_mode) then RAISE NOTICE 'v_hist_len %',
v_hist_len;

end if;

END IF;

END $$ LANGUAGE plpgsql;