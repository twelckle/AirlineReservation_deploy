create table airline
	(airline_name	varchar(100),
	 primary key (airline_name)
	);

	

create table airline_staff
	(airline_name	varchar(100), 
	 username 		varchar(100),
	 pwd	varchar(100),
	 first_name		varchar(100),
	 last_name		varchar(100),
	 date_of_birth 	date,
	 primary key (username),
	 foreign key (airline_name) references airline(airline_name)
	);

create table staff_email
	(username 		varchar(100),
	 email_id  varchar(100),
	 primary key (username, email_id),
	 foreign key (username) references airline_staff(username)
	);

create table staff_phone
	(username 		varchar(100),
	 phone_num  	varchar(15),
	 primary key (username, phone_num),
	 foreign key (username) references airline_staff(username)
	);

create table airplane
	(airline_name			varchar(100),
	 airplaneID				varchar(20),
	 num_of_seats			int,
	 manufacutring_company	varchar(100),
	 manufacutring_date		date,
	 model_num				varchar(20),
	 primary key (airline_name, airplaneID),
	 foreign key (airline_name) references airline(airline_name)		
	);

create table maintenance
	(airline_name		varchar(100),
	 airplaneID			varchar(20),
	 st_date			date,
	 st_time			time,
	 end_date			date,
	 end_time			time,
	 primary key(airline_name, airplaneID, st_date, st_time),
	 foreign key(airline_name, airplaneID) references airplane(airline_name, airplaneID)
	);

create table airport
	(code				varchar(30),
	 airport_name		varchar(100),
	 city				varchar(100),
	 country			varchar(100),
	 num_of_terminals	int,
	 airport_type		varchar(100) CHECK (airport_type IN ('international', 'domestic', 'both')),
	 primary key(code)
	);

create table flight
	(airline_name					varchar(100),
	 departure_airport 				varchar(30),
	 arrival_airport				varchar(30),
	 assigned_airplane_airline		varchar(100),
	 assigned_airplaneID			varchar(20),
	 flight_num						varchar(20),
	 departure_date					date,
	 departure_time					time,
	 arrival_date					date,
	 arrival_time					time,
	 base_price_ticket				decimal,
	 flight_status					varchar(8) CHECK (flight_status IN ('on_time', 'delayed', 'canceled')),

	 primary key(airline_name, flight_num, departure_date, departure_time),
	 foreign key(airline_name) references airline(airline_name),
	 foreign key(assigned_airplane_airline, assigned_airplaneID) references airplane(airline_name, airplaneID),
	 foreign key(departure_airport) references airport(code),
	 foreign key(arrival_airport) references airport(code)
	);

create table ticket
	(airline_name		varchar(100),
	 flight_num			varchar(20),
	 departure_date		date,
	 departure_time		time,
	 ticketID			int,
	 
	 primary key(ticketID),
	 foreign key(airline_name, flight_num, departure_date, departure_time)
	 references flight(airline_name, flight_num, departure_date, departure_time)
	);

create table customer
	(email_id				varchar(100),
	 first_name				varchar(100),
	 last_name				varchar(100),
	 pwd					varchar(100),
	 building_num			int,
	 street_name			varchar(100),
	 apt_num				int,
	 city					varchar(100),
	 state_name				varchar(100),
	 zipcode				varchar(20),
	 passport_num			varchar(50),
	 passport_country		varchar(50),
	 passport_expiration 	date,
	 date_of_birth			date,

	 primary key (email_id)
	);

create table customer_phone
	(email_id		varchar(100),
	 phone_num		varchar(15),
	 
	 primary key (email_id, phone_num),
	 foreign key (email_id) references customer(email_id)
	);

create table review
	(ticketID			int,
	 email_id			varchar(100),
	 rate				int check (rate > 0 and rate < 6),
	 comment			varchar(500),

	 primary key(ticketID),
	 foreign key(ticketID) references ticket(ticketID),
	 foreign key(email_id) references customer(email_id)
	);

create table purchase
	(ticketID				int,
	 email_id				varchar(100),
	 first_name				varchar(100),
	 last_name				varchar(100),
	 date_of_birth			date,
	 card_type				varchar(6) check (card_type in("debit", "credit")),
	 card_num				bigint,
	 name_on_card			varchar(100),
	 expiration_date		date,
	 purchase_date			date,
	 purchase_time			time,
	 primary key(ticketID),
	 foreign key(ticketID) references ticket(ticketID),
	 foreign key(email_id) references customer(email_id)
	);