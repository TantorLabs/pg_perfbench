DO $$ DECLARE v_debug_mode BOOLEAN := FALSE;

v_access_lob_flag BOOLEAN;

v_max_rows_to_return INT := floor(random() * 20) + 1;

v_start_day TIMESTAMP;

v_symbol CHAR(15);

v_co_id BIGINT;

-- v_max_comp_len 
-- v_tart
-- v_symbol
-- v_52_wk_high
-- v_52_wk_high_date
-- v_52_wk_low
-- v_52_wk_low_date
-- v_ceo_name
-- v_co_ad_ctry
-- v_co_ad_div
-- v_co_ad_linel
-- v_co_ad_line2
-- v_co_ad_town
-- v_co_desc
-- v_co_name
-- v_co_st_id
v_cp_co_name VARCHAR(60) [];

v_cp_in_name VARCHAR(50) [];

-- v_day
v_day_len INT;

-- v_divid
-- v_ex_ad_ctry
-- v_ex_ad_div
-- v_ex_ad_line1
-- v_ex_ad_line2
-- v_ex_ad_town
-- v_ex_ad_zip
-- v_ex_close
-- v_ex_date
-- v_ex_desc
-- v_ex_name
-- v_ex_num_symb
-- v_ex_open
-- v_fin
v_fin_len INT;

-- v_last_open
-- v_last_price
-- v_last_vol
-- v_news
-- v_news_len
-- v_num_out
-- v_open_date
-- v_pe_ratio
-- v_s_name
-- v_sp_rate
-- v_start_date
-- v_yield
rec RECORD;

v_max_attempts INT;

BEGIN ---generate start_day as input 
v_max_attempts := 10;

LOOP
SELECT
    dm_date INTO v_start_day
FROM
    daily_market TABLESAMPLE system (5)
WHERE
    random() < 0.01
LIMIT
    1;

v_max_attempts := v_max_attempts - 1;

EXIT
WHEN v_start_day IS NOT NULL
OR v_max_attempts = 0;

END LOOP;

if (v_debug_mode) then RAISE NOTICE 'v_start_day %',
v_start_day;

end if;

---generate symbol as input 
select
    s_symb into v_symbol
from
    security
order by
    random()
limit
    1;

if (v_debug_mode) then RAISE NOTICE 'v_symbol %',
v_symbol;

end if;

--generate v_access_lob_flag as input 
v_access_lob_flag := random() >= 0.5;

if (v_debug_mode) then RAISE NOTICE 'v_access_lob_flag %',
v_access_lob_flag;

end if;

------
-- -- Security-Detail_Frame-1
select
    -- S_NAME,     ---- s_name = 
    CO_ID --,     ---- co_id = 
    -- CO_NAME,     ---- co_name = 
    -- CO_SP_RATE     ---- sp_rate = 
    -- CO_CEO,     ---- ceo_name = 
    -- CO_DESC,     ---- co_desc = 
    -- CO_OPEN_DATE,     ---- open_date = 
    -- CO_ST_ID,     ---- co_st_id = 
    -- CA.AD_LINE1,     ---- co_ad_line1 = 
    -- CA.AD_LINE2,     ---- co_ad_line2 = 
    -- ZCA.ZC_TOWN,     ---- co_ad_town = 
    -- ZCA.ZC_DIV,     ---- co_ad_div = 
    -- CA.AD_ZC_CODE,     ---- co_ad_zip = 
    -- CA.AD_CTRY,     ---- co_ad_ctry = 
    -- S_NUM_OUT,     ---- num_out = 
    -- S_START_DATE,     ---- start_date = 
    -- S_EXCH_DATE,     ---- exch_date = 
    -- S_PE,     ---- pe_ratio = 
    -- S_52WK_HIGH,     ---- 52_wk_high = 
    -- S_52WK_HIGH_DATE,     ---- 52_wk_high_date = 
    -- S_52WK_LOW,     ---- 52_wk_low = 
    -- S_52WK_LOW_DATE,     ---- 52_wk_low_date = 
    -- S_DIVIDEND,     ---- divid = 
    -- S_YIELD,     ---- yield = 
    -- ZEA.ZC_DIV,     ---- ex_ad_div = 
    -- EA.AD_CTRY     ---- ex_ad_ctry = 
    -- EA.AD_LINE1,     ---- ex_ad_line1 = 
    -- EA.AD_LINE2,     ---- ex_ad_line2 = 
    -- ZEA.ZC_TOWN,     ---- ex_ad_town = 
    -- EA.AD_ZC_CODE,     ---- ex_ad_zip = 
    -- EX_CLOSE,     ---- ex_close = 
    -- EX_DESC,     ---- ex_desc = 
    -- EX_NAME,     ---- ex_name = 
    -- EX_NUM_SYMB,     ---- ex_num_symb = 
    -- EX_OPEN     ---- ex_open = 
    into v_co_id
