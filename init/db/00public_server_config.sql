-- public.public_server_config definition

-- Drop table

-- DROP TABLE public.public_server_config;

CREATE TABLE public.public_server_config (
	serverid int8 NOT NULL,
	is_ephemeral bool NOT NULL DEFAULT true,
	CONSTRAINT public_server_config_pk PRIMARY KEY (serverid)
);