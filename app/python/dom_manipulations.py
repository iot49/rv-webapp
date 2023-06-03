from pyscript import Element
from js import document, console
from datetime import datetime

from utilities import config, ids
from dom_factory import make_nav, make_view, make_entities, make_entity


_MSG_COUNT = 0

def message(msg):
    global _MSG_COUNT
    msg_div = document.createElement('div')
    msg_div.className = 'w3-code'
    dt = datetime.now().strftime("%H:%M:%S")
    msg_div.innerText = msg
    h_div = document.createElement('h4')
    h_div.innerText = f"[{_MSG_COUNT:04d}] {dt}"
    cont_div = document.createElement('div')
    cont_div.appendChild(h_div)
    cont_div.appendChild(msg_div)
    cont_div.className = 'w3-panel w3-card w3-light-grey'
    document.getElementById('messages').appendChild(cont_div)


def create_views():
    try:
        main_element = document.getElementById("main")
        nav_icons = document.getElementById("nav-icons")

        # remove all views & nav icons, in case create_views is called multiple times (configuration update)
        # note: getElementsByClassName does not reliably return all elements!
        for v in main_element.querySelectorAll(".view"):
            if v.parentNode == main_element:
                main_element.removeChild(v)
        for v in nav_icons.querySelectorAll(".view-link"):
            if v.parentNode == nav_icons:
                nav_icons.removeChild(v)

        views = config.get_views()
        for i, view in enumerate(reversed(views)):
            # view-1 is first view
            i = len(views)-i
            # add icon to navbar
            nav  = make_nav(view.get('icon', 'question_mark'))
            nav.id = f"nav-view-{i}"
            nav_icons.prepend(nav)

            # create view
            view_e = make_view()
            view_e.id = f"view-{i}"

            entities_e = make_entities()
            for eid in view.get('entities', []):
                entity_config = config.get_entity_config(eid)
                entity_e = make_entity(ids.css(eid), entity_config.get('icon', ''), entity_config.get('name', eid))
                entities_e.append(entity_e)

            # add entities
            view_e.append(entities_e)
            # add to main
            main_element.append(view_e)
    except Exception as e:
        console.log("***** create_views", str(e))


_CURRENT_PAGE = 'view-1'

def show_page(id: str, last_page=None) -> str:
    """Hide all pages (elements in main), except the one with the specified id.
    Returns id of previous page shown."""
    global _CURRENT_PAGE
    prev = _CURRENT_PAGE
    # console.log(f"SHOW_PAGE {id}")
    try:
        for page in document.getElementById("main").children:
            page.hidden = page.id != id
            # console.log(f"PAGE {page.id}.hidden = {page.hidden}")
        _CURRENT_PAGE = last_page or id
    except Exception as e:
        message(f"***** {show_page}: {e}")
    return prev