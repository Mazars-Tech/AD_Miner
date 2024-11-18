from ad_miner.sources.modules.controls import Control
from ad_miner.sources.modules.controls import register_control

from ad_miner.sources.modules.page_class import Page
from ad_miner.sources.modules.grid_class import Grid


@register_control
class fgpp(Control):
    "Legacy control"

    def __init__(self, arguments, requests_results) -> None:
        super().__init__(arguments, requests_results)

        self.azure_or_onprem = "on_premise"
        self.category = "misc"
        self.control_key = "fgpp"

        self.title = "Users FGPP"
        self.description = "FGPP applied to a user, directly or via a group"
        self.risk = "FGPP change password and lockout policies if defined"
        self.poa = "The FGPP values overwrite the GPO values"

        self.fgpps = requests_results["get_fgpp"]

    def run(self):
        fgpps = self.fgpps
        # create the page
        page = Page(
            self.arguments.cache_prefix,
            "fgpp",
            "Users FGPP",
            self.get_dico_description(),
        )
        # create the grid
        grid = Grid("Users FGPP")
        # create the headers
        headers = [
            "affected object",
            "fgpp name",
            "minimumPasswordLength",
            "minimumPasswordAge",
            "maximumPasswordAge",
            "clearTextPassword",
            "passwordHistorySize",
            "passwordComplexity",
            "lockoutDuration",
            "lockoutThreshold",
            "lockoutObservationWindow",
        ]
        # get the grid data
        grid_data = []
        for (
            obj,
            fgppName,
            minPassLen,
            minPassAge,
            maxPassAge,
            clearTextPass,
            passHistSize,
            passComp,
            lockThre,
            lockDur,
            lockObsWin,
        ) in fgpps:
            tmp_data = {}
            tmp_data["affected object"] = obj if obj != None else "X"
            tmp_data["fgpp name"] = fgppName if fgppName != None else "X"
            tmp_data["minimumPasswordLength"] = (
                minPassLen if minPassLen != None else "X"
            )
            tmp_data["minimumPasswordAge"] = minPassAge if minPassAge != None else "X"
            tmp_data["maximumPasswordAge"] = maxPassAge if maxPassAge != None else "X"
            tmp_data["clearTextPassword"] = (
                clearTextPass if clearTextPass != None else "X"
            )
            tmp_data["passwordHistorySize"] = (
                passHistSize if passHistSize != None else "X"
            )
            tmp_data["passwordComplexity"] = passComp if passComp != None else "X"
            tmp_data["lockoutDuration"] = lockDur if lockDur != None else "X"
            tmp_data["lockoutThreshold"] = lockThre if lockThre != None else "X"
            tmp_data["lockoutObservationWindow"] = (
                lockObsWin if lockObsWin != None else "X"
            )
            grid_data.append(tmp_data)

        grid.setheaders(headers)
        grid.setData(grid_data)
        page.addComponent(grid)
        page.render()

        self.data = len(self.fgpps)
        self.name_description = f"{self.data} FGPP defined"

    def get_rating(self) -> int:
        return -1 if len(self.fgpps) == 0 else 5
