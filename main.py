import requests, pickle
from requests.adapters import HTTPAdapter, Retry
from dotenv import load_dotenv
from prompt_toolkit import PromptSession
from prompt_toolkit.shortcuts import ProgressBar

from ui import *
from models import ElectivesCategory
from actions import authenticate, fetch_available_electives, fetch_electives_ids, enroll_selected_electives
from functions import visualize_response


def setup():
    disclaimer()

    if not os.getenv('USERNAME') or not os.getenv('PASSWORD'):
        get_credentials()


def run():
    session = requests.Session()
    retries = Retry(total=100,
                    backoff_factor=0.1,
                    status_forcelist=[500, 502, 503, 504])
    session.mount('https://', HTTPAdapter(max_retries=retries))

    with ProgressBar() as pb:
        progress_iter = pb(range(3), label='Вписване...')
        authenticate(session, progress_iter)
        print('Успешно вписан!\n')

    if not os.getenv('CAMPAIGN_START_DATE'):
        campaign_start = get_campaign_start_date()
    else:
        campaign_start = datetime.datetime.strptime(os.getenv('CAMPAIGN_START_DATE'), '%Y-%m-%d')
    electives_categories = select_electives_categories()

    with ProgressBar() as pb:
        progress_iter = pb(range(1), label='Извличане на избираеми...')

        available_electives = fetch_available_electives(session, electives_categories, progress_iter)
        # print('\nИзбираемите са извлечени успешно!')
        time.sleep(2)

    # sort electives by length
    available_electives.sort(key=len)
    print(available_electives)

    verified_selection = []
    selected_electives = []
    last_confirmation_before_post_result = False
    prompt_session = PromptSession()

    while not verified_selection or last_confirmation_before_post_result is False:
        # clear console
        print("\033[H\033[J")
        temp_electives = available_electives.copy()

        print_available_electives(temp_electives)
        print('Сега трябва да избереш желаните избираеми, въвеждай ги по един на ред, след което натисни Ctrl+D')

        selected_electives = select_electives(prompt_session, temp_electives)
        verified_selection = verify_selected_electives([(i, name) for i, name in enumerate(selected_electives)])
        if not verified_selection:
            continue
        selected_electives = [selected_electives[i] for i in verified_selection]

        last_confirmation_before_post_result = last_confirmation_before_post(selected_electives)
        if not last_confirmation_before_post_result:
            continue

    countdown_to_campaign(campaign_start)
    # wait 5 secs before posting
    time.sleep(5)

    # clear console
    print("\033[H\033[J")
    if last_confirmation_before_post_result:
        with ProgressBar() as pb:
            progress_iter = iter(pb(range(2), label='Извличане на id на избираеми за form-data...'))
            next(progress_iter)
            electives_ids = fetch_electives_ids(session, electives_categories)
            try:
                next(progress_iter)
            except StopIteration:
                pass
            progress_iter = iter(pb(range(2), label='Записване за избираеми...'))
            next(progress_iter)
            result = enroll_selected_electives(session, electives_categories, selected_electives, electives_ids)
            try:
                next(progress_iter)
            except StopIteration:
                pass
            if success_message(selected_electives):
                visualize_response(result)

    else:
        print('Чао!')


def main():
    setup()
    run()


if __name__ == '__main__':
    load_dotenv()
    main()
