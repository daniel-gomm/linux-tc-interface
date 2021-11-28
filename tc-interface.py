import os
import jsonpickle

DEV_NAME = "eth0"

AVAILABLE_PRIO_BANDS = [2, 3, 4, 5, 6, 7, 8, 9, 10]

DELAY_RULES = {}

IP_FILTERS = {}

PORT_FILTERS = {}

COMBINED_FILTERS = {}

#Templates for commands

ADD_QDISC_COMMAND = "sudo tc qdisc add dev {0} root handle 1: prio bands 16 priomap 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0"

COMBINED_RULE_COMMAND = "sudo tc qdisc add dev {0} parent 1:{1} handle 1{1}: netem delay {2}ms {3}ms distribution normal loss {4}%"

LOSS_RULE_COMMAND = "sudo tc qdisc add dev {0} parent 1:{1} handle 1{1}: netem loss {2}%"

REDUCED_COMBINED_RULE_COMMAND = "sudo tc qdisc add dev {0} parent 1:{1} handle 1{1}: netem delay {2}ms loss {3}%"

ADD_IP_FILTER_COMMAND = "sudo tc filter add dev {0} protocol ip parent 1:0 prio 1 u32 match ip dst {1}/32 flowid 1:{2}"

ADD_PORT_FILTER_COMMAND = "sudo tc filter add dev {0} protocol ip parent 1:0 prio 1 u32 match ip sport {1} 0xffff flowid 1:{2}"

ADD_COMBINED_FILTER_COMMAND = "sudo tc filter add dev {0} protocol ip parent 1:0 prio 1 u32 match ip dst {1}/32 match ip sport {2} 0xffff flowid 1:{3}"

DELETE_RULES_COMMAND = "sudo tc qdisc del dev {0} root"

#Other constants

CONFIG_PATH = "./.config"

class DelayRule:

    def __init__(self, avg_delay:int, sd:int, rule_name:str, prio_band:int=None, package_loss:float = 0.0) -> None:
        self._rule_name = rule_name
        self._avg_delay = avg_delay
        self._sd = sd
        self._package_loss = package_loss
        if prio_band:
            self._prio_band = prio_band
            AVAILABLE_PRIO_BANDS.remove(prio_band)
        else:
            self._prio_band = AVAILABLE_PRIO_BANDS.pop()
        DELAY_RULES[rule_name] = self
    
    def start_rule(self)->None:
        if self._avg_delay > 0:
            if self._sd > 0:
                os.system(COMBINED_RULE_COMMAND.format(DEV_NAME, self._prio_band, self._avg_delay, self._sd, self._package_loss))
            else:
                os.system(REDUCED_COMBINED_RULE_COMMAND.format(DEV_NAME, self._prio_band, self._avg_delay, self._package_loss))
        else:
            os.system(LOSS_RULE_COMMAND.format(DEV_NAME, self._prio_band, self._package_loss))
        print(f"Started rule {self._rule_name}")
    
    def get_prio_band(self)->int:
        return self._prio_band


class IPFilter:

    def __init__(self, ip_address:str, delay_rule_name:str, filter_name:str) -> None:
        self._ip_address = ip_address
        self._delay_rule = DELAY_RULES[delay_rule_name]
        self._filter_name = filter_name
        IP_FILTERS[filter_name] = self
    
    def start_filter(self)->None:
        os.system(ADD_IP_FILTER_COMMAND.format(DEV_NAME, self._ip_address, self._delay_rule.get_prio_band()))
        #print(ADD_IP_FILTER_COMMAND.format(DEV_NAME, self._ip_address, self._delay_rule.get_prio_band()))
        print(f"Started filter {self._filter_name} for rule {self._delay_rule._rule_name}")


class PortFilter:

    def __init__(self, port:int, delay_rule_name:str, filter_name:str) -> None:
        self._port = port
        self._delay_rule = DELAY_RULES[delay_rule_name]
        self._filter_name = filter_name
        PORT_FILTERS[filter_name] = self
    
    def start_filter(self)->None:
        os.system(ADD_PORT_FILTER_COMMAND.format(DEV_NAME, self._port, self._delay_rule.get_prio_band()))
        print(f"Started filter {self._filter_name} for rule {self._delay_rule._rule_name}")

