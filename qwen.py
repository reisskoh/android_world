"""
Run a single "Add Contact" task in AndroidWorld for experimental purposes.
"""

import argparse
import base64
import logging
import os
import pickle

from dotenv import dotenv_values, load_dotenv
from openai import OpenAI

from android_world.agents import infer, t3a
from android_world.env import env_launcher
from android_world.env.interface import AsyncEnv
from android_world.task_evals.single.contacts import ContactsAddContact
from android_world.task_evals.single.system import SystemWifiTurnOnVerify
from run import _find_adb_directory


def encode_image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


class OpenAIWrapper:
    def __init__(self):
        self.client = OpenAI(
            api_key=dotenv_values()["OPENAI_API_KEY"],
        )

    def predict(self, prompt: str) -> str:
        response = self.client.responses.create(
            model="gpt-5-mini",
            reasoning={"effort": "minimal"},
            input=[{"role": "user", "content": prompt}],
        )
        return response.output_text, None, response


class OpenRouterWrapper:
    def __init__(self, model: str):
        self.model = model
        self.client = OpenAI(
            api_key=dotenv_values()["OPENROUTER_API_KEY"],
            base_url="http://localhost:8080/v1",
        )

    def predict(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content, None, response


def setup_environment(
    console_port: int, emulator_setup: bool, adb_path: str
) -> AsyncEnv:
    """Initializes and returns the AndroidWorld environment."""
    os.environ["GRPC_VERBOSITY"] = "ERROR"
    os.environ["GRPC_TRACE"] = "none"

    logging.getLogger().setLevel(logging.ERROR)

    env = env_launcher.load_and_setup_env(
        console_port=console_port,
        emulator_setup=emulator_setup,
        adb_path=adb_path,
    )
    env.reset(go_home=True)
    return env


def run_task(env) -> None:
    """Runs the ContactsAddContact task once using Tri + GPT-5 agent."""
    task_type = ContactsAddContact
    params = task_type.generate_random_params()
    task = task_type(params)
    task.initialize_task(env)

    agent = t3a.T3A(env, OpenRouterWrapper("Qwen/Qwen3-VL-235B-A22B-Instruct-FP8"))
    max_steps = int(task.complexity * 10)

    print(f"🎯 Goal: {task.goal}")

    for _ in range(max_steps):
        response = agent.step(task.goal)

        if response.done:
            break

    success = task.is_successful(env) == 1
    print(f"{'✅ Task Successful' if success else '❌ Task Failed'} — {task.goal}")

    env.close()


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run AndroidWorld ContactsAddContact task."
    )
    parser.add_argument(
        "--adb-path", default=_find_adb_directory(), help="Path to adb binary."
    )
    parser.add_argument(
        "--setup",
        action="store_true",
        help="Perform emulator setup (only required once).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5554,
        help="Console port of the running Android device (default: 5554).",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    env = setup_environment(args.port, args.setup, args.adb_path)
    run_task(env)


if __name__ == "__main__":
    main()






