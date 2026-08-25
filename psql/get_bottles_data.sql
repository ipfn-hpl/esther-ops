
-- DROP FUNCTION get_bottles_data(integer, text);
CREATE OR REPLACE FUNCTION get_bottles_data(p_report_id integer, p_phase text DEFAULT 'CC_start')
RETURNS TABLE (
    id            INTEGER,
    n2            REAL,
    o2            REAL,
    he1           REAL,
    h2            REAL,
    he2           REAL,
    n2_command    REAL
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_n2 REAL;
    v_o2 REAL;
    v_he1 REAL;
    v_h2 REAL;
    v_he2 REAL;
    v_n2_command REAL;
BEGIN
      -- fetch the sample values into a variable
    SELECT s.float_val::real
    INTO v_n2
    FROM sample s
    WHERE s.reports_id = p_report_id
      AND s.short_name  = 'PT101'
      AND s.pulse_phase = p_phase;

    SELECT MAX(s.float_val)::real
    INTO v_o2
    FROM sample s
    WHERE s.reports_id = p_report_id
      AND s.short_name  = 'PT201'
      AND s.pulse_phase = p_phase;

    SELECT s.float_val::real
    INTO v_he1
    FROM sample s
    WHERE s.reports_id = p_report_id
      AND s.short_name  = 'PT301'
      AND s.pulse_phase = p_phase;

    SELECT MAX(s.float_val)::real
    INTO v_h2
    FROM sample s
    WHERE s.reports_id = p_report_id
      AND s.short_name  = 'PT401'
      AND s.pulse_phase = p_phase;

    SELECT s.float_val::real
    INTO v_he2
    FROM sample s
    WHERE s.reports_id = p_report_id
      AND s.short_name  = 'PT501'
      AND s.pulse_phase = p_phase;

    SELECT s.float_val::real
    INTO v_n2_command
    FROM sample s
    WHERE s.reports_id = p_report_id
      AND s.short_name  = 'PT801'
      AND s.pulse_phase = p_phase;

    RETURN QUERY
    SELECT
        r.id,
        v_n2 AS n2,
        v_o2 AS o2,
        v_he1 AS he1,
        v_h2 AS h2,
        v_he2 AS he2,
        v_n2_command AS n2_command
    FROM reports r
    -- LEFT JOIN sample s ON s.reports_id = r.id
    WHERE r.id = p_report_id
    GROUP BY r.id;
END;
$$;
-- SELECT * FROM get_bottles_data(100, 'CC_start');
