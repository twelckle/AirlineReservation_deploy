#Import Flask Library
from flask import Flask, render_template, request, session, url_for, redirect
# import pymysql.cursors
import hashlib
import uuid
import random
from datetime import datetime
import os
import psycopg2

#Initialize the app from Flask
app = Flask(__name__)

#Configure MySQL
conn = psycopg2.connect(os.environ['DATABASE_URL'], sslmode='require')

####################################################################
#HOME - New Customer / Not logged in

#Define a route for the index - home
@app.route('/')
def home():
	return render_template('index.html')

#Define route for customer login
@app.route('/customer-login')
def customer_login():
	return render_template('customer-login.html')

# Customer loginAuth and registerAuth, other related functions can be found in the CUSTOMER section below the "HOME - New Customer / Not logged in" section

@app.route('/customer-register')
def customer_register():
	return render_template('customer-register.html')

@app.route('/search')
def search():
	return render_template('search.html')

@app.route('/searchresults', methods=['GET', 'POST'])
def search_flights():
    if request.method == 'POST':
        # Get data from form
        origin_code = request.form['origin']
        destination_code = request.form['destination']
        departure_date = request.form['departure_date']
        trip_type = request.form.get('trip') # Get the trip type (one-way or round-trip)
        return_date = request.form.get('return_date') if 'return_date' in request.form else None


        # SQL Query the database
        cursor = conn.cursor()
            # Query for fetching all the details from flight table
            # cursor.execute(
            #     'SELECT * FROM flight WHERE departure_airport = %s AND arrival_airport = %s AND departure_date = %s',
            #     (origin_code, destination_code, departure_date)
            # )
        # Query for fetching all the details + dynamic price from flight table
        cursor.execute('''
        SELECT *,
        CAST(base_price_ticket * IF(((total_seats - available_seats) / total_seats) >= 0.8, 1.25, 1) AS DECIMAL(10,2)) AS dynamic_price
        FROM flight
        WHERE departure_airport = %s AND arrival_airport = %s AND departure_date = %s 
        AND available_seats > 0 AND flight_status != 'canceled'
		''', (origin_code, destination_code, departure_date))
        outbound_flights = cursor.fetchall()

        # If round-trip, query the database for inbound flights
        if trip_type == 'round-trip' and return_date:
                # Query for fetching all the details from flight table
                # cursor.execute(
                #     'SELECT * FROM flight WHERE departure_airport = %s AND arrival_airport = %s AND departure_date = %s',
                #     (destination_code, origin_code, return_date)
                # )
            # Query for fetching all the details + dynamic price from flight table
            cursor.execute('''
                SELECT *,
                CAST(base_price_ticket * IF(((total_seats - available_seats) / total_seats) >= 0.8, 1.25, 1) AS DECIMAL (10,2)) AS dynamic_price
                FROM flight
                WHERE departure_airport = %s AND arrival_airport = %s AND departure_date = %s
                AND available_seats > 0 AND flight_status != 'canceled'
                ''', (destination_code, origin_code, return_date))
        inbound_flights = cursor.fetchall()

        cursor.close()

        # Render the results in a HTML table
        return render_template('searchresults.html', outbound_flights=outbound_flights, inbound_flights=inbound_flights, trip_type=trip_type)
    
    # If method is GET, just render the search form
    return render_template('search.html')
####################################################################

####################################################################
# CUSTOMER

@app.route('/registerAuth', methods=['GET', 'POST'])
def registerAuth():
    customer_email = request.form['emailid']
    cursor = conn.cursor()

    # Check if email already exists
    query = 'SELECT * FROM customer WHERE email_id = %s'
    cursor.execute(query, (customer_email))
    emailExists = cursor.fetchone()

    if (emailExists): 
        # The emailExists variable has data - same email found in the database
        return render_template('customer-register.html', error = "This user already exists in the database. Try Logging in")
        
    else:
        # Verified as a new user - email not found
        customer_password = hashlib.md5(request.form['password'].encode()).hexdigest()
        first_name = request.form['fname']
        last_name = request.form['lname']
        date_of_birth = request.form['date-of-birth']
        building_num = request.form['building-num']
        street_name = request.form['street-name']
        apt_num = request.form['apt-num']
        city = request.form['city']
        state = request.form['state']
        zip_code = request.form['zip-code']
        passport_num = request.form['passport-number']
        passport_country = request.form['passport-country']
        passport_expiry = request.form['passport-expiry']
        insert_newcustomer_query = 'INSERT INTO customer VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'
        
        try:
            cursor.execute(insert_newcustomer_query, (
                customer_email, first_name, last_name, customer_password, 
                building_num, street_name, apt_num, city, state, zip_code, 
                passport_num, passport_country, passport_expiry, date_of_birth,
            ))
            phone_numbers = request.form.getlist('customer_phone[]')
            insert_phone_query = 'INSERT INTO customer_phone VALUES(%s, %s)'
            phone_already_query = 'SELECT * from customer_phone where email_id = %s and phone_num = %s'
            for phone in phone_numbers:
                if(phone == ''): continue
                cursor.execute(phone_already_query, (customer_email, phone))
                phoneExists = cursor.fetchone();
                if(phoneExists is None):
                    cursor.execute(insert_phone_query, (customer_email, phone))
            conn.commit()
            cursor.close()
            # Redirect to login page after registration
            return redirect(url_for('customer_login'))
        except Exception as e:
            print(e)
            # Handle errors and rollback transaction
            conn.rollback()
            cursor.close()
            # Show an error message
            return render_template('customer-register.html', error="An error occurred during registration.")

@app.route('/loginAuth', methods=['GET', 'POST'])
def LoginAuth():
    #fetch login information from the form
    email = request.form['email']
    password = hashlib.md5(request.form['password'].encode()).hexdigest()
        
    #queries database to see if such tuple exists
    cursor = conn.cursor()
    query = 'SELECT * FROM customer WHERE email_id = %s and pwd = %s'
    cursor.execute(query, (email, password))
    data = cursor.fetchone()
    cursor.close()
        
    error = None
    if(data):
        # If tuple exists - create a session for the the user and login
        session['email'] = email
        session['password'] = password
        session['fname'] = data['first_name']
        session['lname'] = data['last_name']
        session['dob'] = data['date_of_birth']
        
        # If login is successful, check if the user was trying to make a purchase
        if session.pop('attempting_purchase', None):
            # Redirect to the purchase route if they were trying to buy something
            selected_outbound = session.get('selected_outbound')
            selected_inbound = session.get('selected_inbound')
            total_cost = session.get('total_cost')
            # return redirect(url_for('purchase'))
            ######
            # Since I want the flight details in a table, I need to execute those queries again here.
            # Copy Pasted from the customer-purchase function
            cursor = conn.cursor()
            details_selected_outbound = None
            details_selected_inbound = None # This is to ensure a successful build and run, since inbound is not always present
            
            outbound_details = selected_outbound.split('_')
        
            details_selected_outbound_query = '''
            SELECT *,
            CAST(base_price_ticket * IF(((total_seats - available_seats) / total_seats) >= 0.8, 1.25, 1) AS DECIMAL(10,2)) AS dynamic_price
            FROM flight
            WHERE airline_name = %s AND flight_num = %s AND departure_date = %s AND departure_time = %s
            AND available_seats > 0 AND flight_status != 'canceled'
            '''
            cursor.execute(details_selected_outbound_query, (outbound_details[1], 
                                                 outbound_details[0], outbound_details[2], outbound_details[3]))
            details_selected_outbound = cursor.fetchall() # To be passed on to the HTML to display
            
            if selected_inbound:
                inbound_details = selected_inbound.split('_')
                details_selected_inbound_query = '''
                SELECT *,
                CAST(base_price_ticket * IF(((total_seats - available_seats) / total_seats) >= 0.8, 1.25, 1) AS DECIMAL(10,2)) AS dynamic_price
                FROM flight
                WHERE airline_name = %s AND flight_num = %s AND departure_date = %s AND departure_time = %s
                AND available_seats > 0 AND flight_status != 'canceled'
                '''
                cursor.execute(details_selected_inbound_query, (inbound_details[1], 
                                                    inbound_details[0], inbound_details[2], inbound_details[3]))            
                details_selected_inbound = cursor.fetchall() # To be passed on to the HTML to display
            
            cursor.close()
            # Paste from the Customer Purchase ends
            ######
            return render_template('customer-purchase.html',
                                   selected_outbound=selected_outbound,
                                   selected_inbound=selected_inbound, total_cost=total_cost,
                                   details_selected_outbound=details_selected_outbound,
                                  details_selected_inbound=details_selected_inbound)
        else:
            # If not, redirect to the customer's home page
            return redirect(url_for('customerHome'))
    else:
        # Throw an error message if the tuple does not exist
        error = 'Invalid login or username'
        return render_template('customer-login.html', error=error)

