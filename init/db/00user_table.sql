-- public.user_table definition

-- Drop table

-- DROP TABLE public.user_table;

CREATE TABLE public.user_table (
	user_id int8 NOT NULL,
	api_key varchar NOT NULL,
	instance_address varchar NOT NULL,
	user_name varchar NOT NULL
);