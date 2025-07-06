-- Airline inserts
INSERT INTO airline VALUES ("United");
INSERT INTO airline VALUES ("Jet Blue");
INSERT INTO airline VALUES ("Delta");
INSERT INTO airline VALUES ("American Airlines");
INSERT INTO airline VALUES ("Southwest");
INSERT INTO airline VALUES ("Alaska Airlines");
INSERT INTO airline VALUES ("Air Canada");
INSERT INTO airline VALUES ("British Airways");
INSERT INTO airline VALUES ("Emirates");
INSERT INTO airline VALUES ("Lufthansa");



-- Airport inserts
INSERT INTO airport VALUES ("JFK", "John F. Kennedy International Airport", "New York City", "USA", 5, "both");
INSERT INTO airport VALUES ("LAX", "Los Angeles International Airport", "Los Angeles", "USA", 6, "both");
INSERT INTO airport VALUES ("ORD", "O'Hare International Airport", "Chicago", "USA", 5, "both");
INSERT INTO airport VALUES ("ATL", "Hartsfield–Jackson Atlanta International Airport", "Atlanta", "USA", 6, "both");
INSERT INTO airport VALUES ("DFW", "Dallas/Fort Worth International Airport", "Dallas-Fort Worth", "USA", 5, "both");
INSERT INTO airport VALUES ("DEN", "Denver International Airport", "Denver", "USA", 4, "both");
INSERT INTO airport VALUES ("SFO", "San Francisco International Airport", "San Francisco", "USA", 4, "both");
INSERT INTO airport VALUES ("SEA", "Seattle–Tacoma International Airport", "Seattle", "USA", 4, "both");
INSERT INTO airport VALUES ("MIA", "Miami International Airport", "Miami", "USA", 3, "both");
INSERT INTO airport VALUES ("BOS", "Logan International Airport", "Boston", "USA", 3, "both");
INSERT INTO airport VALUES ("LHR", "Heathrow Airport", "London", "UK", 5, "both");
INSERT INTO airport VALUES ("CDG", "Charles de Gaulle Airport", "Paris", "France", 4, "both");
INSERT INTO airport VALUES ("FRA", "Frankfurt Airport", "Frankfurt", "Germany", 4, "both");
INSERT INTO airport VALUES ("HND", "Haneda Airport", "Tokyo", "Japan", 5, "both");
INSERT INTO airport VALUES ("SYD", "Sydney Kingsford Smith Airport", "Sydney", "Australia", 3, "both");

-- Airplane inserts
INSERT INTO airplane VALUES ("Jet Blue", "B6623", 200, "Airbus", "2015-01-15", "A320");
INSERT INTO airplane VALUES ("United", "UA410", 700, "Boeing", "2014-03-25", "B787");
INSERT INTO airplane VALUES ("United", "UA448", 300, "Airbus", "2014-03-25", "A321neo");
INSERT INTO airplane VALUES ("United", "UA002", 3, "Airbus", "2018-03-25", "A321");

-- Airline_staff inserts
INSERT INTO airline_staff VALUES ("Jet Blue", "ss14741", "ss14741_1", "Sri Pranav", "Srivatsavai", "2003-09-26" );
INSERT INTO airline_staff VALUES ("Jet Blue", "tlw9927", "tlw9927_1", "Theo", "Welckle", "2002-05-15" );