def isNotValidCustomer():
	if(len(session) == 0): return True # No pair in session dictionary i.e. no session created yet
	if(session['email'] is None): return True 
	if(session['password'] is None): return True
	email = session['email']
	password = session['password']
	cursor = conn.cursor()
	query = 'SELECT * FROM customer WHERE email_id = %s and pwd = %s'
	cursor.execute(query, (email, password))
	data = cursor.fetchone()
	cursor.close()
	if(data is None): return True
	return False

@app.route('/customerHome', methods=['GET','POST'])
def customerHome():
        if(isNotValidCustomer()):
            return redirect(url_for('customer_login'))
        else:
            # If customer logs in after selecting flights
            if 'selected_outbound' in session or 'selected_inbound' in session:
                # return redirect(url_for('purchase'))
                return render_template('customer-home.html', fname = session['fname'])
            #session active - so pass the fname and other variables as necessary
            return render_template('customer-home.html', fname = session['fname'])

@app.route('/customer-logout')
def customer_logout():
    # Clear all the session data
    session.clear()
    return redirect(url_for('customer_login'))

@app.route('/customer-purchase', methods=['GET', 'POST'])
def purchase():
    if request.method == 'POST':
        if isNotValidCustomer():
            # Customer is not logged in but is trying to make a purchase
            session['selected_outbound'] = request.form.get('selected_outbound')
            session['selected_inbound'] = request.form.get('selected_inbound')
            session['total_cost'] = request.form['total_cost'] 
            session['outbound_cost'] = request.form['outbound_cost'] 
            session['inbound_cost'] = request.form['inbound_cost'] 
            # print(session['outbound_cost'], session['inbound_cost'], session['total_cost']) # Debugging purpose
            # Set a flag to indicate a purchase attempt
            session['attempting_purchase'] = True
            # Redirect to login page
            return redirect(url_for('customer_login'))
        else:
            # Customer is logged in and has selected flights

            # Missing these 2 lines made me spend 2 days. Flagging this to cherish my debugging skills later
            # Retrieve selected flights from the form or the session
            session['selected_outbound'] = request.form.get('selected_outbound')
            session['selected_inbound'] = request.form.get('selected_inbound')
            ##
            session['total_cost'] = request.form['total_cost'] 
            session['outbound_cost'] = request.form['outbound_cost'] 
            session['inbound_cost'] = request.form['inbound_cost'] 
            # print(session['outbound_cost'], session['inbound_cost'], session['total_cost']) # Debugging purpose

            selected_outbound = request.form.get('selected_outbound') or session.get('selected_outbound')
            selected_inbound = request.form.get('selected_inbound') or session.get('selected_inbound')
            total_cost = request.form.get('total_cost') or session.get('total_cost')

            cursor = conn.cursor()
            details_selected_outbound = None
            details_selected_inbound = None # This is to ensure a successful build and run, since inbound is not always present
            
            # Format: EK201_Emirates_2023-11-07_15:00:00
            outbound_details = selected_outbound.split('_')
        
            details_selected_outbound_query = '''
            SELECT *,
            CAST(base_price_ticket * IF(((total_seats - available_seats) / total_seats) >= 0.8, 1.25, 1) AS DECIMAL(10,2)) AS dynamic_price
            FROM flight
            WHERE airline_name = %s AND flight_num = %s AND departure_date = %s AND departure_time = %s
            AND available_seats > 0 AND flight_status != 'canceled'
            '''
            cursor.execute(details_selected_outbound_query, (outbound_details[1], 
                                                 outbound_details[0], outbound_details[2], outbound_details[3]))
            details_selected_outbound = cursor.fetchall() # To be passed on to the HTML to display
            
            if selected_inbound:
                inbound_details = selected_inbound.split('_')
                details_selected_inbound_query = '''
                SELECT *,
                CAST(base_price_ticket * IF(((total_seats - available_seats) / total_seats) >= 0.8, 1.25, 1) AS DECIMAL(10,2)) AS dynamic_price
                FROM flight
                WHERE airline_name = %s AND flight_num = %s AND departure_date = %s AND departure_time = %s
                AND available_seats > 0 AND flight_status != 'canceled'
                '''
                cursor.execute(details_selected_inbound_query, (inbound_details[1], 
                                                    inbound_details[0], inbound_details[2], inbound_details[3]))            
                details_selected_inbound = cursor.fetchall() # To be passed on to the HTML to display

            
            # Clear the flights from the session if they were stored
            # session.pop('selected_outbound', None)
            # session.pop('selected_inbound', None)
            # session.pop('total_cost', None)
            # Commented because - using these in customer-purchase-confirmation
            
            cursor.close()
            # Render the purchase page with the selected flights
            return render_template('customer-purchase.html', 
                                   selected_outbound=selected_outbound,
                                   selected_inbound=selected_inbound, total_cost=total_cost,
                                   details_selected_inbound=details_selected_inbound,
                                   details_selected_outbound=details_selected_outbound)
    else:
        return render_template('customer-purchase.html')


def generate_ticket_id(cursor):
    max_int = 2147483647  # Maximum value for a signed 4-byte integer
    while True:
        # Generate a random ticket ID
        ticket_id = random.randint(1, max_int)
        cursor.execute('SELECT ticketID FROM ticket WHERE ticketID = %s', (ticket_id))
        result = cursor.fetchone()
        if result is None:
            return ticket_id

