import streamlit as st
import pandas as pd
import sqlite3
import smtplib, ssl
from email.mime.text import MIMEText
from datetime import datetime
import hashlib

#Form admin page
#This script allows to run the admin page for the form, through which it is possible to create a new event,
#modify the allowed participants list and manually add or remove winners.

#Functions definition.

def event_created(title,date,time):

    #This function is executed when a new event is created. It allows to save the event details in the db,
    #and send an email to the allowed participants and replaces the event creation form with the delete event button.
   
    #Connection to db.
    con = sqlite3.connect('./data/form.db')

    #Push event details in db.
    event = pd.DataFrame(data = {'event': title, 'date': date.strftime('%d/%m/%Y'), 'time': time}, index=[0])
    event.to_sql('event', con, if_exists='replace', index=False)

    #Replace event creation form with delete event button.
    form_entered = pd.read_sql_query('SELECT * from form_entered', con)
    form_entered['Form entered'][0] = 1
    form_entered.to_sql('form_entered', con, if_exists='replace', index=False)

    #Pull allowed participants list from db.
    allowed_participants = pd.read_sql_query('SELECT * from allowed_participants', con)

    #Send email to allowed participants.
    subject='Take part in the '+event['event'][0]+' contest!'
    body='sample email'
    mail(allowed_participants['Email'].values.tolist(),subject,body) 

    #Close connection to db.
    con.close()

def event_pre_deleted():
    
    #This function is executed when the delete event button is pressed.
    #It allows to replace the delete event button with the confirm delete event button.

    #Connection to db.
    con = sqlite3.connect('./data/form.db')

    #Replace delete event button with confirm delete event button.
    form_entered = pd.read_sql_query('SELECT * from form_entered', con)
    form_entered['Form entered'][0] = 2
    form_entered.to_sql('form_entered', con, if_exists='replace', index=False)

    #Close connection to db.
    con.close()

def event_deleted():

    #This function is executed when the confirm delete event button is pressed. It allows to delete the event details from the db (and so the event),
    #clear the participants list, and replace the confirm delete event button with the event creation form.

    #Connection to db.
    con = sqlite3.connect('./data/form.db')

    #Delete event details from db.
    evento = pd.DataFrame(data = {'Event': [], 'date': [], 'time': []})
    evento.to_sql('evento', con, if_exists='replace', index=False)

    #Clear participants list.
    contestants_list = pd.DataFrame(data = {'Name': [], 'Surname': [], 'Email': [], 'Registration date and time': []})
    contestants_list.to_sql('contestants_list', con, if_exists='replace', index=False)

    #Replace cancel button with form
    form_entered = pd.read_sql_query('SELECT * from form_entered', con)
    form_entered['Form entered'][0] = 0
    form_entered.to_sql('form_entered', con, if_exists='replace', index=False)

    #Close connection to db.
    con.close()

def event_restored():
    #This function is executed when the restore event button is pressed. It allows to replace the restore event button with the event creation form.

    #Connection to db.
    con = sqlite3.connect('./data/form.db')

    #Replace restore event button with event creation form.
    form_entered = pd.read_sql_query('SELECT * from form_entered', con)
    form_entered['Form entered'][0] = 1
    form_entered.to_sql('form_entered', con, if_exists='replace', index=False)

    #Close connection to db.
    con.close()

def mail(recipient, subject, body):

    port = 465
    smtp_server = 'sample.server'
    sender_email = 'sample@mail.com'
    password = 'sample.password'
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = ', '.join(recipient)

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, recipient, msg.as_string())

def encrypt_password(hash_string):
    sha_signature = \
        hashlib.sha256(hash_string.encode()).hexdigest()
    return sha_signature

