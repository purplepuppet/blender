import os
import bpy
import subprocess
from . import perforceUtils as p4utils
from bpy.types import Panel
from bpy.types import Operator, PropertyGroup
from bpy.props import IntProperty, BoolProperty, StringProperty, CollectionProperty, PointerProperty, EnumProperty
from bpy.app.handlers import persistent


bl_info = {
    "name": "PP_Tools",
    "description": "Purple Puppet Perforce Tools Addon.",
    "author": "Purple Puppet",
    "version": (1, 0, 0),
    "blender": (3, 3, 0),
    "location": "PP_Tools Panel",
    "wiki_url": "http://www.github.com"
}

currentClients = p4utils.getP4UserClients()

# UI Operators


class PPTOOLS_OT_p4Connect(Operator):
    """Connect to P4 server"""
    bl_idname = "pptools.connect"
    bl_label = "Connect"
    bl_description = "Connect to P4 server."
    p4utils.checkLogged()

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        global currentClients
        scn = bpy.context.scene
        pptools_settings = scn.pptools_settings

        try:
            subprocess.check_output(["p4", "set", "P4USER={}".format(pptools_settings.user)], shell=True)
            subprocess.check_output(["p4", "set", "P4PORT={}".format(pptools_settings.server)], shell=True)
            subprocess.check_output(["p4", "set", "P4CLIENT={}".format(pptools_settings.client)], shell=True)
            subprocess.check_output(["echo", "{}|".format(pptools_settings.password), "p4", "login"], shell=True)
        except:
            self.report({"ERROR"}, "Not logged")
            return {"FINISHED"}

        pptools_settings.logged = True
        currentClients = p4utils.getP4UserClients()

        clientsList = list()
        selectedIndex = 0
        for index, item in enumerate(currentClients[0]):
            clientsList.append(item[1])
            if item[1] == pptools_settings.client:
                selectedIndex = index

        pptools_settings.clients = str(selectedIndex)

        return {"FINISHED"}


class PPTOOLS_OT_p4Disconnect(Operator):
    """Connect to P4 server"""
    bl_idname = "pptools.disconnect"
    bl_label = "Disconnect"
    bl_description = "Disconnect to P4 server."
    p4utils.checkLogged()

    @classmethod
    def poll(cls, context):
        return True

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        scn = bpy.context.scene
        pptools_settings = scn.pptools_settings

        output = subprocess.check_output(["p4", "logout"], shell=True)
        pptools_settings.logged = False
        

        return {"FINISHED"}


class PPTOOLS_OT_p4setClient(Operator):
    """Switch to a new P4 client selected"""
    bl_idname = "pptools.set_client"
    bl_label = "Change the current client?"
    bl_description = "Set a new P4 Client."

    @classmethod
    def poll(cls, context):
        return True

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        scn = bpy.context.scene
        pptools_settings = scn.pptools_settings

        clientsList = list()
        for item in context.scene.pptools_settings.bl_rna.properties["clients"].enum_items:
            clientsList.append(item.name)
        selectedIndex = int(context.scene.pptools_settings.clients)
        selectedClient = clientsList[selectedIndex]

        subprocess.check_output(["p4", "set", "P4CLIENT={}".format(selectedClient)], shell=True)
        pptools_settings.client = selectedClient


        return {"FINISHED"}


# P4 Operators


class PPTOOLS_OT_addScene(Operator):
    bl_idname = "pptools.add_scene"
    bl_label = "Add File"
    bl_description = "Add the current scene in perforce."

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        if not p4utils.isVersioned(bpy.data.filepath):
            result = p4utils.addFile(bpy.data.filepath)
            if not result[0]:
                self.report({"ERROR"}, result[1])
                return {"FINISHED"}

            self.report({"INFO"}, result[1])
        else:
            self.report({"INFO"}, "The file is currently versioned.")
            return {"FINISHED"}

        return {"FINISHED"}


class PPTOOLS_OT_checkoutScene(Operator):
    bl_idname = "pptools.checkout_scene"
    bl_label = "Checkout File"
    bl_description = "Checkout the current file in perforce."

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        if not p4utils.isVersioned(bpy.data.filepath):
            self.report({"ERROR"}, "The file is not versioned in the current client.")
            return {"FINISHED"}

        sceneStatus = p4utils.fileStatus(bpy.data.filepath)
        if sceneStatus[0] != "free":
            if sceneStatus[0] == "error":
                self.report({"ERROR"}, sceneStatus[1])
            else:
                if sceneStatus[1].rpartition(": ")[-1] == p4utils.getP4User():
                    self.report({"INFO"}, "The scene was already checked out")
                else:
                    self.report({"ERROR"}, sceneStatus[1])
            return {"FINISHED"}

        result = p4utils.checkoutFile(bpy.data.filepath)
        if not result[0]:
            self.report({"ERROR"}, result[1])
            return {"FINISHED"}

        self.report({"INFO"}, "File was checked out.")

        return {"FINISHED"}


