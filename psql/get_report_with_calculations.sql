-- Do first:
-- DROP FUNCTION get_report_with_calculations(integer);
CREATE OR REPLACE FUNCTION get_report_with_calculations(p_report_id integer)
RETURNS TABLE (
    id                INTEGER,
    series CHAR(8),
    shot              INTEGER,
    -- chief_engineer_id SMALLINT,
    --researcher_id     SMALLINT,
    cc_pressure_sp    REAL,
    he_sp             REAL,
    h2_sp             REAL,
    o2_sp             REAL,
    n2_flushing       BOOLEAN,
    press_purge_end   REAL,
    -- calculated columns
    -- total_gas_sp      REAL,
    o2_fraction       REAL,
    h2_fraction       REAL,
    he_fraction       REAL,
    o2_stoich       REAL,
    h2_stoich       REAL,
    he_stoich       REAL
    -- he_h2_ratio       REAL
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_ambient_pressure REAL;
    v_purge_end REAL;
    v_end_o2 REAL;
    v_end_he1 REAL;
    v_end_h2 REAL;
    v_end_he2 REAL;
    v_end_abs REAL;
    v_partial_o2 REAL;
    v_partial_he1 REAL;
    v_partial_h2 REAL;
    v_partial_he2 REAL;
    v_o2_fraction REAL;
    v_h2_fraction REAL;
    v_he_fraction REAL;
    v_stoich_o2  REAL;
    v_stoich_h2  REAL;
    v_stoich_he  REAL;
BEGIN
      -- fetch the sample values into a variable
    SELECT MAX(s.float_val)::real
    INTO v_ambient_pressure
    FROM sample s
    WHERE s.reports_id = p_report_id
      AND s.short_name  = 'ambient_pressure'
      AND s.pulse_phase = 'CC_start';

    SELECT MAX(s.float_val)::real
    INTO v_purge_end
    FROM sample s
    WHERE s.reports_id = p_report_id
      AND TRIM(s.short_name)  = 'PT901'
      AND TRIM(s.pulse_phase) = 'CC_purge_end';

    SELECT MAX(s.float_val)::real
    INTO v_end_he1
    FROM sample s
    WHERE s.reports_id = p_report_id
      AND TRIM(s.short_name)  = 'PT901'
      AND TRIM(s.pulse_phase) = 'CC_he1_end';

    SELECT MAX(s.float_val)::real
    INTO v_end_o2
    FROM sample s
    WHERE s.reports_id = p_report_id
      AND TRIM(s.short_name)  = 'PT901'
      AND TRIM(s.pulse_phase) = 'CC_o2_end';

    SELECT MAX(s.float_val)::real
    INTO v_end_h2
    FROM sample s
    WHERE s.reports_id = p_report_id
      AND TRIM(s.short_name)  = 'PT901'
      AND TRIM(s.pulse_phase) = 'CC_h2_end';

    SELECT MAX(s.float_val)::real
    INTO v_end_he2
    FROM sample s
    WHERE s.reports_id = p_report_id
      AND TRIM(s.short_name)  = 'PT901'
      AND TRIM(s.pulse_phase) = 'CC_he2_end';

    -- 3. Calculations between locals
    -- IF v_purge_ratio IS NULL OR v_partial_o2 IS NULL THEN
        -- (
    v_partial_o2 := NULL;
    v_partial_he1 := NULL;
    v_partial_h2 := NULL;
    v_partial_he2 := NULL;
    v_stoich_o2 := NULL;
    v_stoich_h2 := NULL;
    v_stoich_he := NULL;
    IF v_purge_end IS NULL THEN
      v_partial_o2 := NULL;
    ELSE
      IF v_ambient_pressure IS NULL THEN
        v_end_abs := 1.0 + v_purge_end  + v_end_he2; 
      ELSE
        v_end_abs := v_ambient_pressure/1000.0 + v_purge_end + v_end_he2;
      END IF;
      -- IF v_end_he2 IS NULL THEN
      -- ELSE
      IF v_end_he2 IS NOT NULL THEN
        -- IF v_end_o2 IS NULL THEN
        --   v_partial_o2 := NULL;
        --   v_partial_he1 := NULL;
        -- ELSE
        IF v_end_o2 IS NOT NULL THEN
          v_partial_o2 := (v_end_o2 - v_purge_end);
          v_o2_fraction := (v_partial_o2 / v_end_abs);
          IF v_end_he1 IS NULL THEN
            v_partial_he1 := NULL;
          ELSE
            v_partial_he1 := (v_end_he1 - v_end_o2);
            --v_o2_fraction := (v_partial_o2 / v_end_he2);
          END IF;
          IF v_end_h2 IS NULL THEN
            v_partial_h2 := NULL;
          ELSE
            v_partial_h2 := (v_end_h2 - v_end_he1);
            v_h2_fraction := (v_partial_h2 / v_end_abs);
            v_partial_he2 := (v_end_he2 - v_end_h2);
            v_he_fraction := 1.0 - v_o2_fraction -v_h2_fraction;
            v_stoich_o2 := 2.0/v_h2_fraction * v_o2_fraction;
            v_stoich_h2 := 2.0;
            v_stoich_he := 2.0/v_h2_fraction * v_he_fraction;
       -- (( v_ambient_pressure/1000.0 + v_purge_end+ v_partial_he1 + v_partial_he2 ) / NULLIF(v_end_he2, 0))::real  AS he_fraction,
          END IF;
        END IF;
      END IF;
    END IF;
    -- v_partial_o2  := (v_end_o2 - v_purge_end);
    -- v_partial_h2  := (v_end_h2 - v_end_he1);
    -- v_partial_he2 := (v_end_he2 - v_end_h2);
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
        -- r.chief_engineer_id,
        -- r.researcher_id,
        r.cc_pressure_sp,
        r.he_sp,
        r.h2_sp,
        r.o2_sp,
        r.n2_flushing,
        -- calculations, in the SAME order as RETURNS TABLE
        v_purge_end                                  AS press_purge_end,
        --(r.he_sp + r.h2_sp + r.o2_sp)::real                       AS total_gas_sp,
        -- (r.he_sp / NULLIF(r.he_sp + r.h2_sp + r.o2_sp, 0))::real  AS he_fraction,
        -- (r.h2_sp / NULLIF(r.he_sp + r.h2_sp + r.o2_sp, 0))::real  AS h2_fraction,
         -- (r.o2_sp / NULLIF(r.he_sp + r.h2_sp + r.o2_sp, 0))::real  AS o2_fraction,
        -- (v_partial_o2 / NULLIF(v_end_he2, 0))::real  AS o2_fraction,
        -- (v_partial_o2 / NULLIF(v_end_he2, 0))::real  
        v_o2_fraction AS o2_fraction,
        -- (v_partial_h2 / NULLIF(v_end_he2, 0))::real  AS h2_fraction,
        v_h2_fraction AS h2_fraction,
        -- (( v_ambient_pressure/1000.0 + v_purge_end+ v_partial_he1 + v_partial_he2 ) / NULLIF(v_end_he2, 0))::real  AS he_fraction,
        v_he_fraction AS he_fraction,
        v_stoich_o2  AS o2_stoich,
        (2.0)::real  AS h2_stoich,
        (v_stoich_he)::real  AS he_stoich

        -- (r.he_sp / NULLIF(r.h2_sp, 0))::real   AS he_h2_ratio
    FROM reports r
    -- LEFT JOIN sample s ON s.reports_id = r.id
    WHERE r.id = p_report_id
    GROUP BY r.id;
END;
$$;
