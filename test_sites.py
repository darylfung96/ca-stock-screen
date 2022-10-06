# Implementation of Selenium test automation for this Selenium Python Tutorial
import pytest
import sys
from time import sleep

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc


def test_lambdatest_todo_app():
	chrome_options = uc.ChromeOptions()
	chrome_options.add_argument("--disable-popup-blocking")
	chrome_options.add_argument("--incognito")
	chrome_driver = uc.Chrome(options=chrome_options)

	chrome_driver.get('https://www.tradingview.com/markets/stocks-canada/sectorandindustry-sector/')
	chrome_driver.maximize_window()

	market_cap = chrome_driver.find_elements(By.XPATH, "//div[@data-field='market_cap_basic']")
	assert len(market_cap) > 0

	sectors = chrome_driver.find_elements(By.XPATH, "//a[@rel='noopener']")
	assert len(sectors) > 0

	sectors_text = [sector.text for sector in sectors]
	sectors = [sector.get_attribute('href') for sector in sectors]
	sector = sectors[0]
	chrome_driver.get(sector)

	navigation_contents = chrome_driver.find_elements(By.CLASS_NAME, 'itemContent-RgmcRkjO')
	assert len(navigation_contents) > 0

	chrome_driver.close()