-- public.channel_table definition

-- Drop table

-- DROP TABLE public.channel_table;

CREATE TABLE public.channel_table (
	guild_id int8 NOT NULL,
	channel_id int8 NOT NULL,
	instance_address varchar NOT NULL,
	api_key varchar NOT NULL,
	CONSTRAINT channel_table_pk PRIMARY KEY (guild_id)
);