import datetime
from bastoebot.disruption_message import DisruptionMessage, space_clean

def parse_date(day_str, time_str):
    return datetime.datetime.strptime("{} {}".format(day_str, time_str), "%Y%m%d %H%M%S")

class Disruption:
    def __init__(self, data, himMsgEdgeL, locL):
        """
        Parameters
        ----------
        data : dict
            himL element of the JSON returned by the API
        """
        self.hid = data["hid"]
        self.title = space_clean(data["head"].strip())
        self.start_date = parse_date(data["sDate"], data["sTime"])
        self.end_date = parse_date(data["eDate"], data["eTime"])
        self.prio = data["prio"]
        self.prod = data["prod"]
        self.set_impact(data["impactL"])
        mod_date = parse_date(data["lModDate"], data["lModTime"])
        self.mod_date = mod_date
        if "text" in data:
            self.messages = [DisruptionMessage(mod_date, data["text"])]
        else:
            self.messages = []
        self.sort_messages()
        self.set_location(data["edgeRefL"], himMsgEdgeL, locL)
        self.set_impact(data["impactL"])

    def set_location(self, edgeL, himMsgEdgeL, locL):
        for e in edgeL:
            edge = himMsgEdgeL[e]
            self.text_from = locL[edge.get("fLocX", "")].get("name", "unknown")
            self.text_to = locL[edge.get("tLocX", "")].get("name", None)

    def set_impact(self, impactL):
        self.impact_regional = None
        self.impact_ic = None
        self.impact_freight = None
        for i in impactL:
            if i["prodCode"] == "SPNV":
                self.impact_regional = i.get("impact", "")
            elif i["prodCode"] == "SPFV":
                self.impact_ic = i.get("impact", "")
            elif i["prodCode"] == "SGV":
                self.impact_freight = i.get("impact", "")

    def merge(self, other):
        """
        Merge this instance with another instance.
        """
        if self.hid != other.hid:
            raise Exception("Hid is different.")
        self.prod = self.prod | other.prod
        self.prio = max(self.prio, other.prio)
        self.messages = merge_messages(self.messages, other.messages)
        self.sort_messages()

    def sort_messages(self):
        self.messages.sort(key=lambda entry: entry.mod_date)
