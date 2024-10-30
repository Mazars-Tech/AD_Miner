import os
import importlib

control_list = []


def register_control(cls):
    "Decorator to register every control that should be run by AD Miner"
    control_list.append(cls)
    return cls


class Control:
    """Every control should inheritate from this class.
    It contains requests results and define essential structure."""

    def __init__(self, arguments, requests_results) -> None:
        self.arguments = arguments
        self.requests_results = requests_results
        self.title = ""
        self.description = ""
        self.interpretation = ""
        self.risk = ""
        self.poa = ""

    def run(self):
        error_message = "Your control " + str(self)
        error_message += " should have a run() function defined."
        raise NotImplementedError(error_message)

    def get_rating(self) -> int:
        error_message = "Your control " + str(self)
        error_message += " should have a get_rating() function defined."
        raise NotImplementedError(error_message)

    def get_dico_description(self) -> dict:
        self.dico_description: dict[str, str] = {
            "title": self.title,
            "description": self.description,
            "interpretation": self.interpretation,
            "risk": self.risk,
            "poa": self.poa,
        }
        return self.dico_description


__all__ = []


dirname = os.path.dirname(os.path.abspath(__file__))

for filename in os.listdir(dirname):
    if (
        filename != "__init__.py"
        and os.path.isfile(os.path.join(dirname, filename))
        and filename.endswith(".py")
    ):
        module_name = filename[:-3]  # Remove ".py" extension
        __all__.append(module_name)
        module = importlib.import_module(f".{module_name}", package=__name__)
