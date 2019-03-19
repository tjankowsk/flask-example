import socket
import sys
import os
import datetime
import pymysql
from flask import Flask, render_template, g, current_app, request
import flask.cli
import flask_env
import click

INIT_DB = [
    #"CREATE DATABASE IF NOT EXISTS showcase",
    #"CREATE USER showcase_user@'%' identified by password",
    #"grant all on showcase.* to showcase_user@'%'",
    "CREATE TABLE IF NOT EXISTS nodes (name VARCHAR(255), last_active DATETIME)",
    "CREATE TABLE IF NOT EXISTS visitors (visitor_name VARCHAR(1024), visit_date DATETIME)"
]
FIND_NODE = "SELECT * FROM nodes where name = %s"
INSERT_NODE = "INSERT INTO nodes(name, last_active) VALUES (%s, %s)"
UPDATE_NODE = "UPDATE nodes SET last_active = %s WHERE name = %s"
GET_NODES = "SELECT * FROM nodes WHERE last_active > %s"
INSERT_VISITOR = "INSERT INTO visitors(visitor_name, visit_date) values (%s, %s)"
GET_VISITORS = "SELECT visitor_name, visit_date from visitors order by 2 desc limit 5"

class Configuration(metaclass=flask_env.MetaFlaskEnv):
    MYSQL_PORT = 3306
    MYSQL_HOST = "localhost"
    MYSQL_DB = "showcase"
    MYSQL_USER = "showcase_user"
    MYSQL_PASS = "password"

    DB_CONN = None

def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()

@click.command('init-db')
@flask.cli.with_appcontext
def init_db_command():
    init_db()
    click.echo("Initiated the DB")

app = Flask(__name__)
app.config.from_object(Configuration)
app.teardown_appcontext(close_db)
app.cli.add_command(init_db_command)

def init_db():
    connection = get_db()
    cur = connection.cursor()
    for statement in INIT_DB:
        cur.execute(statement)


def update_active_node():
    connection = get_db()
    cur = connection.cursor()
    cur.execute(FIND_NODE, [socket.gethostname()])
    if not cur.fetchall():
        cur.execute(INSERT_NODE, [socket.gethostname(), datetime.datetime.utcnow()])
        connection.commit()
        print(INSERT_NODE, [socket.gethostname(), datetime.datetime.utcnow()])
    else:
        cur.execute(UPDATE_NODE, [datetime.datetime.utcnow(), socket.gethostname()])
        connection.commit()
        print(UPDATE_NODE, [datetime.datetime.utcnow(), socket.gethostname()])

def register_visitor(visitor_data):
    connection = get_db()
    cur = connection.cursor()
    cur.execute(INSERT_VISITOR, [visitor_data, datetime.datetime.utcnow()])
    connection.commit()

def get_visitors():
    connection = get_db()
    cur = connection.cursor(pymysql.cursors.DictCursor)
    cur.execute(GET_VISITORS)
    return cur.fetchall()

def active_hosts():
    connection = get_db()
    cur = connection.cursor(pymysql.cursors.DictCursor)
    cur.execute(GET_NODES,
                [datetime.datetime.utcnow() - datetime.timedelta(minutes=5)])
    hosts = cur.fetchall()
    return ",".join([x["name"] for x in hosts])

def get_db():
    if 'db' not in g:
        g.db= pymysql.connect(
            port=current_app.config['MYSQL_PORT'],
            host=current_app.config['MYSQL_HOST'],
            database=current_app.config['MYSQL_DB'],
            user=current_app.config['MYSQL_USER'],
            password=current_app.config['MYSQL_PASS']
        )
    return g.db

@app.route("/")
def hostname():
    print(datetime.datetime.utcnow())
    register_visitor(request.headers["User-Agent"])
    visitors = get_visitors()
    print(visitors)
    update_active_node()
    return render_template("index.html",
                           hostname=socket.gethostname(),
                           hosts=active_hosts(),
                           visit_history=visitors)
if __name__ == '__main__':
    app.before_first_request(init_db)
    app.run(host='0.0.0.0', port=5000)