@app.route('/customer-purchase-confirmation', methods=['GET','POST'])
def purchase_confirmation():
    if(isNotValidCustomer()):
        # The user is not logged in, redirect them to the login page
        return redirect(url_for('customer_login'))

    # Retrieve the session variables to confirm the purchase
    customer_email = session['email']
    customer_fname = session['fname'], 
    customer_lname = session['lname'], 
    # customer_dob = session['dob'] having an error with the date format
    selected_outbound = session.pop('selected_outbound', None)
    # selected_outbound = session.get('selected_outbound')
    selected_inbound = session.pop('selected_inbound', None)
    # selected_inbound = session.get('selected_inbound')

    # Remember the total cost calculated by JavaScript in searchresults.html
    total_cost = session.get('total_cost')
    outbound_cost = session.get('outbound_cost')
    inbound_cost = session.get('inbound_cost')

    # print(selected_inbound, selected_outbound)
    # total_cost = session.pop('total_cost', None)

    # Check whether the ticket is for the customer logged in or someone else
    buying_for_others = request.form.get('buying_for_others') == 'yes'
    # print(buying_for_others)
    if buying_for_others:
        # print("buying for others activated")
        # Get the passenger details from the form
        passenger_fname = request.form.get('passenger_fname')
        passenger_lname = request.form.get('passenger_lname')
        passenger_dob = request.form.get('passenger_dob')

    # Process the form data from the customer-purchase page to confirm the purchase
    card_type = request.form['card_type']
    card_number = request.form['card_number']
    name_on_card = request.form['name_on_card']
    expiration_date = request.form['expiration_date']

    # Generate a unique ticketID
    cursor = conn.cursor()
    outboundTicketID = generate_ticket_id(cursor)
    inboundTicketID = generate_ticket_id(cursor) if selected_inbound else None

    # Add tuples to ticket, purchase & Update flight
    try:
        if selected_outbound:
            # Add data to ticket table: Insert into ticket table first due to the foreign key references from Purchase to Ticket
            outbound_details = selected_outbound.split('_') # Split the concatenated data from HTML/JS
            ticket_insert_query = '''
            INSERT INTO ticket (ticketID, airline_name, flight_num, departure_date, departure_time)
            VALUES (%s, %s, %s, %s, %s)
            '''
            cursor.execute(ticket_insert_query, (outboundTicketID, outbound_details[1], outbound_details[0], outbound_details[2], outbound_details[3]))

            if buying_for_others:
				# Customer buying a ticket for someone else
                purchase_insert_query = '''
                INSERT INTO purchase (ticketID, email_id, first_name, last_name, date_of_birth, card_type, card_num, name_on_card, expiration_date, purchase_date, purchase_time, amount_paid)
                SELECT %s, %s, %s, %s, %s, %s, %s, %s, %s, CURDATE(), CURTIME(), %s
                FROM customer WHERE email_id = %s
                '''
                cursor.execute(purchase_insert_query, 
                    (outboundTicketID, 
                        customer_email,
						passenger_fname,
						passenger_lname,
						passenger_dob,
                        card_type, 
                        card_number, 
                        name_on_card, 
                        expiration_date,
                        outbound_cost, 
                        customer_email))
            else:
                # Customer buying a ticket for himself - Add data to purchase table
                purchase_insert_query = '''
                INSERT INTO purchase (ticketID, email_id, first_name, last_name, date_of_birth, card_type, card_num, name_on_card, expiration_date, purchase_date, purchase_time, amount_paid)
                SELECT %s, %s, first_name, last_name, date_of_birth, %s, %s, %s, %s, CURDATE(), CURTIME(), %s
                FROM customer WHERE email_id = %s
                '''
                cursor.execute(purchase_insert_query, 
                    (outboundTicketID, 
                        customer_email, 
                        card_type, 
                        card_number, 
                        name_on_card, 
                        expiration_date,
                        outbound_cost, 
                        customer_email))
            
            # Update available seats on flight table
            update_seats_query = 'UPDATE flight SET available_seats = available_seats - 1 WHERE airline_name = %s AND flight_num = %s AND departure_date = %s AND departure_time = %s'
            cursor.execute(update_seats_query, (outbound_details[1], outbound_details[0], outbound_details[2], outbound_details[3]))
            
        if selected_inbound:
            # Add data to ticket table
            inbound_details = selected_inbound.split('_')
            ticket_insert_query = '''
            INSERT INTO ticket (ticketID, airline_name, flight_num, departure_date, departure_time)
            VALUES (%s, %s, %s, %s, %s)
            '''
            cursor.execute(ticket_insert_query, (inboundTicketID, inbound_details[1], inbound_details[0], inbound_details[2], inbound_details[3]))

            if buying_for_others:
				# Customer buying a ticket for someone else
                purchase_insert_query_return = '''
                INSERT INTO purchase (ticketID, email_id, first_name, last_name, date_of_birth, card_type, card_num, name_on_card, expiration_date, purchase_date, purchase_time, amount_paid)
                SELECT %s, %s, %s, %s, %s, %s, %s, %s, %s, CURDATE(), CURTIME(), %s
                FROM customer WHERE email_id = %s
                '''
                cursor.execute(purchase_insert_query_return, 
                    (inboundTicketID, 
                        customer_email,
						passenger_fname,
						passenger_lname,
						passenger_dob,
                        card_type, 
                        card_number, 
                        name_on_card, 
                        expiration_date,
                        inbound_cost, 
                        customer_email))
            else:
                # Customer buying a ticket for himself - Add data to purchase table
                purchase_insert_query_return = '''
                INSERT INTO purchase (ticketID, email_id, first_name, last_name, date_of_birth, card_type, card_num, name_on_card, expiration_date, purchase_date, purchase_time, amount_paid)
                SELECT %s, %s, first_name, last_name, date_of_birth, %s, %s, %s, %s, CURDATE(), CURTIME(), %s
                FROM customer WHERE email_id = %s
                '''
                cursor.execute(purchase_insert_query_return, 
                    (inboundTicketID, 
                        customer_email, 
                        card_type, 
                        card_number, 
                        name_on_card, 
                        expiration_date,
                        inbound_cost, 
                        customer_email))        

            # Update available seats on flight table
            update_seats_query = 'UPDATE flight SET available_seats = available_seats - 1 WHERE airline_name = %s AND flight_num = %s AND departure_date = %s AND departure_time = %s'
            cursor.execute(update_seats_query, (inbound_details[1], inbound_details[0], inbound_details[2], inbound_details[3]))

        # Commit the changes to the database
        conn.commit()

    except Exception as e:
         print('Could not proceed with purchase transaction. Aborting.')
         print(e)
         conn.rollback()
         error = "Could not complete the transaction. Aborted."
         return render_template('customer-purchase.html', error=error)

    finally:
        # Ensure cursor is closed regardless
        cursor.close()

    # After processing, redirect to a page that confirms the purchase
    return render_template('customer-purchase-confirmation.html', outboundTicketID=outboundTicketID, inboundTicketID=inboundTicketID)

@app.route('/customer-all-purchases', methods=['GET','POST'])
def customer_all_purchases():
    if(isNotValidCustomer()):
        # The user is not logged in, redirect them to the login page
        return redirect(url_for('customer_login'))
    
    customer_email = session['email'] # To load the customer data accordingly
    cursor = conn.cursor()

    # Query to get the Purchase History and connected Ticket data
    spending_history_query = '''
            SELECT p.ticketID, p.amount_paid, p.purchase_date, p.purchase_time, 
            t.airline_name, t.flight_num ,t.departure_date, t.departure_time 
            FROM `purchase` as p ,`ticket` as t 
            WHERE t.ticketID = p.ticketID AND p.email_id = %s
            ORDER BY purchase_date DESC, purchase_time DESC;
            '''
    cursor.execute(spending_history_query, (customer_email))
    spending_history_data = cursor.fetchall()

    # Query to get the total amount spent by the customer in session
    total_spent_query = 'SELECT SUM(amount_paid) AS total_amount FROM `purchase` WHERE email_id = %s'
    cursor.execute(total_spent_query, (customer_email))
    total_spent_amount = cursor.fetchone()

    cursor.close()
    
    return render_template('customer-all-purchases.html', spending_history_data=spending_history_data,
                           total_spent_amount=total_spent_amount['total_amount'] )

