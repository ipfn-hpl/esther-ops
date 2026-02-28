CREATE OR REPLACE FUNCTION get_system_list(p_phase INT, p_system_id INT)
RETURNS TABLE(item_id INT, item_order SMALLINT, item_name TEXT, role TEXT, subsystem TEXT)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT i.id, i.seq_order, i.name, r.short_name, s.name
    FROM item i
    INNER JOIN role r ON i.role_id=r.id
    INNER JOIN subsystem s ON i.subsystem_id=s.id
    WHERE i.day_phase_id = p_phase AND i.subsystem_id = p_system_id
    ORDER BY i.seq_order ASC;
        -- SELECT o.id, c.name, o.total
        -- FROM orders o
        -- JOIN customers c ON c.id = o.customer_id
        -- WHERE o.status = p_status;
END;
$$;

-- Call it like a table
--SELECT * FROM get_processed_orders('pending');
