--create tables

--:'data_path'

DROP TABLE IF EXISTS account_permission CASCADE;
CREATE TABLE account_permission (
  ap_ca_id BIGINT NOT NULL,
  ap_acl CHAR(4) NOT NULL,
  ap_tax_id VARCHAR(20) NOT NULL,
  ap_l_name VARCHAR(25) NOT NULL,
  ap_f_name VARCHAR(20) NOT NULL
);

DROP TABLE IF EXISTS customer CASCADE;
CREATE TABLE customer (
  c_id BIGINT NOT NULL,
  c_tax_id VARCHAR(20) NOT NULL,
  c_st_id CHAR(4) NOT NULL,
  c_l_name VARCHAR(25) NOT NULL,
  c_f_name VARCHAR(20) NOT NULL,
  c_m_name CHAR(1),
  c_gndr CHAR(1),
  c_tier SMALLINT NOT NULL,
  c_dob DATE NOT NULL,
  c_ad_id BIGINT NOT NULL,
  c_ctry_1 VARCHAR(3),
  c_area_1 VARCHAR(3),
  c_local_1 VARCHAR(10),
  c_ext_1 VARCHAR(5),
  c_ctry_2 VARCHAR(3),
  c_area_2 VARCHAR(3),
  c_local_2 VARCHAR(10),
  c_ext_2 VARCHAR(5),
  c_ctry_3 VARCHAR(3),
  c_area_3 VARCHAR(3),
  c_local_3 VARCHAR(10),
  c_ext_3 VARCHAR(5),
  c_email_1 VARCHAR(50),
  c_email_2 VARCHAR(50)
);

DROP TABLE IF EXISTS customer_account CASCADE;
CREATE TABLE customer_account (
  ca_id BIGINT NOT NULL,
  ca_b_id BIGINT NOT NULL,
  ca_c_id BIGINT NOT NULL,
  ca_name VARCHAR(50),
  ca_tax_st SMALLINT NOT NULL,
  ca_bal DECIMAL(12,2) NOT NULL
);

DROP TABLE IF EXISTS customer_taxrate CASCADE;
CREATE TABLE customer_taxrate (
  cx_tx_id CHAR(4) NOT NULL,
  cx_c_id BIGINT NOT NULL
);

DROP TABLE IF EXISTS holding CASCADE;
CREATE TABLE holding (
  h_t_id BIGINT NOT NULL,
  h_ca_id BIGINT NOT NULL,
  h_s_symb CHAR(15) NOT NULL,
  h_dts TIMESTAMP NOT NULL,
  h_price DECIMAL(8,2) NOT NULL CHECK (h_price > 0),
  h_qty INTEGER NOT NULL
);

DROP TABLE IF EXISTS holding_history CASCADE;
CREATE TABLE holding_history (
  hh_h_t_id BIGINT NOT NULL,
  hh_t_id BIGINT NOT NULL,
  hh_before_qty INTEGER NOT NULL,
  hh_after_qty INTEGER NOT NULL
);

DROP TABLE IF EXISTS holding_summary CASCADE;
CREATE TABLE holding_summary (
  hs_ca_id BIGINT NOT NULL,
  hs_s_symb CHAR(15) NOT NULL,
  hs_qty INTEGER NOT NULL
);

DROP TABLE IF EXISTS watch_item CASCADE;
CREATE TABLE watch_item (
  wi_wl_id BIGINT NOT NULL,
  wi_s_symb CHAR(15) NOT NULL
);

DROP TABLE IF EXISTS watch_list CASCADE;
CREATE TABLE watch_list (
  wl_id BIGINT NOT NULL,
  wl_c_id BIGINT NOT NULL
);




DROP TABLE IF EXISTS broker CASCADE;
CREATE TABLE broker (
  b_id BIGINT NOT NULL,
  b_st_id CHAR(4) NOT NULL,
  b_name VARCHAR(49) NOT NULL,
  b_num_trades INTEGER NOT NULL,
  b_comm_total DECIMAL(12,2) NOT NULL
);

DROP TABLE IF EXISTS cash_transaction CASCADE;
CREATE TABLE cash_transaction (
  ct_t_id BIGINT NOT NULL,
  ct_dts TIMESTAMP NOT NULL,
  ct_amt DECIMAL(10,2) NOT NULL,
  ct_name VARCHAR(100)
);

DROP TABLE IF EXISTS charge CASCADE;
CREATE TABLE charge (
  ch_tt_id CHAR(3) NOT NULL,
  ch_c_tier SMALLINT NOT NULL,
  ch_chrg DECIMAL(10,2) NOT NULL CHECK (ch_chrg > 0)
);