@app.route('/customer-spending', methods=['GET','POST'])
def customer_spending():
    if(isNotValidCustomer()):
        # The user is not logged in, redirect them to the login page
        return redirect(url_for('customer_login'))
    
    customer_email = session['email'] # To load the customer data accordingly
    cursor = conn.cursor()

    # Query to get the total amount spent by the customer in the last 1 year
    total_spent_past_year_query = '''
        SELECT SUM(amount_paid) AS total_amount
        FROM `purchase`
        WHERE email_id = %s AND purchase_date BETWEEN DATE_SUB(CURDATE(), INTERVAL 1 YEAR) AND CURDATE()
    '''
    cursor.execute(total_spent_past_year_query, (customer_email,))
    total_spent_past_year = cursor.fetchone()

    # Query to get the month-wise spending for the last six months
    monthly_spending_query = '''
        SELECT MONTHNAME(purchase_date) AS month, YEAR(purchase_date) AS year, 
            SUM(amount_paid) AS total_amount 
        FROM purchase 
        WHERE email_id = %s AND 
            purchase_date BETWEEN DATE_SUB(CURDATE(), INTERVAL 6 MONTH) AND CURDATE() 
        GROUP BY month, year 
        ORDER BY year, month DESC;
    '''
    cursor.execute(monthly_spending_query, (customer_email))
    monthly_spending_data = cursor.fetchall()

    # Initialize variables for date range
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')
    date_range_spending_amount = None
    date_range_monthly_spending_data = None

    # If both start_date and end_date are provided, fetch the data within the range
    if start_date and end_date:
        # Total amount spent in the date range
        amount_in_date_range_query = '''
            SELECT SUM(amount_paid) AS total_amount
            FROM `purchase`
            WHERE email_id = %s AND purchase_date BETWEEN %s AND %s
        '''
        cursor.execute(amount_in_date_range_query, (customer_email, start_date, end_date))
        date_range_spending_amount = cursor.fetchone()
        
        # Month wise spending in the date range
        date_range_monthly_spending_query = '''
        SELECT MONTHNAME(purchase_date) AS month, YEAR(purchase_date) AS year, 
            SUM(amount_paid) AS total_amount 
        FROM purchase 
        WHERE email_id = %s AND 
            purchase_date BETWEEN %s and %s 
        GROUP BY month, year 
        ORDER BY year, month DESC;
        '''
        cursor.execute(date_range_monthly_spending_query, (customer_email, start_date, end_date))
        date_range_monthly_spending_data = cursor.fetchall()
    else:
        date_range_spending_amount = None

    cursor.close()
    
    return render_template('customer-spending.html', total_spent_past_year=total_spent_past_year['total_amount'],
                           monthly_spending_data=monthly_spending_data,
                           start_date=start_date, end_date=end_date, 
                           date_range_spending_amount=date_range_spending_amount, # to fetch total amount only
                           date_range_monthly_spending_data=date_range_monthly_spending_data # to fetch all data
                           )
                           

@app.route('/customer-rate-flight', methods=['GET'])
def customer_rate_flight():
    if(isNotValidCustomer()):
        # The user is not logged in, redirect them to the login page
        return redirect(url_for('customer_login'))
    
    customer_email = session.get('email')  # Retrieve the logged-in user's email from the session
    cursor = conn.cursor()

    # Fetch flights that have not been rated by the user yet: Display details from flight and purchase, and check the review table for existing entries
    query = '''
    SELECT 
        p.ticketID,
        f.airline_name, 
        f.flight_num, 
        f.departure_airport,
        f.arrival_airport,
        f.departure_date, 
        f.departure_time
    FROM 
        purchase p, flight f, ticket t
    WHERE 
        p.ticketID = t.ticketID AND
        t.airline_name = f.airline_name AND
        t.flight_num = f.flight_num AND
        t.departure_date = f.departure_date AND
        t.departure_time = f.departure_time AND
        p.email_id = %s AND 
        (f.arrival_date < CURRENT_DATE() OR (f.arrival_date = CURRENT_DATE() AND f.arrival_time < CURRENT_TIME())) AND
        NOT EXISTS (
            SELECT 1 FROM review r WHERE r.ticketID = p.ticketID
        )
    '''
    cursor.execute(query, (customer_email))
    flights_to_rate = cursor.fetchall()
    cursor.close()

    return render_template('customer-rate-flight.html', flights=flights_to_rate)

@app.route('/customer-submit-rating', methods=['POST'])
def customer_submit_rating():
    # Retrieve data from form
    ticketID = request.form.get('ticketID')
    rate = request.form.get('rate')
    comment = request.form.get('comment')
    customer_email = session.get('email')

    cursor = conn.cursor()
	# Insert the data from the form into the review table
    query = 'INSERT INTO review (ticketID, email_id, rate, comment) VALUES (%s, %s, %s, %s)'
    cursor.execute(query, (ticketID, customer_email, rate, comment))
    conn.commit() 
    cursor.close()

    return redirect(url_for('customer_rate_flight'))

@app.route('/customer-view-flights', methods=['GET','POST'])
def customer_view_flights():
    if(isNotValidCustomer()):
        # The user is not logged in, redirect them to the login page
        return redirect(url_for('customer_login'))

    customer_email = session.get('email')  # Retrieve the logged-in user's email from the session
    cursor = conn.cursor()

    # Fetch upcoming flights
    upcoming_flights_query = '''
        SELECT p.first_name, p.ticketID, f.airline_name, f.flight_num, f.departure_airport, f.arrival_airport, 
        f.departure_date, f.departure_time,
        (f.departure_date > CURRENT_DATE() OR 
        (f.departure_date = CURRENT_DATE() AND f.departure_time > ADDTIME(CURRENT_TIME(), '24:00:00'))) AS can_cancel
        FROM purchase p, flight f, ticket t WHERE p.ticketID = t.ticketID AND 
        t.airline_name = f.airline_name AND
        t.flight_num = f.flight_num AND
        t.departure_date = f.departure_date AND
        t.departure_time = f.departure_time AND
        p.email_id = %s
        AND f.departure_date >= CURRENT_DATE()
        ORDER BY departure_date ASC, departure_time ASC
    '''
    # The above SQL Query has a boolean value that shows whether the flight is less than 24 hours away, by which the user cannot be provided an option to cancel
    cursor.execute(upcoming_flights_query, (customer_email,))
    upcoming_flights = cursor.fetchall()

     # Fetch previous flights
    previous_flights_query = '''
        SELECT p.first_name, p.ticketID, f.airline_name, f.flight_num, f.departure_airport, f.arrival_airport, 
        f.departure_date, f.departure_time
        FROM purchase p, flight f, ticket t WHERE p.ticketID = t.ticketID AND 
        t.airline_name = f.airline_name AND
        t.flight_num = f.flight_num AND
        t.departure_date = f.departure_date AND
        t.departure_time = f.departure_time AND
        p.email_id = %s
        AND f.departure_date < CURRENT_DATE()
        ORDER BY departure_date DESC, departure_time DESC
    '''
    cursor.execute(previous_flights_query, (customer_email))
    previous_flights = cursor.fetchall()

    cursor.close()

    return render_template('customer-view-flights.html', upcoming_flights = upcoming_flights, previous_flights = previous_flights)

