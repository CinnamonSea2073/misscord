-- public.notes_table definition

-- Drop table

-- DROP TABLE public.notes_table;

CREATE TABLE public.notes_table (
	guild_id int8 NOT NULL,
	notes_id varchar NOT NULL,
	CONSTRAINT notes_table_pk PRIMARY KEY (guild_id)
);