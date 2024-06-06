Create virtual env with diff version of python 
==============================================
Get executable path for desired python version
==============================================  
ie: which python3.10
/usr/bin/python3.10

==========================
Create virtual env python3.10
==========================
virtualenv -p /usr/bin/python3.10 <env_name>

==========================
Install python virtual env
==========================
1. sudo apt-get install python-virtualenv
2. virtualenv realityOneGroup
3. source energy/bin/activate
4. pip3 install Django
5. pip3 install -r requirements.txt 
6. django-admin startproject realityOneApi ==> cd to realityOneApi
7. manage.py startapp api
====
Test
====
8. manage.py runserver

	http://127.0.0.1:8000/ 

=================================
******* Configure pgsql Version (PostgreSQL 16.1) **********
=================================
sudo apt-get install postgresql
sudo apt-get install python-psycopg2
sudo apt-get install libpq-dev python-dev
pip3 install psycopg2

=================================
******* Configure Redis Cache **********
=================================
brew update
brew install redis
1.)Start Redis server.
    brew services start redis
2.)Test if Redis server is running.
    redis-cli ping
3.)Stop Redis server.
    brew services stop redis

==============================================
Change db config in settings.py file as follow
==============================================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'db',
        'USER': 'user',
        'PASSWORD': 'pwd',
        'HOST': 'server',
        'PORT': 'port',
    }
}
=========
Migration
=========
python manage.py makemigrations
python manage.py migrate

==========================
Create Super Admin Account
=================================================
python manage.py createsuperuser --username admin 
(password <password>)
=================================================