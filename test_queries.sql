USE convert_addr;

SELECT COUNT(*) FROM addresses;

SELECT * FROM addresses
ORDER BY RAND()
LIMIT 20;

SELECT * FROM addresses
WHERE LEFT(street,5) = "улица";

SELECT COUNT(*) FROM addresses
WHERE streetType IS NULL;

SELECT * FROM addresses
WHERE id = 777;
