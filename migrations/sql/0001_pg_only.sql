-- =====================================================================
-- SOLO POSTGRESQL (omitir en SQLite): total_cop = suma de ítems (RN-04)
-- Se comprueba al confirmar la transacción, de modo que la reserva y sus
-- ítems puedan insertarse en cualquier orden dentro de la misma transacción.
-- =====================================================================
CREATE FUNCTION fn_check_reservation_total() RETURNS trigger AS $$
DECLARE
    rid UUID;
    expected INTEGER;
    actual INTEGER;
BEGIN
    IF TG_TABLE_NAME = 'reservations' THEN
        rid := NEW.id;
    ELSIF TG_OP = 'DELETE' THEN
        rid := OLD.reservation_id;
    ELSE
        rid := NEW.reservation_id;
    END IF;
    SELECT total_cop INTO expected FROM reservations WHERE id = rid;
    IF NOT FOUND THEN
        RETURN NULL;   -- la reserva ya no existe (borrado en cascada)
    END IF;
    SELECT COALESCE(SUM(cost_cop), 0) INTO actual FROM reservation_items WHERE reservation_id = rid;
    IF expected <> actual THEN
        RAISE EXCEPTION 'total_cop (%) no coincide con la suma de los ítems (%) en la reserva %', expected, actual, rid
            USING ERRCODE = '23514';
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- @@
CREATE CONSTRAINT TRIGGER trg_reservations_total
    AFTER INSERT OR UPDATE OF total_cop ON reservations
    DEFERRABLE INITIALLY DEFERRED
    FOR EACH ROW EXECUTE FUNCTION fn_check_reservation_total();

-- @@
CREATE CONSTRAINT TRIGGER trg_reservation_items_total
    AFTER INSERT OR UPDATE OR DELETE ON reservation_items
    DEFERRABLE INITIALLY DEFERRED
    FOR EACH ROW EXECUTE FUNCTION fn_check_reservation_total();
