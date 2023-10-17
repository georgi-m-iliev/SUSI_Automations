import os
import time
import json
import http.client
import requests
import datetime
import winsound
import tempfile
import webbrowser
from typing import Tuple

from dotenv import load_dotenv
from bs4 import BeautifulSoup


def siren(duration, frequency=1000, delta=50):
    # Calculate the number of cycles for the given duration
    num_cycles = int(duration * 1000)  # winsound expects milliseconds

    # Play the siren sound by altering the frequency over time
    for _ in range(num_cycles):
        winsound.Beep(frequency, 100)
        frequency += delta


def extract_vstate_eventvalidation(soup: BeautifulSoup) -> Tuple[str, str]:
    __vstate = soup.find('input', id='__VSTATE').get('value')
    __eventvalidation = soup.find('input', id='__EVENTVALIDATION').get('value')
    return __vstate, __eventvalidation


def visualize_response(response: requests.models.Response):
    print('\n# # # Stage 5 - Visualize response # # #\n\n')
    print('Creating respose file and opening it... ', end='')
    fd, name = tempfile.mkstemp(suffix='.html')
    try:
        with os.fdopen(fd, 'wb') as file:
            file.write(response.text.encode('utf-8'))
    except Exception as e:
        print('Error! {}'.format(e))
        return

    # print(name)
    webbrowser.open(name)
    print('Done!')
    siren(5)
    time.sleep(10)
    os.unlink(name)


def login_and_get_cookies():
    print('# # # Stage 1 - Login # # #')
    print('Logging in... ', end='')

    login_page_soup = BeautifulSoup(requests.get(os.getenv('LOGIN_URL')).text, 'html.parser')
    __vstate, __eventvalidation = extract_vstate_eventvalidation(login_page_soup)

    session = requests.Session()
    login_response = session.post(
        url=os.getenv('LOGIN_URL'),
        data={
            '__EVENTARGUMENT': '',
            '__EVENTTARGET': '',
            '__EVENTVALIDATION': __eventvalidation,
            '__VIEWSTATE': '',
            '__VSTATE': __vstate,
            'btnSubmit': 'Влез',
            'txtUserName': os.getenv('USER'),
            'txtPassword': os.getenv('PASSWORD')
        },
        headers=json.loads(os.getenv('HEADERS')),
    )

    if login_response.status_code == 200:
        print('Success!')
    else:
        print('Failed!')
        exit(1)

    return {
        'ASP.NET_SessionId': session.cookies.get('ASP.NET_SessionId'),
        'FORMSAUTHCOOKIESU8': session.cookies.get('FORMSAUTHCOOKIESU8')
    }


def wait_campaign_start(wanted_date: str):
    print('\n# # # Stage 1.5 - Wait campaign start # # #')
    print('Waiting for campaign start... ')
    current_time = datetime.datetime.now()
    time_difference = (datetime.datetime.strptime(wanted_date, '%Y-%m-%d %H:%M:%S') - current_time).total_seconds()
    if time_difference > 0:
        print('Will be sleeping for {} seconds'.format(time_difference))
        time.sleep(time_difference)
        print('Campaign started! It is {}'.format(datetime.datetime.now()))


def get_electives_page(cookies) -> BeautifulSoup:
    print('\n# # # Stage 2 - Get electives # # #')
    print('Getting electives page... ', end='')
    electives_request = requests.get(os.getenv('ELECTIVES_URL'), cookies=cookies)
    if electives_request.status_code == 200:
        print('Success!')
    else:
        print('Failed!')
        exit(1)
    soup = BeautifulSoup(electives_request.text, 'html.parser')
    return soup


def get_electives(soup: BeautifulSoup) -> dict:
    print('\n# # # Stage 3 - Extract electives # # #')
    print('Extracting electives... ', end='')
    result = dict()
    electives_table = soup.find('div', id='pnlPage')
    if electives_table is None:
        print('Failed!')
        exit(1)
    electives = electives_table.find_all('table')[2].find_all('tr')[2::2]
    for row in electives:
        elective_name = row.find('td', class_='messageText').find('a').text
        elective_id = row.find('select')['name']
        # print('{}: {}'.format(elective_name, elective_id))
        result[elective_name] = elective_id
    print('Success!')
    return result


def post_selected_electives(
        wanted_electives: list, available_electives: dict, cookies, __vstate, __eventvalidation
) -> requests.models.Response:
    print('\n# # # Stage 4 - Enrollment for electives # # #')
    print("Prepairing form data... ", end='')
    form_data = {
        '__EVENTTARGET': 'rptElectiveDisciplines$_ctl1$cboSubscriptionStatuses',
        '__EVENTVALIDATION': __eventvalidation,
        '__VSTATE': __vstate,
        'cboCategories': '-1',
        'includedInEducationPlan': 'radioIncludedInEducationPlan',
    }

    find_target = True
    for elective in wanted_electives:
        if find_target:
            form_data['__EVENTTARGET'] = 'rptElectiveDisciplines$_ctl{}$cboSubscriptionStatuses'.format(
                available_electives[elective].replace('rptElectiveDisciplines:_ctl', '')
                .replace(':cboSubscriptionStatuses', '')
            )
            find_target = False
        form_data[available_electives[elective]] = '1'
    print('Done!')

    print('Sending request... ', end='')
    # print(json.dumps(form_data, indent=1))
    post_request = requests.post(
        os.getenv('ELECTIVES_URL'),
        cookies=cookies,
        data=form_data,
        headers=json.loads(os.getenv('HEADERS')),
    )

    if post_request.status_code == 200:
        print('Success!')
    else:
        print('Failed!')
    return post_request


def execute_sequence():
    if os.getenv('DEBUG', False):
        print("#-#-#- DEBUG MODE! -#-#-#")
        cookies = {
            'ASP.NET_SessionId': os.getenv('ASP_NET_SESSION_ID'),
            'FORMSAUTHCOOKIESU8': os.getenv('FORMSAUTHCOOKIESU8')
        }
    else:
        cookies = login_and_get_cookies()

    wait_campaign_start(os.getenv('CAMPAIGN_START_DATE'))

    electives_soup = get_electives_page(cookies)
    __vstate, __eventvalidation = extract_vstate_eventvalidation(electives_soup)
    electives = get_electives(electives_soup)

    wanted_electives = ['Алгебра 2', 'Теория на игрите']
    response = post_selected_electives(wanted_electives, electives, cookies, __vstate, __eventvalidation)
    visualize_response(response)


if __name__ == '__main__':
    load_dotenv()
    execute_sequence()
