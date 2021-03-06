from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.contrib import admin, messages
from django.contrib.admin.options import IS_POPUP_VAR
from django.contrib.admin.utils import unquote
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.models import Group
from django.contrib.auth.forms import (UserChangeForm, UserCreationForm,
                                       AdminPasswordChangeForm)
from django.db import router, transaction
from django.db.models import Q
from django.http import Http404, HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.decorators import method_decorator
from django.utils.html import escape
from django.utils.translation import gettext, gettext_lazy as _
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters

from . import constants
from .models import User, StudyManagement, StudyAction


# Helper classes such as list filters, etc

class StudyProgressListFilter(admin.SimpleListFilter):
    """
    Filter by the study progress inherited property
    """
    title = _('study progress')
    parameter_name = 'study_progress'

    def lookups(self, request, model_admin):
        """Return the list of values to show"""
        return tuple([(x, x) for x in sorted(constants.STUDY_PROGRESS_STATES.keys())])

    def queryset(self, request, queryset):
        """Filter the objects"""
        if self.value() is not None:
            admissible_ids = [obj.id for obj in queryset if obj.study_progress == self.value()]
            return queryset.filter(id__in=admissible_ids)
        else:
            return queryset


class ValidDataListFilter(admin.SimpleListFilter):
    """
    Filter by an inferred boolean property in Python
    """
    title = _('valid data')
    parameter_name = 'valid_data'

    def lookups(self, request, model_admin):
        """Return the list of values to show"""
        return (('True', 'Yes'), ('False', 'No'), ('no_blacklist', 'Without Blacklist'))

    def queryset(self, request, queryset):
        """Filter the objects"""
        if self.value() is not None:
            get_valid = (self.value() == 'True')
            no_blacklist = (self.value() == 'no_blacklist')

            if no_blacklist:
                filters = ~Q(username__istartswith='blacklist')
            else:
                filters = Q(ignore_data_reason__isnull=get_valid)
                if get_valid:
                    filters = filters | Q(ignore_data_reason='')

            return queryset.filter(filters)
        return queryset


# Register your models here.


class UserInline(admin.TabularInline):
    model = User
    fields = (
        'username',
        'unique_key',
        'amt_worker_id',
        'study_condition',
        'start_condition',
        'study_progress',
        'num_incorrect',
        'valid_data',
        'num_actions',
        'date_demographics_completed',
        'date_started',
        'date_finished',
        'date_survey_completed',
    )
    readonly_fields = (
        'username',
        'unique_key',
        'amt_worker_id',
        'study_condition',
        'start_condition',
        'study_progress',
        'num_incorrect',
        'valid_data',
        'num_actions',
        'date_demographics_completed',
        'date_started',
        'date_finished',
        'date_survey_completed',
    )
    show_change_link = True
    extra = 0

    def valid_data(self, obj):
        return not obj.invalid_data
    valid_data.boolean = True

    def num_incorrect(self, obj):
        return obj.number_incorrect_knowledge_reviews
    num_incorrect.admin_order_field = 'number_incorrect_knowledge_reviews'


@admin.register(StudyManagement)
class StudyManagementAdmin(admin.ModelAdmin):
    """
    The admin class for the StudyManagement model
    """
    list_display = ('__str__', 'number_people_assigned', 'number_people_qualified', 'max_test_attempts', 'max_number_of_people', 'number_per_condition', 'enabled_study_conditions_list', 'enabled_start_conditions_list')
    save_as = True
    inlines = [ UserInline ]
    readonly_fields = ('number_people_assigned', 'number_people_qualified')

    def number_people_assigned(self, obj):
        """The number of people explicitly assigned to the SM"""
        return obj.user_set.count()

    def number_people_qualified(self, obj):
        """The number of people that satisfy the conditions; regardless of
        whether they've been assigned to the SM"""
        return User.objects.filter(
            Q(is_staff=False) &
            (Q(ignore_data_reason__isnull=True) | Q(ignore_data_reason='')) &
            Q(study_condition__in=obj.enabled_study_conditions_list) &
            Q(start_condition__in=obj.enabled_start_conditions_list)
        ).count()


