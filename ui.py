import os
import time

from prettytable import PrettyTable
from prompt_toolkit import PromptSession, prompt
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.shortcuts import message_dialog, input_dialog, checkboxlist_dialog, ProgressBar, yes_no_dialog


def disclaimer():
    message_dialog(
        title='Внимание!',
        text='Това приложение е предоставено без никаква гаранция!\n'
             'Ако нещо се обърка жестоко и се прецаката, това не е мой проблем.\n'
             'Предупредени сте! Продължавате поемайки отговорността.\n'
              'Ако продължиш, значи си съгласен...',
        ok_text='Давай!'
    ).run()


def get_credentials():
    username = None
    password = None

    while username is None or password is None:
        username = input_dialog(
            title='Какво е потребителското ти име в СУСИ?',
            text='СУСИ потребител:',
            default=os.getenv('USER', ''),
            ok_text='Готово',
            cancel_text='Изход'
        ).run()

        if username is None:
            exit(0)

        password = input_dialog(
            title='Каква е паролата ти?',
            text='СУСИ парола:',
            password=True,
            default=os.getenv('PASSWORD', ''),
            ok_text='Готово',
            cancel_text='Назад'
        ).run()

    os.environ["USERNAME"] = username
    os.environ["PASSWORD"] = password


def print_available_electives(electives: list):
    table = PrettyTable()
    table.title = 'Налични избираеми предмети'
    table.add_column("", electives)
    print(table)
    print('\n')


def select_electives(prompt_session: PromptSession, available_electives: list):
    selected_electives = []
    electives_completer = WordCompleter(available_electives, ignore_case=True)

    while True:
        try:
            elective = prompt_session.prompt(
                message='> ',
                bottom_toolbar=HTML(
                    f'Брой въведени избираеми: <b><style bg="ansired">{len(selected_electives)}</style></b>'
                ),
                completer=electives_completer
            )
            if elective not in available_electives:
                print('Тази избираема не е налична или вече е избрана, опитай пак!')
                continue
            selected_electives.append(elective)
            available_electives.remove(elective)
        except EOFError:
            if not selected_electives:
                print('Не си избрал нито една избираема, опитай пак! Ако искаш да излезеш натисни Ctrl+C')
                continue
            break
        except KeyboardInterrupt:
            print('Чао!')
            exit(0)

    return selected_electives


def verify_selected_electives(selected_electives: list):
    results_array = checkboxlist_dialog(
        title="Избрани избираеми дисциплини",
        text="Провери дали всички желани избираеми са тук, ако искаш да премахнеш някоя използвай тикчето ?",
        values=selected_electives,
        ok_text='Всичко е 6',
        cancel_text='Назад',
        default_values=[i for i in range(len(selected_electives))]
    ).run()

    return results_array


def last_confirmation_before_post(selected_electives: list):
    return yes_no_dialog(
        title='Потвърди избора си',
        text='Ще бъдете записани за следните избираеми:\n' + '\n * ' + '\n * '.join(selected_electives),
        yes_text='Да',
        no_text='Не'
    ).run()


def success_message(selected_electives: list):
    message_dialog(
        title='Успех!',
        text='Успешно записах следните избираеми:\n' + '\n * ' + '\n * '.join(selected_electives),
        ok_text='Давай!'
    ).run()