@app.route('/customer-cancel-flight', methods=['GET','POST'])
def customer_cancel_flight():
    if(isNotValidCustomer()):
        # The user is not logged in, redirect them to the login page
        return redirect(url_for('customer_login'))
    
    # Get the ticketID from customer view flights page
    ticket_id_to_cancel = request.form.get('cancel_ticket_id')
    customer_email = session['email']

    cursor = conn.cursor()

    # Check if the flight is more than 24 hours away
    # (Double checking in the back-end too. Already blocked in the front-end)
    query = '''
    SELECT
        (f.departure_date > CURRENT_DATE() OR 
        (f.departure_date = CURRENT_DATE() AND f.departure_time > ADDTIME(CURRENT_TIME(), '24:00:00'))) AS can_cancel
        FROM purchase p, flight f, ticket t WHERE p.ticketID = t.ticketID AND 
        t.airline_name = f.airline_name AND
        t.flight_num = f.flight_num AND
        t.departure_date = f.departure_date AND
        t.departure_time = f.departure_time AND
        p.ticketID = %s AND p.email_id = %s
        AND f.departure_date >= CURRENT_DATE()
    '''
    cursor.execute(query, (ticket_id_to_cancel, customer_email))
    can_cancel = cursor.fetchone()
    
    if can_cancel and (can_cancel['can_cancel'] == 1):
        try:
            # Add 1 available_seat to the flight
            update_seats_query = '''
            UPDATE flight f
                JOIN ticket t ON f.airline_name = t.airline_name 
                AND f.flight_num = t.flight_num 
                AND f.departure_date = t.departure_date 
                AND f.departure_time = t.departure_time
            SET f.available_seats = f.available_seats + 1
            WHERE t.ticketID = %s;
            '''
            cursor.execute(update_seats_query, (ticket_id_to_cancel))
            
            # Delete the data from purchase and ticket table in the same order
            cursor.execute('DELETE FROM purchase WHERE ticketID = %s AND email_id = %s', (ticket_id_to_cancel, customer_email))
            cursor.execute('DELETE FROM ticket WHERE ticketID = %s', (ticket_id_to_cancel))
            conn.commit()

        except Exception as e:
            conn.rollback()  # Roll back the transaction on error
            print(f"Error: {e}")  # Logging the exception can help in debugging
            error = "Could not complete the cancellation. Aborted."
            return render_template('customer-view-flights.html', error=error)
        
        finally:
            cursor.close()  # Ensure the cursor is closed
    else:
        cursor.close()  # Close cursor if cancellation is not allowed
        error = "Flight cannot be cancelled within 24 hours of departure."
        return render_template('customer-view-flights.html', error=error)

    return redirect(url_for('customer_view_flights'))
# CUSTOMER execution ends here
###################### 

################################################################################################################################
#Airline Staff

##################################################
#REGISTER
@app.route('/register_airline_staff')
def register_airline_staff():
	return render_template('register_airline_staff.html')


#Registers Staff -> puts data into database only if allowed
@app.route('/registerStaff', methods=['GET', 'POST'])
def registerStaff():

	#get query to see whether username already exists
	username = request.form['username']
	cursor = conn.cursor()
	query = 'SELECT * FROM airline_staff WHERE username = %s'
	cursor.execute(query, (username))
	usernameExists = cursor.fetchone()
	
	#get query to see whether airline exists
	airline_name = request.form['airline_name']
	airline_query = 'SELECT * FROM airline where airline_name = %s'
	cursor.execute(airline_query, (airline_name))
	airlineExists = cursor.fetchone()

	error = None
	if(usernameExists):
		#If the previous query returns data, then user exists
		error = "This user already exists"
		return render_template('register_airline_staff.html', error = error)
	elif(airlineExists is None):
		error = "This airline does not exist"
		return render_template('register_airline_staff.html', error = error)

	#if neither of the errors above occur add data to database
	else:

		#insert given user data into airline_staff 
		password = hashlib.md5(request.form['password'].encode()).hexdigest()
		first_name = request.form['first_name']
		last_name = request.form['last_name']
		date_of_birth = request.form['date_of_birth']
		insert_staff_query = 'INSERT INTO airline_staff VALUES(%s, %s, %s, %s, %s, %s)'
		cursor.execute(insert_staff_query, (airline_name, username, password, first_name, last_name, date_of_birth))

		#insert unique phone numbers into staff_phone set
		phone_numbers = request.form.getlist('staff_phone[]')
		insert_phone_query = 'INSERT INTO staff_phone VALUES(%s, %s)'
		phone_already_query = 'SELECT * from staff_phone where username = %s and phone_num = %s'
		for phone in phone_numbers:
			if(phone == ''): continue
			cursor.execute(phone_already_query, (username, phone))
			phoneExists = cursor.fetchone();
			if(phoneExists is None):
				cursor.execute(insert_phone_query, (username, phone))


		#insert unique emails in staff_email
		emails = request.form.getlist('staff_email[]')
		insert_email_query = 'INSERT INTO staff_email VALUES(%s, %s)'
		email_already_query = 'SELECT * from staff_email where username = %s and email_id = %s'
		for email in emails:
			if(email == ''): continue
			cursor.execute(email_already_query, (username, email))
			emailExists = cursor.fetchone();
			if(emailExists is None):
				cursor.execute(insert_email_query, (username, email))

		#if they register they automatically are logged in
		session['username'] = username
		session['password'] = password
		session['first_name'] = first_name
		session['airline'] = airline_name
		
		conn.commit()
		cursor.close()
		return redirect(url_for('staff_home'))

##################################################


##################################################
#LOGIN

@app.route('/login_airline_staff')
def login_airline_staff():
	return render_template('login_airline_staff.html')

@app.route('/loginStaff', methods=['GET', 'POST'])
def loginStaff():

	#grabs information from the forms
	username = request.form['username']
	password = hashlib.md5(request.form['password'].encode()).hexdigest()

	#queries database to see if such tuple exists
	cursor = conn.cursor()
	query = 'SELECT * FROM airline_staff WHERE username = %s and pwd = %s'
	cursor.execute(query, (username, password))
	data = cursor.fetchone()
	cursor.close()


	error = None

	if(data):
		#if tuple exists create a session for the the user and login
		session['username'] = username
		session['password'] = password
		session['airline'] = data['airline_name']
		session['first_name'] = data['first_name']
		return redirect(url_for('staff_home'))
	else:
		#if tuple doesn't exist then throw error message
		error = 'Invalid login or username'
		return render_template('login_airline_staff.html', error=error)

##################################################

#If the staff exists then returns false if Staff does not exist return True or if Session is not open return True
def isNotValidStaff():
	if(len(session) == 0): return True
	if(session['username'] is None): return True
	if(session['password'] is None): return True
	username = session['username']
	password = session['password']
	cursor = conn.cursor()
	query = 'SELECT * FROM airline_staff WHERE username = %s and pwd = %s'
	cursor.execute(query, (username, password))
	data = cursor.fetchone()
	cursor.close()
	if(data is None): return True
	return False


@app.route('/staff_home')
def staff_home():
	if(isNotValidStaff()):
		return redirect(url_for('login_airline_staff'))
	return render_template('staff_home.html', username = session['first_name'])

@app.route('/logout')
def logout():
	session.clear()
	return redirect(url_for('login_airline_staff'))

@app.route('/view_flights')
def view_flights():
	if(isNotValidStaff()):
		return redirect(url_for('login_airline_staff'))

	cursor = conn.cursor()
	thirty_day_query = 'SELECT * FROM flight WHERE airline_name = %s and CURRENT_DATE <= departure_date and departure_date <= DATE_ADD(CURRENT_DATE, INTERVAL 30 DAY) ORDER BY departure_date DESC'
	cursor.execute(thirty_day_query, (session['airline']))
	thirty_day_flights = cursor.fetchall()
	cursor.close()
	message = "Flights in next 30 days"
	return render_template('view_flights.html', outBoundFlights = thirty_day_flights, message = message)

