CREATE OR REPLACE FUNCTION get_next_items(
  p_day_phase_id INT, 
  p_subsystem_id INT,  
  p_role_id INT,  
  p_last_order INT,  
  p_limit INT DEFAULT 5)
RETURNS TABLE (
      item_id INT, 
      item_seq_order SMALLINT, 
      item_name  TEXT
)
LANGUAGE plpgsql
STABLE
AS $$
BEGIN
  RETURN QUERY
    SELECT id, seq_order, name
    FROM item
    WHERE day_phase_id = p_day_phase_id AND subsystem_id = p_subsystem_id AND role_id = p_role_id AND seq_order > p_last_order
    ORDER BY seq_order ASC LIMIT p_limit;
END;
$$;

