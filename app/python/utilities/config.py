
"""
Global app configuration from '/configuration.json'.

    * Initialization:
        * MicroPython: load()
        * Webapp: set(config_from_gateway)
    * use set/get to read/update configuration values
    * get() returns entire configuration as dict of dicts
    * app modifies config, e.g. device discovery, name changes
    * call save regularly to commit changes to config.json (handled by auto_save_config task)
"""

import json
from utilities import ids, timestamp

# set() is overloaded
import builtins   

try:
    # not available in MicroPython
    from fnmatch import fnmatch
except ImportError:
    # bogus version that accepts everyting
    def fnmatch(name, pattern):
        return name

# lazily load config in get/set
_CONFIG = None
_CONFIG_MODIFIED = False
_CONFIG_FILE = '/configuration.json'
_DEFAULT_CONFIG = {}
_CUSTOM_CONFIG = {}


def merge(a, b):
    """Merge b into a.
    In case of conflicts, a takes precedence.
    Result is in a, b is not changed."""
    assert a != None
    for key in b:
        if key in a:
            if isinstance(a[key], dict) and isinstance(b[key], dict):
                merge(a[key], b[key])
        else:
            a[key] = b[key]
    return a


def load(default_config, custom_config):
    """Load configuration from flash."""
    global _CONFIG, _DEFAULT_CONFIG, _CUSTOM_CONFIG
    _DEFAULT_CONFIG = default_config
    _CUSTOM_CONFIG = custom_config
    try:
        with open(_CONFIG_FILE) as stream:
            _CONFIG = json.load(stream)
    except OSError:
        _CONFIG = {}
    # set defaults
    merge(_CONFIG, default_config)
    merge(_CONFIG, custom_config)
    

def save(force=False):
    """Save configuration changes, if any."""
    global _CONFIG, _CONFIG_FILE, _CONFIG_MODIFIED, _DEFAULT_CONFIG, _CUSTOM_CONFIG
    assert _CONFIG != None
    if _CONFIG_MODIFIED or force:
        # set defaults
        merge(_CONFIG, _DEFAULT_CONFIG)
        merge(_CONFIG, _CUSTOM_CONFIG)
        set('timestamp', timestamp())
        with open(_CONFIG_FILE, "w") as stream:
            json.dump(_CONFIG, stream)
        _CONFIG_MODIFIED = False


def modified() -> bool:
    """Returns True if in-memory _CONFIG changed since last save"""
    global _CONFIG_MODIFIED 
    return _CONFIG_MODIFIED


def get(*path) -> str:
    """Get config.
    :param path:   Drill recursively into config dict.
    :return:       Item or none if it does not exist.

    Example::
        import config

        config.get("app", "wifi", "ssid")
        config.get("devices", "Govee a4:c1:38:18:a6:fe", "Temperature")
        # reference to entire configuration
        # Note: do not modify directly (use set instead)
        config.get()
    """
    global _CONFIG
    res = _CONFIG
    assert res != None
    try:
        for p in path:
            res = res[p]
    except KeyError:
        return None
    return res


def set(*p_v):
    """Set config value.
    :param p_v: Last element is value, p_v[:-1] is path.
                New nodes are automatically created, as needed.
                Value may be a str (other types are silently converted to str after save) or a dict.
                Setting value==None deletes the entry from the configuration.
                With only one (dict) argument, set replaces the current config.

    :exceptions:   value_error if called with 1 parameter
                   

    Example::
        import config

        try:
            import micropython
            config.load()
        except:
            config.set(configuration_from_gateway)
            
        config.set("devices", "Govee a4:c1:38:18:a6:fe", "Temperature", "history", 1000)
    """
    global _CONFIG, _CONFIG_MODIFIED
    if len(p_v) == 1 and isinstance(p_v[0], dict):
        _CONFIG = p_v[0]
        _CONFIG_MODIFIED = True
        return True
    assert _CONFIG != None
    if len(p_v) < 2: 
        raise ValueError("No value specified")
    value = p_v[-1]
    field = p_v[-2]
    path = p_v[:-2]
    # print(f"config.set: path={path} field={field} value={value}")
    node = _CONFIG
    for p in path:
        if not isinstance(node, dict): 
            raise AttributeError(f"Node {p} {node} is not a dict")
        leaf = node.get(p)
        if leaf:
            node = leaf
        else:
            leaf = {}
            node[p] = leaf
            node = leaf
    if not isinstance(node, dict): 
        raise AttributeError(f"Node {p} {node} is not a dict!")
    if field in node and node[field] == value:
        # no change: field already set to value
        # print(f"no change {p_v}")
        return
    if value != None:
        node[field] = value
    elif field in node:
        del node[field]
    _CONFIG_MODIFIED = True

    
def get_entity_config(did, aid=None):
    global _CONFIG
    assert _CONFIG != None
    if aid == None:
        aid = ids.aid(did)
        did = ids.did(did)     
    dc = get("devices", did, 'entities', aid) or {}
    # don't modify config!
    dc = dc.copy()
    merge(dc, get('defaults', aid) or {})
    merge(dc, get('defaults', "*") or { "unit": "", "icon": "label", "filter": [ "duplicate" ] })
    dc['device_name'] = get('devices', did, 'name') or did
    if not 'name' in dc:
        dc['name'] = aid
    return dc


def get_views():
    # list of all eid
    eids = builtins.set()
    for did, dev_attr in get('devices').items():
        for aid in dev_attr.get('entities') or {}:
            eids.add(ids.eid(did, aid))
    
    # views
    views = []
    for view in get('views') or []:
        for entity_pattern in view.get('entities') or []:
            entities = []
            if '*' in entity_pattern:
                for eid in eids:
                    if fnmatch(eid, entity_pattern):
                        entities.append(eid)
            else:
                entities.append(entity_pattern)
        views.append({ 'icon': view.get('icon', 'label'), 'entities': entities })
    return views
