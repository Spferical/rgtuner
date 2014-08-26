import rg

# globals for fine-tuning
SPAWN_WEIGHT = 1.0
CANT_EASILY_LEAVE_SPAWN_WEIGHT = 0.5
FIGHTING_FRIENDLY_WEIGHT = 3.75
TO_FIGHT_FRIENDLY_WEIGHT = 1.0
ADJACENT_ENEMIES_WEIGHT = 1.0
ADJACENT_ENEMIES_EXPONENT = 1.0
FRIENDLY_IN_LOC_WEIGHT = 4.0
FRIENDLIES_IN_TROUBLE_WEIGHT = 9.0
REMAIN_BIAS = 0.25
COULD_DIE_WEIGHT = 20.0
CHARGE_WEIGHT = 2.0
ESCAPE_WEIGHT = 1.75
GROUP_WEIGHT = -0.875
ENEMY_IN_LOC_WEIGHT = 34.25
ENEMY_IN_TROUBLE_WEIGHT = 28.75
ENEMY_SUPER_WEAK_WEIGHT = 3.0
NEARBY_FRIENDLIES_IN_SPAWN_WEIGHT = 2.75
NEARBY_FRIENDLIES_IN_DEEP_SPAWN_WEIGHT = 2.75
POSSIBLE_SUICIDERS_WEIGHT = 2.0
SURROUND_WEIGHT = 0.5
MOVE_INTO_ATTACK_WEIGHT = 9.125

#attack weights
FRIENDLY_LOC_ATTACK_WEIGHT = 6.125
ENEMY_ATTACK_HP_WEIGHT = 2.9
ADJACENT_ENEMY_ATTACK_WEIGHT = 5.0
ADJACENT_FRIENDLY_ATTACK_WEIGHT = 1.75
NEARBY_TROUBLED_ENEMY_ATTACK_WEIGHT = 5.375
NEARBY_TROUBLED_FRIENDLY_ATTACK_WEIGHT = 1.25
ATTACK_IN_FUTURE_MOVES_WEIGHT = 20.25
MULTIPLE_ATTACK_WEIGHT = 2.875

# global variable to store the future moves of each ally robot
# we can use this to avoid friendly collisions
future_moves = []
future_attacks = []
# this is used to store the current turn considered by the future_moves array
future_moves_turn = 0


def cant_easily_leave_spawn(loc, game):
    """Returns whether a bot would need 2+ moves to exit the spawn area.
    (i.e. the bot is in spawn and all of the locations around it are occupied/
    obstacle/invalid)"""

    if 'spawn' in rg.loc_types(loc):
        adjacent_locs = rg.locs_around(loc,
                filter_out=['spawn', 'obstacle', 'invalid'])

        all_bots = game.get('robots')

        for loc in adjacent_locs:
            if loc in all_bots:
                adjacent_locs.remove(loc)
        return (len(adjacent_locs) == 0)

    # if the bot is not in spawn, then it can easily leave it
    # by standing still, hehe.
    return False


def bot_is_in_trouble(bot, game):
    """Returns whether a bot is in trouble.
    If a bot could die in the next turn, it is in trouble."""
    return could_die_in_loc(bot.hp, bot.location, bot.player_id, game)


def could_die_in_loc(hp, loc, player_id, game):
    """Returns whether or not a bot could die in a given location,
    based on its hp and player_id.
    Considers the number of enemy bots nearby and whether or not
    the robot is standing on a spawn tile just before more will spawn."""

    adjacent_bots = get_bots_next_to(loc, game)
    adjacent_enemies = [b for b in adjacent_bots if b.player_id != player_id]

    # each adjacent enemy can deal up to 10 damage in a turn
    possible_hp_loss = len(adjacent_enemies) * 10
    if possible_hp_loss >= hp:
        # could die if all of the adjacent_enemies attack
        return True

    if 'spawn' in rg.loc_types(loc):
        if game['turn'] % 10 == 0:
            # next turn, if we remain on the spawn square, it could die
            return True

    return False


