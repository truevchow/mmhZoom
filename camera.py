import math
import logging
import numpy as np
import time

# unfortunately, OpenCV is incompatible with PyQt5, so pyfakewebcam will suffer degraded performance
#import cv2
import pygame
import pygame.camera

pygame.init()
pygame.camera.init()

import pyfakewebcam

num_seconds = 120
fps = 30.0
frame_delay = 1 / fps

num_frames = math.ceil(fps * num_seconds)
skip_frames = 10
freeze_frames = round(fps * 1)

class InputCamera:
    pass

class RealCamera(InputCamera):
    def __init__(self, device_id, size = (640,480)):
        if device_id is None: device_id = RealCamera.get_default_device()
        self.size = size
        self.device_id = device_id

        # create a display surface. standard pygame stuff
        #self.display = pygame.display.set_mode(self.size, 0)

    @staticmethod
    def get_devices():
        devices = pygame.camera.list_cameras()
        return devices

    @staticmethod
    def get_default_device():
        devices = RealCamera.get_cameras()
        if len(devices) == 0:
            raise ValueError("No camera available")
        return devices[0]

    def read(self):
        # https://stackoverflow.com/questions/39003106/python-access-camera-without-opencv?noredirect=1&lq=1
        frame : pygame.Surface = self.vid.get_image()
        frame : np.array = pygame.surfarray.array3d(frame) # slow :(

        #ret, frame = self.vid.read()
        #if not ret: return None

        return frame

        #rgb_frame = frame[:,:,[2,1,0]] # BGR to RGB color conversion
        #return rgb_frame

    def skip(self, n_frames):
        for i in range(n_frames):
            self.vid.read()

    def __enter__(self): 
        self.vid = pygame.camera.Camera(self.device_id, self.size)
        self.vid.start()

        # create a surface to capture to.  for performance purposes
        # bit depth is the same as that of the display surface.
        #self.snapshot = pygame.surface.Surface(self.size, 0, self.display)

        #self.vid: VideoCapture = cv2.VideoCapture(self.device_id)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.vid.stop()
        #self.vid.release() # OpenCV

class OutputCamera:
    @staticmethod
    def find_output_video_device():
        return '/dev/video2' # TODO: dynamically allocate device

    def __init__(self, device_id = None, size = (640,480)):
        self.size = size

        if device_id is None:
            device_id = OutputCamera.find_output_video_device()

        self.device_id = device_id

    def __enter__(self):
        self.vid = pyfakewebcam.FakeWebcam(self.device_id, self.size[0], self.size[1])
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.vid.release()

    def write(self, frame: np.array):
        self.vid.schedule_frame(np.transpose(frame, (1,0,2)))

class VideoLooper:
    def __init__(self, input_camera: InputCamera, output_camera: OutputCamera):
        self.input_camera = input_camera
        self.output_camera = output_camera

    def read_frames(self):
        yield self.input_camera.read()

    #def loop(self):
    #    while True:
    #        for frame in self.read_frames():
    #            if frame is not None:
    #                self.output_camera.write(frame)
    #            time.sleep(frame_delay)

    def loop(self):
        going = True
        while going:
            events = pygame.event.get()
            #for e in events:
            #    if e.type == QUIT or (e.type == KEYDOWN and e.key == K_ESCAPE):
            #        # close the camera safely
            #        self.cam.stop()
            #        going = False
            for frame in self.read_frames():
                if frame is not None:
                    self.output_camera.write(frame)
                time.sleep(frame_delay)


if __name__ == "__main__":
    with RealCamera("/dev/video0") as input_cam:
        with OutputCamera() as output_cam:
            VideoLooper(input_cam, output_cam).loop()