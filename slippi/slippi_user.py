from dataclasses import dataclass, field
from .custom_logging import CustomFormatter

from .slippi_ranks import get_rank
from .slippi_characters import get_character_id, get_character_url

logger = CustomFormatter().get_logger()


def _parse_id(raw_id: str | int | None) -> int | None:
  """Convert a hex string ID (e.g. '0x22d4a6') or int to int."""
  if raw_id is None:
    return None
  if isinstance(raw_id, str) and raw_id.startswith('0x'):
    return int(raw_id, 16)
  return int(raw_id)


@dataclass
class Characters:
  """Represents a character with its ID, name, and game count."""
  character: str = ''
  game_count: int = 0
  id: str | None = None

  def get_character_icon_url(self) -> str:
    """Get the URL of the character's icon."""
    return get_character_url(self.character)

  def get_true_character_id(self) -> int | None:
    """Get the true character ID, accounting for special cases."""
    return get_character_id(self.character)

  def __eq__(self, other: object) -> bool:
    """Check if two Characters instances are equal."""
    if not isinstance(other, Characters):
      return NotImplemented
    return self.character == other.character and self.game_count == other.game_count


@dataclass
class RankedNetplayProfile:
  """Represents a ranked netplay profile."""
  id: int | None = None
  rating_ordinal: float = 1100
  rating_update_count: int | None = None
  wins: int = 0
  losses: int = 0
  daily_global_placement: int | None = None
  daily_regional_placement: int | None = None
  continent: str | None = None
  characters: list[Characters] = field(default_factory=list)


@dataclass
class SubscriptionStatus:
  """Represents the subscription status."""
  active: bool = False
  level: str = 'NONE'
  gift: bool = False


@dataclass
class SlippiUser:
  """Represents a Slippi user with their display name, connect code, subscription status, and ranked netplay profile."""
  display_name: str = ''
  connect_code: str = ''
  sub_status: SubscriptionStatus = field(default_factory=SubscriptionStatus)
  ranked_profile: RankedNetplayProfile = field(default_factory=RankedNetplayProfile)

  def __init__(self, slippi_data: dict):
    """Initialize the SlippiUser object based on the provided Slippi data."""
    logger.info('SlippiUser created')

    # Set defaults
    self.display_name = ''
    self.connect_code = ''
    self.sub_status = SubscriptionStatus()
    self.ranked_profile = RankedNetplayProfile()

    if not slippi_data['data']['getUser']:
      return

    user_data = slippi_data['data']['getUser']
    ranked_data = user_data['rankedNetplayProfile']

    self.display_name = user_data['displayName']
    self.connect_code = user_data['connectCode']['code']

    if 'activeSubscription' in user_data and user_data['activeSubscription']:
      sub_data = user_data['activeSubscription']
      self.sub_status = SubscriptionStatus(
        level=sub_data['level'],
        gift=bool(sub_data['hasGiftSub']),
        active=sub_data['level'] != 'NONE',
      )

    characters_list = [
      Characters(
        character=c['character'],
        game_count=c['gameCount'],
        id=c.get('id'),
      )
      for c in ranked_data['characters']
      if c
    ]

    self.ranked_profile = RankedNetplayProfile(
      id=_parse_id(ranked_data['id']),
      rating_ordinal=ranked_data['ratingOrdinal'],
      rating_update_count=ranked_data['ratingUpdateCount'],
      wins=ranked_data['wins'] or 0,
      losses=ranked_data['losses'] or 0,
      continent=ranked_data['continent'] or 'NONE',
      daily_global_placement=ranked_data['dailyGlobalPlacement'] or 0,
      daily_regional_placement=ranked_data['dailyRegionalPlacement'] or 0,
      characters=characters_list,
    )

    self.slippi_data = slippi_data

  def get_rank(self) -> str:
    """Get the rank of the Slippi user based on their ranked profile."""
    if (self.ranked_profile.wins + self.ranked_profile.losses) < 5:
      return 'None' if not self.ranked_profile.wins and self.ranked_profile.losses else 'Pending'
    return get_rank(self.ranked_profile.rating_ordinal,
                    self.ranked_profile.daily_global_placement)

  def get_user_profile_page(self) -> str:
    """Get the URL of the user's profile page."""
    return f'https://slippi.gg/user/{self.connect_code.replace("#", "-")}'

  def get_main_character(self) -> Characters | None:
    """Get the main character of the Slippi user based on game count."""
    if not self.ranked_profile.characters:
      return None
    return max(self.ranked_profile.characters, key=lambda c: c.game_count)
