import re

import imageio
import panda_gym
import gymnasium as gym
from gymnasium import wrappers
import time
import numpy as np
import imageio.v2 as iio
from Utils import clear_text
from slack_claude import Conversation
from panda_gym.utils import distance

class RobotPickPlaceArm(object):
    def __init__(self):
        self.env = gym.make('PandaPickAndPlace-v3', render_mode="rgb_array", renderer="OpenGL")
        self.frames = []
        # self.env = gym.wrappers.RecordVideo(self.env,video_folder='./video/')
        self.observation, info = self.env.reset()
        self.distance_threshold = 0.01
        self.gripper = -1
        # command patten
        self.pattern = r'move_to\((.*)\)|open_gripper\(\)|close_gripper\(\)|get_block_position\(' \
                       r'\)|get_goal_position\(\)|='

        # robot brain
        self.conversation = Conversation()

    def save_video(self):
        imageio.v2.mimwrite("result_" + str(time.time()) + ".mp4", self.frames)

    def get_block_position(self):
        pos = self.observation["achieved_goal"][0:3]
        x = pos[0]
        y = pos[1]
        z = pos[2]
        return x, y, z

    def get_goal_position(self):
        pos = self.observation["desired_goal"][0:3]
        x = pos[0]
        y = pos[1]
        z = pos[2]
        return x, y, z

    def move_to(self, x, y, z):
        while True:
            current_position = self.observation["observation"][0:3]
            desired_position = np.array([x, y, z])
            action = np.concatenate([5.0 * (desired_position - current_position), np.array([self.gripper])])

            self.frames.append(self.env.render())
            self.observation, reward, terminated, truncated, info = self.env.step(action)
            d = distance(current_position, desired_position)
            if np.array(d < self.distance_threshold, dtype=bool):
                break
            time.sleep(0.1)

    def close_gripper(self):
        if self.gripper == -1:
            return
        else:
            self.gripper = -1
            action = np.array([0, 0, 0, self.gripper])

            self.frames.append(self.env.render())
            self.observation, reward, terminated, truncated, info = self.env.step(action)

    def open_gripper(self):
        self.gripper = 1
        action = np.array([0, 0, 0, self.gripper])

        self.frames.append(self.env.render())
        self.observation, reward, terminated, truncated, info = self.env.step(action)

    def str_to_action(self, text):
        commands = clear_text(pattern=self.pattern, text=text)
        for command in commands:
            exec(command, {"move_to": self.move_to,
                           "open_gripper": self.open_gripper,
                           "close_gripper": self.close_gripper,
                           "get_block_position": self.get_block_position,
                           "get_goal_position": self.get_goal_position}, globals())
            print("executed command:", command)
            time.sleep(2)

    @staticmethod
    def main_prompt():

        manipulator_simple_robot = f"""
        Imagine we are working with a manipulator robot. This is a robotic arm that has a gripper attached to its end effector. The gripper is in the closed position in the beginning. I would like you to assist me in sending commands to this robot. At any point, you have access to the following functions. You are not to use any hypothetical functions.
        get_goal_position(): get the X, Y, Z coordinates of the goal.get_block_position(): get the X, Y, Z coordinates of the block. move_to(X,Y,Z): Given an X, Y, Z position, move the arm to that position. open_gripper(): Open the gripper close_gripper(): Close the gripper
        Note that before interacting with objects, you will have to figure out a safe position above the object (based on the height of the object) before using the gripper, so you don't knock the object away accidentally.
        The workspace contains single block placed on a table. Let us assume the block (tall is 0.02), so you have to figure out an appropriate safe height for the gripper based on the size of the object.
        I want you to give me code that drops the block into goal position
        """
        return manipulator_simple_robot

    def plan_exec(self):
        self.conversation.get_input(self.main_prompt())
        commands = self.conversation.get_bot_response_from_history(not_just_print=True)
        self.str_to_action(commands)


robot = RobotPickPlaceArm()
robot.plan_exec()
robot.save_video()