def get_weakest_bot(bots):
    """Returns the weakest bot out of a list of bots.
    If no bots exist, returns None"""
    assert len(bots) != 0

    # bots have 50 hp max
    least_hp = 51
    weakest_bot = None

    for bot in bots:
        if bot.hp < least_hp:
            weakest_bot = bot
            least_hp = bot.hp

    return weakest_bot


def get_bots_next_to(location, game):
    """Returns all bots next to a location."""

    all_bots = game.get('robots')
    bots = []
    for loc in all_bots.keys():
        if loc in rg.locs_around(location):
            bots.append(all_bots[loc])
    return bots


def get_bot_in_location(location, game):
    """Returns the bot in the given location."""
    bots = game.get('robots')
    if location in bots.keys():
        return bots[location]
    else:
        return None


def is_possible_suicider(bot, game):
    """Returns whether a bot is a possible suicider based on a kinda
    restrictive algorithm.

    Returns true if the sum of the hp of all enemy bots is greater than
    the bot's hp and there are more than 1 adjacent enemy bots and
    there is at least one adjacent bot that would die."""

    # get all adjacent enemies of suicider
    adjacent_bots = get_bots_next_to(bot.location, game)
    for bot2 in adjacent_bots:
        if bot2.player_id == bot.player_id:
            adjacent_bots.remove(bot2)

    # whether the total possible hp hit would outweigh the
    # hp lost
    if (sum([min(bot2.hp, 15) for bot2 in adjacent_bots]) > bot.hp):
        if len(adjacent_bots) > 1:
            for bot2 in adjacent_bots:
                if bot2.hp <= 15:
                    return True
    return False