-- Flight inserts
INSERT INTO flight VALUES ('Jet Blue', 'JFK', 'HYD', 'Jet Blue', 'B6623', 'JB101', '2023-11-07', '08:00:00', '2023-11-08', '21:00:00', 750.00, 'on_time',(SELECT num_of_seats FROM airplane WHERE airline_name = 'Jet Blue' AND airplaneID = 'B6623'),(SELECT num_of_seats FROM airplane WHERE airline_name = 'Jet Blue' AND airplaneID = 'B6623'));
INSERT INTO flight VALUES ('United', 'PVG', 'JFK', 'United', 'UA002', 'UA204', '2023-11-07', '13:00:00', '2023-11-07', '19:30:00', 1200.00, 'delayed',(SELECT num_of_seats FROM airplane WHERE airline_name = 'United' AND airplaneID = 'UA002'),(SELECT num_of_seats FROM airplane WHERE airline_name = 'United' AND airplaneID = 'UA002'));
INSERT INTO flight VALUES ('Jet Blue', 'HYD', 'JFK', 'Jet Blue', 'B6623', 'JB302', '2023-11-09', '20:30:00', '2023-11-10', '05:00:00', 800.00, 'canceled',(SELECT num_of_seats FROM airplane WHERE airline_name = 'Jet Blue' AND airplaneID = 'B6623'),(SELECT num_of_seats FROM airplane WHERE airline_name = 'Jet Blue' AND airplaneID = 'B6623'));
INSERT INTO flight VALUES ('United', 'JFK', 'PVG', 'United', 'UA410', 'UA408', '2023-11-08', '09:45:00', '2023-11-09', '11:15:00', 1300.00, 'on_time',(SELECT num_of_seats FROM airplane WHERE airline_name = 'United' AND airplaneID = 'UA410'),(SELECT num_of_seats FROM airplane WHERE airline_name = 'United' AND airplaneID = 'UA410'));
INSERT INTO flight VALUES ('Jet Blue', 'PVG', 'HYD', 'Jet Blue', 'B6623', 'JB404', '2023-11-10', '23:00:00', '2023-11-11', '02:30:00', 900.00, 'delayed',(SELECT num_of_seats FROM airplane WHERE airline_name = 'Jet Blue' AND airplaneID = 'B6623'),(SELECT num_of_seats FROM airplane WHERE airline_name = 'Jet Blue' AND airplaneID = 'B6623'));
INSERT INTO flight VALUES ('United', 'HYD', 'PVG', 'United', 'UA448', 'UA506', '2023-11-11', '15:30:00', '2023-11-12', '08:45:00', 1100.00, 'on_time',(SELECT num_of_seats FROM airplane WHERE airline_name = 'United' AND airplaneID = 'UA448'),(SELECT num_of_seats FROM airplane WHERE airline_name = 'United' AND airplaneID = 'UA448'));
INSERT INTO flight VALUES ('Jet Blue', 'JFK', 'PVG', 'Jet Blue', 'B6623', 'JB607', '2023-11-12', '17:00:00', '2023-11-13', '09:00:00', 950.00, 'canceled',(SELECT num_of_seats FROM airplane WHERE airline_name = 'Jet Blue' AND airplaneID = 'B6623'),(SELECT num_of_seats FROM airplane WHERE airline_name = 'Jet Blue' AND airplaneID = 'B6623'));
INSERT INTO flight VALUES ('United', 'PVG', 'HYD', 'United', 'UA002', 'UA708', '2023-11-13', '22:15:00', '2023-11-14', '03:40:00', 1150.00, 'delayed',(SELECT num_of_seats FROM airplane WHERE airline_name = 'United' AND airplaneID = 'UA002'),(SELECT num_of_seats FROM airplane WHERE airline_name = 'United' AND airplaneID = 'UA002'));

-- Ticket inserts
INSERT INTO ticket VALUES ('Jet Blue', 'JB101', '2023-11-07', '08:00:00', 10001);
INSERT INTO ticket VALUES ('United', 'UA204', '2023-11-07', '13:00:00', 10002);
INSERT INTO ticket VALUES ('Jet Blue', 'JB302', '2023-11-09', '20:30:00', 10003);
INSERT INTO ticket VALUES ('United', 'UA408', '2023-11-08', '09:45:00', 10004);

-- Customer inserts
INSERT INTO customer VALUES ('john.doe@example.com', 'John', 'Doe', 'jD123$%', 100, 'Maple Street', 10, 'Springfield', 'Illinois', '62704', 'A12345678', 'USA', '2030-01-01', '1980-06-15');
INSERT INTO customer VALUES ('jane.smith@example.com', 'Jane', 'Smith', 'js!@#789', 200, 'Oak Avenue', 5, 'Liberty City', 'New York', '10001', 'B87654321', 'USA', '2031-02-15', '1985-10-22');
INSERT INTO customer VALUES ('alice.brown@example.com', 'Alice', 'Brown', 'aBc123!!', 301, 'Elm Street', 21, 'Metropolis', 'California', '90001', 'C23456789', 'USA', '2032-05-20', '1990-03-30');

-- Customer_Phone inserts
INSERT INTO customer_phone VALUES ('john.doe@example.com', '+11234561234');
INSERT INTO customer_phone VALUES ('john.doe@example.com', '+11234567890');
INSERT INTO customer_phone VALUES ('jane.smith@example.com', '+12345678902');

-- Purchase inserts
INSERT INTO purchase VALUES (10001, 'john.doe@example.com', 'John', 'Doe', '1980-06-15', 'credit', 1234567890123456, 'John Doe', '2025-12-31', '2023-11-05', '10:30:00');
INSERT INTO purchase VALUES (10002, 'jane.smith@example.com', 'Jane', 'Smith', '1985-10-22', 'debit', 2345678901234567, 'Jane Smith', '2026-11-30', '2023-11-05', '14:45:00');
INSERT INTO purchase VALUES (10003, 'alice.brown@example.com', 'Alice', 'Brown', '1990-03-30', 'credit', 3456789012345678, 'Alice Brown', '2027-10-15', '2023-11-06', '16:20:00');

-- Staff_Phone inserts
INSERT INTO staff_phone VALUES ("tlw9927", "+19234454356");
INSERT INTO staff_phone VALUES ("ss14741", "+12234356545");

-- Staff_Email inserts
INSERT INTO staff_email VALUES ("tlw9927", "tlw9927@nyu.edu");
INSERT INTO staff_email VALUES ("ss14741", "ss14741@nyu.edu");

ALTER TABLE purchase ADD COLUMN amount_paid DECIMAL(10, 2); -- Added this to capture final sold price as well.
