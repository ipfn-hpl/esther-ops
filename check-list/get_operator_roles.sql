CREATE OR REPLACE FUNCTION get_operator_roles(p_operator_id INT) 
RETURNS TABLE(role_id SMALLINT, role_name TEXT)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
   SELECT o.role_id, r.name 
   FROM operator_roles o
   INNER JOIN role r ON o.role_id = r.id
   WHERE o.operator_id = p_operator_id;
END;
$$;

-- Call it like a table
-- SELECT role_id, role_name FROM get_operator_roles(2);
