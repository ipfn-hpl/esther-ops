CREATE OR REPLACE FUNCTION get_last_reports(p_limit INT DEFAULT 10)
RETURNS TABLE (
      id INT, 
      series_name CHARACTER, 
      shot INT, 
      ce_id SMALLINT, 
      re_id SMALLINT, 
      cc_pressure_sp REAL,
      he_sp REAL  ,
      h2_sp REAL, 
      o2_sp REAL 
)
LANGUAGE plpgsql
STABLE
AS $$
BEGIN
    RETURN QUERY
      SELECT *
      FROM (
        SELECT r.id, r.series_name, r.shot, r.chief_engineer_id, 
        r.researcher_id, r.cc_pressure_sp, r.he_sp, r.h2_sp, r.o2_sp 
        FROM reports r
        ORDER BY id DESC LIMIT p_limit) s
      ORDER BY id ASC;
END;
$$;