def check_password():

    #This function handles authentication. Returns True if the password is correct, False otherwise.

    def password_entered():
        #Check if the password is correct.
        if (
            encrypt_password(st.session_state['username']) in st.secrets['passwords']
            and encrypt_password(st.session_state['password'])
            == st.secrets['passwords'][encrypt_password(st.session_state['username'])]
        ):
            st.session_state['password_correct'] = True
            del st.session_state['password']
            del st.session_state['username']
        else:
            st.session_state['password_correct'] = False

    if 'password_correct' not in st.session_state:
        #Upon first run, ask for username and password.
        st.text_input('Username', on_change=password_entered, key='username')
        st.text_input(
            'Password', type='password', on_change=password_entered, key='password')
        return False
    elif not st.session_state['password_correct']:
        #If password is wrong, show error message and ask for username and password again.
        st.text_input('Username', on_change=password_entered, key='username')
        st.text_input(
            'Password', type='password', on_change=password_entered, key='password')
        st.error('Username o password incorretti')
        return False
    else:
        #Correct password.
        return True


#Connection to db.
con = sqlite3.connect('./data/form.db')

#Pulling contestants list, past winners list and form_entered variable.
contestants_list = pd.read_sql_query('SELECT * from contestants_list', con)

past_winners_list = pd.read_sql_query('SELECT * from past_winners_list', con)

form_entered = pd.read_sql_query('SELECT * from form_entered', con)


#Frontend

#Removing menu button.
hide_streamlit_style = '''
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
'''
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

#Title
st.title('Admin page')

if True: #check_password():

    if form_entered['Form entered'][0] == 0: #Check variable Form entered, if it is 0, show event creation form.
        
        st.header('Event creation')

        with st.form(key='new_event'):

            columns_new_event = st.columns(3)

            with columns_new_event[0]:

                title = st.text_input('Title')

            with columns_new_event[1]:

                date = st.date_input('Date')

            with columns_new_event[2]:

                time = st.text_input('Time (HH:MM)')

            enter_event_button = st.form_submit_button('Enter')
            
        if enter_event_button == 1:

            event_created(title,date,time)
            st.experimental_rerun() #Allows the sequentially running frontend to display the elements correctly.
      
    elif form_entered['Form entered'][0] == 1: #Check variable Form entered, if it is 1, show delete event button.

        st.header('Delete event')

        tasto_annulla=st.button('Delete event', on_click=event_pre_deleted)

    else:  #Check form entered variable, if equal to 2 show confirm delete and restore buttons.
        st.header('Delete event')
        col1, col2= st.columns(2)

        with col1:
            confirm_delete_button=st.button('Confirm delete', on_click=event_deleted)
        
        with col2:
            confirm_delete_button=st.button('Restore event', on_click=event_restored)


    st.header('Allowed participants list upload box')

    allowed_participants_file = st.file_uploader(label = 'Upload one XLSX file', type = 'xlsx', accept_multiple_files = False)

    if allowed_participants_file is not None:

        allowed_participants = pd.read_excel(allowed_participants_file)

        allowed_participants.to_sql('allowed_participants', con, if_exists='replace', index=False)

        st.write(allowed_participants)


    st.header('Manually add a winner')

    with st.form(key='add_winner', clear_on_submit=True):

        add_winner_columns = st.columns(4)

        with add_winner_columns[0]:

            added_name = st.text_input('Name')

        with add_winner_columns[1]:

            added_surname = st.text_input('Surname')

        with add_winner_columns[2]:

            added_email = st.text_input('Email')

        with add_winner_columns[3]:

            added_event = st.text_input('Event')

        add_winner_button = st.form_submit_button('Enter')
            
        if add_winner_button == 1:

            row_to_be_added=[added_name, added_surname, added_email, datetime.now(), added_event]

            past_winners_list.loc[past_winners_list.shape[0] + 1] = row_to_be_added

    st.header('Manually remove a winner')

    with st.form(key='remove_winner', clear_on_submit=True):
        
        removed_email = st.text_input('Email')

        remove_winner_button = st.form_submit_button('Enter')
            
        if remove_winner_button == 1:

            past_winners_list = past_winners_list[past_winners_list.Email != removed_email]

    st.header('Contestants list')
    st.dataframe(contestants_list)

    st.header('Past winners list')
    st.dataframe(past_winners_list)

    st.write()

past_winners_list = past_winners_list.applymap(str)
past_winners_list.to_sql('past_winners_list', con, if_exists='replace', index=False)

con.close()
