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
     press_purge_end   REAL,
     --press_purge_end2   REAL,
    he_h2_ratio       REAL
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_purge_end REAL;
    v_partial_o2 REAL;
    v_partial_he1 REAL;
    v_partial_h2 REAL;
    v_partial_he2 REAL;
    v_end_o2 REAL;
    v_end_he1 REAL;
    v_end_h2 REAL;
    v_end_he2 REAL;
    v_gas_sum   REAL;
BEGIN
      -- fetch the sample values into a variable
    SELECT MAX(s.float_val)::real
    INTO v_purge_end
    FROM sample s
    WHERE s.reports_id = p_report_id
      AND TRIM(s.short_name)  = 'PT901'
      AND TRIM(s.pulse_phase) = 'CC_purge_end';

    SELECT MAX(s.float_val)::real
    INTO v_end_he2
    FROM sample s
    WHERE s.reports_id = p_report_id
      AND TRIM(s.short_name)  = 'PT901'
      AND TRIM(s.pulse_phase) = 'CC_he2_end';

    SELECT MAX(s.float_val)::real
    INTO v_end_o2
    FROM sample s
    WHERE s.reports_id = p_report_id
      AND TRIM(s.short_name)  = 'PT901'
      AND TRIM(s.pulse_phase) = 'CC_o2_end';

    -- 3. Calculations between locals
    v_partial_o2 := (v_end_o2 - v_purge_end);
      -- v_purge_ratio := v_purge_end / NULLIF(v_gas_sum, 0);
      --
    -- 4. Conditional logic using locals
    -- IF v_purge_ratio IS NULL THEN
    --     v_is_leaky  := NULL;
    --     v_corrected := NULL;
    -- ELSIF v_purge_ratio > 1.1 THEN
    --     v_is_leaky  := TRUE;
    --     v_corrected := v_purge_end * 0.95;   -- apply correction
    -- ELSE
    --     v_is_leaky  := FALSE;
    --     v_corrected := v_purge_end;
    -- END IF;

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
        -- calculations, in the SAME order as RETURNS TABLE
        (r.he_sp + r.h2_sp + r.o2_sp)::real                       AS total_gas_sp,
        (r.he_sp / NULLIF(r.he_sp + r.h2_sp + r.o2_sp, 0))::real  AS he_fraction,
        (r.h2_sp / NULLIF(r.he_sp + r.h2_sp + r.o2_sp, 0))::real  AS h2_fraction,
         -- (r.o2_sp / NULLIF(r.he_sp + r.h2_sp + r.o2_sp, 0))::real  AS o2_fraction,
          v_purge_end                                              AS press_purge_end,
        (v_partial_o2 / NULLIF(v_end_he2, 0))::real  AS o2_fraction,

        (r.he_sp / NULLIF(r.h2_sp, 0))::real   AS he_h2_ratio
    FROM reports r
    -- LEFT JOIN sample s ON s.reports_id = r.id
    WHERE r.id = p_report_id
    GROUP BY r.id;
END;
$$;
