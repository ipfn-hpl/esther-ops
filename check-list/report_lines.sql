CREATE OR REPLACE FUNCTION get_processed_orders(p_status TEXT)
RETURNS TABLE(order_id INT, customer_name TEXT, total NUMERIC)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
        SELECT o.id, c.name, o.total
        FROM orders o
        JOIN customers c ON c.id = o.customer_id
        WHERE o.status = p_status;
END;
$$;

-- Call it like a table
SELECT * FROM get_processed_orders('pending');
