class AlreadyResearchingError(Exception):
    def __init__(self):
        self.message = "There is already a research in progress, you cannot have more than one in progress"
        super().__init__(self.message)


class AlreadyResearchedError(Exception):
    def __init__(self):
        self.message = "This research is already done, you cannot do the same research twice"
        super().__init__(self.message)


class MutuallyExclusiveResearchError(Exception):
    def __init__(self):
        self.message = "This research cannot be done since its mutually exclusive research has already been done"
        super().__init__(self.message)


class RequiredResearchesNotCompletedError(Exception):
    def __init__(self):
        self.message = "You cannot start this research without completing previous ones"
        super().__init__(self.message)


class ProducingTwoSameItemsAtTheSameTimeError(Exception):
    def __init__(self):
        self.message = "Players cannot produce two items of one research at the same time"
        super().__init__(self.message)


class ProducingTooManyItemsError(Exception):
    def __init__(self):
        self.message = "There are 3 item productions in progress already, you cannot have more than 3 at the same time"
        super().__init__(self.message)


class ItemsPerResearchLimitError(Exception):
    def __init__(self):
        self.message = "Players cannot produce more than 3 items of the same research"
        super().__init__(self.message)


class ResearchNotFoundInPlayerDataError(Exception):
    def __init__(self):
        self.message = "Research was not found in player's research list"
        super().__init__(self.message)


class ResearchNotFinishedError(Exception):
    def __init__(self):
        self.message = "Research is not finished yet, you cannot produce its item"
        super().__init__(self.message)


class ResearchNotFoundError(Exception):
    def __init__(self):
        self.message = "This research was not found in database"
        super().__init__(self.message)


class ItemProductionNotFinishedError(Exception):
    def __init__(self):
        self.message = "Your item production is not finished yet, you cannot produce another item"
        super().__init__(self.message)


class ItemCountBelowZeroError(Exception):
    def __init__(self):
        self.message = "Item count cannot be below zero"
        super().__init__(self.message)
