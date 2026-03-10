import pytest
from slippi.slippi_api import SlippiRankedAPI


@pytest.fixture
def get_class_api():
  return SlippiRankedAPI()


def test_is_valid_connect_code(get_class_api):
  api = get_class_api
  assert api.is_valid_connect_code('ABCD#1234')
  assert api.is_valid_connect_code('ABCDEFG#0')
  assert api.is_valid_connect_code('A#0')
  assert api.is_valid_connect_code('A#1234567')
  assert not api.is_valid_connect_code('ABCDEFGH#1234567')
  assert not api.is_valid_connect_code('A#12345678')
  assert not api.is_valid_connect_code('ABC123')


def test_get_player_data(get_class_api):
  api = get_class_api

  code = 'SO#0'
  results = api._get_player_data(connect_code=code)

  assert results
  assert results['data']
  assert results['data']['getUser']

  user = results['data']['getUser']
  assert user['connectCode']['code'] == 'SO#0'
  assert user['rankedNetplayProfile']
  assert user['rankedNetplayProfile']['wins']
  assert user['rankedNetplayProfile']['losses']
  assert user['rankedNetplayProfile']['characters']

  # Check for nonexistent user
  code = 'ABCDEFG#0'
  results = api._get_player_data(code)
  assert results
  assert results['data']
  assert not results['data']['getUser']


def test_get_player_ranked_data(get_class_api):
  api = get_class_api

  results = api.get_player_ranked_data('so#0')
  assert results
  results = api.get_player_ranked_data('abcde')
  assert not results


def test_does_exist(get_class_api):
  api = get_class_api

  assert api.does_exist('so#0')
  assert not api.does_exist('abcde')
