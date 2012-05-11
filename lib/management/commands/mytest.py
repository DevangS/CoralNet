from django.core.management.base import NoArgsCommand
from django.core.management.commands.test import Command as TestCommand
from django.core.management import call_command

class Command(NoArgsCommand):
    option_list = TestCommand.option_list
    help = 'Runs the test suite for all applications in settings.MY_INSTALLED_APPS.'

    requires_model_validation = False

    def handle_noargs(self, **options):
        from django.conf import settings

        print "Running tests for the following apps:\n{0}\n".format(
            ', '.join(settings.MY_INSTALLED_APPS))

        call_command('test', *settings.MY_INSTALLED_APPS, **options)