DROP TABLE IF EXISTS commission_rate CASCADE;
CREATE TABLE commission_rate (
  cr_c_tier SMALLINT NOT NULL,
  cr_tt_id CHAR(3) NOT NULL,
  cr_ex_id CHAR(6) NOT NULL,
  cr_from_qty INTEGER NOT NULL CHECK (cr_from_qty >= 0),
  cr_to_qty INTEGER NOT NULL CHECK (cr_to_qty > cr_from_qty),
  cr_rate DECIMAL(5,2) NOT NULL CHECK (cr_rate >= 0)
);

DROP TABLE IF EXISTS settlement CASCADE;
CREATE TABLE settlement (
  se_t_id BIGINT NOT NULL,
  se_cash_type VARCHAR(40) NOT NULL,
  se_cash_due_date DATE NOT NULL,
  se_amt DECIMAL(10,2) NOT NULL
);

DROP TABLE IF EXISTS trade CASCADE;
CREATE TABLE trade (
  t_id BIGINT NOT NULL,
  t_dts TIMESTAMP NOT NULL,
  t_st_id CHAR(4) NOT NULL,
  t_tt_id CHAR(3) NOT NULL,
  t_is_cash BOOLEAN NOT NULL,
  t_s_symb CHAR(15) NOT NULL,
  t_qty INTEGER NOT NULL CHECK (t_qty > 0),
  t_bid_price DECIMAL(8,2) NOT NULL CHECK (t_bid_price > 0),
  t_ca_id BIGINT NOT NULL,
  t_exec_name VARCHAR(49) NOT NULL,
  t_trade_price DECIMAL(8,2),
  t_chrg DECIMAL(10,2) NOT NULL CHECK (t_chrg >= 0),
  t_comm DECIMAL(10,2) NOT NULL CHECK (t_comm >= 0),
  t_tax DECIMAL(10,2) NOT NULL CHECK (t_tax >= 0),
  t_lifo BOOLEAN NOT NULL
);

DROP TABLE IF EXISTS trade_history CASCADE;
CREATE TABLE trade_history (
  th_t_id BIGINT NOT NULL,
  th_dts TIMESTAMP NOT NULL,
  th_st_id CHAR(4) NOT NULL
);

DROP TABLE IF EXISTS trade_request CASCADE;
CREATE TABLE trade_request (
  tr_t_id BIGINT NOT NULL,
  tr_tt_id CHAR(3) NOT NULL,
  tr_s_symb CHAR(15) NOT NULL,
  tr_qty INTEGER NOT NULL CHECK (tr_qty > 0),
  tr_bid_price DECIMAL(8,2) NOT NULL CHECK (tr_bid_price > 0),
  tr_b_id BIGINT NOT NULL
);

DROP TABLE IF EXISTS trade_type CASCADE;
CREATE TABLE trade_type (
  tt_id CHAR(3) NOT NULL,
  tt_name VARCHAR(12) NOT NULL,
  tt_is_sell BOOLEAN NOT NULL,
  tt_is_mrkt BOOLEAN NOT NULL
);





DROP TABLE IF EXISTS company CASCADE;
CREATE TABLE company (
  co_id BIGINT NOT NULL,
  co_st_id CHAR(4) NOT NULL,
  co_name VARCHAR(60) NOT NULL,
  co_in_id CHAR(2) NOT NULL,
  co_sp_rate CHAR(4) NOT NULL,
  co_ceo VARCHAR(46) NOT NULL,
  co_ad_id BIGINT NOT NULL,
  co_desc VARCHAR(150) NOT NULL,
  co_open_date DATE NOT NULL
);

DROP TABLE IF EXISTS company_competitor CASCADE;
CREATE TABLE company_competitor (
  cp_co_id BIGINT NOT NULL,
  cp_comp_co_id BIGINT NOT NULL,
  cp_in_id CHAR(2) NOT NULL
);

DROP TABLE IF EXISTS daily_market CASCADE;
CREATE TABLE daily_market (
  dm_date DATE NOT NULL,
  dm_s_symb CHAR(15) NOT NULL,
  dm_close DECIMAL(8,2) NOT NULL,
  dm_high DECIMAL(8,2) NOT NULL,
  dm_low DECIMAL(8,2) NOT NULL,
  dm_vol BIGINT NOT NULL
);

