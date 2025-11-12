--
-- PostgreSQL database dump
--

\restrict 0gG84LBh0TgiSb5CT6HjetrSjxxL3PIqp3idp57aFd1YEB2gg1nMLh0GmLjvgyD

-- Dumped from database version 18.0
-- Dumped by pg_dump version 18.0

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: flow_records; Type: TABLE; Schema: public; Owner: yourproductivity_user1
--

CREATE TABLE public.flow_records (
    id integer NOT NULL,
    user_id bigint NOT NULL,
    duration_minutes integer NOT NULL,
    recorded_at timestamp without time zone NOT NULL,
    username character varying(255)
);


ALTER TABLE public.flow_records OWNER TO yourproductivity_user1;

--
-- Name: flow_records_id_seq; Type: SEQUENCE; Schema: public; Owner: yourproductivity_user1
--

CREATE SEQUENCE public.flow_records_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.flow_records_id_seq OWNER TO yourproductivity_user1;

--
-- Name: flow_records_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: yourproductivity_user1
--

ALTER SEQUENCE public.flow_records_id_seq OWNED BY public.flow_records.id;


--
-- Name: sprint_records; Type: TABLE; Schema: public; Owner: yourproductivity_user1
--

CREATE TABLE public.sprint_records (
    id integer NOT NULL,
    user_id bigint NOT NULL,
    duration_minutes integer NOT NULL,
    recorded_at timestamp without time zone NOT NULL,
    username character varying(255)
);


ALTER TABLE public.sprint_records OWNER TO yourproductivity_user1;

--
-- Name: sprint_records_id_seq; Type: SEQUENCE; Schema: public; Owner: yourproductivity_user1
--

CREATE SEQUENCE public.sprint_records_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.sprint_records_id_seq OWNER TO yourproductivity_user1;

--
-- Name: sprint_records_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: yourproductivity_user1
--

ALTER SEQUENCE public.sprint_records_id_seq OWNED BY public.sprint_records.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: yourproductivity_user1
--

CREATE TABLE public.users (
    id bigint NOT NULL,
    telegram_id bigint NOT NULL,
    username character varying(255),
    created_at timestamp without time zone NOT NULL
);


ALTER TABLE public.users OWNER TO yourproductivity_user1;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: yourproductivity_user1
--

CREATE SEQUENCE public.users_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.users_id_seq OWNER TO yourproductivity_user1;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: yourproductivity_user1
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: flow_records id; Type: DEFAULT; Schema: public; Owner: yourproductivity_user1
--

ALTER TABLE ONLY public.flow_records ALTER COLUMN id SET DEFAULT nextval('public.flow_records_id_seq'::regclass);


--
-- Name: sprint_records id; Type: DEFAULT; Schema: public; Owner: yourproductivity_user1
--

ALTER TABLE ONLY public.sprint_records ALTER COLUMN id SET DEFAULT nextval('public.sprint_records_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: yourproductivity_user1
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Data for Name: flow_records; Type: TABLE DATA; Schema: public; Owner: yourproductivity_user1
--

COPY public.flow_records (id, user_id, duration_minutes, recorded_at, username) FROM stdin;
\.


--
-- Data for Name: sprint_records; Type: TABLE DATA; Schema: public; Owner: yourproductivity_user1
--

COPY public.sprint_records (id, user_id, duration_minutes, recorded_at, username) FROM stdin;
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: yourproductivity_user1
--

COPY public.users (id, telegram_id, username, created_at) FROM stdin;
\.


--
-- Name: flow_records_id_seq; Type: SEQUENCE SET; Schema: public; Owner: yourproductivity_user1
--

SELECT pg_catalog.setval('public.flow_records_id_seq', 19, true);


--
-- Name: sprint_records_id_seq; Type: SEQUENCE SET; Schema: public; Owner: yourproductivity_user1
--

SELECT pg_catalog.setval('public.sprint_records_id_seq', 4, true);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: yourproductivity_user1
--

SELECT pg_catalog.setval('public.users_id_seq', 3, true);


--
-- Name: flow_records flow_records_pkey; Type: CONSTRAINT; Schema: public; Owner: yourproductivity_user1
--

ALTER TABLE ONLY public.flow_records
    ADD CONSTRAINT flow_records_pkey PRIMARY KEY (id);


--
-- Name: sprint_records sprint_records_pkey; Type: CONSTRAINT; Schema: public; Owner: yourproductivity_user1
--

ALTER TABLE ONLY public.sprint_records
    ADD CONSTRAINT sprint_records_pkey PRIMARY KEY (id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: yourproductivity_user1
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: ix_users_telegram_id; Type: INDEX; Schema: public; Owner: yourproductivity_user1
--

CREATE UNIQUE INDEX ix_users_telegram_id ON public.users USING btree (telegram_id);


--
-- Name: flow_records flow_records_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: yourproductivity_user1
--

ALTER TABLE ONLY public.flow_records
    ADD CONSTRAINT flow_records_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(telegram_id);


--
-- Name: sprint_records sprint_records_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: yourproductivity_user1
--

ALTER TABLE ONLY public.sprint_records
    ADD CONSTRAINT sprint_records_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(telegram_id);


--
-- Name: SCHEMA public; Type: ACL; Schema: -; Owner: pg_database_owner
--

GRANT CREATE ON SCHEMA public TO yourproductivity_user;
GRANT ALL ON SCHEMA public TO yourproductivity_user1;


--
-- Name: DEFAULT PRIVILEGES FOR SEQUENCES; Type: DEFAULT ACL; Schema: public; Owner: postgres
--

ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT ALL ON SEQUENCES TO yourproductivity_user1;


--
-- Name: DEFAULT PRIVILEGES FOR TABLES; Type: DEFAULT ACL; Schema: public; Owner: postgres
--

ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT ALL ON TABLES TO yourproductivity_user1;


--
-- PostgreSQL database dump complete
--

\unrestrict 0gG84LBh0TgiSb5CT6HjetrSjxxL3PIqp3idp57aFd1YEB2gg1nMLh0GmLjvgyD

