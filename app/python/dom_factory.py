from js import document, console
from utilities import ids


def make_element(cls, content=None, *, tag="div"):
    e = document.createElement("div")
    e.className = cls
    if content == None:
        pass
    elif isinstance(content, str):
        # which is it?
        # e.textContent = content  
        e.innerText = content
    elif isinstance(content, (list, tuple)):
        for child in content:
            e.appendChild(child)
    else:
        e.appendChild(content)
    return e


def make_i(icon, cls="material-icons-outlined"):
    return make_element(cls, tag="i", content=icon)


def make_nav(icon):
    i = make_i(icon)
    return make_element("link view-link w3-bar-item w3-button", i, tag="a")


def make_view():
    return make_element("view")


def make_entities():
    return make_element("entities")


def make_entity(eid, icon, name):
    name = make_element("entity-name", name)
    value = make_element("entity-value")
    name_value = make_element("entity-name-value", ( name, value ))
    icon = make_element("entity-icon", make_i(icon))
    entity = make_element(f"entity {ids.css(eid)}", (icon, name_value))
    return entity