@admin.register(StudyAction)
class StudyActionAdmin(admin.ModelAdmin):
    """
    The admin class for the StudyAction model
    """
    list_display = (
        '__str__',
        'start_timestamp',
        'decision_duration',
        'start_state',
        'diagnoses',
        'certainty',
        'action',
        'browser_refreshed',
        'corrupted_dx',
        'corrupted_ax',
        'chose_dx',
        'chose_ax',
        'optimal_dx',
        'optimal_ax',
    )
    list_filter = (
        'user__study_condition',
        'user__start_condition',
        'user__study_management',
    )
    readonly_fields = (
        'duration',
        'decision_duration',
        'corrupted_dx',
        'corrupted_ax',
        'chose_dx',
        'chose_ax',
        'optimal_dx',
        'optimal_ax',
    )
    ordering = ('user', 'start_timestamp')

    def certainty(self, obj):
        return obj.diagnosis_certainty
    certainty.admin_order_field = 'diagnosis_certainty'

    def corrupted_dx(self, obj):
        return obj.corrupted_dx_suggestions
    corrupted_dx.boolean = True

    def corrupted_ax(self, obj):
        return obj.corrupted_ax_suggestions
    corrupted_ax.boolean = True

    def chose_dx(self, obj):
        return obj.chose_dx_suggestion
    chose_dx.boolean = True

    def chose_ax(self, obj):
        return obj.chose_ax_suggestion
    chose_ax.boolean = True

    def optimal_dx(self, obj):
        return obj.chose_dx_optimal
    optimal_dx.boolean = True

    def optimal_ax(self, obj):
        return obj.chose_ax_optimal
    optimal_ax.boolean = True


# Special requirements for the redefined auth models

