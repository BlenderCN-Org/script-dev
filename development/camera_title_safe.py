# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# <pep8 compliant>
bl_info = {
    "name": "Camera Add Title Safe",
    "description": "Add Camera Title Safe: A Blender Python operator for adding a mesh-based title-safe frame to a 3D camera. The frame's size adjusts automatically to active scene's render resolution and aspect ratio, and is independent to the 3D camera's own scale.",
    "author": "Adhi Hargo, Aditia A. Pratama",
    "version": (0, 6),
    "blender": (2, 66,1),
    "location": "3D View > Tool Shelf (T-key) or press 'K' in 3D viewport", 
    "warning": "",
    "wiki_url": "https://github.com/aditiapratama/script-dev/wiki",
    "tracker_url": "https://github.com/aditiapratama/script-dev",
    "category": "3D View"}

import bpy

TITLESAFE_FRAME_SUFFIX = 'titlesafe_frame'

def draw_object_item(self, context):
    layout = self.layout
        
    layout.operator("object.camera_toggle_titlesafe_frame",
                    icon="OUTLINER_DATA_CAMERA")

class CameraPollMixin:

    @classmethod
    def poll(self, context):
        return context.active_object and context.active_object.type == 'CAMERA'

class VIEW3D_OT_toggle_titlesafe_frame(CameraPollMixin, bpy.types.Operator):
    '''Toggle title-safe frame'''
    bl_idname = 'object.camera_toggle_titlesafe_frame'
    bl_label = 'Toggle Camera Title Safe'
    bl_options = {'REGISTER', 'UNDO'}

    frame_scale = bpy.props.FloatProperty(
        name = 'Frame Scale',
        default = 1.0,
        min = 0,
        max = 1.24,
        description = "Scale the frame against Blender's default",
        )

    def execute(self, context):
        camera = context.active_object
        if not (camera and camera.type == 'CAMERA'):
            return {'CANCELLED'}

        if any(map(lambda x: x.name.endswith(TITLESAFE_FRAME_SUFFIX),
                   camera.children)):
            self.remove_titlesafe_frame(context, camera)
        else:
            self.create_titlesafe_frame(context, camera)

        return {'FINISHED'}

    def remove_titlesafe_frame(self, context, camera):
        for obj in camera.children:
            if obj.name.endswith(TITLESAFE_FRAME_SUFFIX):
                obj.name += "_deleted"
                context.scene.objects.unlink(obj)
                bpy.data.objects.remove(obj)

    def create_titlesafe_frame(self, context, camera):
        frame_name = "%s_%s" % (camera.name, TITLESAFE_FRAME_SUFFIX)
        frame_data = bpy.data.meshes.new(frame_name)
        frame_data.from_pydata([(-1, -1, -1), (-1, 1, -1),
                                (1, 1, -1), (1, -1, -1),
                                (-.99, -.99, -1), (-.99, .99, -1),
                                (.99, .99, -1), (.99, -.99, -1)],
                               [(0, 1), (1, 2), (2, 3), (3, 0),
                                # (4, 5), (5, 6), (6, 7), (7, 4),
                                # (0, 4), (1, 5), (2, 6), (3, 7)
                                ],
                               [# (0, 1, 5, 4), (1, 2, 6, 5),
                                # (2, 3, 7, 6), (3, 0, 4, 7)
                                ])
        frame = bpy.data.objects.new(frame_name, object_data = frame_data)
        context.scene.objects.link(frame)

        frame.parent = camera
        context.scene.update()
        frame.layers = camera.layers
        frame.hide_select = True
        frame.draw_type = 'WIRE'
        frame.lock_location = frame.lock_rotation = frame.lock_scale =\
            [True, True, True]

        fcurve_driver = frame.driver_add('scale')
        drivers = [f.driver for f in fcurve_driver]
        for d in drivers:
            var = d.variables.new()
            var.name = 'rX'
            target = var.targets[0]
            target.id_type = 'SCENE'
            target.id = context.scene
            target.data_path = 'render.resolution_x'

            var = d.variables.new()
            var.name = 'rY'
            target = var.targets[0]
            target.id_type = 'SCENE'
            target.id = context.scene
            target.data_path = 'render.resolution_y'

            var = d.variables.new()
            var.name = 'arX'
            target = var.targets[0]
            target.id_type = 'SCENE'
            target.id = context.scene
            target.data_path = 'render.pixel_aspect_x'

            var = d.variables.new()
            var.name = 'arY'
            target = var.targets[0]
            target.id_type = 'SCENE'
            target.id = context.scene
            target.data_path = 'render.pixel_aspect_y'

            var = d.variables.new()
            var.name = 'scX'
            target = var.targets[0]
            target.id_type = 'OBJECT'
            target.id = camera
            target.data_path = 'scale[0]'

            var = d.variables.new()
            var.name = 'scY'
            target = var.targets[0]
            target.id_type = 'OBJECT'
            target.id = camera
            target.data_path = 'scale[1]'
            
            var = d.variables.new()
            var.name = 'scale_z'
            target = var.targets[0]
            target.id_type = 'OBJECT'
            target.id = camera
            target.data_path = 'scale[2]'

            var = d.variables.new()
            var.name = 'fl'
            target = var.targets[0]
            target.id_type = 'CAMERA'
            target.id = camera.data
            target.data_path = 'lens'

        drivers[0].expression = '((%(fs)s if rX > rY '\
            'else %(fs)s * ((rX*arX) / (rY*arY))) * (35.0/fl)) / scX'\
            % dict(fs = .365 * self.frame_scale)
        drivers[1].expression = '((%(fs)s if rY > rX '\
            'else %(fs)s * ((rY*arY) / (rX*arX))) * (35.0/fl)) / scY'\
            % dict(fs = .411 * self.frame_scale)
        drivers[2].expression = '1 / scale_z'

        camera.select = True
        frame.select = False
        context.scene.objects.active = camera

class VIEW3D_PT_titlesafe(CameraPollMixin, bpy.types.Panel):
    bl_label = "Camera Tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"

    draw = draw_object_item
        
class VIEW3D_MT_titlesafe(CameraPollMixin, bpy.types.Menu):
    bl_label = "Camera Tools"
    
    draw = draw_object_item
        
        

addon_keymaps = []

def register():
    bpy.utils.register_module(__name__)
     
    wm = bpy.context.window_manager
    
    km = wm.keyconfigs.addon.keymaps.new(name='Object Mode', space_type='EMPTY')
    kmi = km.keymap_items.new('wm.call_menu', 'K', 'PRESS')
    kmi.properties.name = 'camera.tools_menu' 

    addon_keymaps.append(km)

def unregister():
    bpy.utils.unregister_module(__name__)
    
    wm = bpy.context.window_manager
    for km in addon_keymaps:
        wm.keyconfigs.addon.keymaps.remove(km)
    del addon_keymaps[:]
 
if __name__ == "__main__":
    register()
  