class CombinedFilter:

    def __init__(self, ip_address:str, port:int, delay_rule_name:str, filter_name:str) -> None:
        self._ip_address = ip_address
        self._port = port
        self._delay_rule = DELAY_RULES[delay_rule_name]
        self._filter_name = filter_name
        COMBINED_FILTERS[filter_name] = self
    
    def start_filter(self)->None:
        os.system(ADD_COMBINED_FILTER_COMMAND.format(DEV_NAME, self._ip_address, self._port, self._delay_rule.get_prio_band()))
        print(f"Started filter {self._filter_name} for rule {self._delay_rule._rule_name}")


def start_command():
    os.system(DELETE_RULES_COMMAND.format(DEV_NAME))
    os.system(ADD_QDISC_COMMAND.format(DEV_NAME))
    for delay_rule in DELAY_RULES.values():
        delay_rule.start_rule()
    for filter_rule in IP_FILTERS.values():
        filter_rule.start_filter()
    for filter_rule in PORT_FILTERS.values():
        filter_rule.start_filter()
    for filter_rule in COMBINED_FILTERS.values():
        filter_rule.start_filter()

def stop_command():
    os.system(DELETE_RULES_COMMAND.format(DEV_NAME))


def save_configurarions():
    with open(f"{CONFIG_PATH}/delay_rules.json", "w") as f:
        f.writelines(jsonpickle.encode(DELAY_RULES))
    with open(f"{CONFIG_PATH}/ip_filters.json", "w") as f:
        f.writelines(jsonpickle.encode(IP_FILTERS))
    with open(f"{CONFIG_PATH}/port_filters.json", "w") as f:
        f.writelines(jsonpickle.encode(PORT_FILTERS))
    with open(f"{CONFIG_PATH}/combined_filters.json", "w") as f:
        f.writelines(jsonpickle.encode(COMBINED_FILTERS))
    print("Configuration has been saved")

def load_configurations():
    with open(f"{CONFIG_PATH}/delay_rules.json", "r") as f:
        contents = "".join(f.readlines())
        if not contents == None:
            delay_rules = jsonpickle.decode(contents, classes=DelayRule)
    with open(f"{CONFIG_PATH}/ip_filters.json", "r") as f:
        contents = "".join(f.readlines())
        if not contents == None:
            ip_filters = jsonpickle.decode(contents, classes=IPFilter)
    with open(f"{CONFIG_PATH}/port_filters.json", "r") as f:
        contents = "".join(f.readlines())
        if not contents == None:
            port_filters = jsonpickle.decode(contents, classes=PortFilter)
    with open(f"{CONFIG_PATH}/combined_filters.json", "r") as f:
        contents = "".join(f.readlines())
        if not contents == None:
            combined_filters = jsonpickle.decode(contents, classes=CombinedFilter)
    with open(f"{CONFIG_PATH}/dev_name.json") as f:
        contents = "".join(f.readlines())
        if not contents == None:
            dev_name = jsonpickle.decode(contents, classes=dict)["DEV_NAME"]
    return delay_rules, ip_filters, port_filters, combined_filters, dev_name

def remove_used_prio_bands():
    for rule in DELAY_RULES.values():
        AVAILABLE_PRIO_BANDS.remove(rule._prio_band)

def remove_filter(filter_name:str):
    if filter_name in IP_FILTERS.keys():
        del IP_FILTERS[filter_name]
    elif filter_name in PORT_FILTERS.keys():
        del PORT_FILTERS[filter_name]
    elif filter_name in COMBINED_FILTERS.keys():
        del COMBINED_FILTERS[filter_name]

def remove_rule(rule_name:str):
    corresponding_filters = [filter._filter_name for filter in IP_FILTERS.values() if filter._delay_rule._rule_name == rule_name]
    for filter_name in corresponding_filters:
        remove_filter(filter_name)
    AVAILABLE_PRIO_BANDS.append(DELAY_RULES[rule_name]._prio_band)
    del DELAY_RULES[rule_name]

def list_rules()->str:
    s = ""
    for rule in DELAY_RULES.values():
        s += f"{rule._rule_name} with avg delay of {rule._avg_delay}, a standard deviation of {rule._sd} and a package loss of {rule._package_loss}%\n"
    return s[:-1]

def list_filters()->str:
    s = "IP Filters:\n"
    for filter in IP_FILTERS.values():
        s += f"{filter._filter_name} filtering ip {filter._ip_address} using rule {filter._delay_rule._rule_name}\n"
    s += "Port Filters:\n"
    for filter in PORT_FILTERS.values():
        s += f"{filter._filter_name} filtering port {filter._port} using rule {filter._delay_rule._rule_name}\n"
    s += "Combined Filters:\n"
    for filter in COMBINED_FILTERS.values():
        s += f"{filter._filter_name} filtering ip {filter._ip_address} and port {filter._port} using rule {filter._delay_rule._rule_name}\n"
    return s[:-1]