csrf_protect_m = method_decorator(csrf_protect)
sensitive_post_parameters_m = method_decorator(sensitive_post_parameters())


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """
    The admin class for the User model, without the email and name fields
    """
    add_form_template = 'admin/auth/user/add_form.html'
    change_user_password_template = None
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('unique_key', 'amt_worker_id')}),
        (_('Study Conditions'), {'fields': ('study_management', 'study_condition', 'start_condition', 'study_progress', 'scenario_completed', 'number_incorrect_knowledge_reviews', 'ignore_data_reason')}),
        (_('Important dates'), {'fields': ('last_login', 'date_modified', 'date_demographics_completed', 'date_started', 'date_finished', 'date_survey_completed')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser')#, 'groups', 'user_permissions'),
        }),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2'),
        }),
    )
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm
    list_display = (
        'username',
        'amt_worker_id',
        'unique_key',
        'study_management',
        'study_condition',
        'start_condition',
        'study_progress',
        'num_incorrect',
        'valid_data',
        'demographics_duration',
        'instructions_duration',
        'study_duration',
        'survey_duration',
    )
    list_filter = ('study_condition', 'start_condition', StudyProgressListFilter, ValidDataListFilter, 'study_management', 'is_superuser')
    list_editable = ('study_management',)
    search_fields = ('username', 'amt_worker_id', 'unique_key', 'study_condition', 'start_condition')
    ordering = ('username', 'date_joined', 'last_login')
    filter_horizontal = ('groups', 'user_permissions')
    readonly_fields = (
        'study_progress',
        'valid_data',
        'num_incorrect',
        'last_login',
        'date_modified',
        'demographics_duration',
        'instructions_duration',
        'study_duration',
        'survey_duration',
    )
    actions = ['reset_study_progress', 'reset_invalid_data']

    def valid_data(self, obj):
        return not obj.invalid_data
    valid_data.boolean = True

    def num_incorrect(self, obj):
        return obj.number_incorrect_knowledge_reviews
    num_incorrect.admin_order_field = 'number_incorrect_knowledge_reviews'

    def demographics_duration(self, obj):
        return (
            (obj.date_demographics_completed - obj.last_login)
            if obj.date_demographics_completed is not None and obj.last_login is not None
            else None
        )

    def instructions_duration(self, obj):
        return (
            (obj.date_started - obj.date_demographics_completed)
            if obj.date_started is not None and obj.date_demographics_completed is not None
            else None
        )

    def study_duration(self, obj):
        return (
            (obj.date_finished - obj.date_started)
            if obj.date_finished is not None and obj.date_started is not None
            else None
        )

    def survey_duration(self, obj):
        return (
            (obj.date_survey_completed - obj.date_finished)
            if obj.date_survey_completed is not None and obj.date_finished is not None
            else None
        )

    def reset_study_progress(self, request, queryset):
        """Reset the study progress of the selected users"""
        for obj in queryset:
            obj.reset_progress()
        self.message_user(request, f'Study progress reset for {len(queryset)} {"user" if len(queryset) == 1 else "users"}')

    def reset_invalid_data(self, request, queryset):
        """Reset the invalid data state for the user"""
        for obj in queryset:
            obj.reset_invalid_data()
        self.message_user(request, f'Data validity reset for {len(queryset)} {"user" if len(queryset) == 1 else "users"}')

    def get_fieldsets(self, request, obj=None):
        if not obj:
            return self.add_fieldsets
        return super().get_fieldsets(request, obj)

    def get_form(self, request, obj=None, **kwargs):
        """
        Use special form during user creation
        """
        defaults = {}
        if obj is None:
            defaults['form'] = self.add_form
        defaults.update(kwargs)
        return super().get_form(request, obj, **defaults)

    def get_urls(self):
        return [
            path(
                '<id>/password/',
                self.admin_site.admin_view(self.user_change_password),
                name='auth_user_password_change',
            ),
        ] + super().get_urls()

    def lookup_allowed(self, lookup, value):
        # Don't allow lookups involving passwords.
        return not lookup.startswith('password') and super().lookup_allowed(lookup, value)

    @sensitive_post_parameters_m
    @csrf_protect_m
    def add_view(self, request, form_url='', extra_context=None):
        with transaction.atomic(using=router.db_for_write(self.model)):
            return self._add_view(request, form_url, extra_context)

    def _add_view(self, request, form_url='', extra_context=None):
        # It's an error for a user to have add permission but NOT change
        # permission for users. If we allowed such users to add users, they
        # could create superusers, which would mean they would essentially have
        # the permission to change users. To avoid the problem entirely, we
        # disallow users from adding users if they don't have change
        # permission.
        if not self.has_change_permission(request):
            if self.has_add_permission(request) and settings.DEBUG:
                # Raise Http404 in debug mode so that the user gets a helpful
                # error message.
                raise Http404(
                    'Your user does not have the "Change user" permission. In '
                    'order to add users, Django requires that your user '
                    'account have both the "Add user" and "Change user" '
                    'permissions set.')
            raise PermissionDenied
        if extra_context is None:
            extra_context = {}
        username_field = self.model._meta.get_field(self.model.USERNAME_FIELD)
        defaults = {
            'auto_populated_fields': (),
            'username_help_text': username_field.help_text,
        }
        extra_context.update(defaults)
        return super().add_view(request, form_url, extra_context)

    @sensitive_post_parameters_m
    def user_change_password(self, request, id, form_url=''):
        user = self.get_object(request, unquote(id))
        if not self.has_change_permission(request, user):
            raise PermissionDenied
        if user is None:
            raise Http404(_('%(name)s object with primary key %(key)r does not exist.') % {
                'name': self.model._meta.verbose_name,
                'key': escape(id),
            })
        if request.method == 'POST':
            form = self.change_password_form(user, request.POST)
            if form.is_valid():
                form.save()
                change_message = self.construct_change_message(request, form, None)
                self.log_change(request, user, change_message)
                msg = gettext('Password changed successfully.')
                messages.success(request, msg)
                update_session_auth_hash(request, form.user)
                return HttpResponseRedirect(
                    reverse(
                        '%s:%s_%s_change' % (
                            self.admin_site.name,
                            user._meta.app_label,
                            user._meta.model_name,
                        ),
                        args=(user.pk,),
                    )
                )
        else:
            form = self.change_password_form(user)

        fieldsets = [(None, {'fields': list(form.base_fields)})]
        adminForm = admin.helpers.AdminForm(form, fieldsets, {})

        context = {
            'title': _('Change password: %s') % escape(user.get_username()),
            'adminForm': adminForm,
            'form_url': form_url,
            'form': form,
            'is_popup': (IS_POPUP_VAR in request.POST or
                         IS_POPUP_VAR in request.GET),
            'add': True,
            'change': False,
            'has_delete_permission': False,
            'has_change_permission': True,
            'has_absolute_url': False,
            'opts': self.model._meta,
            'original': user,
            'save_as': False,
            'show_save': True,
            **self.admin_site.each_context(request),
        }

        request.current_app = self.admin_site.name

        return TemplateResponse(
            request,
            self.change_user_password_template or
            'admin/auth/user/change_password.html',
            context,
        )

    def response_add(self, request, obj, post_url_continue=None):
        """
        Determine the HttpResponse for the add_view stage. It mostly defers to
        its superclass implementation but is customized because the User model
        has a slightly different workflow.
        """
        # We should allow further modification of the user just added i.e. the
        # 'Save' button should behave like the 'Save and continue editing'
        # button except in two scenarios:
        # * The user has pressed the 'Save and add another' button
        # * We are adding a user in a popup
        if '_addanother' not in request.POST and IS_POPUP_VAR not in request.POST:
            request.POST = request.POST.copy()
            request.POST['_continue'] = 1
        return super().response_add(request, obj, post_url_continue)


