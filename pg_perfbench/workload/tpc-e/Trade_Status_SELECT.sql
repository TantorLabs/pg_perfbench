DO $$ DECLARE v_acct_id BIGINT;

v_max_attempts INT := 10;

BEGIN --generate acct_id from Customer accounts
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

IF(v_acct_id = NULL) THEN
SELECT
    ca_id INTO v_acct_id
FROM
    CUSTOMER_ACCOUNT
order by
    random()
LIMIT
    1;

END IF;

PERFORM T_ID,
--trade_id[] =
T_DTS,
--trade_dts[] =
ST_NAME,
--status_name[] =
TT_NAME,
--type_name[] =
T_S_SYMB,
--symbol[] =
T_QTY,
--trade_qty[] =
T_EXEC_NAME,
--exec_name[] =
T_CHRG,
--charge[] =
S_NAME,
--s_name[] =
EX_NAME --ex_name[] =
from
    TRADE,
    STATUS_TYPE,
    TRADE_TYPE,
    SECURITY,
    EXCHANGE
where
    T_CA_ID = v_acct_id
    and ST_ID = T_ST_ID
    and TT_ID = T_TT_ID
    and S_SYMB = T_S_SYMB
    and EX_ID = S_EX_ID
order by
    T_DTS desc
LIMIT
    50;

PERFORM C_L_NAME, --cust_l_name =
C_F_NAME, --cust_f_name =
B_NAME --broker_name =
from
    CUSTOMER_ACCOUNT,
    CUSTOMER,
    BROKER
where
    CA_ID = v_acct_id
    and C_ID = CA_C_ID
    and B_ID = CA_B_ID;

END $$ LANGUAGE plpgsql;