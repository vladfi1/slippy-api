import time
import threading
import requests
from re import match

import logging

from .custom_logging import CustomFormatter
from .slippi_user import SlippiUser

# Get the logger instance from custom formatter
logger = CustomFormatter().get_logger()

# GraphQL query for player data
query = """
query UserProfilePageQuery($cc: String, $uid: String) {
  getUser(connectCode: $cc, fbUid: $uid) {
    ...userProfilePage
    __typename
  }
}

fragment userProfilePage on User {
  fbUid
  displayName
  connectCode {
    code
    __typename
  }
  status
  activeSubscription {
    level
    hasGiftSub
    __typename
  }
  rankedNetplayProfile {
    ...profileFields
    __typename
  }
  rankedNetplayProfileHistory {
    ...profileFields
    season {
      id
      startedAt
      endedAt
      name
      status
      __typename
    }
    __typename
  }
  __typename
}

fragment profileFields on NetplayProfile {
  id
  ratingOrdinal
  ratingUpdateCount
  wins
  losses
  dailyGlobalPlacement
  dailyRegionalPlacement
  continent
  characters {
    character
    gameCount
    __typename
  }
  __typename
}
"""


class _RateLimiter:
  """Simple rate limiter allowing max_calls per period seconds."""

  def __init__(self, max_calls: int, period: float):
    self._min_interval = period / max_calls
    self._lock = threading.Lock()
    self._last_call = 0.0

  def __enter__(self):
    with self._lock:
      now = time.monotonic()
      wait = self._min_interval - (now - self._last_call)
      if wait > 0:
        time.sleep(wait)
      self._last_call = time.monotonic()
    return self

  def __exit__(self, *args):
    pass


class SlippiRankedAPI:
  def __init__(self, max_calls: int = 1, period: float = 1.0):
    """Initialize the API with a rate limit of max_calls per period seconds."""
    self._limiter = _RateLimiter(max_calls=max_calls, period=period)

  @staticmethod
  def is_valid_connect_code(connect_code: str) -> bool:
    """Check if the given connect code is valid."""
    logger.info(f'is_valid_connect_code: {connect_code}')
    return bool(match(r"^(?=.{3,9}$)[a-zA-Z]{1,7}#[0-9]{1,7}$", connect_code))

  def _get_player_data(self, connect_code: str, is_max: bool = False) -> dict | None:
    """Get player data from the Slippi API."""
    variables = {
      "cc": connect_code.upper(),
      "uid": connect_code.upper()
    }
    payload = {
      "operationName": "UserProfilePageQuery",
      "query": query,
      "variables": variables
    }
    headers = {"content-type": "application/json"}
    response = requests.post('https://internal.slippi.gg', json=payload, headers=headers)
    return response.json()

  def get_player_data_throttled(self, connect_code: str, is_max: bool = False) -> dict | None:
    """Get player data with rate limiting."""
    with self._limiter:
      return self._get_player_data(connect_code, is_max)

  def get_player_ranked_data(self, connect_code: str, is_max: bool = False) -> SlippiUser | None:
    """Get ranked player data, returning None if the player does not exist."""
    player_data = self.get_player_data_throttled(connect_code, is_max)
    if not player_data or not player_data['data']['getUser']:
      return None
    return SlippiUser(player_data)

  def does_exist(self, connect_code: str) -> bool:
    """Return True if a player with the given connect code exists."""
    results = self.get_player_data_throttled(connect_code)
    if not results or not results['data']['getUser']:
      return False
    return True