@app.route('/viewFlights', methods=['GET', 'POST'])
def viewFlights():
	if(isNotValidStaff()):
		return redirect(url_for('login_airline_staff'))

	cursor = conn.cursor()
	flight_num = request.form.get('flight_num')
	start_date = request.form.get('start_date')
	end_date = request.form.get('end_date')
	departure_airport = request.form.get('departure_airport')
	arrival_airport = request.form.get('arrival_airport')

	search_flight_query = "SELECT * FROM flight WHERE "
	conditions = []
	query_conditions = []

	if flight_num:
		conditions.append("flight_num = %s")
		query_conditions.append(flight_num)
	if start_date and end_date:
		conditions.append("departure_date BETWEEN %s AND %s")
		query_conditions.append(start_date)
		query_conditions.append(end_date)
	elif start_date:
		conditions.append("departure_date >= %s")
		query_conditions.append(start_date)
	elif end_date:
		conditions.append("departure_date <= %s")
		query_conditions.append(end_date)
	if(departure_airport):
		conditions.append("departure_airport = %s")
		query_conditions.append(departure_airport)
	if(arrival_airport):
		conditions.append("arrival_airport = %s")
		query_conditions.append(arrival_airport)

	conditions.append("airline_name = %s")
	query_conditions.append(session['airline'])

	if conditions:
		search_flight_query += " AND ".join(conditions)

	cursor.execute(search_flight_query, tuple(query_conditions))
	searchResults = cursor.fetchall()
	message = "Here are the results for your query"

	for flight in searchResults:
		current_date = datetime.now().date()
		current_time = datetime.now().time()
		dep_time_string = str(flight['departure_time'])


		departure_time_nonString = datetime.strptime(dep_time_string, '%H:%M:%S').time()
		if(current_date > flight['departure_date']):
			flight['review'] = 'Reviews'
		elif(current_date == flight['departure_date'] and current_time >= departure_time_nonString):
			flight['review'] = 'Reviews'
		


	return render_template('view_flights.html', outBoundFlights = searchResults, message = message)

@app.route('/change_status', methods=['GET'])
def change_status():
	if(isNotValidStaff()):
		return redirect(url_for('login_airline_staff'))

	cursor = conn.cursor()
	flight_query = 'SELECT * FROM flight WHERE airline_name = %s and flight_num = %s and departure_date = %s and departure_time = %s'
	cursor.execute(flight_query, (request.args.get('param2'), request.args.get('param1'), request.args.get('param3'), request.args.get('param4')))
	flight = cursor.fetchone()
	cursor.close()


	return render_template('change_status.html', flight = flight)


@app.route('/changeStatus', methods=['GET','POST'])
def changeStatus():
	if(isNotValidStaff()):
		return redirect(url_for('login_airline_staff'))

	selected_status = request.form['status']
	cursor = conn.cursor()

	flight_change_query = 'UPDATE flight set flight_status = %s where airline_name = %s and flight_num = %s and departure_date = %s and departure_time = %s'
	flight_query = 'SELECT * FROM flight WHERE airline_name = %s and flight_num = %s and departure_date = %s and departure_time = %s'

	airline_name = request.form.get('airline_name')
	flight_num = request.form.get('flight_num')
	departure_date = request.form.get('departure_date')
	departure_time = request.form.get('departure_time')

	cursor.execute(flight_change_query, (selected_status, airline_name, flight_num, departure_date, departure_time))
	cursor.execute(flight_query, (airline_name, flight_num, departure_date, departure_time))
	flight = cursor.fetchone()
	conn.commit()
	cursor.close()

	return render_template('change_status.html', flight = flight)

@app.route('/see_customers', methods=['GET'])
def see_customers():
	if(isNotValidStaff()):
		return redirect(url_for('login_airline_staff'))
	
	airline_name = request.args.get('param2')
	flight_num = request.args.get('param1')
	departure_date = request.args.get('param3')
	departure_time = request.args.get('param4')

	cursor = conn.cursor()
	flight_query = 'SELECT * FROM flight WHERE airline_name = %s and flight_num = %s and departure_date = %s and departure_time = %s'
	cursor.execute(flight_query, (airline_name, flight_num, departure_date, departure_time))
	flight = cursor.fetchone()

	customer_query = 'SELECT * FROM purchase where ticketID in (SELECT ticketID from ticket where airline_name = %s and flight_num = %s and departure_date = %s and departure_time = %s)'
	cursor.execute(customer_query, (airline_name, flight_num, departure_date, departure_time))
	customers = cursor.fetchall()

	cursor.close()
	return render_template('see_customers.html', flight = flight, customers = customers)


@app.route('/create_new_flight', methods=['GET', 'POST'])
def create_new_flight():
	if(isNotValidStaff()):
		return redirect(url_for('login_airline_staff'))
	return render_template('create_new_flight.html')

@app.route('/createNewFlight', methods=['GET','POST'])
def createNewFlight():
	if(isNotValidStaff()):
		return redirect(url_for('login_airline_staff'))

	cursor = conn.cursor();
	flight_num = request.form['flight_num']
	departure_date = request.form['departure_date']
	departure_time = request.form['departure_time']
	flight_exists_query = 'SELECT * FROM flight where airline_name = %s and flight_num = %s and departure_time = %s and departure_date = %s'
	cursor.execute(flight_exists_query, (session['airline'], flight_num, departure_time, departure_date))
	flightExists = cursor.fetchone()

	#get query to see whether arrival airport exists
	arrival_airport = request.form['arrival_airport']
	arrival_aiport_query = 'SELECT * FROM airport where code = %s'
	cursor.execute(arrival_aiport_query, (arrival_airport))
	arrivalAirportExists = cursor.fetchone()

	#get query to see whether departure airport exists
	departure_airport = request.form['departure_airport']
	departure_aiport_query = 'SELECT * FROM airport where code = %s'
	cursor.execute(departure_aiport_query, (departure_airport))
	departureAirportExists = cursor.fetchone()

	#get query to see whether Airplane exists
	assigned_airplane_airline = request.form['assigned_airplane_airline']
	airplane_ID = request.form['assigned_airplaneID']
	assigned_airplane_airline_query = 'SELECT * FROM airplane where airline_name = %s and airplaneID = %s'
	cursor.execute(assigned_airplane_airline_query, (assigned_airplane_airline, airplane_ID))
	assignedAirplane = cursor.fetchone()

	#see if flight is scheudled for maintenance
	arrival_date = request.form['arrival_date']
	arrival_time = request.form['arrival_time']
	maintenance_check_query = 'SELECT * FROM maintenance where airline_name = %s and airplaneID = %s'
	cursor.execute(maintenance_check_query, (assigned_airplane_airline, airplane_ID))
	flight_maintenances = cursor.fetchall()

	arrival_date_NonStr = datetime.strptime(arrival_date, "%Y-%m-%d").date()
	departure_date_NonStr = datetime.strptime(departure_date, "%Y-%m-%d").date()
	arrival_time_NonStr = datetime.strptime(str(arrival_time), '%H:%M').time()
	departure_time_nonStr = datetime.strptime(str(departure_time), '%H:%M').time()

	if((arrival_date_NonStr, arrival_time_NonStr) <= (departure_date_NonStr, departure_time_nonStr)):
		error = "Can't have a flight land before it takes off"
		cursor.close()
		return render_template('create_new_flight.html', error = error)

	for maintenance in flight_maintenances:
		#returns true if the maintancence and flight overlap
		st_time = str(maintenance['st_time'])
		end_time = str(maintenance['end_time'])
		maintenance_start_time = datetime.strptime(st_time, '%H:%M:%S').time()
		maintenance_end_time = datetime.strptime(end_time, '%H:%M:%S').time()

		if  (arrival_date_NonStr, arrival_time_NonStr) >= (maintenance['st_date'], maintenance_start_time) and (departure_date_NonStr, departure_time_nonStr) <= (maintenance['end_date'], maintenance_end_time):
			error = "Flight Interferes with scheduled maintenance and therefore can not be created"
			cursor.close()
			return render_template('create_new_flight.html', error = error)

	
	if(flightExists is not None):
		error = "This Flight Already Exists"
		cursor.close()
		return render_template('create_new_flight.html', error = error)
	
	elif(arrivalAirportExists is None):
		error = "This Arrival Airport Does Not Exist"
		cursor.close()
		return render_template('create_new_flight.html', error = error)

	elif(departureAirportExists is None):
		error = "This Departure Aiport Does Not Exist"
		cursor.close()
		return render_template('create_new_flight.html', error = error)

	elif(assignedAirplane is None):
		error = "This Airplane Does Not Exist"
		cursor.close()
		return render_template('create_new_flight.html', error = error)

	else:
		base_price = request.form['base_price_ticket']
		selected_status = request.form['status'];
		total_seats_query = 'SELECT num_of_seats from airplane where airline_name = %s and airplaneID = %s'
		cursor.execute(total_seats_query, (assigned_airplane_airline, airplane_ID))
		total_seats = cursor.fetchone();
		insert_flight_query = 'INSERT INTO flight VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'
		cursor.execute(insert_flight_query, (session['airline'], departure_airport, arrival_airport, assigned_airplane_airline, airplane_ID, flight_num, departure_date, departure_time, arrival_date, arrival_time, base_price, selected_status, total_seats['num_of_seats'], total_seats['num_of_seats']))




		conn.commit()
		
		thirty_day_query = 'SELECT * FROM flight WHERE airline_name = %s and CURRENT_DATE <= departure_date and departure_date <= DATE_ADD(CURRENT_DATE, INTERVAL 30 DAY) ORDER BY departure_date DESC'
		cursor.execute(thirty_day_query, (session['airline']))
		thirty_day_flights = cursor.fetchall()
		cursor.close()
		cursor.close()
		message = "Flights in next 30 days"
		createFlight = 'Successfully Created a New Flight'
		return render_template('view_flights.html', outBoundFlights = thirty_day_flights, message = message, createFlight = createFlight)


