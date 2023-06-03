from js import document, window, console
import yaml, json

from utilities import config
from dom_manipulations import message, show_page
import gateway


def restore_config_event():

    async def restore_event(event=None):
        try:
            file_handles = await window.showOpenFilePicker()
        except Exception as e:
            console.log("***** restore_event", str(e))
            return
        if len(file_handles) < 1:
            console.log("NO FILE")
            return
        file = file_handles[0]
        try:
            content = await file.getFile()
            content = await content.text()
            content = yaml.safe_load(content)
            if content == None: content = {}
            console.log(f"FILE CONTENTS: '{content}'")
            await gateway.send({ "tag": "config_put", "value": content })
            console.log(f"FILE SENT")
        except Exception as e:
            console.log(f"***** restore_event: {e}")
        
    
    if not hasattr(window, 'showOpenFilePicker'):
        return    
    file_select = document.getElementById("restore-config")
    file_select.disabled = False
    try:
        file_select.onclick = restore_event
    except Exception as e:
        console.log(f"***** Add restore_event: {e}")


def backup_config_event(element_id, dumper):

    async def backup_event(event=None):
        try:
            file_handle = await window.showSaveFilePicker()
        except Exception as e:
            console.log("***** backup_event show", str(e))
            return
        
        content = dumper(config.get(), indent=4)

        try:
            file = await file_handle.createWritable()
            await file.write(content)
            await file.close()
        except Exception as e:
            console.log(f"***** backup_event write", str(e))

    if not hasattr(window, 'showSaveFilePicker'):
        return    
    file_save = document.getElementById(element_id)
    file_save.disabled = False
    try:
        file_save.onclick = backup_event
    except Exception as e:
        console.log(f"***** Add backup_event: {e}")


def configuration_editor_event():
    # TODO
    # popup to edit select configuration items, e.g.
    # wifi credentials, secret passcode, ...
    pass


def add_nav_events():
    # right side menu events
    configuration_editor_event()
    backup_config_event("backup-config", yaml.dump)
    backup_config_event("export-config", json.dumps)
    restore_config_event()
    if not config.get('app', 'release'):
        document.getElementById("export-config").classList.remove("hidden-link")
        document.getElementById("nav-terminal").classList.remove("hidden-link")


    def nav_event(event=None):
        if event == None:
            message("***** nav_event is None???")
        else:
            # drop the -nav prefix
            # console.log(f"EVENT target = {event.currentTarget.id[4:]}")
            show_page(event.currentTarget.id[4:])
            event.preventDefault()
    
    nav_icons = document.getElementById("nav-icons")
    for nav in nav_icons.querySelectorAll(".link"):
        try:
            nav.onclick = nav_event
        except Exception as e:
            console.log("***** Add nav: {e}")

    # nav_icons are hidden in index.html by default (at app startup)
    # now that the app is up, make them visible
    nav_icons.hidden = False
