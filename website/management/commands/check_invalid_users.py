#!/usr/bin/env python
# Post process data and mark users as invalid

from django.conf import settings
from django.core import management
from django.core.management.base import BaseCommand, CommandError

from dining_room.models import User


# Helper function

def message_if_true(check, msg):
    return msg if check else None


# Create the Command class

class Command(BaseCommand):
    """
    Iterate through all users and check if their data is valid. If not, state
    a reason why
    """

    DEFAULT_INCORRECT_REVIEWS = 10

    help = "Check users to see if the data is valid"

    def add_arguments(self, parser):
        parser.add_argument("--user-ids", nargs='*', default=[x.pk for x in User.objects.order_by('pk')], help="The user ids to get actions for")
        parser.add_argument("--incorrect-reviews", default=Command.DEFAULT_INCORRECT_REVIEWS)

    def handle(self, *args, **options):
        verbosity = options.get('verbosity')
        users = User.objects.filter(pk__in=options['user_ids'])

        # Setup the list of checks
        checks = {
            'incorrect_reviews': {
                'func': self._check_num_review_questions,
                'msg': "too many incorrect reviews",
                'incorrect_reviews': options['incorrect_reviews'],
            },
            'did_not_finish': {
                'func': self._check_finished,
                'msg': "did not finish",
            },
            'staff': {
                'func': self._check_staff,
                'msg': "staff",
            },
        }

        # Iterate through the users and get their data
        for user in users:
            if user.invalid_data:
                if verbosity > 1:
                    self.stdout.write(f"Skipping {user}: invalid")
                continue

            for check_name, check_options in checks.items():
                if user.invalid_data:
                    break

                result = check_options['func'](user, **check_options)
                if result is not None:
                    if verbosity > 0:
                        self.stdout.write(f"{user} failed {check_name}; making invalid")
                    user.ignore_data_reason = result
                    user.save()

            # Print a status message
            if verbosity > 1:
                self.stdout.write(f"Check complete for {user}")

        # Print a completion message
        self.stdout.write(self.style.SUCCESS("Users checked!"))

    def _check_num_review_questions(self, user, **options):
        return message_if_true(
            user.number_incorrect_knowledge_reviews > options['incorrect_reviews'],
            options['msg']
        )
    def _check_finished(self, user, **options):
        return message_if_true(user.study_progress != 'SURVEYED', options['msg'])

    def _check_staff(self, user, **options):
        return message_if_true(user.is_staff, options['msg'])