if __name__ == "__main__":
    DELAY_RULES, IP_FILTERS, PORT_FILTERS, COMBINED_FILTERS, DEV_NAME = load_configurations()
    remove_used_prio_bands()
    start_command()
    print("#"*25 + "Linux Trafic Control Interface" + "#"*25)
    print(f"Current rules:\n\n{list_rules()}")
    print(f"\nCurrent filters:\n\n{list_filters()}")
    while True:
        inp = input("\nar: Add rule\naf: Add Filter\napf: Add Port Filter\naif: Add IP Filter\ns: Stop All Rules\nw: Save current set of rules\nrr: Remove Rule\nrf: Remove Filter\nlr: List Rules\nlf: List Filters\nrs: Restart Rules\nrst: Reset (delte all rules and reset qdisc)\ne: Exit\n\n~>")
        if inp == "ar":
            avg_delay = int(input("Average Delay:"))
            sd = int(input("Standard Deviation:"))
            loss = float(input("Package Loss:"))
            rule_name = input("Rule Name:")
            try:
                new_rule = DelayRule(avg_delay, sd, rule_name, package_loss = loss)
                new_rule.start_rule()
                print(f"Rule {rule_name} started")
            except:
                if len(AVAILABLE_PRIO_BANDS) == 0:
                    print("Encountered an error while creating the rule.\nAll prio band are already occupied. You have to remove another rule before specifiying a new one.")
                else:
                    print("Encountered an error while creating the rule.")
        elif inp == "af":
            print(f"Current rules:\n\n{list_rules()}")
            ip_add = input("IP Address:")
            port = int(input("Port:"))
            rule_name = input("Corresponding Rule Name:")
            filter_name = input("Filter Name:")
            try:
                new_filter = CombinedFilter(ip_add, port, rule_name, filter_name)
                new_filter.start_filter()
                print("Filter started")
            except KeyError:
                print(f"Encountered an error while creating the filter.\nThe rule {rule_name} is not recognized.")
        elif inp == "aif":
            print(f"Current rules:\n\n{list_rules()}")
            ip_add = input("IP Address:")
            rule_name = input("Corresponding Rule Name:")
            filter_name = input("Filter Name:")
            try:
                new_filter = IPFilter(ip_add, rule_name, filter_name)
                new_filter.start_filter()
                print("Filter started")
            except KeyError:
                print(f"Encountered an error while creating the filter.\nThe rule {rule_name} is not recognized.")
        elif inp == "apf":
            print(f"Current rules:\n\n{list_rules()}")
            port = int(input("Port:"))
            rule_name = input("Corresponding Rule Name:")
            filter_name = input("Filter Name:")
            try:
                new_filter = PortFilter(port, rule_name, filter_name)
                new_filter.start_filter()
                print("Filter started")
            except KeyError:
                print(f"Encountered an error while creating the filter.\nThe rule {rule_name} is not recognized.")
        elif inp == "s":
            stop_command()
            print("All rules have been stopped")
        elif inp == "w":
            save_configurarions()
        elif inp == "rr":
            print(f"Current rules:\n\n{list_rules()}")
            print("Removing the rule and all associated filters")
            rule_name = input("Name of the rule to be deleted:")
            try:
                remove_rule(rule_name)
                print("This change will only come into effect once a restart is triggered")
            except:
                print(f"The rule {rule_name} could not be deleted")      
        elif inp == "rf":
            print(f"Current filters:\n\n{list_filters()}")
            filter_name = input("Name of the filter to be deleted:")
            try:
                remove_filter(filter_name)
                print("This change will only come into effect once a restart is triggered")
            except:
                print(f"The filter {filter_name} could not be deleted")
        elif inp == "rs":
            print("Stopping all rules")
            stop_command()
            print("Starting all rules again")
            start_command()
        elif inp == "lr":
            print(f"Current rules:\n\n{list_rules()}")
        elif inp == "lf":
            print(f"Current filters:\n\n{list_filters()}")
        elif inp == "rst":
            DELAY_RULES = {}
            IP_FILTERS = {}
            PORT_FILTERS = {}
            COMBINED_FILTERS = {}
            stop_command()
            print("All rules have been stopped; qdisc has been reset\nExiting...")
            save_configurarions()
        elif inp == "e":
            save_configurarions()
            break
        else:
            print("Invalid Input!")