DROP TABLE IF EXISTS exchange CASCADE;
CREATE TABLE exchange (
  ex_id CHAR(6) NOT NULL,
  ex_name VARCHAR(100) NOT NULL,
  ex_num_symb INTEGER NOT NULL,
  ex_open SMALLINT NOT NULL,
  ex_close SMALLINT NOT NULL,
  ex_desc VARCHAR(150),
  ex_ad_id BIGINT NOT NULL
);

DROP TABLE IF EXISTS financial CASCADE;
CREATE TABLE financial (
  fi_co_id BIGINT NOT NULL,
  fi_year SMALLINT NOT NULL,
  fi_qtr SMALLINT NOT NULL,
  fi_qtr_start_date DATE NOT NULL,
  fi_revenue DECIMAL(15,2) NOT NULL,
  fi_net_earn DECIMAL(15,2) NOT NULL,
  fi_basic_eps DECIMAL(10,2) NOT NULL,
  fi_dilut_eps DECIMAL(10,2) NOT NULL,
  fi_margin DECIMAL(10,2) NOT NULL,
  fi_inventory DECIMAL(15,2) NOT NULL,
  fi_assets DECIMAL(15,2) NOT NULL,
  fi_liability DECIMAL(15,2) NOT NULL,
  fi_out_basic BIGINT NOT NULL,
  fi_out_dilut BIGINT NOT NULL
);

DROP TABLE IF EXISTS industry CASCADE;
CREATE TABLE industry (
  in_id CHAR(2) NOT NULL,
  in_name VARCHAR(50) NOT NULL,
  in_sc_id CHAR(2) NOT NULL
);

DROP TABLE IF EXISTS last_trade CASCADE;
CREATE TABLE last_trade (
  lt_s_symb CHAR(15) NOT NULL,
  lt_dts TIMESTAMP NOT NULL,
  lt_price DECIMAL(8,2) NOT NULL,
  lt_open_price DECIMAL(8,2) NOT NULL,
  lt_vol BIGINT NOT NULL
);





DROP TABLE IF EXISTS news_item CASCADE;
CREATE TABLE news_item (
  ni_id BIGINT NOT NULL,
  ni_headline VARCHAR(80) NOT NULL,
  ni_summary VARCHAR(255) NOT NULL,
  ni_item BYTEA NOT NULL,
  ni_dts TIMESTAMP NOT NULL,
  ni_source VARCHAR(30) NOT NULL,
  ni_author VARCHAR(30)
);

DROP TABLE IF EXISTS news_xref CASCADE;
CREATE TABLE news_xref (
  nx_ni_id BIGINT NOT NULL,
  nx_co_id BIGINT NOT NULL
);

DROP TABLE IF EXISTS sector CASCADE;
CREATE TABLE sector (
  sc_id CHAR(2) NOT NULL,
  sc_name VARCHAR(30) NOT NULL
);

DROP TABLE IF EXISTS security CASCADE;
CREATE TABLE security (
  s_symb CHAR(15) NOT NULL,
  s_issue CHAR(6) NOT NULL,
  s_st_id CHAR(4) NOT NULL,
  s_name VARCHAR(70) NOT NULL,
  s_ex_id CHAR(6) NOT NULL,
  s_co_id BIGINT NOT NULL,
  s_num_out BIGINT NOT NULL,
  s_start_date DATE NOT NULL,
  s_exch_date DATE NOT NULL,
  s_pe DECIMAL(10,2) NOT NULL,
  s_52wk_high DECIMAL(8,2) NOT NULL,
  s_52wk_high_date DATE NOT NULL,
  s_52wk_low DECIMAL(8,2) NOT NULL,
  s_52wk_low_date DATE NOT NULL,
  s_dividend DECIMAL(10,2) NOT NULL,
  s_yield DECIMAL(5,2) NOT NULL
);





DROP TABLE IF EXISTS address CASCADE;
CREATE TABLE address (
  ad_id BIGINT NOT NULL,
  ad_line1 VARCHAR(80),
  ad_line2 VARCHAR(80),
  ad_zc_code CHAR(12) NOT NULL,
  ad_ctry VARCHAR(80)
);

DROP TABLE IF EXISTS status_type CASCADE;
CREATE TABLE status_type (
  st_id CHAR(4) NOT NULL,
  st_name CHAR(10) NOT NULL
);

DROP TABLE IF EXISTS taxrate CASCADE;
CREATE TABLE taxrate (
  tx_id CHAR(4) NOT NULL,
  tx_name VARCHAR(50) NOT NULL,
  tx_rate DECIMAL(6,5) NOT NULL CHECK (tx_rate >= 0)
);

