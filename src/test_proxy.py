import os
import sys
import django

from django.core.management import call_command

# small test script that sets a variable and calls tests
# this is annoying but might work

# todo make this a command

def main(args: list[str]):

    # todo hardcoded
    os.environ['DJANGO_TEST_DB'] = 'tests.sqlite3'
    os.environ['DJANGO_SETTINGS_MODULE'] = "group4.settings"

    django.setup()
    call_command('makemigrations')
    call_command('migrate', verbosity=1, interactive=False)

    call_command('test', args)

if __name__ == "__main__":
    print(sys.argv)
    if len(sys.argv) > 2: 
        exit("Too many arguments")

    sys.argv.pop(0)

    main(sys.argv)
