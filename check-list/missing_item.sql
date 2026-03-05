
CREATE OR REPLACE FUNCTION missing_item(
  p_item_id INT, 
  OUT role_short_name TEXT,
  OUT item_name TEXT,
  OUT seq_order  INT,
  OUT subsystem_name TEXT,
  OUT phase_short_name TEXT
)
LANGUAGE plpgsql
AS $$
BEGIN
    SELECT r.short_name
    INTO role_short_name
    FROM item i
    INNER JOIN role r ON i.role_id = r.id
    WHERE i.id = p_item_id;

    SELECT i.name
    INTO item_name
    FROM item i 
    WHERE i.id = p_item_id;

    SELECT i.seq_order
    INTO seq_order
    FROM item i 
    WHERE i.id = p_item_id;

    SELECT s.name
    INTO subsystem_name
    FROM item i
    INNER JOIN subsystem s ON i.subsystem_id = s.id
    WHERE i.id = p_item_id;

    SELECT d.short_name
    INTO phase_short_name
    FROM item i
    INNER JOIN day_phase d ON i.day_phase_id = d.id
    WHERE i.id = p_item_id;
END;
$$;

-- Call it like a table
-- SELECT role_short_name, item_name, seq_order, subsystem_name, phase_short_name FROM missing_item(3);
-- OR access individually:
-- SELECT (missing_item(3)).item_name;
