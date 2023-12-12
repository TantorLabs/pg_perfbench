DO $$ DECLARE arr_table_names TEXT [] := ARRAY ['ACCOUNT_PERMISSION', 'ADDRESS', 'COMPANY', 'CUSTOMER', 'CUSTOMER_TAXRATE', 'DAILY_MARKET', 'EXCHANGE', 'FINANCIAL', 'NEWS_ITEM', 'SECURITY', 'TAXRATE', 'WATCH_ITEM'];

v_debug_mode BOOLEAN := FALSE;

v_table_name TEXT;

v_last_execution timestamp;

v_next_index INT;

--vars:
-- Account permissions 
v_acct_id BIGINT := NULL;

-- input parameters
v_acl CHAR(4) := NULL;

v_max_attempts int := 0;

-- Address 
v_c_id BIGINT := NULL;

-- also use for Customer, CUSTOMER_TAXRATE
v_line2 TEXT;

v_ad_id BIGINT;

--also use for  NEWS_ITEM
-- Company
v_co_id BIGINT := NULL;

--also use for NEWS_ITEM
v_sprate CHAR(4);

-- Customer
v_lenMindspring INT;

v_email2 CHAR(50);

v_len INT;

-- CUSTOMER_TAXRATE
v_old_tax_rate CHAR(3);

v_new_tax_rate CHAR(3);

v_tax_num INT;

-- DAILY_MARKET 
v_day_of_month INT := 0;

v_symbol CHAR(15) := NULL;

v_vol_incr INT := 0;

-- EXCHANGE, FINANCIAL
v_row_count INT := 0;

-- NEWS_ITEM
-- TAXRATE
v_tx_id CHAR(4) := NULL;

v_cnt INT := 0;

--also use for WATCH_ITEM
v_tx_name CHAR(50);

-- WATCH_ITEM
v_old_symbol CHAR(15);

v_new_symbol CHAR(15);

--
BEGIN
SELECT
    last_value,
    last_execution INTO v_table_name,
    v_last_execution
FROM
    data_maintenance_sequence
WHERE
    session_id = pg_backend_pid() FOR
UPDATE
;

-- blocked transctn
-- Check interval
IF NOW() - v_last_execution < INTERVAL '3 seconds' THEN RETURN;

END IF;

-- Init first value
IF v_table_name IS NULL THEN
INSERT INTO
    data_maintenance_sequence(session_id, last_execution, last_value)
VALUES
    (pg_backend_pid(), NOW(), arr_table_names [1]) ON CONFLICT(session_id) DO
UPDATE
SET
    last_execution = NOW(),
    last_value = arr_table_names [1];

v_table_name := arr_table_names [1];

ELSE -- Init currnt value 
v_next_index = (
    ARRAY_POSITION(arr_table_names, v_table_name) % ARRAY_LENGTH(arr_table_names, 1)
) + 1;

UPDATE
    data_maintenance_sequence
SET
    last_execution = NOW(),
    last_value = arr_table_names [v_next_index]
WHERE
    session_id = pg_backend_pid();

v_table_name := arr_table_names [v_next_index];

END IF;

-----------------
-- Select random acl
-- v_max_attempts := 10;
IF v_table_name = 'ACCOUNT_PERMISSION' THEN v_max_attempts := 10;

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

-- 
SELECT
    AP_ACL INTO v_acl
FROM
    ACCOUNT_PERMISSION
WHERE
    AP_CA_ID = v_acct_id
ORDER BY
    AP_ACL DESC
LIMIT
    1;

IF v_acl != '1111' THEN
UPDATE
    ACCOUNT_PERMISSION
SET
    AP_ACL = '1111'
WHERE
    AP_CA_ID = v_acct_id
    AND AP_ACL = v_acl;
if(v_debug_mode) then 
RAISE NOTICE 'update ACCOUNT_PERMISSION with AP_ACL = 1111 % %',
v_acct_id,
v_acl;
end if;

ELSE
UPDATE
    ACCOUNT_PERMISSION
SET
    AP_ACL = '0011'
WHERE
    AP_CA_ID = v_acct_id
    AND AP_ACL = v_acl;
if(v_debug_mode) then 
RAISE NOTICE 'update ACCOUNT_PERMISSION with other % %',
v_acct_id,
v_acl;
end if;
END IF;

ELSIF v_table_name = 'ADDRESS' THEN v_max_attempts := 10;

-- generate v_c_id as input
LOOP
SELECT
    c_id INTO v_c_id