@app.route('/create_new_airplane', methods=['GET', 'POST'])
def create_new_airplane():
	if(isNotValidStaff()):
		return redirect(url_for('login_airline_staff'))
	return render_template('create_new_airplane.html')

@app.route('/createNewAirplane', methods=['GET','POST'])
def createNewAirplane():
	if(isNotValidStaff()):
		return redirect(url_for('login_airline_staff'))

	cursor = conn.cursor()
	airplane_ID = request.form['airplaneID']

	airplane_exists_query = 'SELECT * from airplane where airplaneID = %s and airline_name = %s'
	cursor.execute(airplane_exists_query, (airplane_ID, session['airline']))
	airplaneExists = cursor.fetchone()

	if(airplaneExists is not None):
		error = "This airplane already exists"
		cursor.close()
		return render_template('create_new_airplane.html', error = error)

	else:
		num_of_seats = request.form['num_of_seats']
		manufacturing_company = request.form['manufacturing_company']
		manufacturing_date = request.form['manufacturing_date']
		model_num = request.form['model_num']
		insert_airplane_query = 'INSERT INTO airplane VALUES(%s, %s, %s, %s, %s, %s)'
		cursor.execute(insert_airplane_query, (session['airline'], airplane_ID, num_of_seats, manufacturing_company, manufacturing_date, model_num))
		conn.commit();
		cursor.close()
		return redirect(url_for('view_airplanes'))

@app.route('/view_airplanes', methods=['GET', 'POST'])
def view_airplanes():
	if(isNotValidStaff()):
		return redirect(url_for('login_airline_staff'))
	cursor = conn.cursor()
	airplanes_query = 'SELECT * FROM airplane where airline_name = %s'
	cursor.execute(airplanes_query, (session['airline']))
	airplanes = cursor.fetchall();
	cursor.close()

	message = "Successfully Created New Airplane"

	return render_template('view_airplanes.html', airplanes = airplanes, message = message)


@app.route('/create_new_airport', methods=['GET', 'POST'])
def create_new_airport():
	if(isNotValidStaff()):
		return redirect(url_for('login_airline_staff'))
	return render_template('create_new_airport.html')

@app.route('/createNewAirport', methods=['GET','POST'])
def createNewAirport():
	if(isNotValidStaff()):
		return redirect(url_for('login_airline_staff'))

	cursor = conn.cursor()
	airport_code = request.form['code']
	airport_exists_query = 'SELECT * FROM airport where code = %s'
	cursor.execute(airport_exists_query, (airport_code))
	airportExists = cursor.fetchone()

	if(airportExists is not None):
		error = 'This airport code has already been used'
		cursor.close()
		return render_template('create_new_airport.html', error = error)
	else:
		airport_name = request.form['airport_name']
		airport_city = request.form['city']
		airport_country = request.form['country']
		airport_terminals = request.form['terminals']
		airport_type = request.form['airport_type']
		new_airport_insert = 'INSERT INTO airport VALUES (%s, %s, %s, %s, %s, %s)'

		cursor.execute(new_airport_insert, (airport_code, airport_name, airport_city, airport_city, airport_terminals, airport_type))
		conn.commit();
		cursor.close();
		success = 'Airport ' + airport_code + ' has Successfully been created'
		return render_template('create_new_airport.html', success = success)

@app.route('/search_flight_ratings', methods=['GET', 'POST'])
def search_flight_ratings():
	if(isNotValidStaff()):
		return redirect(url_for('login_airline_staff'))
	return render_template('search_flight_ratings.html')


@app.route('/searchFlightRatings', methods=['GET', 'POST'])
def searchFlightRatings():
	if(isNotValidStaff()):
		return redirect(url_for('login_airline_staff'))

	cursor = conn.cursor()
	airline_name = request.form['airline_name']
	flight_num = request.form['flight_num']
	departure_date = request.form['departure_date']
	departure_time = request.form['departure_time']

	flight_exists_query = 'SELECT * FROM flight where airline_name = %s and flight_num = %s and departure_time = %s and departure_date = %s'
	cursor.execute(flight_exists_query, (airline_name, flight_num, departure_time, departure_date))
	flightExists = cursor.fetchone()

	current_date = datetime.now().date()
	current_time = datetime.now().time()

	departure_date_nonString = datetime.strptime(departure_date, '%Y-%m-%d').date()
	departure_time_nonString = datetime.strptime(departure_time, '%H:%M').time()

	if(flightExists is None):
		error = 'This Flight does not exist'
		return render_template('search_flight_ratings.html', error = error)
	elif(departure_date_nonString > current_date and departure_time_nonString > current_time):
		error = 'This Flight has not happened yet and therefore has no reviews'
		return render_template('search_flight_ratings.html', error = error)

	return printFlightRatings(flightExists)


@app.route('/printFlightRatings', methods=['GET','POST'])
def printFlightRatings(flight):
	if(isNotValidStaff()):
		return redirect(url_for('login_airline_staff'))

	cursor = conn.cursor()
	reviews_query = 'SELECT * FROM review where ticketID in (SELECT ticketID FROM ticket WHERE airline_name = %s and flight_num = %s and departure_date = %s and departure_time = %s)'
	review_avg_query = 'SELECT avg(rate) as avgRate FROM review where ticketID in (SELECT ticketID FROM ticket WHERE airline_name = %s and flight_num = %s and departure_date = %s and departure_time = %s)'
	cursor.execute(reviews_query, (flight['airline_name'], flight['flight_num'], flight['departure_date'], flight['departure_time']))
	reviews = cursor.fetchall()
	cursor.execute(review_avg_query, (flight['airline_name'], flight['flight_num'], flight['departure_date'], flight['departure_time']))
	avgReview = cursor.fetchone()
	cursor.close()

	return render_template('print_flight_ratings.html', reviews = reviews, avgReview = avgReview, flight = flight)


