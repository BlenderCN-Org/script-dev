# Author: Adhi Hargo (cadmus.sw@gmail.com)
# License: GPL v2

import bpy

class CameraAddTitleSafe(bpy.types.Operator):
    bl_idname = 'object.camera_add_title_safe'
    bl_label = 'Add Camera Title Safe'
    bl_options = {'REGISTER', 'UNDO'}
    
    frame_scale = bpy.props.FloatProperty(
        name = 'Frame Scale',
        default = 1.0,
        min = 0,
        max = 1.24,
        description = "Scale the frame against Blender's default",
        )

    def execute(self, context):
        if (not context.active_object or
            context.active_object.type != 'CAMERA'):
            return {'CANCELLED'}

        name_suffix = "titlesafe_frame"
        camera = context.active_object
        for o in camera.children:
            if o.name.endswith(name_suffix):
                return {'CANCELLED'}

        frame_name = "%s_%s" % (camera.name, name_suffix)
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

        drivers[0].expression = '((%(fs)s if rX > rY else %(fs)s * ((rX*arX) / (rY*arY))) * (35.0/fl)) / scX' % dict(fs = .365 * self.frame_scale)
        drivers[1].expression = '((%(fs)s if rY > rX else %(fs)s * ((rY*arY) / (rX*arX))) * (35.0/fl)) / scY' % dict(fs = .365 * self.frame_scale)
        drivers[2].expression = '1 / scale_z'

        camera.select = True
        frame.select = False
        context.scene.objects.active = camera

        return {'FINISHED'}

def register():
    bpy.utils.register_class(CameraAddTitleSafe)
    
register()