DROP TABLE IF EXISTS zip_code CASCADE;
CREATE TABLE zip_code (
  zc_code CHAR(12) NOT NULL,
  zc_town VARCHAR(80) NOT NULL,
  zc_div VARCHAR(80) NOT NULL
);


-- DROP TABLE IF EXISTS data_maintenance_sequence;
-- CREATE UNLOGGED TABLE  data_maintenance_sequence (
--     session_id integer PRIMARY KEY,
--     last_execution timestamp,
--     last_value text
-- ) TABLESPACE ram_tablespace;

DROP TABLE IF EXISTS data_maintenance_sequence;
CREATE TABLE  data_maintenance_sequence (
    session_id integer PRIMARY KEY,
    last_execution timestamp,
    last_value text
) 
-- --filling tables
    \copy customer FROM '/flat_out/Customer.txt' DELIMITER '|';
    \copy customer_account FROM '/flat_out/CustomerAccount.txt' DELIMITER '|';
    \copy customer_taxrate FROM 'flat_out/CustomerTaxrate.txt' DELIMITER '|';
    \copy holding FROM 'flat_out/Holding.txt' DELIMITER '|';
    \copy holding_history FROM 'flat_out/HoldingHistory.txt' DELIMITER '|';
    \copy holding_summary FROM 'flat_out/HoldingSummary.txt' DELIMITER '|';
    \copy watch_item FROM 'flat_out/WatchItem.txt' DELIMITER '|';
    \copy watch_list FROM 'flat_out/WatchList.txt' DELIMITER '|';
    \copy broker FROM 'flat_out/Broker.txt' DELIMITER '|';
    \copy cash_transaction FROM 'flat_out/CashTransaction.txt' DELIMITER '|';
    \copy charge FROM 'flat_out/Charge.txt' DELIMITER '|';
    \copy commission_rate FROM 'flat_out/CommissionRate.txt' DELIMITER '|';
    \copy settlement FROM 'flat_out/Settlement.txt' DELIMITER '|';
    \copy trade FROM 'flat_out/Trade.txt' DELIMITER '|';
    \copy trade_history FROM 'flat_out/TradeHistory.txt' DELIMITER '|';
    \copy trade_request FROM 'flat_out/TradeRequest.txt' DELIMITER '|';
    \copy trade_type FROM 'flat_out/TradeType.txt' DELIMITER '|';
    \copy company FROM 'flat_out/Company.txt' DELIMITER '|';
    \copy company_competitor FROM 'flat_out/CompanyCompetitor.txt' DELIMITER '|';
    \copy daily_market FROM 'flat_out/DailyMarket.txt' DELIMITER '|';
    \copy exchange FROM 'flat_out/Exchange.txt' DELIMITER '|';
    \copy financial FROM 'flat_out/Financial.txt' DELIMITER '|';
    \copy industry FROM 'flat_out/Industry.txt' DELIMITER '|';
    \copy last_trade FROM 'flat_out/LastTrade.txt' DELIMITER '|';
    \copy news_item FROM 'flat_out/NewsItem.txt' DELIMITER '|';
    \copy news_xref FROM 'flat_out/NewsXRef.txt' DELIMITER '|';
    \copy sector FROM 'flat_out/Sector.txt' DELIMITER '|';
    \copy security FROM 'flat_out/Security.txt' DELIMITER '|';
    \copy address FROM 'flat_out/Address.txt' DELIMITER '|';
    \copy status_type FROM 'flat_out/StatusType.txt' DELIMITER '|';
    \copy taxrate FROM 'flat_out/Taxrate.txt' DELIMITER '|';
    \copy zip_code FROM 'flat_out/ZipCode.txt' DELIMITER '|';


    -- \copy account_permission FROM '/tmp/AccountPermission.txt' DELIMITER '|';
    -- \copy customer FROM '/tmp/Customer.txt' DELIMITER '|';
    -- \copy customer_account FROM '/tmp/CustomerAccount.txt' DELIMITER '|';
    -- \copy customer_taxrate FROM '/tmp/CustomerTaxrate.txt' DELIMITER '|';
    -- \copy holding FROM '/tmp/Holding.txt' DELIMITER '|';
    -- \copy holding_history FROM '/tmp/HoldingHistory.txt' DELIMITER '|';
    -- \copy holding_summary FROM '/tmp/HoldingSummary.txt' DELIMITER '|';
    -- \copy watch_item FROM '/tmp/WatchItem.txt' DELIMITER '|';
    -- \copy watch_list FROM '/tmp/WatchList.txt' DELIMITER '|';
    -- -- \copy COPY broker FROM '/tmp/Broker.txt' DELIMITER '|';
    -- \copy cash_transaction FROM '/tmp/CashTransaction.txt' DELIMITER '|';
    -- \copy charge FROM '/tmp/Charge.txt' DELIMITER '|';
    -- \copy commission_rate FROM '/tmp/CommissionRate.txt' DELIMITER '|';
    -- \copy settlement FROM '/tmp/Settlement.txt' DELIMITER '|';
    -- \copy trade FROM '/tmp/Trade.txt' DELIMITER '|';
    -- \copy trade_history FROM '/tmp/TradeHistory.txt' DELIMITER '|';
    -- -- \copy COPY trade_request FROM '/tmp/TradeRequest.txt' DELIMITER '|';
    -- \copy trade_type FROM '/tmp/TradeType.txt' DELIMITER '|';
    -- \copy company FROM '/tmp/Company.txt' DELIMITER '|';
    -- \copy company_competitor FROM '/tmp/CompanyCompetitor.txt' DELIMITER '|';
    -- \copy daily_market FROM '/tmp/DailyMarket.txt' DELIMITER '|';
    -- \copy exchange FROM '/tmp/Exchange.txt' DELIMITER '|';
    -- \copy financial FROM '/tmp/Financial.txt' DELIMITER '|';
    -- \copy industry FROM '/tmp/Industry.txt' DELIMITER '|';
    -- \copy last_trade FROM '/tmp/LastTrade.txt' DELIMITER '|';
    -- \copy news_item FROM '/tmp/NewsItem.txt' DELIMITER '|';
    -- \copy news_xref FROM '/tmp/NewsXRef.txt' DELIMITER '|';
    -- \copy sector FROM '/tmp/Sector.txt' DELIMITER '|';
    -- \copy security FROM '/tmp/Security.txt' DELIMITER '|';
    -- \copy address FROM '/tmp/Address.txt' DELIMITER '|';
    -- \copy status_type FROM '/tmp/StatusType.txt' DELIMITER '|';
    -- \copy taxrate FROM '/tmp/Taxrate.txt' DELIMITER '|';
    -- \copy zip_code FROM '/tmp/ZipCode.txt' DELIMITER '|';