# Create proxy views on the model

def create_modeladmin(modeladmin, model, name=None, verbose_name_plural=None):
    """
    Create a proxy model on the fly for a given model and register that model
    with the admin site. From:
        https://stackoverflow.com/questions/2223375/multiple-modeladmins-views-for-same-model-in-django-admin
    """
    class Meta:
        proxy = True
        app_label = model._meta.app_label

    if verbose_name_plural is not None:
        Meta.verbose_name_plural = verbose_name_plural

    attrs = {'__module__': '', 'Meta': Meta}

    newmodel = type(name, (model,), attrs)
    admin.site.register(newmodel, modeladmin)
    return modeladmin


class DemographicsAdmin(admin.ModelAdmin):
    """
    The view into the demographics information on the model
    """

    fieldsets = (
        (None, {
            'fields': (('username', 'amt_worker_id', 'study_condition', 'start_condition', 'study_progress', 'valid_data'), ('date_finished', 'date_demographics_completed'))
        }),
        ('Demographics', { 'fields': ('age_group', 'gender', 'robot_experience') }),
    )
    list_display = ('username', 'amt_worker_id', 'study_condition', 'num_incorrect', 'valid_data', 'date_finished', 'age_group', 'gender', 'robot_experience')
    list_filter = ('study_condition', StudyProgressListFilter, ValidDataListFilter, 'study_management')
    ordering = ('date_finished', 'username', 'study_condition')
    search_fields = ('username', 'study_condition', 'amt_worker_id')
    readonly_fields = ('username', 'amt_worker_id', 'study_condition', 'start_condition', 'date_finished', 'date_demographics_completed', 'study_progress', 'valid_data')

    def valid_data(self, obj):
        return not obj.invalid_data
    valid_data.boolean = True

    def num_incorrect(self, obj):
        return obj.number_incorrect_knowledge_reviews
    num_incorrect.admin_order_field = 'number_incorrect_knowledge_reviews'

create_modeladmin(DemographicsAdmin, User, name='Demographics', verbose_name_plural='Demographics')


class StudyActionInline(admin.TabularInline):
    """Inline object for the study actions"""
    model = StudyAction
    fields = (
        'action_idx',
        'start_timestamp',
        'duration',
        'start_state',
        'diagnoses',
        'certainty',
        'action',
        'next_state',
        'decision_duration',
        'browser_refreshed',
        'corrupted_dx',
        'corrupted_ax',
        'chose_dx',
        'chose_ax',
    )
    readonly_fields = (
        'action_idx',
        'start_timestamp',
        'duration',
        'start_state',
        'diagnoses',
        'certainty',
        'action',
        'next_state',
        'decision_duration',
        'dx_decision_duration',
        'ax_decision_duration',
        'browser_refreshed',
        'corrupted_dx',
        'corrupted_ax',
        'chose_dx',
        'chose_ax',
    )
    ordering = ('start_timestamp',)
    show_change_link = True
    extra = 0

    def certainty(self, obj):
        return obj.diagnosis_certainty
    certainty.admin_order_field = 'diagnosis_certainty'

    def corrupted_dx(self, obj):
        return obj.corrupted_dx_suggestions
    corrupted_dx.boolean = True

    def corrupted_ax(self, obj):
        return obj.corrupted_ax_suggestions
    corrupted_ax.boolean = True

    def chose_dx(self, obj):
        return obj.chose_dx_suggestion
    chose_dx.boolean = True

    def chose_ax(self, obj):
        return obj.chose_ax_suggestion
    chose_ax.boolean = True


