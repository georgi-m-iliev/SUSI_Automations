import os
import time
import requests
import tempfile
import webbrowser
from typing import Tuple

from bs4 import BeautifulSoup

from models import ElectivesCategory


def visualize_response(response: requests.models.Response):
    """ Creates a temporary file with the response and opens it in the default browser. """
    fd, name = tempfile.mkstemp(suffix='.html')
    try:
        with os.fdopen(fd, 'wb') as file:
            # Writing the html response in the file
            file.write(response.text.encode('utf-8'))
    except Exception as e:
        print('Error! {}'.format(e))
        return

    # Should open it in the default browser
    webbrowser.open(name)
    # Giving the browser some time to open the file, then the os can dispose of the file
    time.sleep(3)
    os.unlink(name)


def extract_vstate_eventvalidation(soup: BeautifulSoup) -> Tuple[str, str]:
    vstate = soup.find('input', id='__VSTATE').get('value')
    eventvalidation = soup.find('input', id='__EVENTVALIDATION').get('value')
    return vstate, eventvalidation


def extract_electives_from_queries(electives_names_request: requests.Response) -> list:
    electives_names_soup = BeautifulSoup(electives_names_request.text, 'html.parser')

    names = list()
    electives_table = electives_names_soup.find_all('table')[11]
    if electives_table is None:
        raise Exception('Failed to extract electives table!')

    electives = electives_table.find_all('tr')[2::2]
    for row in electives:
        names.append(row.find('td', class_='messageText').find('a').text)

    return names


def extract_electives_ids(electives_request: requests.Response) -> dict:
    electives_table = BeautifulSoup(electives_request.text, 'html.parser').find('div', id='pnlPage')
    if electives_table is None:
        raise Exception('Failed to extract electives table!')

    electives_ids = {}
    electives_soup = electives_table.find_all('table')[2].find_all('tr')[2::2]
    for row in electives_soup:
        elective_name = row.find('td', class_='messageText').find('a').text
        if row.find('select') is None:
            elective_id = None
        else:
            elective_id = row.find('select')['name']
        print(f'Found {elective_name}: {elective_id}')
        electives_ids[elective_name] = elective_id

    return electives_ids


def prepare_electives_form_data(session: requests.Session, categories: ElectivesCategory, wanted_electives: list, available_electives: dict) -> dict:
    vstate_eventvalidation_request = session.get(os.getenv('ELECTIVES_URL'))
    vstate, eventvalidation = extract_vstate_eventvalidation(
        BeautifulSoup(vstate_eventvalidation_request.text, 'html.parser')
    )

    form_data = {
        '__EVENTTARGET': 'rptElectiveDisciplines$_ctl1$cboSubscriptionStatuses',
        '__EVENTVALIDATION': eventvalidation,
        '__VSTATE': vstate,
        'cboCategories': '-1',
        'disciplineType': categories.discipline_type.value,
        'includedInEducationPlan': categories.plan_type.value,
    }

    eventtarget_first_wanted_elective = True
    for elective in wanted_electives:
        if eventtarget_first_wanted_elective:
            form_data['__EVENTTARGET'] = 'rptElectiveDisciplines$_ctl{}$cboSubscriptionStatuses'.format(
                available_electives[elective].replace('rptElectiveDisciplines:_ctl', '')
                .replace(':cboSubscriptionStatuses', '')
            )
            eventtarget_first_wanted_elective = False
        form_data[available_electives[elective]] = '1'

    return form_data