FROM
    CUSTOMER TABLESAMPLE system (5)
WHERE
    random() < 0.01
LIMIT
    1;

v_max_attempts := v_max_attempts - 1;

EXIT
WHEN v_acct_id IS NOT NULL
OR v_max_attempts = 0;

END LOOP;

--
if(v_debug_mode) then 
RAISE NOTICE 'Address table v_c_id % ',
v_c_id;
end if;
IF v_c_id != 0 THEN
SELECT
    AD_LINE2,
    AD_ID INTO v_line2,
    v_ad_id
FROM
    ADDRESS,
    CUSTOMER
WHERE
    AD_ID = C_AD_ID
    AND C_ID = v_c_id;

ELSE
SELECT
    AD_LINE2,
    AD_ID INTO v_line2,
    v_ad_id
FROM
    ADDRESS,
    COMPANY
WHERE
    AD_ID = CO_AD_ID
    AND CO_ID = v_c_id;

END IF;
if(v_debug_mode) then 
RAISE NOTICE 'Address table v_line2, v_ad_id % %',
v_line2,
v_ad_id;
end if;
IF v_line2 != 'Apt. 10C' THEN
UPDATE
    ADDRESS
SET
    AD_LINE2 = 'Apt. 10C'
WHERE
    AD_ID = v_ad_id;

ELSE
UPDATE
    ADDRESS
SET
    AD_LINE2 = 'Apt. 22'
WHERE
    AD_ID = v_ad_id;

END IF;

ELSIF v_table_name = 'COMPANY' THEN v_max_attempts := 10;

-- generate v_c_id as input
LOOP
SELECT
    co_id INTO v_co_id
FROM
    COMPANY
order by
    random()
LIMIT
    1;

v_max_attempts := v_max_attempts - 1;

EXIT
WHEN v_acct_id IS NOT NULL
OR v_max_attempts = 0;

END LOOP;

--
if(v_debug_mode) then 
RAISE NOTICE 'COMPANY table v_co_id %',
v_co_id;
end if;
SELECT
    CO_SP_RATE INTO v_sprate
FROM
    COMPANY
WHERE
    CO_ID = v_co_id;
if(v_debug_mode) then 
RAISE NOTICE 'COMPANY table v_sprate %',
v_sprate;
end if;
IF v_sprate != 'ABA' THEN
UPDATE
    COMPANY
SET
    CO_SP_RATE = 'ABA'
WHERE
    CO_ID = v_co_id;

ELSE
UPDATE
    COMPANY
SET
    CO_SP_RATE = 'AAA'
WHERE
    CO_ID = v_co_id;

END IF;

ELSIF v_table_name = 'CUSTOMER' THEN v_lenMindspring := LENGTH('@mindspring.com');

v_max_attempts := 10;

-- generate v_c_id as input
LOOP
SELECT
    c_id INTO v_c_id
FROM
    CUSTOMER TABLESAMPLE system (5)
WHERE
    random() < 0.01
LIMIT
    1;

v_max_attempts := v_max_attempts - 1;

EXIT
WHEN v_acct_id IS NOT NULL
OR v_max_attempts = 0;

END LOOP;

--
SELECT
    C_EMAIL_2 INTO v_email2
FROM
    CUSTOMER
WHERE
    C_ID = c_id;

v_len := LENGTH(v_email2);

IF v_len - v_lenMindspring > 0
AND RIGHT(v_email2, v_lenMindspring) = '@mindspring.com' THEN
UPDATE
    CUSTOMER
SET
    C_EMAIL_2 = LEFT(C_EMAIL_2, POSITION('@' IN C_EMAIL_2)) || 'earthlink.com'
WHERE
    C_ID = c_id;

ELSE
UPDATE
    CUSTOMER
SET
    C_EMAIL_2 = LEFT(C_EMAIL_2, POSITION('@' IN C_EMAIL_2)) || 'mindspring.com'
WHERE
    C_ID = c_id;

END IF;

if(v_debug_mode) then 
RAISE NOTICE 'CUSTOMER table v_len %',
v_len;
end if;
ELSIF v_table_name = 'CUSTOMER_TAXRATE' THEN v_max_attempts := 10;

-- generate v_c_id as input
LOOP
SELECT
    c_id INTO v_c_id
FROM
    CUSTOMER TABLESAMPLE system (5)
WHERE
    random() < 0.01
LIMIT
    1;

v_max_attempts := v_max_attempts - 1;

EXIT
WHEN v_acct_id IS NOT NULL
OR v_max_attempts = 0;