--3 create keys


ALTER TABLE account_permission ADD CONSTRAINT pk_account_permission PRIMARY KEY (ap_ca_id, ap_tax_id);
ALTER TABLE customer ADD CONSTRAINT pk_customer PRIMARY KEY (c_id);
ALTER TABLE customer_account ADD CONSTRAINT pk_customer_account PRIMARY KEY (ca_id);
ALTER TABLE customer_taxrate ADD CONSTRAINT pk_customer_taxrate PRIMARY KEY (cx_c_id, cx_tx_id);
ALTER TABLE holding ADD CONSTRAINT pk_holding PRIMARY KEY (h_t_id);
ALTER TABLE holding_history ADD CONSTRAINT pk_holding_history PRIMARY KEY (hh_t_id, hh_h_t_id);
ALTER TABLE holding_summary ADD CONSTRAINT pk_holding_summary PRIMARY KEY (hs_ca_id, hs_s_symb);
ALTER TABLE watch_item ADD CONSTRAINT pk_watch_item PRIMARY KEY (wi_wl_id, wi_s_symb);
ALTER TABLE watch_list ADD CONSTRAINT pk_watch_list PRIMARY KEY (wl_id);
ALTER TABLE broker ADD CONSTRAINT pk_broker PRIMARY KEY (b_id);
ALTER TABLE cash_transaction ADD CONSTRAINT pk_cash_transaction PRIMARY KEY (ct_t_id);
ALTER TABLE charge ADD CONSTRAINT pk_charge PRIMARY KEY (ch_tt_id, ch_c_tier);
ALTER TABLE commission_rate ADD CONSTRAINT pk_commission_rate PRIMARY KEY (cr_c_tier, cr_tt_id, cr_ex_id, cr_from_qty);
ALTER TABLE settlement ADD CONSTRAINT pk_settlement PRIMARY KEY (se_t_id);
ALTER TABLE trade ADD CONSTRAINT pk_trade PRIMARY KEY (t_id);
ALTER TABLE trade_history ADD CONSTRAINT pk_trade_history PRIMARY KEY (th_t_id, th_st_id);
ALTER TABLE trade_request ADD CONSTRAINT pk_trade_request PRIMARY KEY (tr_t_id);
ALTER TABLE trade_type ADD CONSTRAINT pk_trade_type PRIMARY KEY (tt_id);
ALTER TABLE company ADD CONSTRAINT pk_company PRIMARY KEY (co_id);
ALTER TABLE company_competitor ADD CONSTRAINT pk_company_competitor PRIMARY KEY (cp_co_id, cp_comp_co_id, cp_in_id);
ALTER TABLE daily_market ADD CONSTRAINT pk_daily_market PRIMARY KEY (dm_s_symb, dm_date);
ALTER TABLE exchange ADD CONSTRAINT pk_exchange PRIMARY KEY (ex_id);
ALTER TABLE financial ADD CONSTRAINT pk_financial PRIMARY KEY (fi_co_id, fi_year, fi_qtr);
ALTER TABLE industry ADD CONSTRAINT pk_industry PRIMARY KEY (in_id);
ALTER TABLE last_trade ADD CONSTRAINT pk_last_trade PRIMARY KEY (lt_s_symb);
ALTER TABLE news_item ADD CONSTRAINT pk_news_item PRIMARY KEY (ni_id);
ALTER TABLE news_xref ADD CONSTRAINT pk_news_xref PRIMARY KEY (nx_co_id, nx_ni_id);
ALTER TABLE sector ADD CONSTRAINT pk_sector PRIMARY KEY (sc_id);
ALTER TABLE security ADD CONSTRAINT pk_security PRIMARY KEY (s_symb);
ALTER TABLE address ADD CONSTRAINT pk_address PRIMARY KEY (ad_id);
ALTER TABLE status_type ADD CONSTRAINT pk_status_type PRIMARY KEY (st_id);
ALTER TABLE taxrate ADD CONSTRAINT pk_taxrate PRIMARY KEY (tx_id);
ALTER TABLE zip_code ADD CONSTRAINT pk_zip_code PRIMARY KEY (zc_code);

