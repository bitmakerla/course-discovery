from datetime import datetime, timedelta
from django.core.exceptions import ValidationError
from django.test import TestCase
from pytz import timezone

from course_discovery.apps.core.models import User
from course_discovery.apps.core.tests.factories import UserFactory
from course_discovery.apps.course_metadata.models import Person
from course_discovery.apps.course_metadata.tests.factories import PersonFactory
from course_discovery.apps.publisher.forms import CustomCourseForm, CustomCourseRunForm, PublisherUserCreationForm


class UserModelChoiceFieldTests(TestCase):
    """
    Tests for the publisher model "UserModelChoiceField".
    """

    def setUp(self):
        super(UserModelChoiceFieldTests, self).setUp()
        self.course_form = CustomCourseForm()

    def test_course_form(self):
        """
        Verify that UserModelChoiceField returns `full_name` as choice label.
        """
        user = UserFactory(username='test_user', full_name='Test Full Name')
        self._assert_choice_label(user.full_name)

    def test_team_admin_without_full_name(self):
        """
        Verify that UserModelChoiceField returns `username` if `full_name` is empty.
        """
        user = UserFactory(username='test_user', full_name='', first_name='', last_name='')
        self._assert_choice_label(user.username)

    def _assert_choice_label(self, expected_name):
        self.course_form.fields['team_admin'].queryset = User.objects.all()
        self.course_form.fields['team_admin'].empty_label = None

        # we need to loop through choices because it is a ModelChoiceIterator
        for __, choice_label in self.course_form.fields['team_admin'].choices:
            self.assertEqual(choice_label, expected_name)


class PersonModelMultipleChoiceTests(TestCase):

    def test_person_multiple_choice(self):
        """
        Verify that PersonModelMultipleChoice returns `full_name` and `profile_image_url` as choice label.
        """
        course_form = CustomCourseRunForm()
        course_form.fields['staff'].empty_label = None

        person = PersonFactory()
        course_form.fields['staff'].queryset = Person.objects.all()

        # we need to loop through choices because it is a ModelChoiceIterator
        for __, choice_label in course_form.fields['staff'].choices:
            expected = '<img src="{url}"/><span>{full_name}</span>'.format(
                full_name=person.full_name,
                url=person.get_profile_image_url
            )
            self.assertEqual(choice_label.strip(), expected)


class PublisherUserCreationFormTests(TestCase):
    """
    Tests for the publisher `PublisherUserCreationForm`.
    """

    def test_clean_groups(self):
        """
        Verify that `clean` raises `ValidationError` error if no group is selected.
        """
        user_form = PublisherUserCreationForm()
        user_form.cleaned_data = {'username': 'test_user', 'groups': []}
        with self.assertRaises(ValidationError):
            user_form.clean()

        user_form.cleaned_data['groups'] = ['test_group']
        self.assertEqual(user_form.clean(), user_form.cleaned_data)


class PublisherCourseRunEditFormTests(TestCase):
    """
    Tests for the publisher 'CustomCourseRunForm'.
    """

    def test_minimum_effort(self):
        """
        Verify that 'clean' raises 'ValidationError' error if Minimum effort is greater
        than Maximum effort.
        """
        run_form = CustomCourseRunForm()
        run_form.cleaned_data = {'min_effort': 4, 'max_effort': 2}
        with self.assertRaises(ValidationError):
            run_form.clean()

        run_form.cleaned_data['min_effort'] = 1
        self.assertEqual(run_form.clean(), run_form.cleaned_data)

    def test_course_run_dates(self):
        """
        Verify that 'clean' raises 'ValidationError' if the Start date is in the past
        Or if the Start date is after the End date
        """
        run_form = CustomCourseRunForm()
        current_datetime = datetime.now(timezone('US/Central'))
        run_form.cleaned_data = {'start': current_datetime + timedelta(days=3),
                                 'end': current_datetime + timedelta(days=1)}
        with self.assertRaises(ValidationError):
            run_form.clean()

        run_form.cleaned_data = {'start': current_datetime - timedelta(days=3),
                                 'end': current_datetime + timedelta(days=3)}
        with self.assertRaises(ValidationError):
            run_form.clean()

        run_form.cleaned_data['start'] = current_datetime + timedelta(days=1)
        run_form.cleaned_data['end'] = current_datetime + timedelta(days=3)
        self.assertEqual(run_form.clean(), run_form.cleaned_data)
