--postgres 14
CREATE TABLE public.ec2_instance_pricing_test (
    pk character varying(255) PRIMARY KEY NOT NULL,
    date date NOT NULL,
    instance_type character varying(20) NOT NULL,
    operating_system character varying(60) NOT NULL,
    region character varying(15) NOT NULL,
    cost_per_hr double precision,
    cpu_ct integer,
    ram_size_gb real,
    storage_type character varying(20),
    network_throughput character varying(20)
);

ALTER TABLE public.ec2_instance_pricing_test OWNER TO scrpr_test;
-- ALTER TABLE ONLY public.ec2_instance_pricing_test ADD CONSTRAINT ec2_instance_pricing_test_pkey PRIMARY KEY (pk);

INSERT INTO ec2_instance_pricing_test (pk, date, instance_type, operating_system, region, cost_per_hr, cpu_ct, ram_size_gb, storage_type, network_throughput)
VALUES (
    '1900-01-01-xyz.test-operating system test-region test',
    '1900-01-01',
    'xyz.test',
    'operating system test',
    'region test',
    10.1234,
    129,
    767.5,
    'storage type test',
    'network thruput test'
);

--CREATE TABLE IF NOT EXISTS metric_data_test (
CREATE TABLE IF NOT EXISTS metric_data (
    -- run_no SERIAL PRIMARY KEY,
    run_no SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    threads INTEGER NOT NULL,
    oses INTEGER,
    regions INTEGER,
    t_init FLOAT,
    t_run FLOAT,
    s_csv INTEGER,
    s_db INTEGER,
    reported_errors INTEGER,
    command_line VARCHAR(512)
);

-- ALTER TABLE metric_data_test OWNER TO scrpr_test;
-- ALTER TABLE ONLY metric_data_test
--     ADD CONSTRAINT metric_data_test_pkey PRIMARY KEY (run_no);
ALTER TABLE metric_data OWNER TO scrpr_test;
-- ALTER TABLE ONLY metric_data ADD CONSTRAINT metric_data_pkey PRIMARY KEY (run_no);

INSERT INTO metric_data (date, threads, oses, regions, t_init, t_run, s_csv, s_db, reported_errors, command_line)
VALUES (
    '1900-01-01',
    1,
    1,
    1,
    10.01,
    60.06,
    123456,
    234567,
    0,
    'test command line'
);
