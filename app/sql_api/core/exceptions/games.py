class GameSessionIsClosedError(Exception):
    def __init__(self):
        self.message = "Player cannot perform any actions that can make impact on the game while session is closed; Session is already closed"
        super().__init__(self.message)


class GameSessionIsNotClosedError(Exception):
    def __init__(self):
        self.message = "Another game cannot be selected while current game session is open; Session is already open"
        super().__init__(self.message)
