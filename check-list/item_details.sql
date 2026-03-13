CREATE OR REPLACE FUNCTION item_details(p_item_id INT)
RETURNS RECORD
LANGUAGE plpgsql
AS $$
DECLARE
    result RECORD;
BEGIN
    SELECT d.short_name, s.name, r.short_name, i.id, i.seq_order, i.name
    FROM item i
    INTO result
    INNER JOIN subsystem s ON i.subsystem_id = s.id
    INNER JOIN day_phase d ON i.day_phase_id = d.id
    INNER JOIN role r ON i.role_id = r.id
    WHERE i.id = p_item_id;

    RETURN result;
END;
$$;

-- Must define column types when calling
--SELECT * FROM item_details(4) AS (d_short_name TEXT, s_name TEXT, r_short_name TEXT, i_id INT,  i_seq_order SMALLINT, i_name TEXT);
