-- your_script.sql

-- Установка значения внешней переменной
-- \set external_value :external_value

-- Вывод значения внешней переменной
-- DO $$ 
-- BEGIN 
  select * from :external_value; 
-- END $$;