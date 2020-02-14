import itertools
import datetime
import random

from django.test import SimpleTestCase, TestCase, Client
from django.db.models import Q
from django.urls import reverse
from django.contrib.messages import get_messages
from django.utils import timezone

from dining_room.models import User, StudyManagement
from dining_room.forms import CreateUserForm
from dining_room.utils import DropboxConnection


# The tests for the various forms and views go here

class LoginTestCase(TestCase):
    """
    A simple test case to test whether logins work
    """
    def test_login(self):
        sm = StudyManagement.get_default()

        # Create a user. Password should be the same as their username
        user = User.objects.create_user('test_user', 'test_user')
        user.study_condition = User.StudyConditions.DXAX_100
        user.start_condition = User.StartConditions.AT_COUNTER_OCCLUDING_ABOVE_MUG
        user.save()

        # Log the user in and test the log in as well as the user's association
        # to the manager object in the DB
        logged_in = self.client.login(username='test_user', password='test_user')
        self.assertTrue(logged_in)
        self.assertEqual(sm, user.study_management)


class CreateUserTestCase(TestCase):
    """
    Test the CreateUserForm and the assignment of users to conditions
    """

    START_CONDITIONS = [User.StartConditions.AT_COUNTER_ABOVE_MUG, User.StartConditions.AT_COUNTER_OCCLUDING_ABOVE_MUG]
    STUDY_CONDITIONS = [User.StudyConditions.BASELINE, User.StudyConditions.DXAX_100]

    def setUp(self):
        sm = StudyManagement.get_default()
        sm.enabled_start_conditions = "\n".join(CreateUserTestCase.START_CONDITIONS)
        sm.enabled_study_conditions = StudyManagement.convert_to_enabled_study_conditions(CreateUserTestCase.STUDY_CONDITIONS)
        sm.data_directory = 'userdata_test'
        sm.max_number_of_people = 4
        sm.number_per_condition = 1
        sm.save()

    def _assertSuccess(self, response):
        self.assertRedirects(response, reverse('dining_room:login'), fetch_redirect_response=False)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(messages, [])

    def _assertFail(self, response):
        self.assertRedirects(response, reverse('dining_room:login'), fetch_redirect_response=False)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(1, len(messages))
        self.assertIn("Thank you for your time", str(messages[0]))
        for msg in messages:
            msg.used = True

    def test_create_a_user(self):
        response = self.client.post(reverse('dining_room:create'))
        self._assertSuccess(response)

    def test_fail_surpass_total_max(self):
        sm = StudyManagement.get_default()
        sm.max_number_of_people = 0
        sm.save()
        response = self.client.post(reverse('dining_room:create'))
        self._assertFail(response)

    def test_fail_surpass_total_max_post_add(self):
        sm = StudyManagement.get_default()
        sm.max_number_of_people = 1
        sm.save()
        response = self.client.post(reverse('dining_room:create'))
        self._assertSuccess(response)
        response = self.client.post(reverse('dining_room:create'))
        self._assertFail(response)

    def test_fail_surpass_per_condition_max(self):
        sm = StudyManagement.get_default()
        sm.number_per_condition = 0
        sm.save()
        response = self.client.post(reverse('dining_room:create'))
        self._assertFail(response)

    def test_fail_surpass_per_condition_max_post_add(self):
        sm = StudyManagement.get_default()
        sm.max_number_of_people = 10
        sm.save()
        for _ in itertools.product(CreateUserTestCase.STUDY_CONDITIONS, CreateUserTestCase.START_CONDITIONS):
            response = self.client.post(reverse('dining_room:create'))
            self._assertSuccess(response)

        response = self.client.post(reverse('dining_room:create'))
        self._assertFail(response)

    def test_invalidate_user_based_on_timestamp(self):
        response = self.client.post(reverse('dining_room:create'))
        self._assertSuccess(response)

        user = User.objects.order_by('-date_joined')[0]
        user.last_login = timezone.now() - datetime.timedelta(minutes=47)
        user.save()
        self.assertFalse(user.invalid_data)

        response = self.client.post(reverse('dining_room:create'))
        self._assertSuccess(response)
        user.refresh_from_db()
        self.assertTrue(user.invalid_data)

    def test_expected_number_of_users(self):
        base_user_qs = User.objects.filter(Q(is_staff=False) & (Q(ignore_data_reason__isnull=True) | Q(ignore_data_reason='')))

        for study_condition in User.StudyConditions:
            self.assertEqual(0, base_user_qs.filter(study_condition=study_condition).count())
        for start_condition in User.StartConditions:
            self.assertEqual(0, base_user_qs.filter(start_condition=start_condition).count())

        # Add users and check the number
        for _ in itertools.product(CreateUserTestCase.STUDY_CONDITIONS, CreateUserTestCase.START_CONDITIONS):
            response = self.client.post(reverse('dining_room:create'))
            self._assertSuccess(response)

        response = self.client.post(reverse('dining_room:create'))
        self._assertFail(response)

        for study_condition in User.StudyConditions:
            self.assertEqual(
                0 if study_condition not in CreateUserTestCase.STUDY_CONDITIONS else 2,
                base_user_qs.filter(study_condition=study_condition).count()
            )

        for start_condition in User.StartConditions:
            self.assertEqual(
                0 if start_condition not in CreateUserTestCase.START_CONDITIONS else 2,
                base_user_qs.filter(start_condition=start_condition).count()
            )

        # Invalidate a user
        user = random.choice(base_user_qs)
        user.last_login = timezone.now() - datetime.timedelta(minutes=47)
        user.save()

        # Add another user and check the counts
        another_client = Client()
        response = another_client.post(reverse('dining_room:create'))
        self._assertSuccess(response)

        for study_condition in User.StudyConditions:
            self.assertEqual(
                0 if study_condition not in CreateUserTestCase.STUDY_CONDITIONS else 2,
                base_user_qs.filter(study_condition=study_condition).count()
            )

        for start_condition in User.StartConditions:
            self.assertEqual(
                0 if start_condition not in CreateUserTestCase.START_CONDITIONS else 2,
                base_user_qs.filter(start_condition=start_condition).count()
            )

class CSVTestCase(SimpleTestCase):
    """
    Test the CSV generation and saving
    """

    EXPECTED_CSV_HEADERS = [
        'timestamp',
        'start_state',
        'diagnoses',
        'diagnosis_certainty',
        'action',
        'next_state',
        'video_loaded_time',
        'video_stop_time',
        'dx_selected_time',
        'dx_confirmed_time',
        'ax_selected_time',
        'corrupted_dx_suggestions',
        'corrupted_ax_suggestions',
    ]

    def test_csv_headers(self):
        self.assertListEqual(CSVTestCase.EXPECTED_CSV_HEADERS, DropboxConnection.USERDATA_CSV_HEADERS)