class PPTOOLS_OT_submitScene(Operator):
    bl_idname = "pptools.submit_scene"
    bl_label = "Submit File"

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        pptools_settings = context.scene.pptools_settings
        self.layout.prop(pptools_settings, "submitDesc")

    def execute(self, context):
        # Check if the file is versioned
        pptools_settings = context.scene.pptools_settings

        if not p4utils.isVersioned(bpy.data.filepath) and not p4utils.isAddMarked(bpy.data.filepath):
            self.report({"ERROR"}, "The file is not versioned in the current client.")
            return {"FINISHED"}

        sceneStatus = p4utils.fileStatus(bpy.data.filepath)
        if sceneStatus[0] == "blocked":
            if sceneStatus[1].rpartition(": ")[-1] == p4utils.getP4User():
                result = p4utils.submitFile(bpy.data.filepath, pptools_settings.submitDesc)
                if result:
                    self.report({"INFO"}, "The scene was submitted successfully.")
                else:
                    self.report({"ERROR"}, "There was a problem submitting the scene.")
                return {"FINISHED"}
            else:
                self.report({"ERROR"}, sceneStatus[1])
                return {"FINISHED"}
        else:
            self.report({"ERROR"}, "You don't have the scene checked out.")
            return {"FINISHED"}


class PPTOOLS_OT_isLatestVersion(Operator):
    bl_idname = "pptools.is_latest_version"
    bl_label = "Is Latest?"
    bl_description = "Check if the scene is in the latest version."

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        if not p4utils.isVersioned(bpy.data.filepath):
            self.report({"ERROR"}, "The file is not versioned in the current client.")
            return {"FINISHED"}

        if p4utils.isLatest(bpy.data.filepath):
            self.report({"INFO"}, "The scene is in the latest version.")
            return {"FINISHED"}
        else:
            self.report({"WARNING"}, "The scene is not in the latest version.")
            return {"FINISHED"}


class PPTOOLS_OT_getLatestVersion(Operator):
    bl_idname = "pptools.get_latest_version"
    bl_label = "Get Latest"
    bl_description = "Get the latest version of the current scene."

    @classmethod
    def poll(cls, context):
        return True

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        self.layout.label(text="You will override the current scene. Continue?")

    def execute(self, context):
        if not p4utils.isVersioned(bpy.data.filepath):
            self.report({"ERROR"}, "The file is not versioned in the current client.")
            return {"FINISHED"}

        if p4utils.isLatest(bpy.data.filepath):
            self.report({"WARNING"}, "The scene was already in the latest version.")
            return {"FINISHED"}

        if p4utils.getLatest(bpy.data.filepath):
            self.report({"INFO"}, "The latest version was downloaded. Please, reopen the scene.")
            return {"FINISHED"}
        else:
            self.report({"ERROR"}, "The latest version was not downloaded.")
            return {"FINISHED"}


class PPTOOLS_OT_revertScene(Operator):
    bl_idname = "pptools.revert_scene"
    bl_label = "Revert file"
    bl_description = "Revert the current scene."

    @classmethod
    def poll(cls, context):
        return True

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        self.layout.label(text="You will lost your current changes. Continue?")

    def execute(self, context):
        if not p4utils.isVersioned(bpy.data.filepath):
            self.report({"ERROR"}, "The file is not versioned in the current client.")
            return {"FINISHED"}

        if p4utils.revertFile(bpy.data.filepath):
            self.report({"INFO"}, "The scene was reverted to the latest version. Please, reopen it.")
            return {"FINISHED"}
        else:
            self.report({"ERROR"}, "The scene was not reverted.")
            return {"FINISHED"}


class PPTOOLS_OT_showinexplorer(Operator):
    bl_idname = "pptools.show_in_explorer"
    bl_label = "Show in Explorer"
    bl_description = "Open a windows explorer with the current scene"

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):

        if not os.path.exists(bpy.data.filepath):
            self.report({"ERROR"}, "Error: The scene path doesn't exists.")
            return {"FINISHED"}

        subprocess.call(r'explorer /select,"' + bpy.data.filepath.replace("/", "\\") + '"')

        return {"FINISHED"}



# Drawing


