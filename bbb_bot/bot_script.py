import argparse
import json
import logging
import signal
import subprocess
import time
import uuid

from bigbluebutton_api_python import BigBlueButton

from selenium import webdriver
from selenium.webdriver import ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait

logger = logging.getLogger()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--bot", metavar="name", default=uuid.uuid4())

    parser.add_argument("--meeting-id", required=True,
                        help="ID of BBB Meeting")
    parser.add_argument("--meeting-password",
                        help="Password of BBB Meeting")

    parser.add_argument("--bbb-url", required=True,
                        help="BBB's url (see `bbb-conf --secret`)")
    parser.add_argument("--bbb-secret", required=True,
                        help="BBB's shared secret (see `bbb-conf --secret`)")

    parser.add_argument("--use-microphone", action="store_true",
                        help="Use chromium's fake device flag to send clicking noises.")
    parser.add_argument("--join-params", default={}, type=json.loads,
                        help="Additional bbb join link parameters as json")

    parser.add_argument("--log-level", default="INFO",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(level=args.log_level)
    if args.log_level == "DEBUG":
        logging.getLogger("selenium").setLevel(logging.INFO)
        logging.getLogger("urllib3").setLevel(logging.INFO)

    # Create bbb join link
    bbb = BigBlueButton(args.bbb_url, args.bbb_secret)
    if not args.meeting_password:
        logger.debug("Retrieving attendee password...")
        args.meeting_password = bbb.get_meeting_info(args.meeting_id).get_meetinginfo().get_attendeepw()
    link = bbb.get_join_meeting_url(
        f"Bot {args.bot}",
        meeting_id=args.meeting_id,
        password=args.meeting_password,
        params=args.join_params
    )
    logger.debug(f"Generated join url: {link}")

    # Test pulseaudio
    for i in range(3):
        p = subprocess.run("pulseaudio --check", shell=True)
        if p.returncode != 0:
            logger.error("Pulseaudio hasn't started yet. Starting it")
            subprocess.run("pulseaudio --kill", shell=True)
            subprocess.run("pulseaudio -D", shell=True)
        else:
            logger.info("Pulseaudio is already running.")
            break

    # Open browser and link
    options = ChromeOptions()
    options.headless = True
    options.add_argument("--use-fake-ui-for-media-stream")  # Don't ask for microphone permissions
    options.add_argument("--use-fake-device-for-media-stream")  # Send random click noises to microphone
    browser = webdriver.Chrome(options=options)
    logger.debug("Started selenium")
    browser.get(link)

    # Little shorthand function
    def wait_for_xpath(xpath, timeout=60):
        WebDriverWait(browser, timeout).until(expected_conditions.visibility_of_element_located((By.XPATH, xpath)))

    # Joining audio
    logger.debug("Waiting for audio modal...")
    wait_for_xpath("//button[@aria-label='Close Join audio modal']")

    if args.use_microphone:
        logger.debug("Clicking 'Microphone'...")
        browser.find_element(by=By.XPATH, value="//button[@aria-label='Microphone']").click()

        logger.debug("Waiting for echo test...")
        wait_for_xpath("//button[@aria-label='Echo is audible']")

        logger.debug("Clicking 'Echo is audible'...")
        browser.find_element(by=By.XPATH, value="//button[@aria-label='Echo is audible']").click()

    else:
        logger.debug("Clicking 'Listen only'...")
        browser.find_element(by=By.XPATH, value="//button[@aria-label='Listen only']").click()

    logger.info(f"Joined meeting '{args.meeting_id}' as '{args.bot}' with {'microphone' if args.use_microphone else 'audio'}")

    # Sleep on main thread
    try:
        logger.debug("Going to sleep until SIGTERM")
        while True:
            time.sleep(1000)

    except KeyboardInterrupt:
        logger.debug("Got SIGTERM")

    # Cleanup and quit
    browser.quit()
    logger.debug("Closed selenium")


def sigterm2sigint(_signal, _frame):
    raise KeyboardInterrupt


if __name__ == '__main__':
    signal.signal(signal.SIGTERM, sigterm2sigint)
    main()
