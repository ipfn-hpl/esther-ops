CREATE OR REPLACE FUNCTION check_missing_items(p_report_id INT, p_item INT)
-- RETURNS TABLE(after_id INT, checked BOOL)
RETURNS TABLE(after_id INT, required INT, status INT, found BOOLEAN)
LANGUAGE plpgsql
AS $$
DECLARE
    rec RECORD;
    found_rec RECORD;
    -- check_rec RECORD;
    v_cnt INT;
BEGIN
    FOR rec IN
        SELECT after_item_id, min_status
        FROM precedence
        WHERE item_id = p_item
    LOOP
        -- Run a secondary query per row
        SELECT complete_status_id
        INTO found_rec
        FROM complete c
        --WHERE c.report_id = p_report_id AND c.item_id = rec.after_item_id AND c.complete_status_id <= rec.min_status;
        WHERE c.report_id = p_report_id AND c.item_id = rec.after_item_id;
        --Using SELECT 1 is a common practice in the EXISTS clause 
        -- because you don't need to retrieve the actual data; just checking for existence is sufficient.
        -- SELECT EXISTS (
        -- SELECT 1
        -- FROM complete
        --WHERE report_id = p_report_id AND item_id = rec.after_item_id);
        -- Populate the output row and emit it
        IF FOUND THEN
          --SELECT complete_status_id 
          --INTO check_rec_rec
          ----FROM complete;
          after_id      := rec.after_item_id;
          --cnt           := v_cnt;
          required      := rec.min_status;
          found         := false;
          IF found_rec.complete_status_id > rec.min_status THEN
            status        := found_rec.complete_status_id;
            v_cnt := 11;
          ELSE
            status        := -2;
          END IF;    

          --SELECT complete_status_id 
        ELSE

          after_id      := rec.after_item_id;
          --cnt           := v_cnt;
          required      := rec.min_status;
          status        := -1;
          found         := false;

        END IF;    
        -- checked       := exists;

        RETURN NEXT;  -- appends current row to the result set
    END LOOP;
END;
$$;

