import os
import bpy
from bpy.types import Panel
from bpy.types import Operator
from bpy.utils import previews
from . import perforce
from . import bl_info


custom_icons = bpy.utils.previews.new()


class PURPLEPUPPET_TOOLS_PT_PANEL(Panel):
    bl_idname = 'PURPLEPUPPET_TOOLS_PT_PANEL'
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_label = "Purple Puppet {}".format(".".join([str(x) for x in bl_info.get("version")]))
    bl_category = "Purple Puppet"

    def draw_header(self, context):
        layout = self.layout

        row = layout.row()
        row.label(
            text="",
            icon_value=custom_icons["purple_puppet_icon"].icon_id
        )

    def draw(self, context):
        layout = self.layout


classes = [
    PURPLEPUPPET_TOOLS_PT_PANEL
]


def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    perforce.register()

    custom_icons.load("purple_puppet_icon", os.path.join(os.path.dirname(__file__), "src", "img", "pplogo-icon_01_tiny.png"), 'IMAGE')


def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
    
    bpy.utils.previews.remove(custom_icons)

if __name__ == "__main__":
    register()
