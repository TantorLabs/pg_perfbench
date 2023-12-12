# https://github.com/O2eg/pg_anon/blob/master/dict/test.py
{
	
		"tpc-c":{
			"schema":"schm_other_1",
			"table":"some_tbl",
			"fields": {
					"val":"'text const'"
			}
		},
		"tpc-e":{
			"schema":"schm_other_2",
			"table":"some_tbl",
			"raw_sql": "SELECT id, val || ' modified' as val FROM schm_other_2.some_tbl"
		}
}