END LOOP;

--
SELECT
    CX_TX_ID INTO v_old_tax_rate
FROM
    CUSTOMER_TAXRATE
WHERE
    CX_C_ID = v_c_id
    AND (
        CX_TX_ID LIKE 'US%'
        OR CX_TX_ID LIKE 'CN%'
    );

IF LEFT(v_old_tax_rate, 2) = 'US' THEN IF v_old_tax_rate = 'US5' THEN v_new_tax_rate := 'US1';

ELSE v_tax_num := ASCII(RIGHT(v_old_tax_rate, 1)) - ASCII('0') + 1;

v_new_tax_rate := 'US' || CHR(v_tax_num + ASCII('0'));

END IF;

ELSE IF v_old_tax_rate = 'CN4' THEN v_new_tax_rate := 'CN1';

ELSE v_tax_num := ASCII(RIGHT(v_old_tax_rate, 1)) - ASCII('0') + 1;

v_new_tax_rate := 'CN' || CHR(v_tax_num + ASCII('0'));

END IF;

END IF;

if(v_debug_mode) then 
RAISE NOTICE 'values  % %',
v_new_tax_rate,
v_old_tax_rate;
end if;
UPDATE
    CUSTOMER_TAXRATE
SET
    CX_TX_ID = v_new_tax_rate
WHERE
    CX_C_ID = v_c_id
    AND CX_TX_ID = v_old_tax_rate;

if(v_debug_mode) then 
RAISE NOTICE 'CUSTOMER_TAXRATE table v_old_tax_rate %',
v_old_tax_rate;
end if;
ELSIF v_table_name = 'DAILY_MARKET' THEN -- generate v_vol_incr as input 
SELECT
    floor(-100 + random() * 100) :: int INTO v_vol_incr;

-- generate random v_day_of_month
SELECT
    floor(1 + random() * 31) :: int INTO v_day_of_month;

v_max_attempts := 10;

-- generate v_symbol as input
LOOP
SELECT
    S_SYMB INTO v_symbol
FROM
    SECURITY TABLESAMPLE system (5)
WHERE
    random() < 0.01
LIMIT
    1;

v_max_attempts := v_max_attempts - 1;

EXIT
WHEN v_acct_id IS NOT NULL
OR v_max_attempts = 0;

END LOOP;

--
-- Assume day_of_month and vol_incr are passed into the function or initialized prior
UPDATE
    DAILY_MARKET
SET
    DM_VOL = DM_VOL + v_vol_incr
WHERE
    DM_S_SYMB = v_symbol
    AND EXTRACT(
        DAY
        FROM
            DM_DATE :: DATE
    ) = v_day_of_month;

if(v_debug_mode) then 
RAISE NOTICE 'DAILY_MARKET table v_vol_incr %',
v_vol_incr;
end if;
ELSIF v_table_name = 'EXCHANGE' THEN
SELECT
    COUNT(*) INTO v_row_count
FROM
    EXCHANGE
WHERE
    EX_DESC LIKE '%LAST UPDATED%';

IF v_row_count = 0 THEN
UPDATE
    EXCHANGE
SET
    EX_DESC = EX_DESC || ' LAST UPDATED ' || NOW();

ELSE
UPDATE
    EXCHANGE
SET
    EX_DESC = LEFT(EX_DESC, LENGTH(EX_DESC) - LENGTH(NOW() :: TEXT)) || NOW() :: TEXT;

END IF;

ELSIF v_table_name = 'FINANCIAL' THEN v_max_attempts := 10;

-- generate v_c_id as input
LOOP
SELECT
    co_id INTO v_co_id
FROM
    COMPANY
order by
    random()
LIMIT
    1;

v_max_attempts := v_max_attempts - 1;

EXIT
WHEN v_acct_id IS NOT NULL
OR v_max_attempts = 0;

END LOOP;

--
SELECT
    COUNT(*) INTO v_row_count
FROM
    FINANCIAL
WHERE
    FI_CO_ID = v_co_id
    AND EXTRACT(
        DAY
        FROM
            FI_QTR_START_DATE :: DATE
    ) = '01';

IF v_row_count > 0 THEN
UPDATE
    FINANCIAL
SET
    FI_QTR_START_DATE = FI_QTR_START_DATE + INTERVAL '1 day'
WHERE
    FI_CO_ID = v_co_id;

ELSE
UPDATE
    FINANCIAL
SET
    FI_QTR_START_DATE = FI_QTR_START_DATE - INTERVAL '1 day'