ALTER TABLE account_permission ADD CONSTRAINT fk_account_permission_ca
 FOREIGN KEY (ap_ca_id) REFERENCES customer_account (ca_id);
ALTER TABLE customer ADD CONSTRAINT fk_customer_st
 FOREIGN KEY (c_st_id) REFERENCES status_type (st_id);
ALTER TABLE customer ADD CONSTRAINT fk_customer_ad
 FOREIGN KEY (c_ad_id) REFERENCES address (ad_id);
ALTER TABLE customer_account ADD CONSTRAINT fk_customer_account_b
 FOREIGN KEY (ca_b_id) REFERENCES broker (b_id);
ALTER TABLE customer_account ADD CONSTRAINT fk_customer_account_c
 FOREIGN KEY (ca_c_id) REFERENCES customer (c_id);
ALTER TABLE customer_taxrate ADD CONSTRAINT fk_customer_taxrate_tx
 FOREIGN KEY (cx_tx_id) REFERENCES taxrate (tx_id);
ALTER TABLE customer_taxrate ADD CONSTRAINT fk_customer_taxrate_c
 FOREIGN KEY (cx_c_id) REFERENCES customer (c_id);
ALTER TABLE holding ADD CONSTRAINT fk_holding_t
 FOREIGN KEY (h_t_id) REFERENCES trade (t_id);
ALTER TABLE holding ADD CONSTRAINT fk_holding_hs
 FOREIGN KEY (h_ca_id, h_s_symb) REFERENCES holding_summary (hs_ca_id, hs_s_symb);
ALTER TABLE holding_history ADD CONSTRAINT fk_holding_history_t1
 FOREIGN KEY (hh_h_t_id) REFERENCES trade (t_id);
ALTER TABLE holding_history ADD CONSTRAINT fk_holding_history_t2
 FOREIGN KEY (hh_t_id) REFERENCES trade (t_id);
ALTER TABLE holding_summary ADD CONSTRAINT fk_holding_summary_ca
 FOREIGN KEY (hs_ca_id) REFERENCES customer_account (ca_id);
ALTER TABLE holding_summary ADD CONSTRAINT fk_holding_summary_s
 FOREIGN KEY (hs_s_symb) REFERENCES security (s_symb);
ALTER TABLE watch_item ADD CONSTRAINT fk_watch_item_wl
 FOREIGN KEY (wi_wl_id) REFERENCES watch_list (wl_id);
ALTER TABLE watch_item ADD CONSTRAINT fk_watch_item_s
 FOREIGN KEY (wi_s_symb) REFERENCES security (s_symb);
ALTER TABLE watch_list ADD CONSTRAINT fk_watch_list_c
 FOREIGN KEY (wl_c_id) REFERENCES customer (c_id);

ALTER TABLE broker ADD CONSTRAINT fk_broker_st
 FOREIGN KEY (b_st_id) REFERENCES status_type (st_id);
