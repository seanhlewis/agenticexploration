from direct.showbase.ShowBase import ShowBase
from panda3d.core import WindowProperties, Vec3, BitMask32
from panda3d.bullet import BulletWorld, BulletRigidBodyNode, BulletTriangleMesh, BulletTriangleMeshShape
from panda3d.bullet import BulletCharacterControllerNode, BulletCapsuleShape
from direct.showbase.InputStateGlobal import inputState
from panda3d.bullet import BulletDebugNode
from direct.gui.OnscreenText import OnscreenText
from panda3d.core import TextNode
from panda3d.core import PNMImage
import numpy as np
import socket
import pickle
import threading
import cv2

class FPSApp(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        # Disable the default camera controller
        self.disable_mouse()

        # Set up key controls
        self.accept("escape", self.do_exit)
        self.accept("space", self.do_jump)

        # Movement controls
        self.accept("w", self.set_key, ["forward", True])
        self.accept("w-up", self.set_key, ["forward", False])
        self.accept("s", self.set_key, ["backward", True])
        self.accept("s-up", self.set_key, ["backward", False])
        self.accept("a", self.set_key, ["left", True])
        self.accept("a-up", self.set_key, ["left", False])
        self.accept("d", self.set_key, ["right", True])
        self.accept("d-up", self.set_key, ["right", False])

        # Mouse control variables
        self.accept("mouse1", self.lock_mouse)
        self.accept("escape", self.unlock_mouse)
        self.mouse_locked = False
        self.pitch = 0
        self.yaw = 0
        self.mouse_sensitivity = 0.1

        # Set up the physics
        self.setup_physics()

        # Load the level and player
        self.load_level()
        self.create_player()

        # Camera follows the player
        self.camera.reparent_to(self.player_node)
        self.camera.set_pos(0, 0, 1.5)  # Adjust camera height

        # Camera FOV
        self.camLens.set_fov(90)  # Default FOV is 40; increase to make it wider

        # Update tasks
        self.task_mgr.add(self.update, 'update')
        self.task_mgr.add(self.update_physics, 'physics')
        self.task_mgr.add(self.update_info, "update_info")

        # Display instructions
        self.fps_text = OnscreenText(
            text="FPS: 0",
            pos=(-1.3, 0.9),  # Bottom-left corner
            scale=0.05,
            fg=(1, 1, 1, 1),  # White text
            align=TextNode.A_left,
            parent=self.aspect2d,
        )

        self.coords_text = OnscreenText(
            text="Pos: (0, 0, 0)",
            pos=(-1.3, 0.8),  # Slightly below the FPS
            scale=0.05,
            fg=(1, 1, 1, 1),
            align=TextNode.A_left,
            parent=self.aspect2d,
        )

        # Set up socket client
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect(('localhost', 12345))

        self.frame_counter = 0
        self.screenshot_interval = 10

        # Add the screenshot capture task
        self.task_mgr.add(self.capture_and_send_screenshot, 'CaptureScreenshotTask')

    def capture_and_send_screenshot(self, task):
        self.frame_counter += 1
        if self.frame_counter % self.screenshot_interval == 0:
            # Render the frame
            self.graphicsEngine.renderFrame()

            # Capture the display region
            dr = self.camNode.getDisplayRegion(0)
            tex = dr.getScreenshot()
            data = tex.getRamImage()

            # Convert to NumPy array
            array = np.array(memoryview(data), dtype=np.uint8)
            array = array.reshape((tex.getYSize(), tex.getXSize(), 4))  # 4 channels (RGBA)
            array = array[::-1, :, :3]  # Flip vertically and remove alpha channel

            # Process the screenshot
            # threading.Thread(target=self.process_screenshot, args=(array,)).start()
            self.process_screenshot(array)

        return task.cont

    def process_screenshot(self, array):
        try:
            # Compress the screenshot
            success, compressed = cv2.imencode('.jpg', array, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
            if success:
                # Serialize and add length prefix
                data = pickle.dumps(compressed)
                size = len(data).to_bytes(4, 'big')  # Length as 4 bytes (big-endian)

                # Send length prefix followed by data
                self.sock.sendall(size + data)
                print(f"Screenshot sent. Size: {len(data)} bytes")
            else:
                print("Error: Failed to compress the screenshot.")
        except Exception as e:
            print(f"Error sending screenshot: {e}")




    def setup_physics(self):
        """Set up the Bullet physics world."""
        self.physics_world = BulletWorld()
        self.physics_world.set_gravity(Vec3(0, 0, -9.81))

        # Add debug renderer
        debug_node = BulletDebugNode('Debug')
        debug_node.show_wireframe(True)
        self.debug_np = self.render.attach_new_node(debug_node)
        self.physics_world.set_debug_node(self.debug_np.node())

        # Optionally, show the debug renderer
        self.debug_np.show()

    def load_level(self):
        """Load the GLB model and create collision shapes."""
        # Load the model
        self.level_model = self.loader.load_model("de_dust_2_with_real_light.glb")
        self.level_model.reparent_to(self.render)
        
        self.level_model.set_scale(2.0)  # Scale up the model to twice its original size

        # Apply all transformations to the model
        self.level_model.flatten_strong()

        # self.level_model.set_scale(2.0)  # Scale up the model to twice its original size
        # self.level_model.set_hpr(0, 90, 0)  # Adjust as needed


        # Create collision mesh from the model
        mesh = BulletTriangleMesh()
        
        # Function to extract geometry
        def add_geom(node_path):
            for node in node_path.find_all_matches('**/+GeomNode'):
                geom_node = node.node()
                for geom in geom_node.get_geoms():
                    mesh.add_geom(geom)
        
        add_geom(self.level_model)
        
        # Create a collision shape and node
        shape = BulletTriangleMeshShape(mesh, dynamic=False)
        level_node = BulletRigidBodyNode('Level')
        level_node.add_shape(shape)
        level_node.set_into_collide_mask(BitMask32.bit(0))  # Set appropriate collision mask
        
        # Attach the collision node to the level model instead of render
        self.level_np = self.level_model.attach_new_node(level_node)
        self.physics_world.attach(level_node)

    def create_player(self):
        """Create the player character with a character controller."""
        # Create a capsule shape for the character
        height = 1.75
        radius = 0.4
        shape = BulletCapsuleShape(radius, height - 2 * radius)

        # Create the character controller
        char_controller = BulletCharacterControllerNode(shape, 0.4, 'Player')
        self.player_node = self.render.attach_new_node(char_controller)
        # self.player_node.set_collide_mask(BitMask32(0x1))  # Match level collision mask
        # self.player_node.set_into_collide_mask(BitMask32(0x1))  # Correct usage
        # self.player.set_from_collide_mask(BitMask32(0x1))  # Enable collisions with other objects
        self.player_node.set_collide_mask(BitMask32.bit(0))  # Player is a "from" object

        self.player_node.set_pos(50, 75, 10)  # Spawn position
        # self.player_node.set_hpr(90, 0, 0)    # Face left (90 degrees heading)
        self.physics_world.attach_character(char_controller)
        self.camera.set_hpr(90, 0, 0)  # Rotate the camera to face left

        # Movement variables
        self.speed = 5
        self.jump_speed = 5
        self.airborne = False

    def set_key(self, key, value):
        """Set the state of movement keys."""
        inputState.set(key, value)

    def do_exit(self):
        """Exit the application."""
        self.userExit()

    def do_jump(self):
        """Make the player jump."""
        if not self.airborne:  # Ensure the player is grounded
            self.player_node.node().do_jump()  # Trigger the jump
            self.airborne = True  # Mark the player as airborne


    def lock_mouse(self):
        """Lock the mouse to the window and hide the cursor."""
        print("Locking mouse")
        if not self.mouse_locked:
            print("Mouse locked")
            props = WindowProperties()
            props.set_cursor_hidden(True)
            props.set_mouse_mode(WindowProperties.M_relative)
            self.win.request_properties(props)
            self.mouse_locked = True

    def unlock_mouse(self):
        print("Unlocking mouse")
        """Unlock the mouse and show the cursor."""
        if self.mouse_locked:
            print("Mouse unlocked")
            props = WindowProperties()
            props.set_cursor_hidden(False)
            props.set_mouse_mode(WindowProperties.M_absolute)
            self.win.request_properties(props)
            self.mouse_locked = False

    def process_inputs(self, dt):
        """Process keyboard and mouse inputs."""
        # Mouse look
        if self.mouse_locked:
            md = self.win.get_pointer(0)
            delta_x = md.get_x() - self.win.get_x_size() // 2
            delta_y = md.get_y() - self.win.get_y_size() // 2

            # Update yaw and pitch based on mouse movement
            self.yaw -= delta_x * self.mouse_sensitivity
            self.pitch -= delta_y * self.mouse_sensitivity
            self.pitch = max(-90, min(90, self.pitch))  # Clamp pitch to [-90, 90]

            # Apply the rotation to the camera
            self.camera.set_hpr(self.yaw, self.pitch, 0)

            # Center the mouse cursor for relative movement
            self.win.move_pointer(0, self.win.get_x_size() // 2, self.win.get_y_size() // 2)

        # Movement
        walk_direction = Vec3(0, 0, 0)
        if inputState.is_set('forward'):
            walk_direction.y += 1
        if inputState.is_set('backward'):
            walk_direction.y -= 1
        if inputState.is_set('left'):
            walk_direction.x -= 1
        if inputState.is_set('right'):
            walk_direction.x += 1

        # Only move if there is input
        if walk_direction.length_squared() > 0:
            walk_direction.normalize()
            walk_direction *= self.speed

            # Transform the movement vector by the camera's rotation
            cam_quat = self.camera.get_quat(self.render)  # Get camera's orientation
            transformed_direction = cam_quat.xform(walk_direction)

            # Flatten movement to the XZ plane (disable vertical movement)
            transformed_direction.z = 0
            if transformed_direction.length_squared() > 0:
                transformed_direction.normalize()
                transformed_direction *= self.speed

            # Apply movement to the character
            self.player_node.node().set_linear_movement(transformed_direction, True)
        else:
            # Stop movement if no keys are pressed
            self.player_node.node().set_linear_movement(Vec3(0, 0, 0), True)

    def update(self, task):
        """Update task called every frame."""
        dt = globalClock.get_dt()

        self.process_inputs(dt)

        # Check if the player is on the ground
        result = self.physics_world.contact_test(self.player_node.node())
        self.airborne = True
        for contact in result.get_contacts():
            if contact.get_manifold_point().get_local_point_b().z < 0.1:
                self.airborne = False
                break

        return task.cont

    def update_physics(self, task):
        """Physics simulation task."""
        dt = globalClock.get_dt()
        self.physics_world.do_physics(dt, 10, 0.008)
        return task.cont
    
    def update_info(self, task):
        """Update FPS and player position."""
        # Update FPS
        fps = globalClock.get_average_frame_rate()
        self.fps_text.setText(f"FPS: {fps:.1f}")

        # Update player position
        player_pos = self.player_node.get_pos(self.render)
        self.coords_text.setText(f"Pos: ({player_pos.x:.1f}, {player_pos.y:.1f}, {player_pos.z:.1f})")

        return task.cont


app = FPSApp()
app.run()
