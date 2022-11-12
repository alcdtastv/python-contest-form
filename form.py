import streamlit as st
import pandas as pd
from datetime import datetime
import sqlite3
import smtplib, ssl
from email.mime.text import MIMEText
from PIL import Image

#This script allows to run a web page to manage the registration for contests.

#Functions definition.
def mail(recipient, subject, body):
    port = 465
    smtp_server = 'sample.server'
    sender_email = 'sample.mail.com'
    password = 'sample.password'
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = ', '.join(recipient)

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, recipient, msg.as_string())

#Connection to the database.
con = sqlite3.connect('./data/form.db')

#Pulling contestants list, past winners list e allowed participants list.
contestants_list = pd.read_sql_query('SELECT * from contestants_list', con)

past_winners_list = pd.read_sql_query('SELECT * from past_winners_list', con)

event = pd.read_sql_query('SELECT * from event', con)

allowed_participants = pd.read_sql_query('SELECT * from allowed_participants', con)

#Frontend

#Removing menu button.
hide_streamlit_style = '''
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
'''
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

#Page title
if event.shape[0] == 0:
    st.title('No planned events')

else:
    #Title
    st.title(event['event'][0])
    st.subheader(event['date'][0]+' '+event['time'][0])

    ncol = contestants_list.shape[1]-1  # col count
    rw = -1

    with st.form(key='registration', clear_on_submit= True): #Data entry form
        cols = st.columns(ncol)
        rwdta = []

        for i in range(ncol):
            rwdta.append(cols[i].text_input(contestants_list.columns[i]))

        if st.form_submit_button('enter'):
            rw = contestants_list.shape[0] + 1
            rwdta.append(datetime.now())

            if rwdta[2] in contestants_list['Email'].values:
                st.write('You are already registered.')

            elif rwdta[2] not in allowed_participants['Email'].values:
                st.write('Invalid email address.')

            elif rwdta[2] in past_winners_list['Email'].values:
                st.write('Unable to register, you already won a previous event.')

            else:
                contestants_list.loc[rw] = rwdta
                contestants_list = contestants_list.applymap(str)
                contestants_list.to_sql('contestants_list', con, if_exists='replace', index=False)

                subject='Registration confirmed for '+event['event'][0]
                body='Dear '+rwdta[0]+',\n\nThank you for your registration for the '+event['event'][0]+' event.\n\nBest regards,\n\nsample Team'
                mail([rwdta[2]],subject,body)
                st.write('Registration confirmed.')

con.close()

#Images
image = Image.open('./data/sample.png')
st.image(image)

with open('./data/rules.txt', 'r', encoding='utf-8') as file:
    rules = file.read()

with open('./data/GDPR.txt', 'r', encoding='utf-8') as file:
    GDPR = file.read()

#Displaying rules and GDPR.
st.markdown(rules, unsafe_allow_html=True)
st.caption('<sup>1</sup> General Data Protection Regulation', unsafe_allow_html=True)
st.caption(GDPR)