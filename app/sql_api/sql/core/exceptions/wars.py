class WarCooldownNotFinishedError(Exception):
    def __init__(self):
        self.message = "Player cannot declare war until the end of 30 minutes cooldown"
        super().__init__(self.message)


class PlayerWarLimitError(Exception):
    def __init__(self):
        self.message = "Player cannot be attacked by more than 3 other players"
        super().__init__(self.message)


class AlreadyInWarError(Exception):
    def __init__(self):
        self.message = "Player can't declare another was while being in a war"
        super().__init__(self.message)


class InvalidWarError(Exception):
    def __init__(self):
        self.message = "The war between 2 passed players does not exist"
        super().__init__(self.message)


class PlayerIsNotEliminatedError(Exception):
    def __init__(self):
        self.message = "Living player can't be revived"
        super().__init__(self.message)
