import sqlite3
from flask import Flask, render_template, request, url_for, flash, redirect
from werkzeug.exceptions import abort
from collections import defaultdict
from datetime import datetime

app = Flask(__name__)

# Connection to DB
def get_db_connection():
    conn = sqlite3.connect('parlements.db')
    conn.row_factory = sqlite3.Row
    return conn

# Get liste des députés
def get_deputes():
    conn = get_db_connection()
    deputes = conn.execute('SELECT * FROM deputes').fetchall()
    conn.close()
    if deputes is None:
        abort(404)
    return deputes

# Calcul la moyenne de participation par législature
def moyenne_scrutins(legislature = 0):
    conn = get_db_connection()
    if legislature == 0:
        scrutins = conn.execute('SELECT * FROM scrutins').fetchall()
    else:
        scrutins = conn.execute('SELECT * FROM scrutins where legislature = ?', (legislature,)).fetchall()
    if scrutins is None:
        return None
    moyennes = []
    for scrutin in scrutins:
        add = scrutin["votes_pour"] + scrutin["votes_contre"] + scrutin["votes_abstention"] + scrutin["non_votants"]
        moyenne = round(add / 577. * 100, 2)
        moyennes.append(moyenne)
    if len(moyennes) == 0:
        return None
    moyenne = round(sum(moyennes) / len(moyennes), 2)
    conn.close()
    return moyenne

# Calcul la moyenne de participation par scrutins
def get_percent_scrutins(legislature = 0):
    conn = get_db_connection()
    if legislature == 0:
        scrutins = conn.execute('SELECT * FROM scrutins ORDER BY date_seance ASC').fetchall()
    else:
        scrutins = conn.execute('SELECT * FROM scrutins where legislature = ? ORDER BY date_seance ASC', (legislature,)).fetchall()
    if scrutins is None:
        return None
    percent = {}
    for scrutin in scrutins:
        add = scrutin["votes_pour"] + scrutin["votes_contre"] + scrutin["votes_abstention"] + scrutin["non_votants"]
        moyenne = round(add / 577. * 100, 2)
        entry = [scrutin["numero"], moyenne, scrutin["date_seance"]]
        # If the key does not exist in the dictionary, initialize it with an empty list
        if scrutin["legislature"] not in percent:
            percent[scrutin["legislature"]] = []
        percent[scrutin["legislature"]].append(entry)
    conn.close()
    return percent

# Get liste des législature
def list_legislature():
    conn = get_db_connection()
    rows = conn.execute('SELECT legislature FROM deputes').fetchall()
    unique = set(row['legislature'] for row in rows)
    legislatures = sorted(unique, reverse=True)
    conn.close()
    return legislatures

# Calcul de la moyenne de participation par session
def average_votes_per_day(data):
    result = {}
    
    for index, entries in data.items():
        daily_votes = defaultdict(list)
        
        for entry in entries:
            numero, votes, date_str = entry
            date = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S.%f')
            daily_votes[date].append(votes)
        
        avg_votes_per_day = []
        for date, votes_list in daily_votes.items():
            avg_vote = sum(votes_list) / len(votes_list)
            avg_votes_per_day.append([avg_vote, date.strftime('%Y-%m-%d %H:%M:%S.%f')])
        
        # Sort by date to maintain order
        avg_votes_per_day.sort(key=lambda x: datetime.strptime(x[1], '%Y-%m-%d %H:%M:%S.%f'))
        
        result[index] = avg_votes_per_day
    
    return result

@app.route('/', methods=('GET', 'POST'))
@app.route('/<int:legislature>/', methods=('GET', 'POST'))
def index(legislature = 0):
    conn = get_db_connection()
    percent_scrutins = get_percent_scrutins(legislature)
    moyenne = moyenne_scrutins(legislature)
    legislatures = list_legislature()
    average_votes_per_day(percent_scrutins)
    if moyenne is None:
        return render_template('en_cours.html', legislatures=legislatures, legislature=legislature)
    conn.close()
    return render_template('index.html', moyenne=moyenne, legislatures=legislatures, legislature=legislature, percent_scrutins=percent_scrutins)

@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404

# data = {
#     15: [
#         ['1', 99.65, '2017-07-04 00:00:00.000000'],
#         ['2', 26.17, '2017-07-06 00:00:00.000000']
#     ],
#     16: [
#         ['1', 45.12, '2017-07-05 00:00:00.000000'],
#         ['2', 32.89, '2017-07-07 00:00:00.000000']
#     ]
# }