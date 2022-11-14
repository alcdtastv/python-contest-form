import pandas as pd
import schedule
import sqlite3
import smtplib, ssl
from email.mime.text import MIMEText
from datetime import datetime, timedelta

# This script allows to select a random winner from the contestants list and to send the emails regarding the outcome of the contest.
# To do so, it checks every minute the existence of an event in the db and pulls its date and time.
# If an event is found, it checks if the current time is equal to the event time minus 96 hours. If so, it selects a random winner and sends the emails.

def mail(recipient,subject,body):
    port = 465
    smtp_server = "sample.server"
    sender_email = "sample@email.com"
    password = 'sample.password'
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = ", ".join(recipient)

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, recipient, msg.as_string())

def job():
    #Connection to the database.
    con = sqlite3.connect("./data/form.db")

    #Pull event.
    event = pd.read_sql_query("SELECT * from event", con)

    if event.shape[0] == 0: #If no event is found, print 'No event'.
        print('No event')

    else:
        date_string = event['date'][0] + ' ' + event['time'][0]
        date_datetime = datetime.strptime(date_string, "%d/%m/%Y %H:%M")
        if date_datetime <= datetime.now() + timedelta(hours=96): #Check ora dell'event = ora corrente + 96 ore

            #Pull contestants list and past winners list
            contestants_list = pd.read_sql_query("SELECT * from contestants_list", con)
            past_winners_list = pd.read_sql_query("SELECT * from past_winners_list", con)

            if contestants_list.shape[0] == 0:
                
                #Send email to the organizer if no contestants are found.
                subject = 'No contestants ' + event['event'][0] + ' ' + event['date'][0] + ' ' + event['time'][0]
                body = 'No contestants'
                mail(['sample@email.com'] ,subject, body)

                #Delete event from db.
                event = pd.DataFrame(data = {'event': [], 'date': [], 'time': []})
                event.to_sql("event", con, if_exists="replace", index=False)

                #Reinstate event creation form in admin page
                form_entered = pd.read_sql_query("SELECT * from form_entered", con)
                form_entered['Form entered'][0] = 0
                form_entered.to_sql("form_entered", con, if_exists="replace", index=False)

                print('No contestants')

            else:
                #Select random winner
                winner=contestants_list.sample()

                #Check that the winner has not won al
                if winner.reset_index()['Email'][0] in past_winners_list['Email'].values:
                    winner = contestants_list[contestants_list.Email != winner.reset_index()['Email'][0]].sample

                #Send email to the winner
                subject='Contest result ' + event['event'][0]
                body='You won the contest ' + event['event'][0] + ' ' + event['date'][0] + ' ' + event['time'][0]
                mail([winner.reset_index()['Email'][0]], subject, body)

                #Send email to the losers
                losers_list=contestants_list[contestants_list.Email != winner.reset_index()['Email'][0]]
                subject='Contest result ' + event['event'][0]
                body='You lost the contest ' + event['event'][0] + ' ' + event['date'][0] + ' ' + event['time'][0]
                losers_list.Email.apply(lambda x: mail([x], subject, body))

                #Add winner to past winners list
                winner['event'] = event['event'][0]
                past_winners_list=pd.concat([past_winners_list,winner])
                past_winners_list.to_sql("past_winners_list", con, if_exists="replace", index=False)

                #Clear contestants list
                contestants_list = pd.DataFrame(data = {'Name': [], 'Surname': [], 'Email': [], 'Registration date and time': []})
                contestants_list.to_sql("contestants_list", con, if_exists="replace", index=False)

                #Delete event from db.
                event = pd.DataFrame(data = {'event': [], 'date': [], 'time': []})
                event.to_sql("event", con, if_exists="replace", index=False)

                #Reactivate event creation form in admin page
                form_entered = pd.read_sql_query("SELECT * from form_entered", con)
                form_entered['Form entered'][0] = 0
                form_entered.to_sql("form_entered", con, if_exists="replace", index=False)

                print('Success')

        
        else:
            print('Not yet')

    con.close()

schedule.every(1).minutes.do(job)

while True:
    schedule.run_pending()