class PPTOOLS_PT_p4Tools(Panel):
    """Adds a custom panel to the TEXT_EDITOR"""
    bl_idname = 'PPTOOLS_PT_p4Tools'
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_label = "Perforce"
    bl_category = "Purple Puppet"
    bl_parent_id = "PURPLEPUPPET_TOOLS_PT_PANEL"

    def draw(self, context):
        layout = self.layout
        scn = bpy.context.scene
        pptools_settings = context.scene.pptools_settings

        row = layout.row()
        row.label(text="Purple Puppet")

        if pptools_settings.logged:
            row = layout.row()
            row.label(text="P4 Server: {}".format(pptools_settings.server))

            row = layout.row()
            row.prop(pptools_settings, "clients")

            row = layout.row()
            col = row.column()
            row.operator("pptools.disconnect")
            split = layout.split()

            row = layout.row()
            row = layout.row()
            row.operator("pptools.add_scene")
            row = layout.row()
            row.operator("pptools.checkout_scene")
            row = layout.row()
            row.operator("pptools.submit_scene")
            row = layout.row()
            row.operator("pptools.is_latest_version")
            row = layout.row()
            row.operator("pptools.get_latest_version")
            row = layout.row()
            row.operator("pptools.revert_scene")
            row = layout.row()
            row.operator("pptools.show_in_explorer")
        else:
            row = layout.row()
            row.label(text="P4 Server:")
            row = layout.row()
            row.prop(pptools_settings, "server", text="")

            row = layout.row()
            row.label(text="P4 Username:")
            row = layout.row()
            row.prop(pptools_settings, "user", text="")

            row = layout.row()
            row.label(text="P4 Client:")
            row = layout.row()
            row.prop(pptools_settings, "client", text="")

            row = layout.row()
            row.label(text="P4 Password:")
            row = layout.row()
            row.prop(pptools_settings, "password", text="")

            row = layout.row()
            row.operator("pptools.connect")

# Callbacks

def client_changed_callback(self, context):
    """Update the client when the current item changes"""
    global currentClients
    
    scn = bpy.context.scene
    pptools_settings = scn.pptools_settings

    clientsList = list()
    # context.scene.pptools_settings.bl_rna.properties["clients"].enum_items
    for item in currentClients[0]:
        clientsList.append(item[1])

    selectedIndex = int(context.scene.pptools_settings.clients)
    selectedClient = clientsList[selectedIndex]

    subprocess.check_output(["p4", "set", "P4CLIENT={}".format(selectedClient)], shell=True)
    pptools_settings.client = selectedClient
    
    return None


def clients_callback(scene, context):
    global currentClients

    if not currentClients:
        currentClients = p4utils.getP4UserClients()
    return currentClients[0]

@persistent
def load_handler(scene):
    global currentClients
    scn = bpy.context.scene
    pptools_settings = scn.pptools_settings
    
    pptools_settings.logged = p4utils.checkLogged()

    if not pptools_settings.logged:
        return
    
    clientsList = list()
    selectedIndex = 0
    clientToFind = p4utils.getP4Client()
    for index, item in enumerate(currentClients[0]):
        clientsList.append(item[1])
        if item[1] == clientToFind:
            selectedIndex = index

    pptools_settings.clients = str(selectedIndex)
    pptools_settings.server = p4utils.getP4Port()

# Collections

class PPTOOLS_pptoolsSettings(PropertyGroup):

    global currentClients

    server: StringProperty(
        name="Server",
        description="P4 Server",
        default=p4utils.getP4Port(),
        maxlen=200
    )
    user: StringProperty(
        name="User",
        description="P4 Username",
        default=p4utils.getP4User(),
        maxlen=200
    )
    client: StringProperty(
        name="Client",
        description="P4 Client",
        default=p4utils.getP4Client(),
        maxlen=200
    )
    clients: EnumProperty(
        name="Clients",
        description="P4 Clients Available",
        items=clients_callback,
        update=client_changed_callback,
        default=int(currentClients[1])
    )
    password: StringProperty(
        name="Password",
        description="P4 Password",
        default="",
        maxlen=200,
        subtype="PASSWORD"
    )
    logged: BoolProperty(
        name="Logged",
        description="If the user is currently logged",
        default=p4utils.checkLogged()
    )
    submitDesc: StringProperty(
        name="Description:"
    )


#  Register & Unregister


classes = (
    PPTOOLS_OT_p4Connect,
    PPTOOLS_OT_p4Disconnect,
    PPTOOLS_OT_p4setClient,
    PPTOOLS_OT_checkoutScene,
    PPTOOLS_OT_isLatestVersion,
    PPTOOLS_OT_getLatestVersion,
    PPTOOLS_OT_revertScene,
    PPTOOLS_OT_addScene,
    PPTOOLS_OT_submitScene,
    PPTOOLS_OT_showinexplorer,
    PPTOOLS_PT_p4Tools,
    PPTOOLS_pptoolsSettings
)


def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
    bpy.types.Scene.pptools_settings = PointerProperty(type=PPTOOLS_pptoolsSettings)
    bpy.app.handlers.load_post.append(load_handler)


def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
    bpy.app.handlers.load_post.remove(load_handler)


if __name__ == "__main__":
    register()
