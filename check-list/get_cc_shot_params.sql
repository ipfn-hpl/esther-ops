CREATE OR REPLACE FUNCTION get_cc_shot_params(p_report_id integer)
RETURNS TABLE (
    ambient_pressure double precision,
    fill_pressure double precision,
    kistler_range double precision,
    kistler_deltaP double precision
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
    SELECT
        -- Query 1
        (
            SELECT float_val 
            FROM sample 
            WHERE short_name='ambientPressure' AND reports_id = p_report_id
        ) AS ambient_pressure,

        -- Query 2
        (
            SELECT float_val 
            FROM sample 
            WHERE short_name='PT901' AND pulse_phase='CC_Step8_End' 
            AND reports_id = p_report_id
        ) AS fill_pressure,

        -- Query 3
        (
            SELECT float_val 
            FROM sample 
            WHERE short_name='CC_Range_Kistler' AND pulse_phase='CC_Pulse' 
            AND reports_id = p_report_id
        ) AS kistler_range,

        -- Query 4
        (
            SELECT float_val 
            FROM sample 
            WHERE short_name='CC_DeltaP_Kistler' AND pulse_phase='CC_Pulse' 
            AND reports_id = p_report_id
        ) AS kistler_deltaP;

END;
$$;

--Call it like this:
-- SELECT *
 --FROM get_cc_shot_params(316);

