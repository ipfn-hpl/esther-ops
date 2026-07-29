CREATE OR REPLACE FUNCTION get_report_with_calculations(p_report_id integer)
RETURNS TABLE (
    id                INTEGER,
    series_name       CHAR(8),
    shot              INTEGER,
    chief_engineer_id SMALLINT,
    researcher_id     SMALLINT,
    cc_pressure_sp    REAL,
    he_sp             REAL,
    h2_sp             REAL,
    o2_sp             REAL,
    n2_flushing       BOOLEAN,
    -- calculated columns
    total_gas_sp      REAL,
    he_fraction       REAL,
    h2_fraction       REAL,
    o2_fraction       REAL,
    press_purge_end REAL,
    he_h2_ratio       REAL
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        r.id,
        r.series_name,
        r.shot,
        r.chief_engineer_id,
        r.researcher_id,
        r.cc_pressure_sp,
        r.he_sp,
        r.h2_sp,
        r.o2_sp,
        r.n2_flushing,
        -- calculations
        -- Get the :WHEREfloat_val for a specific channel + phase combo
        MAX(s.float_val) FILTER (
             WHERE s.short_name = 'PT901' AND s.pulse_phase = 'CC_purge_end'
        ) AS press_purge_end,
        --(r.he_sp + r.h2_sp + r.o2_sp)::real                       AS press_purge_end,
        (r.he_sp + r.h2_sp + r.o2_sp)::real                       AS total_gas_sp,
        (r.he_sp / NULLIF(r.he_sp + r.h2_sp + r.o2_sp, 0))::real  AS he_fraction,
        (r.h2_sp / NULLIF(r.he_sp + r.h2_sp + r.o2_sp, 0))::real  AS h2_fraction,
        (r.o2_sp / NULLIF(r.he_sp + r.h2_sp + r.o2_sp, 0))::real  AS o2_fraction,
        (r.he_sp / NULLIF(r.h2_sp, 0))::real                      AS he_h2_ratio
    FROM reports r
    JOIN sample s ON s.reports_id = r.id
    WHERE (r.id = p_report_id);
    -- WHERE (p_series_name IS NULL OR r.series_name = p_series_name)
    --   AND (p_shot        IS NULL OR r.shot        = p_shot);
END;
$$;
