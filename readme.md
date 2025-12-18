# Getting started

## Setup steps
- Install python3.13 (homebrew for Mac)
- Git clone repo
- `cd Group-4`
- Run `python3.13 -m venv env` in terminal
- Run `source env/bin/activate` in terminal to activate the virtual environment
- Run `pip install --upgrade pip && pip install -r requirements.txt` in terminal 
- Run `cd src` in terminal

Before the server can be started, you must *compile* tailwind. Do this by: `python3 manage.py tailwind build`.

To start the server, you use: `python3 manage.py runserver`. This is *only* the django server. This will not schedule any tasks. To do that, you must open a new terminal and setup the environment again:
    - `source env/bin/activate`

Now you can start the scheduler with `python3 manage.py runapscheduler`

**Expirimental**: To run both in one go, try `python3 manage.py run_server`. This is not tested, but could work. 

