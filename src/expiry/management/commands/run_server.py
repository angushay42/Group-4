import os
import time
import subprocess
from django.core.management import call_command, BaseCommand

class Command(BaseCommand):
    help = "Runs Django and APScheduler together."

    # def add_arguments(self, parser):
    #     parser.add_argument(
    #         "-t", "--test",         # names
    #         action="store_true",    # defaults to true if given
    #     )

    def handle(self, *args, **options):
        # main
        env = os.environ.copy()
        call_command('makemigrations')
        call_command('migrate')
        sched_proc = subprocess.Popen(
            ["python3", "manage.py", "runapscheduler"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            env=env
        )

        call_command('runserver')
        sched_proc.terminate()

        # wait for process to finish
        time.sleep(0.5)