WHERE
    FI_CO_ID = v_co_id;

END IF;

ELSIF v_table_name = 'NEWS_ITEM' THEN v_max_attempts := 10;

-- generate v_c_id as input
LOOP
SELECT
    co_id INTO v_co_id
FROM
    COMPANY
order by
    random()
LIMIT
    1;

v_max_attempts := v_max_attempts - 1;

EXIT
WHEN v_acct_id IS NOT NULL
OR v_max_attempts = 0;

END LOOP;

--
UPDATE
    NEWS_ITEM
SET
    NI_DTS = NI_DTS + INTERVAL '1 day'
WHERE
    NI_ID IN (
        SELECT
            NX_NI_ID
        FROM
            NEWS_XREF
        WHERE
            NX_CO_ID = v_co_id
    );

ELSIF v_table_name = 'SECURITY' THEN v_max_attempts := 10;

-- generate v_symbol as input
LOOP
SELECT
    S_SYMB INTO v_symbol
FROM
    SECURITY TABLESAMPLE system (5)
WHERE
    random() < 0.01
LIMIT
    1;

v_max_attempts := v_max_attempts - 1;

EXIT
WHEN v_acct_id IS NOT NULL
OR v_max_attempts = 0;

END LOOP;

--
UPDATE
    SECURITY
SET
    S_EXCH_DATE = S_EXCH_DATE + INTERVAL '1 day'
WHERE
    S_SYMB = v_symbol;

ELSIF v_table_name = 'TAXRATE' THEN v_max_attempts := 10;

-- generate v_tx_id as input
LOOP
SELECT
    TX_ID INTO v_tx_id
FROM
    TAXRATE
order by
    random()
LIMIT
    1;

v_max_attempts := v_max_attempts - 1;

EXIT
WHEN v_acct_id IS NOT NULL
OR v_max_attempts = 0;

END LOOP;

--
select
    TX_NAME INTO v_tx_name
from
    TAXRATE
where
    TX_ID = v_tx_id;

IF v_tx_name LIKE '% Tax %' THEN v_tx_name := REPLACE(v_tx_name, ' Tax ', ' tax ');

ELSE v_tx_name := REPLACE(v_tx_name, ' tax ', ' Tax ');

END IF;

UPDATE
    TAXRATE
SET
    TX_NAME = v_tx_name
WHERE
    TX_ID = v_tx_id;

--------------------------------
ELSIF v_table_name = 'WATCH_ITEM' THEN v_max_attempts := 10;

-- generate v_c_id as input
LOOP
SELECT
    c_id INTO v_c_id
FROM
    CUSTOMER TABLESAMPLE system (5)
WHERE
    random() < 0.01
LIMIT
    1;

v_max_attempts := v_max_attempts - 1;

EXIT
WHEN v_acct_id IS NOT NULL
OR v_max_attempts = 0;

END LOOP;

--
SELECT
    COUNT(*) INTO v_cnt
FROM
    WATCH_ITEM,
    WATCH_LIST
WHERE
    WL_C_ID = v_c_id
    AND WI_WL_ID = WL_ID;

v_cnt := (v_cnt + 1) / 2;

SELECT
    WI_S_SYMB INTO v_old_symbol
FROM
    (
        SELECT
            ROW_NUMBER() OVER (
                ORDER BY
                    WI_S_SYMB ASC
            ) AS rnum,
            WI_S_SYMB
        FROM
            WATCH_ITEM,
            WATCH_LIST
        WHERE
            WL_C_ID = v_c_id
            AND WI_WL_ID = WL_ID
        ORDER BY
            WI_S_SYMB ASC
    ) as t_s_symb
WHERE
    t_s_symb.rnum = v_cnt;

SELECT
    S_SYMB INTO v_new_symbol
FROM
    SECURITY
WHERE
    S_SYMB > v_old_symbol
    AND S_SYMB NOT IN (
        SELECT
            WI_S_SYMB
        FROM
            WATCH_ITEM
            JOIN WATCH_LIST ON WI_WL_ID = WL_ID
        WHERE
            WL_C_ID = v_c_id
    )
ORDER BY
    S_SYMB ASC
LIMIT
    1;

UPDATE
    WATCH_ITEM
SET
    WI_S_SYMB = v_new_symbol
FROM
    WATCH_LIST
WHERE
    WI_WL_ID = WL_ID
    AND WL_C_ID = v_c_id
    AND WI_S_SYMB = v_old_symbol;

END IF;

END $$ LANGUAGE plpgsql;