class Robot:

    def sort_bots_closest_first(self, bots):
        """Sorts a list of bots sorted closest to farthest away."""
        return sorted(bots, key=lambda b: rg.wdist(self.location, b.location))

    def get_enemy_bots_next_to(self, location, game):
        """Returns the enemy bots next to a location."""
        enemies = []

        for loc in rg.locs_around(location):
            bot = get_bot_in_location(loc, game)
            if (bot) and (bot.player_id != self.player_id):
                enemies.append(bot)

        return enemies

    def get_friendlies_next_to(self, location, game):
        """Returns the friendly bots next to a location.
        Note: does not return /this/ robot.(filters out any robot whose
        location is equal to this robot's location)"""
        friendlies = []

        for loc in rg.locs_around(location):
            bot = get_bot_in_location(loc, game)
            if (bot) and (bot.player_id == self.player_id):
                if bot.location != self.location:
                    friendlies.append(bot)

        return friendlies

    def get_adjacent_enemy_bots(self, game):
        """Returns a list of the adjacent enemy bots."""
        return self.get_enemy_bots_next_to(self.location, game)

    def is_suiciding_beneficial(self, game):
        """Returns whether or not the bot should suicide on this turn."""
        # get the adjacent bots
        adjacent_bots = self.get_adjacent_enemy_bots(game)

        if (sum([min(bot.hp, 15) for bot in adjacent_bots]) > self.hp):

            # see if the bot can escape to any adjacent location
            for loc in rg.locs_around(self.location,
                    filter_out=['invalid', 'obstacle']):
                # the bot can't escape to the location if there's an enemy in it
                if not could_die_in_loc(self.hp, loc, self.player_id, game):
                    bot_in_loc = get_bot_in_location(loc, game)
                    if bot_in_loc and bot_in_loc.player_id != self.player_id:
                        continue
                    else:
                        return False
            return True

    def get_distance_to_closest_bot(self, game, loc=None,
            friendly=False, enemy=False):
        """Returns the distance from the given location (or, by default,
        this robot's location) to the nearest enemy."""
        if not loc:
            loc = self.location
        bots = game.get('robots')
        shortest_distance = 99999

        for bot in bots.values():
            if bot.location != loc and bot.location != self.location:
                if ((friendly is False) and (enemy is False)) or \
                        (enemy and (bot.player_id != self.player_id)) or \
                        (friendly and (bot.player_id == self.player_id)):
                    dist = rg.wdist(loc, bot.location)
                    shortest_distance = min(dist, shortest_distance)
        return shortest_distance

    def act(self, game):
        """The function called by game.py itself: returns the action the robot
        should take this turn."""

        action = []

        # update the future_moves array if necessary
        # only the first robot will do this
        global future_moves_turn, future_moves, future_attacks
        if future_moves_turn != game['turn']:
            future_moves = []
            future_attacks = []
            future_moves_turn = game['turn']

        #adjacent_bots = self.get_adjacent_enemy_bots(game)
        if self.is_suiciding_beneficial(game):
            action = ['suicide']
        else:
            locs = [self.location] + rg.locs_around(self.location,
                    filter_out=['invalid', 'obstacle'])
            target_loc = self.get_best_loc(locs, game)
            if target_loc != self.location:
                action = ['move', target_loc]
            else:
                attack_locs = rg.locs_around(self.location,
                        filter_out=['invalid', 'obstacle'])
                action = ['attack', self.get_best_attack_loc(attack_locs, game)]

        if action[0] == 'move':
            assert not action[1] in future_moves
            future_moves.append(action[1])
            if action[1] == self.location:
                action = ['guard']
        if action[0] == 'attack':
            future_attacks.append(action[1])

        return action

    def get_best_loc(self, locs, game):
        """Returns the best location out of a list.
        The 'goodness' of a tile is determined by get_tile_goodness()."""
        best_loc_weight = -9999
        best_loc = None
        for loc in locs:
            loc_weight = self.get_tile_goodness(loc, game)
            if loc_weight > best_loc_weight:
                best_loc = loc
                best_loc_weight = loc_weight
        assert best_loc
        return best_loc
    
    def get_enemies_fighting_friendlies(self, enemies, game):
        enemies_fighting_friendlies = []
        for enemy in enemies:
            if self.get_friendlies_next_to(enemy.location, game):
                enemies_fighting_friendlies.append(enemy)
        return enemies_fighting_friendlies
    
    def get_enemies_to_fight_friendlies(self, enemies):
        enemies_to_fight_friendlies = []
        for enemy in enemies:
            for pos in rg.locs_around(enemy.location):
                if pos in future_moves:
                    enemies_to_fight_friendlies.append(enemy)
                    break
        return enemies_to_fight_friendlies

    def get_tile_goodness(self, loc, game):
        """Returns how 'good' a tile is to move to or stay on.
        Based on a whole bunch of factors. Fine-tuning necessary."""

        types = rg.loc_types(loc)
        enemies_next_to_loc = self.get_enemy_bots_next_to(loc, game)
        enemies_next_to_loc_fighting_friendlies = \
                self.get_enemies_fighting_friendlies(
                        enemies_next_to_loc, game)

        enemies_next_to_loc_to_fight_friendlies = \
                self.get_enemies_to_fight_friendlies(enemies_next_to_loc)

        friendlies_next_to_loc = self.get_friendlies_next_to(loc, game)

        nearby_friendlies_in_spawn = []
        nearby_friendlies_in_deep_spawn = []
        for friendly in friendlies_next_to_loc:
            if 'spawn' in rg.loc_types(friendly.location):
                nearby_friendlies_in_spawn.append(friendly)
                if cant_easily_leave_spawn(friendly.location, game):
                    nearby_friendlies_in_deep_spawn.append(friendly)

        friendly_in_loc = enemy_in_loc = False
        if loc != self.location:
            bot_in_location = get_bot_in_location(loc, game)
            if bot_in_location:
                if bot_in_location.player_id == self.player_id:
                    friendly_in_loc = True
                else:
                    enemy_in_loc = True

        else:
            bot_in_location = None
        distance_to_closest_enemy = self.get_distance_to_closest_bot(game,
                loc=loc, enemy=True)

        distance_to_closest_friendly = self.get_distance_to_closest_bot(game,
                loc=loc, friendly=True)

        nearby_friendlies_in_trouble = []
        for friendly in friendlies_next_to_loc:
            if bot_is_in_trouble(friendly, game):
                nearby_friendlies_in_trouble.append(friendly)

        goodness = 0

        # get out of spawn areas, especially if things are about to spawn
        # highest priority: -50 pts if things are about to spawn
        if game['turn'] <= 90:
            goodness -= ('spawn' in types) * ((game['turn'] % 10 == 0) * 50 + SPAWN_WEIGHT)

        # if the bot can't easily leave spawn (e.g. has to move through
        # more spawn area or an enemy to get out) in the location, that's bad
        # the closer to the spawn timer we are, the worse this is, so
        # multiply it by the game turn % 10
        if game['turn'] <= 90:
            goodness -= cant_easily_leave_spawn(loc, game) * (
                    game['turn'] % 10) * CANT_EASILY_LEAVE_SPAWN_WEIGHT

        # if enemies next to the location are fighting or will fight
        # other friendlies, help them
        goodness += len(enemies_next_to_loc_fighting_friendlies) * FIGHTING_FRIENDLY_WEIGHT

        goodness += len(enemies_next_to_loc_to_fight_friendlies) * TO_FIGHT_FRIENDLY_WEIGHT

        # more enemies next to a location, the worse.
        # even worse if a friendly is already in the location
        #    (so the enemies will target that loc)
        # even worse if our hp is low
        # so exponential because of exponential badness I think
        goodness -= (len(enemies_next_to_loc) * ADJACENT_ENEMIES_WEIGHT) ** ADJACENT_ENEMIES_EXPONENT

        goodness -= friendly_in_loc * FRIENDLY_IN_LOC_WEIGHT

        # slight bias towards NOT moving right next to friendlies
        # a sort of lattice, like
        # X X X X
        #  X X X
        # X X X X
        # is the best shape, I think
        #goodness -= len(friendlies_next_to_loc) * 0.05

        # nearby friendlies in trouble will definitely want to escape this turn
        goodness -= len(nearby_friendlies_in_trouble) * FRIENDLIES_IN_TROUBLE_WEIGHT

        if could_die_in_loc(self.hp, loc, self.player_id, game):
            # /try/ not to go where the bot can die
            # seriously
            goodness -= COULD_DIE_WEIGHT

        # all else remaining the same, move towards the center
        goodness -= rg.dist(loc, rg.CENTER_POINT) * 0.01

        # bias towards remaining in place and attacking
        goodness += (loc == self.location) * REMAIN_BIAS
        # especailly if we're only fighting one bot

        if self.hp > 15:
            # if we are strong enough, move close to (2 squares away) the
            #nearest enemy
            goodness -= max(distance_to_closest_enemy, 2) * CHARGE_WEIGHT
        else:
            #otherwise, run away from the nearest enemy, up to 2 squares away
            goodness += min(distance_to_closest_enemy, 2) * ESCAPE_WEIGHT

        # friendlies should group together
        # if a bot is caught alone, bots that actively hunt and surround,
        # e.g. Chaos Witch Quelaang, will murder them
        # so move up to two tiles from the nearest friendly
        goodness -= min(distance_to_closest_friendly, 2) * GROUP_WEIGHT

        # don't move into an enemy
        # it's slightly more ok to move into an enemy that could die in the
        # next turn by staying here, cause he's likely to either run or die
        # it's perfectly alright, maybe even encouraged, to move into a bot
        # that would die from bumping into you anyways (<=5hp)
        if enemy_in_loc:
            goodness -= enemy_in_loc * ENEMY_IN_LOC_WEIGHT
            goodness += (bot_is_in_trouble(bot_in_location, game) *
                    ENEMY_IN_TROUBLE_WEIGHT)
            goodness += ENEMY_SUPER_WEAK_WEIGHT * (bot_in_location.hp <= 5)

        # don't block friendlies trying to move out of spawn!
        # only matters when things will still spawn in the future, of course
        if game['turn'] <= 90:
            # if they can escape through us
            if not 'spawn' in types:
                goodness -= len(nearby_friendlies_in_spawn) * \
                        NEARBY_FRIENDLIES_IN_SPAWN_WEIGHT
            #especially don't block those who can't easily leave spawn
            # (the two lists overlap, so no extra weighting needed)
            goodness -= len(nearby_friendlies_in_deep_spawn) * \
                    NEARBY_FRIENDLIES_IN_DEEP_SPAWN_WEIGHT

        # don't move next to possible suiciders if our hp is low enough to die
        # from them
        for enemy in enemies_next_to_loc_fighting_friendlies:
            if is_possible_suicider(enemy, game) and (self.hp <= 15):
                goodness -= POSSIBLE_SUICIDERS_WEIGHT

        # the more enemies that could move next to the loc, the worse
        # (the more this bot could be surrounded)
        goodness -= min(len(self.get_enemies_that_could_move_next_to(
            loc, game)), 1) * SURROUND_WEIGHT

        # DON'T move into a square if another bot already plans to move there
        goodness -= 999 * (loc in future_moves)

        #allies attacking the same spot is bad, but not the end of the world..
        # e.g. if a robot needs to go through a spot being attacked by an
        # ally to leave spawn, he DEFINITELY still needs to move there
        goodness -= MOVE_INTO_ATTACK_WEIGHT * (loc in future_attacks)

        return goodness

    def get_enemies_that_could_move_next_to(self, loc, game):
        enemies = []
        for bot in game.get('robots').values():
            if bot.player_id != self.player_id:
                if rg.wdist(bot.location, loc) == 2:
                    enemies.append(bot)
        return enemies

    def get_attack_goodness(self, loc, game):
        """Returns how 'good' attacking a certain location is.
        Based upon the number of friendlies and enemies next to the location,
        any bot that is in the location, etc."""
        enemies_next_to_loc = self.get_enemy_bots_next_to(loc, game)
        friendlies_next_to_loc = self.get_friendlies_next_to(loc, game)
        nearby_friendlies_in_trouble = []
        for friendly in friendlies_next_to_loc:
            if bot_is_in_trouble(friendly, game):
                nearby_friendlies_in_trouble.append(friendly)
        nearby_enemies_in_trouble = []
        for enemy in enemies_next_to_loc:
            if bot_is_in_trouble(enemy, game):
                nearby_enemies_in_trouble.append(enemy)
        robot = get_bot_in_location(loc, game)

        goodness = 0

        if robot:
            if robot.player_id == self.player_id:
                # we're attacking a friendly's location
                # no enemy's gonna move into them...
                goodness -= FRIENDLY_LOC_ATTACK_WEIGHT
            else:
                #attacking an enemy is good
                goodness += (100 - robot.hp) * ENEMY_ATTACK_HP_WEIGHT
        else:

            # no bot is at the location
            # so base the goodness on how likely it is for bots to move there

            #more enemies that can move into the location, the better
            # weighted by 3 because even if there are two other friendlies
            # next to the loc, we still want to attack if it's the only square
            # an enemy is next to
            goodness += len(enemies_next_to_loc) * ADJACENT_ENEMY_ATTACK_WEIGHT

            #enemies aren't too likely to move next to a friendly
            goodness -= len(friendlies_next_to_loc) * \
                    ADJACENT_FRIENDLY_ATTACK_WEIGHT

            # if there are enemies in trouble nearby, we want to try and catch
            # them escaping!
            goodness += len(nearby_enemies_in_trouble) * \
                    NEARBY_TROUBLED_ENEMY_ATTACK_WEIGHT

            # nearby friendlies in trouble will definitely want to escape this
            # turn
            # maybe to this square
            goodness -= len(nearby_friendlies_in_trouble) * \
                    NEARBY_TROUBLED_FRIENDLY_ATTACK_WEIGHT

            # don't attack where an ally is already moving to
            # or attacking, at least not too much
            if loc in future_moves:
                goodness -= ATTACK_IN_FUTURE_MOVES_WEIGHT
            elif loc in future_attacks:
                goodness -=  MULTIPLE_ATTACK_WEIGHT
        return goodness

    def get_best_attack_loc(self, locs, game):
        """Determines the best location to attack out of a list of locations.
        Uses get_attack_goodness() to weigh the locations."""
        best_loc_weight = -9999
        best_loc = None
        for loc in locs:
            loc_weight = self.get_attack_goodness(loc, game)
            if loc_weight > best_loc_weight:
                best_loc = loc
                best_loc_weight = loc_weight
        return best_loc
