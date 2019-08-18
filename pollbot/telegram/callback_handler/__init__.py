"""Callback query handling."""
from telegram.ext import run_async
from raven import breadcrumbs

from pollbot.helper.session import hidden_session_wrapper
from pollbot.helper.enums import CallbackType, CallbackResult
from pollbot.models import Poll

from .creation import (
    toggle_anonymity,
    change_poll_type,
    show_poll_type_keyboard,
    all_options_entered,
    toggle_results_visible,
    open_creation_datepicker,
    close_creation_datepicker,
    skip_description,
    cancel_creation,
)

from .vote import (
    handle_vote,
)

from .menu import (
    go_back,
    show_deletion_confirmation,
    show_close_confirmation,
    show_settings,
    show_vote_menu,
    show_menu,
)
from .management import (
    delete_poll,
    close_poll,
    reopen_poll,
    reset_poll,
    clone_poll,
)
from .settings import (
    make_anonymous,
    show_anonymization_confirmation,
    show_styling_menu,
    expect_new_option,
    show_remove_options_menu,
    remove_option,
    toggle_allow_new_options,
    open_new_option_datepicker,
    open_due_date_datepicker,
    pick_due_date,
    open_language_picker,
    change_poll_language,
)
from .styling import (
    toggle_percentage,
    toggle_date_format,
    toggle_summerization,
    set_option_order,
    set_user_order,
)
from .datepicker import (
    set_next_month,
    set_previous_month,
    set_date,
    add_date,
)
from .external import (
    activate_notification,
    open_external_datepicker,
    open_external_menu,
    external_cancel,
)

from .user import (
    change_user_language,
)
from .misc import (
    switch_help,
    show_option_name,
)


class CallbackContext():
    """Contains all important information for handling with callbacks."""

    def __init__(self, session, bot, query, user):
        """Create a new CallbackContext from a query."""
        self.bot = bot
        self.query = query
        self.user = user
        data = self.query.data

        # Extract the callback type, task id
        data = data.split(':')
        self.callback_type = CallbackType(int(data[0]))
        self.payload = data[1]
        try:
            self.action = int(data[2])
        except:
            self.action = data[2]

        self.poll = session.query(Poll).get(self.payload)

        # Try to resolve the callback result, if possible
        self.callback_result = None
        try:
            self.callback_result = CallbackResult(self.action)
        except (ValueError, KeyError):
            pass

        if self.query.message:
            # Get chat entity and telegram chat
            self.tg_chat = self.query.message.chat

    def __repr__(self):
        """Print as string."""
        representation = f'Context: query-{self.data}, poll-({self.poll}), user-({self.user}), '
        representation += f'type-{self.callback_type}, action-{self.action}'

        return representation


@run_async
@hidden_session_wrapper()
def handle_callback_query(bot, update, session, user):
    """Handle callback queries from inline keyboards."""
    context = CallbackContext(session, bot, update.callback_query, user)

    breadcrumbs.record(
        data={
            'query': update.callback_query,
            'data': update.callback_query.data,
            'user': user,
            'callback_type': context.callback_type,
            'callback_result': context.callback_result,
            'poll': context.poll,
        },
        category='callbacks',
    )

    def ignore(session, context):
        context.query.answer("This button doesn't do anything and is just for styling.")

    callback_functions = {
        # Creation
        CallbackType.show_poll_type_keyboard: show_poll_type_keyboard,
        CallbackType.change_poll_type: change_poll_type,
        CallbackType.toggle_anonymity: toggle_anonymity,
        CallbackType.all_options_entered: all_options_entered,
        CallbackType.toggle_results_visible: toggle_results_visible,
        CallbackType.open_creation_datepicker: open_creation_datepicker,
        CallbackType.close_creation_datepicker: close_creation_datepicker,
        CallbackType.pick_date_option: add_date,
        CallbackType.skip_description: skip_description,
        CallbackType.cancel_creation: cancel_creation,

        # Voting
        CallbackType.vote: handle_vote,

        # Menu
        CallbackType.menu_back: go_back,
        CallbackType.menu_vote: show_vote_menu,
        CallbackType.menu_option: show_settings,
        CallbackType.menu_delete: show_deletion_confirmation,
        CallbackType.menu_show: show_menu,
        CallbackType.menu_close: show_close_confirmation,

        # Poll management
        CallbackType.delete: delete_poll,
        CallbackType.close: close_poll,
        CallbackType.reopen: reopen_poll,
        CallbackType.reset: reset_poll,
        CallbackType.clone: clone_poll,

        # Settings
        CallbackType.settings_anonymization_confirmation: show_anonymization_confirmation,
        CallbackType.settings_anonymization: make_anonymous,
        CallbackType.settings_show_styling: show_styling_menu,
        CallbackType.settings_new_option: expect_new_option,
        CallbackType.settings_show_remove_option_menu: show_remove_options_menu,
        CallbackType.settings_remove_option: remove_option,
        CallbackType.settings_toggle_allow_new_options: toggle_allow_new_options,
        CallbackType.settings_open_add_option_datepicker: open_new_option_datepicker,
        CallbackType.settings_open_due_date_datepicker: open_due_date_datepicker,
        CallbackType.settings_pick_due_date: pick_due_date,
        CallbackType.settings_open_language_picker: open_language_picker,
        CallbackType.settings_change_poll_language: change_poll_language,

        # Styling
        CallbackType.settings_toggle_percentage: toggle_percentage,
        CallbackType.settings_toggle_date_format: toggle_date_format,
        CallbackType.settings_toggle_summarization: toggle_summerization,
        CallbackType.settings_user_sorting: set_user_order,
        CallbackType.settings_option_sorting: set_option_order,

        # User
        CallbackType.user_change_language: change_user_language,

        # Datepicker
        CallbackType.set_date: set_date,
        CallbackType.next_month: set_next_month,
        CallbackType.previous_month: set_previous_month,

        # External
        CallbackType.activate_notification: activate_notification,
        CallbackType.external_open_datepicker: open_external_datepicker,
        CallbackType.external_open_menu: open_external_menu,
        CallbackType.external_cancel: external_cancel,

        # Misc
        CallbackType.switch_help: switch_help,
        CallbackType.show_option_name: show_option_name,

        # Ignore
        CallbackType.ignore: ignore,
    }

    callback_functions[context.callback_type](session, context)

    return