class ActionsAdmin(admin.ModelAdmin):
    """
    The view into the actions taken by the user
    """

    fieldsets = (
        (None, {
            'fields': (('username', 'amt_worker_id', 'study_condition', 'start_condition', 'study_progress', 'valid_data'), ('date_started', 'date_finished', 'number_state_requests'))
        }),
    )
    inlines = [ StudyActionInline ]
    list_display = (
        'username',
        'amt_worker_id',
        'study_condition',
        'start_condition',
        'num_incorrect',
        'valid_data',
        'scenario_completed',
        'date_started',
        'duration',
        'num_actions',
        'num_refreshes',
        'confidences',
    )
    list_filter = ('study_condition', 'start_condition', StudyProgressListFilter, ValidDataListFilter, 'study_management', 'scenario_completed')
    ordering = ('date_started', 'username', 'study_condition')
    search_fields = ('username', 'study_condition', 'amt_worker_id')
    readonly_fields = (
        'username',
        'amt_worker_id',
        'study_condition',
        'start_condition',
        'date_started',
        'duration',
        'study_progress',
        'valid_data',
        'scenario_completed',
        'num_actions',
        'num_refreshes',
        'confidences',
    )

    def valid_data(self, obj):
        return not obj.invalid_data
    valid_data.boolean = True

    def num_incorrect(self, obj):
        return obj.number_incorrect_knowledge_reviews
    num_incorrect.admin_order_field = 'number_incorrect_knowledge_reviews'

    def confidences(self, obj):
        return [x.diagnosis_certainty for x in obj.studyaction_set.all().order_by('start_timestamp')]

    def duration(self, obj):
        return (obj.date_finished - obj.date_started) if obj.date_finished is not None and obj.date_started is not None else None

    def num_refreshes(self, obj):
        return obj.studyaction_set.filter(browser_refreshed=True).count()

create_modeladmin(ActionsAdmin, User, name='Actions', verbose_name_plural='Actions')


class SurveysAdmin(admin.ModelAdmin):
    """
    The view into the survey information on the model
    """

    fieldsets = (
        (None, {
            'fields': (('username', 'amt_worker_id', 'valid_data'), ('study_condition', 'start_condition'))
        }),
        ('Survey', {
            'fields': (
                ('date_survey_completed',),
                tuple(User.CUSTOM_SURVEY_FIELD_NAMES + User.SUS_SURVEY_FIELD_NAMES),
                ('comments',)
            )
        }),
    )
    list_display = [
        'username',
        'amt_worker_id',
        'num_incorrect',
        'valid_data',
        'start_condition',
        'study_condition',
    ] + User.CUSTOM_SURVEY_FIELD_NAMES + User.SUS_SURVEY_FIELD_NAMES
    list_filter = ('study_condition', StudyProgressListFilter, ValidDataListFilter, 'study_management')
    ordering = ('date_survey_completed', 'username', 'study_condition')
    search_fields = ('username', 'amt_worker_id', 'study_condition')
    readonly_fields = [
        'username',
        'amt_worker_id',
        'valid_data',
    ]

    def valid_data(self, obj):
        return not obj.invalid_data
    valid_data.boolean = True

    def num_incorrect(self, obj):
        return obj.number_incorrect_knowledge_reviews
    num_incorrect.admin_order_field = 'number_incorrect_knowledge_reviews'

create_modeladmin(SurveysAdmin, User, name='Survey', verbose_name_plural='Surveys')
