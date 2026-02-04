class PlayerNotFoundError(Exception):
    def __init__(self):
        self.message = "Player was not found in database, make sure that game_id and discord_id are valid"
        super().__init__(self.message)


class PlayerIsEliminatedError(Exception):
    def __init__(self):
        self.message = "Player was eliminated and thus can no longer participate in the game"
        super().__init__(self.message)


class PlayerAlreadyRegisteredError(Exception):
    def __init__(self):
        self.message = "Player cannot be registered twice for the one game"
        super().__init__(self.message)


class GameRegistrationIsClosedError(Exception):
    def __init__(self):
        self.message = "Players cannot register or cancel registrations if the game has already started"
        super().__init__(self.message)