@app.route('/view_reviews', methods=['GET'])
def view_reviews():
	if(isNotValidStaff()):
		return redirect(url_for('login_airline_staff'))

	cursor = conn.cursor()
	flight_query = 'SELECT * FROM flight WHERE airline_name = %s and flight_num = %s and departure_date = %s and departure_time = %s'
	cursor.execute(flight_query, (request.args.get('param2'), request.args.get('param1'), request.args.get('param3'), request.args.get('param4')))
	flight = cursor.fetchone()
	cursor.close()

	return printFlightRatings(flight)


@app.route('/schedule_maintenance', methods=['GET', 'POST'])
def schedule_maintenance():
	if(isNotValidStaff()):
		return redirect(url_for('login_airline_staff'))
	return render_template('schedule_maintenance.html')


@app.route('/scheduleMaintenance', methods=['GET','POST'])
def scheduleMaintenance():
	if(isNotValidStaff()):
		return redirect(url_for('login_airline_staff'))

	cursor = conn.cursor()
	airlineName = request.form['airline_name']
	airplaneID = request.form['airplane_ID']
	airplane_query = 'SELECT * FROM airplane WHERE airline_name = %s and airplaneID = %s'
	cursor.execute(airplane_query, (airlineName, airplaneID))
	airplane = cursor.fetchone()

	if(airplane is None):
		error = 'This Airplane does not Exist'
		cursor.close();
		return render_template('schedule_maintenance.html', error = error)
	
	flight_check_query = 'SELECT * from flight where assigned_airplaneID = %s and assigned_airplane_airline = %s'
	cursor.execute(flight_check_query, (airplaneID, airlineName))
	flights = cursor.fetchall()

	for flight in flights:
		arrival_date_NonStr = datetime.strptime(str(flight['arrival_date']), "%Y-%m-%d").date()
		departure_date_NonStr = datetime.strptime(str(flight['departure_date']), "%Y-%m-%d").date()
		arrival_time_NonStr = datetime.strptime(str(flight['arrival_time']), '%H:%M:%S').time()
		departure_time_nonStr = datetime.strptime(str(flight['departure_time']), '%H:%M:%S').time()

		#returns true if the maintancence and flight overlap
		st_date = request.form['start_date']
		end_date = request.form['end_date']
		st_time = str(request.form['start_time'])
		end_time = str(request.form['end_time'])
		maintenance_start_time = datetime.strptime(st_time, '%H:%M').time()
		maintenance_end_time = datetime.strptime(end_time, '%H:%M').time()
		maintenance_start_date = datetime.strptime(st_date, "%Y-%m-%d").date()
		maintenance_end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

		if  (arrival_date_NonStr, arrival_time_NonStr) >= (maintenance_start_date, maintenance_start_time) and (departure_date_NonStr, departure_time_nonStr) <= (maintenance_end_date, maintenance_end_time):
			error = "Maintenance interferes with scheduled flight and therefore can not be created"
			cursor.close()
			return render_template('schedule_maintenance.html', error = error)

	maintenance_insert_query = 'INSERT INTO maintenance VALUES (%s, %s, %s, %s, %s, %s)'
	cursor.execute(maintenance_insert_query, (airlineName, airplaneID, request.form['start_date'], request.form['start_time'], request.form['end_date'], request.form['end_time']))
	conn.commit();
	cursor.close();
	message = 'Successfully scheduled maintenance for given airplane'
	return render_template('schedule_maintenance.html', message = message)

@app.route('/view_frequent_customers', methods=['GET', 'POST'])
def view_frequent_customers():
	if(isNotValidStaff()):
		return redirect(url_for('login_airline_staff'))
	
	cursor = conn.cursor()
	most_frequent_query = 'SELECT email_id, first_name, last_name, date_of_birth, count(*) as frequency from purchase natural join customer natural join ticket where airline_name = %s group by email_id order by frequency desc'
	cursor.execute(most_frequent_query, (session['airline']))
	customers = cursor.fetchall()
	cursor.close()
	return render_template('view_frequent_customers.html', customers = customers)

@app.route('/view_cusomter_flights', methods=['GET'])
def view_cusomter_flights():
	if(isNotValidStaff()):
		return redirect(url_for('login_airline_staff'))

	cursor = conn.cursor()
	user_email_id = request.args.get('param1')
	customer_query = 'SELECT * from customer where email_id = %s'
	cursor.execute(customer_query, (user_email_id))
	customer = cursor.fetchone()

	flights_query = 'SELECT airline_name, departure_airport, arrival_airport, assigned_airplane_airline, assigned_airplaneID, flight_num, departure_date, departure_time, arrival_date, arrival_time, base_price_ticket, flight_status, total_seats, available_seats from (customer, purchase) natural join ticket natural join flight where customer.email_id = purchase.email_id and customer.email_id = %s and airline_name = %s'
	cursor.execute(flights_query, (user_email_id, session['airline']))
	flights = cursor.fetchall();
	cursor.close()
	for flight in flights:
		current_date = datetime.now().date()
		current_time = datetime.now().time()
		dep_time_string = str(flight['departure_time'])


		departure_time_nonString = datetime.strptime(dep_time_string, '%H:%M:%S').time()

		if(current_date > flight['departure_date']):
			flight['review'] = 'Reviews'
		elif(current_date == flight['departure_date'] and current_time >= departure_time_nonString):
			flight['review'] = 'Reviews'
		

	return render_template('view_customer_flights.html', customer = customer, flights = flights)

@app.route('/view_earned_revenue', methods=['GET', 'POST'])
def view_earned_revenue():
	if(isNotValidStaff()):
		return redirect(url_for('login_airline_staff'))

	cursor = conn.cursor();
	monthly_query = 'SELECT sum(amount_paid) as month_amt from purchase natural join ticket where airline_name = %s and purchase_date >= DATE_SUB(CURDATE(), INTERVAL 1 MONTH)'
	cursor.execute(monthly_query, (session['airline']))
	monthly_amount = cursor.fetchone()

	yearly_query = 'SELECT sum(amount_paid) as year_amt from purchase natural join ticket where airline_name = %s and purchase_date >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR)'
	cursor.execute(yearly_query, (session['airline']))
	yearly_amount = cursor.fetchone()
	cursor.close()

	return render_template('view_earned_revenue.html', month = monthly_amount['month_amt'], year = yearly_amount['year_amt'])

@app.route('/check_flight_status', methods=['GET', 'POST'])
def check_flight_status():
    return render_template('check_flight_status.html')

@app.route('/checkFlightStatus', methods=['GET', 'POST'])
def checkFlightStatus():

    cursor = conn.cursor()
    airline = request.form['airline_name']
    flight_num = request.form['flight_num']
    departure_date = request.form['departure']
    arrival_date = request.form['arrival']


    flight_query = 'SELECT * FROM flight where airline_name = %s and flight_num = %s and departure_date = %s and arrival_date = %s'
    cursor.execute(flight_query, (airline, flight_num, departure_date, arrival_date))
    flightExists = cursor.fetchall()
    cursor.close()
    if(not flightExists):
        error = "Sorry this flight does not exist"
        return render_template('check_flight_status.html', error = error)
    else:
        return render_template('check_flight_status.html', flights = flightExists)
##################################################

app.secret_key = 'some key that you will never guess'
# app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=5)
#Run the app on localhost port 5000
# debug = True -> you don't have to restart flask
#for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
	app.run('127.0.0.1', 5000, debug = True)








