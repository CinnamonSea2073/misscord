-- public.genshin_notification definition

-- Drop table

-- DROP TABLE public.genshin_notification;

CREATE TABLE public.user_table (
	user_id int8 NOT NULL,
	api_key char(50) NOT NULL,
	instance_address char(50) NOT NULL,
	user_name char(50) NOT NULL
);