ALTER TABLE cash_transaction ADD CONSTRAINT fk_cash_transaction_t
 FOREIGN KEY (ct_t_id) REFERENCES trade (t_id);
ALTER TABLE charge ADD CONSTRAINT fk_charge_tt
 FOREIGN KEY (ch_tt_id) REFERENCES trade_type (tt_id);
ALTER TABLE commission_rate ADD CONSTRAINT fk_commission_rate_tt
 FOREIGN KEY (cr_tt_id) REFERENCES trade_type (tt_id);
ALTER TABLE commission_rate ADD CONSTRAINT fk_commission_rate_ex
 FOREIGN KEY (cr_ex_id) REFERENCES exchange (ex_id);
ALTER TABLE settlement ADD CONSTRAINT fk_settlement_t
 FOREIGN KEY (se_t_id) REFERENCES trade (t_id);
ALTER TABLE trade ADD CONSTRAINT fk_trade_st
 FOREIGN KEY (t_st_id) REFERENCES status_type (st_id);
ALTER TABLE trade ADD CONSTRAINT fk_trade_tt
 FOREIGN KEY (t_tt_id) REFERENCES trade_type (tt_id);
ALTER TABLE trade ADD CONSTRAINT fk_trade_s
 FOREIGN KEY (t_s_symb) REFERENCES security (s_symb);
ALTER TABLE trade ADD CONSTRAINT fk_trade_ca
 FOREIGN KEY (t_ca_id) REFERENCES customer_account (ca_id);
ALTER TABLE trade_history ADD CONSTRAINT fk_trade_history_t
 FOREIGN KEY (th_t_id) REFERENCES trade (t_id);
ALTER TABLE trade_history ADD CONSTRAINT fk_trade_history_st
 FOREIGN KEY (th_st_id) REFERENCES status_type (st_id);
ALTER TABLE trade_request ADD CONSTRAINT fk_trade_request_t
 FOREIGN KEY (tr_t_id) REFERENCES trade (t_id);
ALTER TABLE trade_request ADD CONSTRAINT fk_trade_request_tt
 FOREIGN KEY (tr_tt_id) REFERENCES trade_type (tt_id);
ALTER TABLE trade_request ADD CONSTRAINT fk_trade_request_s
 FOREIGN KEY (tr_s_symb) REFERENCES security (s_symb);
ALTER TABLE trade_request ADD CONSTRAINT fk_trade_request_b
 FOREIGN KEY (tr_b_id) REFERENCES broker (b_id);

ALTER TABLE company ADD CONSTRAINT fk_company_st
 FOREIGN KEY (co_st_id) REFERENCES status_type (st_id);
ALTER TABLE company ADD CONSTRAINT fk_company_in
 FOREIGN KEY (co_in_id) REFERENCES industry (in_id);
ALTER TABLE company ADD CONSTRAINT fk_company_ad
 FOREIGN KEY (co_ad_id) REFERENCES address (ad_id);
ALTER TABLE company_competitor ADD CONSTRAINT fk_company_competitor_co1
 FOREIGN KEY (cp_co_id) REFERENCES company (co_id);
ALTER TABLE company_competitor ADD CONSTRAINT fk_company_competitor_co2
 FOREIGN KEY (cp_comp_co_id) REFERENCES company (co_id);
ALTER TABLE company_competitor ADD CONSTRAINT fk_company_competitor_in
 FOREIGN KEY (cp_in_id) REFERENCES industry (in_id);
ALTER TABLE daily_market ADD CONSTRAINT fk_daily_market_s
 FOREIGN KEY (dm_s_symb) REFERENCES security (s_symb);
ALTER TABLE exchange ADD CONSTRAINT fk_exchange_ad
 FOREIGN KEY (ex_ad_id) REFERENCES address (ad_id);
ALTER TABLE financial ADD CONSTRAINT fk_financial_co
 FOREIGN KEY (fi_co_id) REFERENCES company (co_id);
ALTER TABLE industry ADD CONSTRAINT fk_industry_sc
 FOREIGN KEY (in_sc_id) REFERENCES sector (sc_id);
ALTER TABLE last_trade ADD CONSTRAINT fk_last_trade_s
 FOREIGN KEY (lt_s_symb) REFERENCES security (s_symb);
ALTER TABLE news_xref ADD CONSTRAINT fk_news_xref_ni
 FOREIGN KEY (nx_ni_id) REFERENCES news_item (ni_id);
ALTER TABLE news_xref ADD CONSTRAINT fk_news_xref_co
 FOREIGN KEY (nx_co_id) REFERENCES company (co_id);
