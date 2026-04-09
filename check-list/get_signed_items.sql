CREATE OR REPLACE FUNCTION get_signed_items(
p_report_id INT, 
p_day_phase_id INT, 
p_subsystem_id INT, 
p_limit INT DEFAULT 10)
RETURNS TABLE (
      item_id INT, 
      seq_order SMALLINT, 
      time_date TIMESTAMP,
      resp TEXT,
      c_status TEXT, 
      item_name  TEXT
)
LANGUAGE plpgsql
STABLE
AS $$
BEGIN
    RETURN QUERY
      SELECT
        c.item_id, 
        i.seq_order, 
        c.time_date, 
        r.short_name AS resp, 
        s.status AS c_status, 
        i.name AS item_name
      FROM (
        SELECT inner_c.item_id, inner_c.time_date, inner_c.complete_status_id
        FROM complete inner_c
        WHERE report_id = p_report_id
        ORDER BY time_date DESC
        LIMIT p_limit
        ) c
        INNER JOIN item i ON c.item_id = i.id 
        INNER JOIN role r ON i.role_id = r.id 
        INNER JOIN complete_status s ON c.complete_status_id = s.id 
        WHERE i.day_phase_id = p_day_phase_id AND i.subsystem_id = p_subsystem_id
        -- AND i.role_id = p_role_id
        ORDER BY c.time_date ASC;
END;
$$;

