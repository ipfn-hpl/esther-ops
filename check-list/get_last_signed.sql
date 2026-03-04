CREATE OR REPLACE FUNCTION get_last_signed(
  p_report_id INT, 
  p_subsystem_id INT,
  p_role_id   INT,
  OUT item_id  INT,
  OUT seq_order  INT
)
LANGUAGE plpgsql
AS $$
BEGIN

    SELECT c.item_id
    INTO item_id
    FROM complete c
    INNER JOIN item i ON c.item_id = i.id
    WHERE c.report_id = p_report_id AND
    i.subsystem_id = p_subsystem_id AND
    i.role_id = p_role_id
    ORDER BY time_date DESC LIMIT 1;

    SELECT item.seq_order 
    INTO seq_order
    FROM item
    WHERE id = item_id;
END;
$$;