ALTER TABLE security ADD CONSTRAINT fk_security_st
 FOREIGN KEY (s_st_id) REFERENCES status_type (st_id);
ALTER TABLE security ADD CONSTRAINT fk_security_ex
 FOREIGN KEY (s_ex_id) REFERENCES exchange (ex_id);
ALTER TABLE security ADD CONSTRAINT fk_security_co
 FOREIGN KEY (s_co_id) REFERENCES company (co_id);

ALTER TABLE address ADD CONSTRAINT fk_address_zc
 FOREIGN KEY (ad_zc_code) REFERENCES zip_code (zc_code);


--4 create fk index

CREATE INDEX i_fk_customer_st ON customer
 (c_st_id);
CREATE INDEX i_fk_customer_ad ON customer
 (c_ad_id);
CREATE INDEX i_fk_customer_account_b ON customer_account
 (ca_b_id);
CREATE INDEX i_fk_customer_account_c ON customer_account
 (ca_c_id);
CREATE INDEX i_fk_customer_taxrate_tx ON customer_taxrate
 (cx_tx_id);
CREATE INDEX i_fk_holding_hs ON holding
 (h_ca_id, h_s_symb);
CREATE INDEX i_fk_holding_history_t1 ON holding_history
 (hh_h_t_id);
CREATE INDEX i_fk_holding_summary_s ON holding_summary
 (hs_s_symb);
CREATE INDEX i_fk_watch_item_s ON watch_item
 (wi_s_symb);
CREATE INDEX i_fk_watch_list_c ON watch_list
 (wl_c_id);
CREATE INDEX i_fk_broker_st ON broker
 (b_st_id);
CREATE INDEX i_fk_commission_rate_tt ON commission_rate
 (cr_tt_id);
CREATE INDEX i_fk_commission_rate_ex ON commission_rate
 (cr_ex_id);
CREATE INDEX i_fk_trade_st ON trade
 (t_st_id);
CREATE INDEX i_fk_trade_tt ON trade
 (t_tt_id);
CREATE INDEX i_fk_trade_history_st ON trade_history
 (th_st_id);
CREATE INDEX i_fk_trade_request_tt ON trade_request
 (tr_tt_id);
CREATE INDEX i_fk_trade_request_s ON trade_request
 (tr_s_symb);
CREATE INDEX i_fk_trade_request_b ON trade_request
 (tr_b_id);
CREATE INDEX i_fk_company_st ON company
 (co_st_id);
CREATE INDEX i_fk_company_in ON company
 (co_in_id);
CREATE INDEX i_fk_company_ad ON company
 (co_ad_id);
CREATE INDEX i_fk_company_competitor_co2 ON company_competitor
 (cp_comp_co_id);
CREATE INDEX i_fk_company_competitor_in ON company_competitor
 (cp_in_id);
CREATE INDEX i_fk_exchange_ad ON exchange
 (ex_ad_id);
CREATE INDEX i_fk_industry_sc ON industry
 (in_sc_id);
CREATE INDEX i_fk_news_xref_ni ON news_xref
 (nx_ni_id);
CREATE INDEX i_fk_security_st ON security
 (s_st_id);
CREATE INDEX i_fk_security_ex ON security
 (s_ex_id);
CREATE INDEX i_fk_security_co ON security
 (s_co_id);
CREATE INDEX i_fk_address_zc ON address
 (ad_zc_code);


--5 create sequence

DROP SEQUENCE IF EXISTS seq_trade_id;
CREATE SEQUENCE seq_trade_id INCREMENT 1;
SELECT SETVAL('seq_trade_id',(SELECT MAX(t_id) FROM trade));

-- 6 analyze

ANALYZE account_permission;
ANALYZE customer;
ANALYZE customer_account;
ANALYZE customer_taxrate;
ANALYZE holding;
ANALYZE holding_history;
ANALYZE holding_summary;
ANALYZE watch_item;
ANALYZE watch_list;
ANALYZE broker;
ANALYZE cash_transaction;
ANALYZE charge;
ANALYZE commission_rate;
ANALYZE settlement;
ANALYZE trade;
ANALYZE trade_history;
ANALYZE trade_request;
ANALYZE trade_type;
ANALYZE company;
ANALYZE company_competitor;
ANALYZE daily_market;
ANALYZE exchange;
ANALYZE financial;
ANALYZE industry;
ANALYZE last_trade;
ANALYZE news_item;
ANALYZE news_xref;
ANALYZE sector;
ANALYZE security;
ANALYZE address;
ANALYZE status_type;
ANALYZE taxrate;
ANALYZE zip_code;