from
    SECURITY,
    COMPANY,
    ADDRESS CA,
    ADDRESS EA,
    ZIP_CODE ZCA,
    ZIP_CODE ZEA,
    EXCHANGE
where
    S_SYMB = v_symbol
    and CO_ID = S_CO_ID
    and CA.AD_ID = CO_AD_ID
    and EA.AD_ID = EX_AD_ID
    and EX_ID = S_EX_ID
    and ca.ad_zc_code = zca.zc_code
    and ea.ad_zc_code = zea.zc_code
LIMIT
    1;

if (v_debug_mode) then RAISE NOTICE 'v_co_id  %',
v_co_id;

end if;

-- -- // Should return max_comp_len (3) rows
for rec in (
    select
        CO_NAME,
        IN_NAME
    from
        COMPANY_COMPETITOR,
        COMPANY,
        INDUSTRY
    where
        CP_CO_ID = v_co_id
        and CO_ID = CP_COMP_CO_ID
        and IN_ID = CP_IN_ID
    limit
        3
) loop if (v_debug_mode) then RAISE NOTICE 'v_cp_co_name v_cp_in_name % %',
rec.CO_NAME,
rec.IN_NAME;

end if;

v_cp_co_name = array_append(v_cp_co_name, rec.CO_NAME);

v_cp_in_name = array_append(v_cp_in_name, rec.IN_NAME);

end loop;

-- -- -- // Should return max_fin_len (20) rows
PERFORM FI_YEAR,
-----fin[].year = 
FI_QTR,
-----fin[].qtr = 
FI_QTR_START_DATE,
-----fin[].strart_date = 
FI_REVENUE,
-----fin[].rev = 
FI_NET_EARN,
-----fin[].net_earn = 
FI_BASIC_EPS,
-----fin[].basic_eps = 
FI_DILUT_EPS,
-----fin[].dilut_eps = 
FI_MARGIN,
-----fin[].margin = 
FI_INVENTORY,
-----fin[].invent = 
FI_ASSETS,
-----fin[].assets = 
FI_LIABILITY,
-----fin[].liab = 
FI_OUT_BASIC,
-----fin[].out_basic = 
FI_OUT_DILUT -----fin[].out_dilut = 
from
    FINANCIAL
where
    FI_CO_ID = v_co_id
order by
    FI_YEAR asc,
    FI_QTR
limit
    20;

GET DIAGNOSTICS v_fin_len = ROW_COUNT;

if (v_debug_mode) then RAISE NOTICE 'v_fin_len %',
v_fin_len;

end if;

-- -- -- // Should return max_rows_to_return rows
-- -- -- // max_rows_to_return is between 5 and 20
PERFORM DM_DATE,
DM_CLOSE,
DM_HIGH,
DM_LOW,
DM_VOL
from
    DAILY_MARKET
where
    DM_S_SYMB = v_symbol
    and DM_DATE >= v_start_day
order by
    DM_DATE asc
limit
    v_max_rows_to_return;

GET DIAGNOSTICS v_day_len = ROW_COUNT;

if (v_debug_mode) then RAISE NOTICE 'v_day_len %',
v_day_len;

end if;

PERFORM LT_PRICE,
----last_price =
LT_OPEN_PRICE,
----last_open =
LT_VOL ----last_vol =
from
    LAST_TRADE
where
    LT_S_SYMB = v_symbol;

-- - --- // Should return max_news_len (2) rows
if (v_access_lob_flag) then PERFORM NI_ITEM,
---news[].item =
NI_DTS,
---news[].dts =
NI_SOURCE,
---news[].src =
NI_AUTHOR ---news[].auth =
---news[].headline =
---news[].summary =
from
    NEWS_XREF,
    NEWS_ITEM
where
    NI_ID = NX_NI_ID
    and NX_CO_ID = v_co_id
limit
    2;

else PERFORM -----news[].item = “”,
NI_DTS,
-----news[].dts =
NI_SOURCE,
-----news[].src =
NI_AUTHOR,
-----news[].auth =
NI_HEADLINE,
-----news[].headline =
NI_SUMMARY -----news[].summary =
from
    NEWS_XREF,
    NEWS_ITEM
where
    NI_ID = NX_NI_ID
    and NX_CO_ID = v_co_id
limit
    2;

-- news_len = row_count
end if;

END $$ LANGUAGE plpgsql;